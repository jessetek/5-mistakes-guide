#!/usr/bin/env bash
# Weekly QC sweep — auto-fixes broken links/images and pushes.
# Schedule: Mondays at 09:00 (see launchd/net.jessetek.weekly-qc-sweep.plist)

TASK_NAME="weekly-qc-sweep"
. "$(cd "$(dirname "$0")" && pwd)/_common.sh"
standard_run "weekly-qc-sweep"
