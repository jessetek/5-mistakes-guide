#!/usr/bin/env bash
# Shared library for jessetek automation runners.
# Sourced by every run-*.sh script. Exports env, defines logging + locking helpers.
# Do not run directly.

set -euo pipefail

# --- Paths ---------------------------------------------------------------
# SCRIPT_DIR = .../landing-page/automation/scripts
# AUTOMATION_DIR = .../landing-page/automation
# PROJECT_ROOT = .../landing-page
# Resolve this file's dir under bash (BASH_SOURCE) OR zsh ($0). The launchd jobs run
# via /bin/zsh because /bin/bash is TCC-blocked from ~/Documents on this Mac.
if [ -n "${BASH_SOURCE:-}" ]; then _common_self="${BASH_SOURCE[0]}"; else _common_self="$0"; fi
SCRIPT_DIR="$(cd "$(dirname "$_common_self")" && pwd)"
AUTOMATION_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
PROJECT_ROOT="$(cd "$AUTOMATION_DIR/.." && pwd)"

PROMPTS_DIR="$AUTOMATION_DIR/prompts"
LOGS_DIR="$AUTOMATION_DIR/logs"
LOCKS_DIR="$AUTOMATION_DIR/.locks"
STATE_DIR="$AUTOMATION_DIR/.state"

mkdir -p "$LOGS_DIR" "$LOCKS_DIR" "$STATE_DIR"

# --- launchd doesn't inherit PATH; bake in the common locations ---------
export PATH="/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin:$HOME/.npm-global/bin:$HOME/.local/bin:$PATH"

# --- Optional config override -------------------------------------------
# Per-machine settings live in automation/config.local.sh (not committed).
# Lets you override CLAUDE_BIN, NOTIFY_EMAIL, etc. per Mac.
if [ -f "$AUTOMATION_DIR/config.local.sh" ]; then
  # shellcheck disable=SC1091
  . "$AUTOMATION_DIR/config.local.sh"
fi

# --- Defaults (overridable via config.local.sh) -------------------------
: "${CLAUDE_BIN:=claude}"
: "${CLAUDE_MODEL:=}"           # empty = use Claude Code default
: "${LOG_RETENTION_DAYS:=30}"
: "${NOTIFY_ON_FAILURE:=1}"     # 0 to disable macOS notifications
: "${DRY_RUN:=0}"

# --- Logging helpers -----------------------------------------------------
TASK_NAME="${TASK_NAME:-task}"
RUN_TS="$(date +%Y-%m-%d_%H-%M-%S)"
LOG_FILE="$LOGS_DIR/${TASK_NAME}-${RUN_TS}.log"

log() {
  printf '[%s] %s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$*" | tee -a "$LOG_FILE" >&2
}

# --- Lock helpers (prevent overlapping runs) ----------------------------
LOCK_FILE="$LOCKS_DIR/${TASK_NAME}.lock"

acquire_lock() {
  if [ -e "$LOCK_FILE" ]; then
    local existing_pid
    existing_pid="$(cat "$LOCK_FILE" 2>/dev/null || echo '')"
    if [ -n "$existing_pid" ] && kill -0 "$existing_pid" 2>/dev/null; then
      log "ABORT: previous $TASK_NAME run still active (pid $existing_pid)"
      exit 0
    fi
    log "stale lock from pid $existing_pid, removing"
    rm -f "$LOCK_FILE"
  fi
  echo "$$" > "$LOCK_FILE"
}

release_lock() {
  rm -f "$LOCK_FILE"
}

# --- Notification on failure --------------------------------------------
notify_failure() {
  local exit_code="$1"
  local msg="${TASK_NAME} failed (exit $exit_code). See $LOG_FILE"
  log "FAIL: $msg"
  if [ "$NOTIFY_ON_FAILURE" = "1" ] && command -v osascript >/dev/null 2>&1; then
    osascript -e "display notification \"$msg\" with title \"jessetek automation\" sound name \"Basso\"" >/dev/null 2>&1 || true
  fi
  # Append to a single rolling failures log so you can grep history fast
  printf '[%s] %s — exit %s — log %s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$TASK_NAME" "$exit_code" "$LOG_FILE" \
    >> "$LOGS_DIR/_failures.log"
}

# --- Log rotation --------------------------------------------------------
rotate_logs() {
  find "$LOGS_DIR" -type f -name '*.log' -mtime "+${LOG_RETENTION_DAYS}" -delete 2>/dev/null || true
}

# --- Pre-flight: are we able to run? ------------------------------------
preflight() {
  if ! command -v "$CLAUDE_BIN" >/dev/null 2>&1; then
    log "ABORT: \`$CLAUDE_BIN\` not on PATH. Install Claude Code or set CLAUDE_BIN in config.local.sh"
    exit 78  # EX_CONFIG
  fi
  if [ ! -d "$PROJECT_ROOT/.git" ]; then
    log "ABORT: $PROJECT_ROOT is not a git repo"
    exit 78
  fi
  if ! command -v git >/dev/null 2>&1; then
    log "ABORT: git not on PATH"
    exit 78
  fi
}

