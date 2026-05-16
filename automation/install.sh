#!/usr/bin/env bash
# Install jessetek automation on this Mac.
# Renders launchd plists with absolute paths, copies them to ~/Library/LaunchAgents,
# and bootstraps them. Idempotent — safe to re-run after updates.

set -euo pipefail

AUTOMATION_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$AUTOMATION_DIR/.." && pwd)"
SCRIPTS_DIR="$AUTOMATION_DIR/scripts"
LOGS_DIR="$AUTOMATION_DIR/logs"
GEN_DIR="$AUTOMATION_DIR/launchd/generated"
TPL_DIR="$AUTOMATION_DIR/launchd"
LAUNCH_AGENTS="$HOME/Library/LaunchAgents"

LABELS=(
  "net.jessetek.daily-health-check"
  "net.jessetek.weekly-rank-watch"
  "net.jessetek.weekly-qc-sweep"
  "net.jessetek.weekly-clarity-review"
  "net.jessetek.monthly-rate-watch"
  "net.jessetek.monthly-date-refresh"
  "net.jessetek.quarterly-perf-audit"
  "net.jessetek.quarterly-city-stats"
  "net.jessetek.quarterly-seo-scan"
)

# Map label → script. Keep aligned with LABELS above.
declare -a SCRIPTS=(
  "$SCRIPTS_DIR/run-daily-health-check.sh"
  "$SCRIPTS_DIR/run-weekly-rank-watch.sh"
  "$SCRIPTS_DIR/run-weekly-qc-sweep.sh"
  "$SCRIPTS_DIR/run-weekly-clarity-review.sh"
  "$SCRIPTS_DIR/run-monthly-rate-watch.sh"
  "$SCRIPTS_DIR/run-monthly-date-refresh.sh"
  "$SCRIPTS_DIR/run-quarterly-perf-audit.sh"
  "$SCRIPTS_DIR/run-quarterly-city-stats.sh"
  "$SCRIPTS_DIR/run-quarterly-seo-scan.sh"
)

# Event-driven wrapper scripts (no plist — invoked manually with argv).
EVENT_SCRIPTS=(
  "$SCRIPTS_DIR/run-new-review.sh"
  "$SCRIPTS_DIR/run-new-city-page.sh"
  "$SCRIPTS_DIR/run-sentry-error.sh"
)

say() { printf '\033[1;36m▸\033[0m %s\n' "$*"; }
warn() { printf '\033[1;33m⚠\033[0m %s\n' "$*"; }
fail() { printf '\033[1;31m✘\033[0m %s\n' "$*" >&2; exit 1; }

# --- Sanity checks ------------------------------------------------------
[ -d "$PROJECT_ROOT/.git" ] || fail "$PROJECT_ROOT is not a git repo. Aborting."
[ -d "$SCRIPTS_DIR" ]       || fail "Missing scripts dir: $SCRIPTS_DIR"
[ -d "$TPL_DIR" ]           || fail "Missing launchd templates dir: $TPL_DIR"

say "Project root:  $PROJECT_ROOT"
say "User:          $(whoami)"
say "LaunchAgents:  $LAUNCH_AGENTS"

mkdir -p "$LOGS_DIR" "$GEN_DIR" "$LAUNCH_AGENTS"

