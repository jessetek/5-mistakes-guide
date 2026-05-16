#!/usr/bin/env bash
# Quarterly city stats refresh (CAR data → neighborhood pages).
# Schedule: 5th of Jan/Apr/Jul/Oct at 13:00 (see launchd/net.jessetek.quarterly-city-stats.plist)

TASK_NAME="quarterly-city-stats"
. "$(cd "$(dirname "$0")" && pwd)/_common.sh"
standard_run "quarterly-city-stats"
