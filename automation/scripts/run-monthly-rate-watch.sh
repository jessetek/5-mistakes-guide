#!/usr/bin/env bash
# Monthly Rate Watch insights post — generates + publishes new post.
# Schedule: 1st of month at 10:00 (see launchd/net.jessetek.monthly-rate-watch.plist)

TASK_NAME="monthly-rate-watch"
. "$(cd "$(dirname "$0")" && pwd)/_common.sh"
standard_run "monthly-rate-watch"
