#!/usr/bin/env bash
# Weekly rank watch — pulls GSC average position for 10 SoCal realtor queries,
# alerts via Telegram only on notable movement.
# Schedule: Mondays at 07:30 (see launchd/net.jessetek.weekly-rank-watch.plist)

TASK_NAME="weekly-rank-watch"
. "$(cd "$(dirname "$0")" && pwd)/_common.sh"
standard_run "weekly-rank-watch"
