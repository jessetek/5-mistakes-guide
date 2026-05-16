#!/usr/bin/env bash
# Monthly date refresh — updates "as of" lines on evergreen posts.
# Schedule: 15th of month at 11:00 (see launchd/net.jessetek.monthly-date-refresh.plist)

TASK_NAME="monthly-date-refresh"
. "$(cd "$(dirname "$0")" && pwd)/_common.sh"
standard_run "monthly-date-refresh"
