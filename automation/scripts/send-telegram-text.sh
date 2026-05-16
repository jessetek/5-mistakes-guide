#!/usr/bin/env bash
# Portable Telegram sender for Jessetek scheduled tasks.
# Replaces the prior send-telegram-text.mjs that lived in the unmounted
# /Jtek website/instagram-stories/ folder. Reads creds from /Jessetek/.env
# and gracefully no-ops if TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID are blank,
# so scheduled tasks never fail just because alerting isn't configured yet.
#
# Usage:
#   send-telegram-text.sh "single line message"
#   send-telegram-text.sh < message.txt        # read from stdin
#   echo "hello" | send-telegram-text.sh
#
# Exit codes:
#   0  success or graceful skip (creds blank)
#   1  bad usage
#   2  Telegram API error
set -euo pipefail

# --- Resolve env file (mounted location is canonical) --------------------
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# Walk up to find /Jessetek/.env — try common spots in order. Caller can
# also point at a specific file by exporting JTEK_ENV before invoking.
ENV_CANDIDATES=(
  "${JTEK_ENV:-}"                                                    # explicit override
  "$SCRIPT_DIR/../../../.env"                                        # landing-page is inside Jessetek (real Mac)
  "$SCRIPT_DIR/../../../Jessetek/.env"                               # Cowork sandbox: landing-page + Jessetek mounted as siblings
  "$HOME/Library/Mobile Documents/com~apple~CloudDocs/Documents/Documents - JtekMac/Claude Code/Jessetek/.env"
  "$SCRIPT_DIR/../.env"                                              # in case copied locally next to automation/
)
ENV_FILE=""
for c in "${ENV_CANDIDATES[@]}"; do
  if [ -f "$c" ]; then ENV_FILE="$c"; break; fi
done

if [ -n "$ENV_FILE" ]; then
  # shellcheck disable=SC2046
  set -a
  # shellcheck disable=SC1090
  . "$ENV_FILE"
  set +a
fi

# --- Read message from arg or stdin --------------------------------------
if [ "$#" -ge 1 ]; then
  MSG="$*"
else
  MSG="$(cat)"
fi

if [ -z "${MSG:-}" ]; then
  echo "send-telegram-text: empty message, nothing to send" >&2
  exit 1
fi

# --- Graceful no-op if creds missing -------------------------------------
TOKEN="${TELEGRAM_BOT_TOKEN:-}"
CHAT="${TELEGRAM_CHAT_ID:-}"
if [ -z "$TOKEN" ] || [ -z "$CHAT" ]; then
  # Log to stderr (captured by automation framework) and exit 0 so callers
  # don't fail. The state file will still record the run.
  echo "send-telegram-text: TELEGRAM_BOT_TOKEN/TELEGRAM_CHAT_ID not set in $ENV_FILE — skipping nudge" >&2
  echo "--- message would have been ---" >&2
  echo "$MSG" >&2
  echo "-------------------------------" >&2
  exit 0
fi

# --- Send -----------------------------------------------------------------
RESP=$(curl -sS -m 10 -w "\nHTTP:%{http_code}" \
  -X POST "https://api.telegram.org/bot${TOKEN}/sendMessage" \
  --data-urlencode "chat_id=${CHAT}" \
  --data-urlencode "text=${MSG}" \
  --data-urlencode "disable_web_page_preview=true")

HTTP=$(echo "$RESP" | tail -1 | sed 's/HTTP://')
BODY=$(echo "$RESP" | sed '$d')

if [ "$HTTP" = "200" ]; then
  exit 0
fi

echo "send-telegram-text: Telegram API HTTP $HTTP" >&2
echo "$BODY" >&2
exit 2
