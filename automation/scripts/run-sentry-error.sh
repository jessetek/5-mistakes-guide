#!/usr/bin/env bash
# Event wrapper: triage a new Sentry error.
# Pipes the entire Sentry payload (email body, page export, JSON dump —
# whatever you have) to Claude as raw text. Claude parses the stack trace
# and either patches our code, logs it as third-party, or no-ops.
#
# Usage (any of these):
#   pbpaste | run-sentry-error.sh
#   run-sentry-error.sh < /path/to/sentry-export.txt
#   cat sentry-email.eml | run-sentry-error.sh
#
# That's it. No argv to fight with.

usage() {
  cat <<'EOF'
Usage: pipe Sentry payload to stdin, e.g.

  pbpaste | run-sentry-error.sh
  run-sentry-error.sh < /path/to/sentry-export.txt
  cat sentry-email.eml | run-sentry-error.sh

The script reads stdin until EOF, embeds the whole blob in the prompt,
and lets Claude figure out the file/line/cause.
EOF
  exit 64
}

if [ -t 0 ]; then
  echo "Error: nothing on stdin." >&2
  echo >&2
  usage
fi

SENTRY_PAYLOAD="$(cat)"

if [ -z "$SENTRY_PAYLOAD" ]; then
  echo "Error: stdin was empty." >&2
  exit 64
fi

# Reject huge payloads — anything over ~50KB is probably a screenshot or
# minified bundle, not a stack trace, and bloats the prompt.
PAYLOAD_BYTES="${#SENTRY_PAYLOAD}"
if [ "$PAYLOAD_BYTES" -gt 51200 ]; then
  echo "Warning: payload is ${PAYLOAD_BYTES} bytes — truncating to 50KB" >&2
  SENTRY_PAYLOAD="${SENTRY_PAYLOAD:0:51200}"
fi

export SENTRY_PAYLOAD
export RENDER_VARS_KEYS="SENTRY_PAYLOAD"

TASK_NAME="event-sentry-error"
. "$(cd "$(dirname "$0")" && pwd)/_common.sh"
standard_run "event-sentry-error"
