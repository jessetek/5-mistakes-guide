#!/usr/bin/env bash
# Remove jessetek automation from this Mac.
# Stops + unloads each launchd job, deletes the LaunchAgents plist.
# Logs and prompts in the project tree are preserved.

set -euo pipefail

LAUNCH_AGENTS="$HOME/Library/LaunchAgents"

LABELS=(
  "net.jessetek.daily-health-check"
  "net.jessetek.weekly-qc-sweep"
  "net.jessetek.weekly-clarity-review"
  "net.jessetek.monthly-rate-watch"
  "net.jessetek.monthly-date-refresh"
  "net.jessetek.quarterly-perf-audit"
  "net.jessetek.quarterly-city-stats"
  "net.jessetek.quarterly-seo-scan"
)

say() { printf '\033[1;36m▸\033[0m %s\n' "$*"; }

for label in "${LABELS[@]}"; do
  dst="$LAUNCH_AGENTS/${label}.plist"
  launchctl bootout "gui/$(id -u)/${label}" 2>/dev/null || true
  if [ -f "$dst" ]; then
    rm -f "$dst"
    say "removed $dst"
  else
    say "(no plist at $dst — already gone)"
  fi
done

say "Uninstalled. Logs in automation/logs/ are preserved."
