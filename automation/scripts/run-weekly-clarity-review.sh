#!/usr/bin/env bash
# Weekly Clarity / UX audit — research only, propose-only audit doc.
# Schedule: Fridays at 14:00 (see launchd/net.jessetek.weekly-clarity-review.plist)

TASK_NAME="weekly-clarity-review"
. "$(cd "$(dirname "$0")" && pwd)/_common.sh"
standard_run "weekly-clarity-review"
