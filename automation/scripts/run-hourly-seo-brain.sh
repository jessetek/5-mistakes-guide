#!/usr/bin/env bash
# Hourly SEO Brain — unattended autonomous SEO execution loop.
# Picks ONE safe, verified action per run; auto-deploys only whitelisted fixes,
# drafts anything bigger for Jesse. Self-contained prompt: prompts/hourly-seo-brain.txt
# Schedule: every hour (launchd/net.jessetek.hourly-seo-brain.plist, StartInterval 3600).
# Model: Opus by default (Jesse's explicit choice). Override with HOURLY_SEO_MODEL in config.local.sh.

TASK_NAME="hourly-seo-brain"
. "$(cd "$(dirname "$0")" && pwd)/_common.sh"

# Force Opus for this task unless overridden (config.local.sh may set HOURLY_SEO_MODEL=sonnet to cut cost).
: "${HOURLY_SEO_MODEL:=opus}"
CLAUDE_MODEL="$HOURLY_SEO_MODEL"

standard_run "hourly-seo-brain"
