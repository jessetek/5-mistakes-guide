#!/usr/bin/env bash
# One-time setup for Google Search Console API access.
#
# What this does:
#   1. Walks you through Google Cloud OAuth client creation (5 min)
#   2. Runs the OAuth flow and exchanges the auth code for a refresh token
#   3. Writes GSC_CLIENT_ID, GSC_CLIENT_SECRET, GSC_REFRESH_TOKEN to .env.local
#   4. Verifies API access works
#
# After this runs successfully, the weekly-gsc-harvest Cowork task starts working
# automatically on the next Sunday 21:00.

set -euo pipefail

ENV_FILE="/Users/jtek/Library/Mobile Documents/com~apple~CloudDocs/Documents/Documents - JtekMac/Claude Code/Jessetek/tools/.env.local"

bold()  { printf '\033[1m%s\033[0m\n' "$*"; }
say()   { printf '\033[1;36m▸\033[0m %s\n' "$*"; }
ok()    { printf '\033[1;32m✓\033[0m %s\n' "$*"; }
warn()  { printf '\033[1;33m⚠\033[0m %s\n' "$*"; }
fail()  { printf '\033[1;31m✘\033[0m %s\n' "$*" >&2; exit 1; }

[ -f "$ENV_FILE" ] || fail "Missing $ENV_FILE"

cat <<'EOF'

╭─────────────────────────────────────────────────────────────╮
│  jessetek.net — Google Search Console API setup             │
│  One-time, ~10 minutes. Re-run if your OAuth token expires. │
╰─────────────────────────────────────────────────────────────╯

You'll need:
  • A Google account that owns/manages jessetek.net in Search Console
  • A Google Cloud project (we'll create one if you don't have one)

Step 1 of 4 — Create OAuth 2.0 client credentials in Google Cloud
═════════════════════════════════════════════════════════════

  Open this URL in your browser:
      https://console.cloud.google.com/apis/credentials

  Then:
   a) Top bar → "Select a project" → New Project
      Name: "jessetek-automation"  (or any name)
      Click Create. Wait for it to finish.

   b) Left sidebar → Library → search "Search Console API" → Enable

   c) Back to APIs & Services → Credentials
      Click "+ CREATE CREDENTIALS" → OAuth client ID

   d) If prompted, configure the OAuth consent screen first:
      User Type: External  → Create
      App name: jessetek-automation
      User support email: jesseonate15@gmail.com
      Developer contact: jesseonate15@gmail.com
      → Save and continue (skip Scopes for now)
      → Add Test User: jesseonate15@gmail.com → Save

   e) Now create the OAuth client ID:
      Application type: Desktop app
      Name: jessetek-cli
      Click Create.

   f) A modal appears with the credentials. Copy:
      • Client ID  (looks like 1234567890-abc...apps.googleusercontent.com)
      • Client secret  (looks like GOCSPX-...)

EOF

read -p "  Paste your Client ID:     " CLIENT_ID
read -p "  Paste your Client secret: " CLIENT_SECRET

[ -n "$CLIENT_ID" ]     || fail "Client ID is empty. Re-run when ready."
[ -n "$CLIENT_SECRET" ] || fail "Client secret is empty. Re-run when ready."

cat <<'EOF'

Step 2 of 4 — Authorize
═══════════════════════

EOF

REDIRECT="urn:ietf:wg:oauth:2.0:oob"  # out-of-band, no local server needed
SCOPE="https://www.googleapis.com/auth/webmasters.readonly"
AUTH_URL="https://accounts.google.com/o/oauth2/v2/auth?client_id=${CLIENT_ID}&redirect_uri=${REDIRECT}&response_type=code&scope=${SCOPE}&access_type=offline&prompt=consent"

cat <<EOF
  Open this URL in your browser:

      ${AUTH_URL}

  Sign in with the Google account that owns jessetek.net in Search Console.
  When Google shows "This app isn't verified", click Advanced → Go to
  jessetek-automation (unsafe) — that's expected for personal-use OAuth.
  Click Continue / Allow on the consent screen.

  Google will then show a code on screen. Copy it.

EOF

read -p "  Paste the authorization code: " AUTH_CODE

[ -n "$AUTH_CODE" ] || fail "Auth code is empty."