# --- Run a prompt non-interactively through Claude Code -----------------
# Args: <prompt-file>
# Pipes stdin → claude -p, appends transcript to LOG_FILE, returns claude's exit code.
run_claude_prompt() {
  local prompt_file="$1"
  if [ ! -f "$prompt_file" ]; then
    log "ABORT: prompt file missing: $prompt_file"
    return 66  # EX_NOINPUT
  fi

  # Substitute __PROJECT_ROOT__ plus any caller-provided RENDER_VARS.
  # RENDER_VARS is an associative array of TOKEN→VALUE the event wrappers
  # populate before calling standard_run. Token form is __NAME__ (no array
  # entry needed for PROJECT_ROOT — always substituted).
  local rendered_prompt
  rendered_prompt="$(cat "$prompt_file")"
  rendered_prompt="${rendered_prompt//__PROJECT_ROOT__/$PROJECT_ROOT}"
  if [ -n "${RENDER_VARS_KEYS:-}" ]; then
    local k v
    for k in $RENDER_VARS_KEYS; do
      v="${!k:-}"
      rendered_prompt="${rendered_prompt//__${k}__/$v}"
    done
  fi
  # Bail loudly if any tokens remain unfilled — better than silently shipping
  # a prompt with literal __FOO__ in it.
  local leftover
  leftover="$(printf '%s' "$rendered_prompt" | grep -oE '__[A-Z][A-Z0-9_]+__' | sort -u | head -5 || true)"
  if [ -n "$leftover" ]; then
    log "ABORT: unfilled prompt tokens: $leftover"
    return 65  # EX_DATAERR
  fi

  log "===== $TASK_NAME starting ====="
  log "PROJECT_ROOT=$PROJECT_ROOT"
  log "CLAUDE_BIN=$CLAUDE_BIN"
  log "prompt=$prompt_file"

  if [ "$DRY_RUN" = "1" ]; then
    log "DRY_RUN=1 — skipping claude invocation"
    log "----- rendered prompt would be: -----"
    # Prefix every line so RESULT lines inside the prompt don't get picked up
    # by print_result_line later.
    printf '%s\n' "$rendered_prompt" | sed 's/^/> /' >> "$LOG_FILE"
    log "----- end rendered prompt -----"
    # Synthesize a fake RESULT line so the dry-run smoke test reports cleanly.
    printf 'RESULT: DRY_RUN_OK\n' >> "$LOG_FILE"
    log "===== $TASK_NAME finished (dry run) ====="
    return 0
  fi

  # Run from the project root so any relative paths in the prompt resolve.
  cd "$PROJECT_ROOT"

  # Build claude argv. --dangerously-skip-permissions is required for
  # unattended autonomous runs (no human present to approve tool calls).
  # If you'd rather the daily health check stay restricted, set
  # CLAUDE_EXTRA_ARGS in config.local.sh per task.
  local claude_args=(-p --dangerously-skip-permissions)
  if [ -n "$CLAUDE_MODEL" ]; then
    claude_args+=(--model "$CLAUDE_MODEL")
  fi
  if [ -n "${CLAUDE_EXTRA_ARGS:-}" ]; then
    # shellcheck disable=SC2206
    local extra=( $CLAUDE_EXTRA_ARGS )
    claude_args+=("${extra[@]}")
  fi

  set +e
  printf '%s' "$rendered_prompt" | "$CLAUDE_BIN" "${claude_args[@]}" >> "$LOG_FILE" 2>&1
  local rc=$?
  set -e

  log "===== $TASK_NAME finished (claude exit $rc) ====="
  return "$rc"
}

# --- Tail the RESULT line from the log so it shows up in launchd output --
print_result_line() {
  local result
  result="$(grep -E '^RESULT: ' "$LOG_FILE" | tail -n 1 || true)"
  if [ -n "$result" ]; then
    printf '%s\n' "$result"
  else
    printf 'RESULT: UNKNOWN (no RESULT line found in log)\n'
  fi
}

# --- Standard runner: call this from each run-*.sh ----------------------
# Args: <prompt-filename-without-extension>
standard_run() {
  local prompt_name="$1"
  local prompt_file="$PROMPTS_DIR/${prompt_name}.txt"

  trap 'rc=$?; notify_failure "$rc"; release_lock; exit "$rc"' ERR
  trap 'release_lock' EXIT

  rotate_logs
  acquire_lock
  preflight

  if run_claude_prompt "$prompt_file"; then
    print_result_line
    log "OK"
  else
    rc=$?
    print_result_line
    notify_failure "$rc"
    return "$rc"
  fi
}
