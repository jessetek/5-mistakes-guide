#!/usr/bin/env bash
# One-time: pull FRED_API_KEY from your Vercel project's production env vars
# and copy it into the Telegram .env.local that the Cowork scheduled tasks read.
#
# Why it exists: FRED_API_KEY only lives in the Vercel dashboard. The Cowork
# daily-rate-movement task runs in the cloud and needs the same key. Vercel CLI
# is already logged in on this Mac because that's how jessetek.net deploys.

set -euo pipefail

PROJECT="/Users/jtek/Library/Mobile Documents/com~apple~CloudDocs/Documents/Documents - JtekMac/Claude Code/Jessetek/landing-page"
TARGET="/Users/jtek/Library/Mobile Documents/com~apple~CloudDocs/Documents/Documents - JtekMac/Claude Code/Jessetek/tools/.env.local"

bold()  { printf '\033[1m%s\033[0m\n' "$*"; }
ok()    { printf '\033[1;32m✓\033[0m %s\n' "$*"; }
warn()  { printf '\033[1;33m⚠\033[0m %s\n' "$*"; }
fail()  { printf '\033[1;31m✘\033[0m %s\n' "$*" >&2; exit 1; }

[ -d "$PROJECT" ] || fail "project not found: $PROJECT"
[ -f "$TARGET" ]  || fail "target .env.local not found: $TARGET"

cd "$PROJECT"

if ! command -v vercel >/dev/null 2>&1; then
  fail "vercel CLI not on PATH. Install with: npm i -g vercel"
fi

bold "Pulling production env vars from Vercel..."
TMP=$(mktemp)
trap 'rm -f "$TMP" "$TMP.bak" "$TARGET.bak"' EXIT

if ! vercel env pull --environment=production "$TMP" --yes; then
  fail "vercel env pull failed. Are you logged into Vercel CLI? Run: vercel login"
fi

KEY=$(grep '^FRED_API_KEY=' "$TMP" | head -1 | cut -d= -f2- | sed 's/^"//;s/"$//')
if [ -z "$KEY" ]; then
  fail "FRED_API_KEY not present in Vercel env. Add it: vercel env add FRED_API_KEY"
fi

if [ "${#KEY}" -lt 16 ]; then
  warn "FRED key looks short (${#KEY} chars). Continuing anyway."
fi

# Update target .env.local — replace the existing line or append.
if grep -q '^FRED_API_KEY=' "$TARGET"; then
  sed -i.bak "s|^FRED_API_KEY=.*|FRED_API_KEY=$KEY|" "$TARGET"
else
  printf '\nFRED_API_KEY=%s\n' "$KEY" >> "$TARGET"
fi

ok "FRED_API_KEY written to .env.local (${#KEY} chars)"

# Quick verification: echo first 4 + last 4 of the key, redact middle
PREVIEW="${KEY:0:4}…${KEY: -4}"
ok "Verified: FRED_API_KEY=$PREVIEW"

bold "Done. The daily-rate-movement Cowork task will start working on its next run (weekdays 07:00)."
