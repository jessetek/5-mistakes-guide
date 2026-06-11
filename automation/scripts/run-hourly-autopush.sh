#!/bin/bash
# net.jessetek.hourly-autopush — push any local SEO-brain commits on main to origin.
# The cloud Cowork task does the SEO work + commits whitelisted safe fixes locally;
# this agent deploys them (Vercel auto-builds from main) whenever the Mac is awake.
# Push-only + ahead-count guard => safe no-op when there's nothing to ship.
REPO="/Users/jesseonate/Documents/Claude Code/Jessetek/landing-page"
LOG="$REPO/automation/logs/hourly-autopush.log"
cd "$REPO" || exit 1
ts="$(date '+%Y-%m-%d %H:%M:%S')"
git fetch -q origin main 2>>"$LOG"
ahead="$(git rev-list --count origin/main..main 2>/dev/null || echo 0)"
if [ "${ahead:-0}" -gt 0 ]; then
  if git push origin main >>"$LOG" 2>&1; then
    echo "$ts  pushed $ahead commit(s) -> origin/main" >>"$LOG"
  else
    echo "$ts  push FAILED (will retry next run)" >>"$LOG"
  fi
else
  echo "$ts  nothing to push" >>"$LOG"
fi