# --- Make scripts executable -------------------------------------------
say "chmod +x scripts"
chmod +x "$SCRIPTS_DIR"/*.sh

# --- Verify claude CLI present -----------------------------------------
if ! command -v claude >/dev/null 2>&1; then
  warn "\`claude\` CLI not on PATH."
  warn "Install with: npm install -g @anthropic-ai/claude-code"
  warn "Then run \`claude\` once to authenticate before scheduled runs fire."
else
  say "claude:        $(command -v claude)"
fi

# --- Verify python3 + pillow (needed for OG image generation) ----------
if ! command -v python3 >/dev/null 2>&1; then
  warn "python3 not on PATH (needed for monthly Rate Watch OG images)."
elif ! python3 -c 'import PIL' >/dev/null 2>&1; then
  warn "Pillow not installed. Run: pip3 install --user pillow"
fi

# --- Render plists with absolute paths ---------------------------------
say "Rendering plists into $GEN_DIR"
for i in "${!LABELS[@]}"; do
  label="${LABELS[$i]}"
  script="${SCRIPTS[$i]}"
  tpl="$TPL_DIR/${label}.plist.template"
  out="$GEN_DIR/${label}.plist"

  [ -f "$tpl" ]    || fail "Missing template: $tpl"
  [ -f "$script" ] || fail "Missing script: $script"

  sed \
    -e "s|__SCRIPT__|${script}|g" \
    -e "s|__PROJECT_ROOT__|${PROJECT_ROOT}|g" \
    -e "s|__LOG_DIR__|${LOGS_DIR}|g" \
    "$tpl" > "$out"

  # Validate plist
  if ! plutil -lint "$out" >/dev/null; then
    fail "plutil rejected $out"
  fi
done

# --- Bootstrap into launchd --------------------------------------------
say "Loading agents (will replace any existing)"
for label in "${LABELS[@]}"; do
  src="$GEN_DIR/${label}.plist"
  dst="$LAUNCH_AGENTS/${label}.plist"

  cp "$src" "$dst"

  # Bootout first to clear any prior version, then bootstrap fresh.
  launchctl bootout "gui/$(id -u)/${label}" 2>/dev/null || true
  if launchctl bootstrap "gui/$(id -u)" "$dst"; then
    say "  loaded $label"
  else
    fail "  failed to bootstrap $label"
  fi
done

# --- Confirm registration ----------------------------------------------
say "Registered jobs:"
for label in "${LABELS[@]}"; do
  if launchctl print "gui/$(id -u)/${label}" >/dev/null 2>&1; then
    printf '  ✓ %s\n' "$label"
  else
    printf '  ✘ %s (NOT registered)\n' "$label"
  fi
done

# --- Helpful next-steps notes ------------------------------------------
cat <<EOF

Done.

Next steps:
  1. If you haven't authenticated the claude CLI on this machine yet, run:
       claude
     and complete login. Scheduled runs use the cached auth.

  2. (Optional) Copy config.local.example.sh to config.local.sh and adjust:
       cp "$AUTOMATION_DIR/config.local.example.sh" "$AUTOMATION_DIR/config.local.sh"

  3. Test a run manually right now (does NOT modify files):
       DRY_RUN=1 "$SCRIPTS_DIR/run-daily-health-check.sh"
       tail -n 50 "$LOGS_DIR"/daily-health-check-*.log | tail -n 50

  4. Force a real run on demand (any time):
       launchctl kickstart -k "gui/\$(id -u)/net.jessetek.daily-health-check"

  5. Watch the logs:
       ls -lt "$LOGS_DIR"
       tail -f "$LOGS_DIR/_failures.log"

Schedule (local time):
  • daily-health-check     every day,     08:00
  • weekly-rank-watch      Mondays,       07:30
  • weekly-qc-sweep        Mondays,       09:00
  • weekly-clarity-review  Fridays,       14:00
  • monthly-rate-watch     1st of month,  10:00
  • monthly-date-refresh   15th of month, 11:00
  • quarterly-perf-audit   Jan/Apr/Jul/Oct  1, 13:00
  • quarterly-city-stats   Jan/Apr/Jul/Oct  5, 13:00
  • quarterly-seo-scan     Jan/Apr/Jul/Oct 10, 13:00

Event-driven wrappers (run manually with argv, not scheduled):
  • run-new-review.sh      "Maria S." "Long Beach" "2 weeks ago" 5 "..."
  • run-new-city-page.sh   "Tustin" "Orange County" "92780,92782" '\$1.2M' 28 80000
  • run-sentry-error.sh    < sentry-payload.txt    (or pbpaste | ...)

To uninstall:  $AUTOMATION_DIR/uninstall.sh
EOF
