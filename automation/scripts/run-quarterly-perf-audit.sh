#!/usr/bin/env bash
# Quarterly performance audit (PSI-driven) — produces PERF-AUDIT-YYYY-MM.md.
# Schedule: 1st of Jan/Apr/Jul/Oct at 13:00 (see launchd/net.jessetek.quarterly-perf-audit.plist)

TASK_NAME="quarterly-perf-audit"
. "$(cd "$(dirname "$0")" && pwd)/_common.sh"
standard_run "quarterly-perf-audit"
