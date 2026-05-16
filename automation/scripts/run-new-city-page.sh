#!/usr/bin/env bash
# Event wrapper: add a new SoCal city page (full neighborhood page + sitemap +
# service-areas grid + areaServed schema bulk-update + OG image).
#
# Usage:
#   run-new-city-page.sh "<city>" "<county>" "<zips>" "<median>" <dom> <population>
#
# Example:
#   run-new-city-page.sh "Tustin" "Orange County" "92780,92782" '$1.2M' 28 80000
#
# Quote median with single quotes so $ doesn't expand.

usage() {
  cat <<EOF
Usage: $(basename "$0") "<city>" "<county>" "<zips>" "<median>" <dom> <population>

Where:
  city        Plain English city name        (e.g. "Tustin")
  county      "LA County" or "Orange County"
  zips        Comma-separated ZIPs           (e.g. "92780,92782")
  median      Median home price string       (e.g. '\$1.2M')
  dom         Average days on market         (integer)
  population  City population                (integer)

Example:
  $(basename "$0") "Tustin" "Orange County" "92780,92782" '\$1.2M' 28 80000
EOF
  exit 64
}

if [ "$#" -ne 6 ]; then
  usage
fi

CITY="$1"
COUNTY="$2"
ZIPS="$3"
MEDIAN="$4"
DOM="$5"
POPULATION="$6"

[ -n "$CITY" ]   || { echo "Error: city is empty"; usage; }
[ -n "$COUNTY" ] || { echo "Error: county is empty"; usage; }
case "$COUNTY" in
  "LA County"|"Orange County") ;;
  *) echo "Warning: county is '$COUNTY' (expected 'LA County' or 'Orange County') — continuing anyway" >&2 ;;
esac
[[ "$DOM" =~ ^[0-9]+$ ]]        || { echo "Error: dom must be an integer"; usage; }
[[ "$POPULATION" =~ ^[0-9]+$ ]] || { echo "Error: population must be an integer"; usage; }

export CITY COUNTY ZIPS MEDIAN DOM POPULATION
export RENDER_VARS_KEYS="CITY COUNTY ZIPS MEDIAN DOM POPULATION"

TASK_NAME="event-new-city-page"
. "$(cd "$(dirname "$0")" && pwd)/_common.sh"
standard_run "event-new-city-page"
