#!/usr/bin/env bash
# Per-machine overrides for jessetek automation.
# Copy this file to `config.local.sh` (gitignored) on each Mac and edit.
# Sourced automatically by scripts/_common.sh.

# Path to the claude binary. Override if `claude` is not on the launchd PATH
# or if you have multiple installs. Find yours with `which claude`.
# CLAUDE_BIN="/opt/homebrew/bin/claude"
# CLAUDE_BIN="$HOME/.npm-global/bin/claude"

# Force a specific Claude model for unattended runs. Leave unset to use the
# Claude Code default. Examples:
# CLAUDE_MODEL="claude-sonnet-4-6"
# CLAUDE_MODEL="claude-opus-4-6"

# Extra args appended to every `claude -p` call. Useful for restricting tools
# on read-only tasks, e.g. force the daily health check to never write:
# CLAUDE_EXTRA_ARGS="--allowedTools Bash,Read,Grep,Glob,WebFetch"

# How long to keep run logs in automation/logs/ before deletion.
# LOG_RETENTION_DAYS=30

# Set to 0 to silence macOS notification on failures.
# NOTIFY_ON_FAILURE=1

# Set DRY_RUN=1 to render the prompt + log it but skip invoking claude.
# Useful for verifying the plumbing without burning tokens.
# DRY_RUN=0
