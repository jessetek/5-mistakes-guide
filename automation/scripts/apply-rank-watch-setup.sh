#!/usr/bin/env bash
# One-shot setup for the new weekly-rank-watch task.
# Idempotent — safe to re-run. Does not require the legacy /Jtek website/
# folder to be mounted; if it's reachable it migrates the existing GSC creds,
# otherwise it tells you to run setup-gsc-oauth.mjs interactively.
#
# Steps:
#   1. Migrate GSC_* creds from the legacy .env.local (if present) into the
#      canonical /Jessetek/.env (creates the file if missing).
#   2. Run install.sh to register the new launchd job.
#   3. Smoke-test get-gsc-rank.mjs.
#   4. Print the kickstart command to test a real run on demand.

set -uo pipefail

# --- Paths --------------------------------------------------------------
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
AUTOMATION_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
PROJECT_ROOT="$(cd "$AUTOMATION_DIR/.." && pwd)"
JESSETEK_DIR="$(cd "$PROJECT_ROOT/.." && pwd)"
ENV_FILE="$JESSETEK_DIR/.env"
LEGACY_ENV="$HOME/Library/Mobile Documents/com~apple~CloudDocs/Documents/Documents - JtekMac/Claude Code/Jtek website/instagram-stories/.env.local"

ok()   { printf '\033[1;32m✓\033[0m %s\n' "$*"; }
info() { printf '\033[1;36m▸\033[0m %s\n' "$*"; }
warn() { printf '\033[1;33m⚠\033[0m %s\n' "$*"; }
fail() { printf '\033[1;31m✘\033[0m %s\n' "$*" >&2; }

echo ""
info "apply-rank-watch-setup — $(date '+%Y-%m-%d %H:%M:%S')"
info "Project root: $PROJECT_ROOT"
info "Env file:     $ENV_FILE"
echo ""

# --- Step 1: Migrate / verify GSC creds --------------------------------
info "Step 1/4 — GSC credentials"

# Make sure the canonical env file exists.
if [ ! -f "$ENV_FILE" ]; then
  touch "$ENV_FILE"
  chmod 600 "$ENV_FILE"
  ok "Created $ENV_FILE (mode 600)"
fi

# Helper: does the canonical .env already have a key?
has_key() {
  grep -qE "^${1}=" "$ENV_FILE" 2>/dev/null
}

# What's missing?
MISSING=()
for k in GSC_CLIENT_ID GSC_CLIENT_SECRET GSC_REFRESH_TOKEN GSC_PROPERTY; do
  if ! has_key "$k"; then MISSING+=("$k"); fi
done

if [ ${#MISSING[@]} -eq 0 ]; then
  ok "All four GSC_* keys already present in $ENV_FILE — nothing to migrate"
else
  info "Missing in canonical env: ${MISSING[*]}"
  if [ -f "$LEGACY_ENV" ]; then
    info "Found legacy env at $LEGACY_ENV — copying GSC_* lines"
    for k in "${MISSING[@]}"; do
      line="$(grep -E "^${k}=" "$LEGACY_ENV" 2>/dev/null | tail -n 1 || true)"
      if [ -n "$line" ]; then
        printf '%s\n' "$line" >> "$ENV_FILE"
        ok "  copied $k"
      else
        warn "  $k not found in legacy env"
      fi
    done
    # Recompute MISSING after migration
    STILL_MISSING=()
    for k in GSC_CLIENT_ID GSC_CLIENT_SECRET GSC_REFRESH_TOKEN GSC_PROPERTY; do
      if ! has_key "$k"; then STILL_MISSING+=("$k"); fi
    done
    if [ ${#STILL_MISSING[@]} -gt 0 ]; then
      warn "Still missing after migration: ${STILL_MISSING[*]}"
      warn "Run interactively to fill them: node \"$AUTOMATION_DIR/setup-gsc-oauth.mjs\""
    else
      ok "All four GSC_* keys now present"
    fi
  else
    warn "Legacy env not reachable at: $LEGACY_ENV"
    warn "You need to run the OAuth flow once (opens browser, ~30 seconds):"
    warn "    node \"$AUTOMATION_DIR/setup-gsc-oauth.mjs\""
    warn "Then re-run this script."
    warn "(Continuing anyway — install.sh will still register the launchd job;"
    warn " the task will just record rank=null with a clear error until creds exist.)"
  fi
fi

echo ""

# --- Step 2: install.sh ------------------------------------------------
info "Step 2/4 — Registering launchd job"
if [ -f "$AUTOMATION_DIR/install.sh" ]; then
  # iCloud-synced files often arrive without the +x bit — invoke via `bash`
  # explicitly so we don't care about exec mode.
  if bash "$AUTOMATION_DIR/install.sh"; then
    ok "install.sh completed"
  else
    fail "install.sh exited non-zero — see output above"
    exit 1
  fi
else
  fail "$AUTOMATION_DIR/install.sh not found"
  exit 1
fi

echo ""

# --- Step 3: Smoke test the GSC reader --------------------------------
info "Step 3/4 — Smoke test get-gsc-rank.mjs"
if command -v node >/dev/null 2>&1; then
  set +e
  out="$(node "$AUTOMATION_DIR/scripts/get-gsc-rank.mjs" "downey realtor" 2>&1)"
  rc=$?
  set -e
  printf '  output: %s\n' "$out"
  if [ "$rc" -ne 0 ]; then
    warn "  (non-zero exit — should not happen; the helper is supposed to always exit 0)"
  fi
  if printf '%s' "$out" | grep -q '"rank":[0-9]'; then
    ok "  Live rank returned — GSC is fully wired"
  elif printf '%s' "$out" | grep -q '"impressions":0'; then
    ok "  GSC creds work; query has no impressions in window (expected for some long-tail terms)"
  elif printf '%s' "$out" | grep -q '"error"'; then
    warn "  Helper reported error — usually means GSC creds aren't set yet (see Step 1)"
  fi
else
  warn "node not found on PATH — skipping smoke test"
fi

echo ""

# --- Step 4: Next-steps ------------------------------------------------
info "Step 4/4 — Next steps"
cat <<EOF

  Force a real run on demand (don't wait for Monday 07:30):
      launchctl kickstart -k "gui/\$(id -u)/net.jessetek.weekly-rank-watch"

  Watch the live log:
      tail -f "$AUTOMATION_DIR/logs/weekly-rank-watch-"*.log

  Disable the redundant Cowork scheduled task:
      Open Cowork → Scheduled sidebar → jessetek-weekly-rank-watch → disable

  Full handoff doc:
      "$AUTOMATION_DIR/HANDOFF-rank-watch.md"

EOF

ok "Done."
