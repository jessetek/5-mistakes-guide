#!/usr/bin/env bash
# Daily health check for jessetek.net. Read-only — never modifies files.
# Schedule: every day at 08:00 (see launchd/net.jessetek.daily-health-check.plist)

TASK_NAME="daily-health-check"
. "$(cd "$(dirname "$0")" && pwd)/_common.sh"
standard_run "daily-health-check"
