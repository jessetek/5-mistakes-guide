#!/usr/bin/env bash
# Event wrapper: a new Google review came in. Adds it to public/reviews.html
# static-fallback grid and pushes.
#
# Usage:
#   run-new-review.sh "<name>" "<city>" "<time-ago>" <stars> "<quote>"
#
# Example:
#   run-new-review.sh "Maria S." "Long Beach" "2 weeks ago" 5 \
#     "Jesse was patient with all our questions and got us into our dream home in Lakewood."

usage() {
  cat <<EOF
Usage: $(basename "$0") "<name>" "<city>" "<time-ago>" <stars 1-5> "<quote>"

Example:
  $(basename "$0") "Maria S." "Long Beach" "2 weeks ago" 5 \\
    "Jesse was amazing — knew the market cold and never pushed."
EOF
  exit 64  # EX_USAGE
}

if [ "$#" -ne 5 ]; then
  usage
fi

NAME="$1"
CITY="$2"
TIME_AGO="$3"
STARS="$4"
QUOTE="$5"

# Basic validation
case "$STARS" in
  1|2|3|4|5) ;;
  *) echo "Error: stars must be 1-5, got '$STARS'"; usage ;;
esac

[ -n "$NAME" ]     || { echo "Error: name is empty"; usage; }
[ -n "$CITY" ]     || { echo "Error: city is empty"; usage; }
[ -n "$TIME_AGO" ] || { echo "Error: time-ago is empty"; usage; }
[ -n "$QUOTE" ]    || { echo "Error: quote is empty"; usage; }

# Tokens to substitute in the prompt template — _common.sh reads these
# named variables via RENDER_VARS_KEYS.
export NAME CITY TIME_AGO STARS QUOTE
export RENDER_VARS_KEYS="NAME CITY TIME_AGO STARS QUOTE"

TASK_NAME="event-new-review"
. "$(cd "$(dirname "$0")" && pwd)/_common.sh"
standard_run "event-new-review"