say "Step 3 of 4 — Exchanging code for refresh token..."

TOKEN_RESP=$(curl -sS -X POST https://oauth2.googleapis.com/token \
  -d "code=${AUTH_CODE}" \
  -d "client_id=${CLIENT_ID}" \
  -d "client_secret=${CLIENT_SECRET}" \
  -d "redirect_uri=${REDIRECT}" \
  -d "grant_type=authorization_code")

REFRESH_TOKEN=$(echo "$TOKEN_RESP" | python3 -c 'import json,sys; d=json.load(sys.stdin); print(d.get("refresh_token","") or "")')
ACCESS_TOKEN=$(echo "$TOKEN_RESP" | python3 -c 'import json,sys; d=json.load(sys.stdin); print(d.get("access_token","") or "")')

if [ -z "$REFRESH_TOKEN" ] || [ -z "$ACCESS_TOKEN" ]; then
  echo "Token exchange failed. Response from Google:" >&2
  echo "$TOKEN_RESP" >&2
  fail "Could not get tokens. Most common cause: auth code already used (one-shot). Re-run from Step 2."
fi
ok "Got refresh token."

say "Step 4 of 4 — Verifying GSC API access..."

# List sites the user has access to
SITES=$(curl -sS "https://searchconsole.googleapis.com/webmasters/v3/sites" \
  -H "Authorization: Bearer ${ACCESS_TOKEN}")

if echo "$SITES" | grep -q '"siteUrl"'; then
  ok "GSC API responded. Sites this account can access:"
  echo "$SITES" | python3 -c 'import json,sys; d=json.load(sys.stdin)
for s in d.get("siteEntry", []):
    print(f"   • {s.get(\"siteUrl\")} ({s.get(\"permissionLevel\",\"?\")})")'
else
  echo "$SITES" >&2
  fail "GSC API didn't return any sites. Make sure the Google account is an owner/full user on jessetek.net in Search Console."
fi

# Determine which property to use — prefer https://jessetek.net/ if present
GSC_PROPERTY=$(echo "$SITES" | python3 -c '
import json, sys
d = json.load(sys.stdin)
sites = [s.get("siteUrl","") for s in d.get("siteEntry", [])]
for pref in ("https://jessetek.net/", "sc-domain:jessetek.net"):
    if pref in sites:
        print(pref); sys.exit(0)
for s in sites:
    if "jessetek.net" in s:
        print(s); sys.exit(0)
')

if [ -z "$GSC_PROPERTY" ]; then
  warn "No jessetek.net property found in your GSC sites. Verify jessetek.net at https://search.google.com/search-console first, then re-run."
  GSC_PROPERTY="https://jessetek.net/"
fi
ok "Using GSC property: $GSC_PROPERTY"

# Write back to .env.local
say "Writing tokens to $ENV_FILE..."

python3 <<PYEOF
import re, os
env_path = os.environ['ENV_FILE']
with open(env_path) as fh:
    content = fh.read()

updates = {
    'GSC_CLIENT_ID': os.environ['CLIENT_ID'],
    'GSC_CLIENT_SECRET': os.environ['CLIENT_SECRET'],
    'GSC_REFRESH_TOKEN': os.environ['REFRESH_TOKEN'],
    'GSC_PROPERTY': os.environ['GSC_PROPERTY'],
}

for key, val in updates.items():
    pattern = rf'^{key}=.*$'
    repl = f'{key}={val}'
    if re.search(pattern, content, re.MULTILINE):
        content = re.sub(pattern, repl, content, count=1, flags=re.MULTILINE)
    else:
        content = content.rstrip() + f'\n{repl}\n'

with open(env_path, 'w') as fh:
    fh.write(content)

print('  written.')
PYEOF
export ENV_FILE CLIENT_ID CLIENT_SECRET REFRESH_TOKEN GSC_PROPERTY

ok "Setup complete."

cat <<'EOF'

You're done. The weekly-gsc-harvest Cowork task fires every Sunday 21:00
and will start producing keyword opportunity reports automatically.

To test it now without waiting:
  1. Open Cowork's Scheduled sidebar
  2. Find "jessetek-weekly-gsc-harvest"
  3. Click "Run now"
  4. Watch your Telegram

If it fails with "auth expired" 6 months from now, just re-run this script.

EOF
