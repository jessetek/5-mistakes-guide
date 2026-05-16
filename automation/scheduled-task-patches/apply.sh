#!/usr/bin/env bash
# Apply pending scheduled-task SKILL.md patches.
#
# Scheduled-task SKILL.md files live outside the Cowork-mounted workspace
# (/Users/jtek/Documents/Claude/Scheduled/...). Scheduled-task sessions also
# can't modify other scheduled tasks via MCP — so we keep patched copies
# here and apply them from Terminal manually after review.
#
# Usage:
#   bash automation/scheduled-task-patches/apply.sh           # apply all
#   bash automation/scheduled-task-patches/apply.sh <name>    # apply one
#
# Re-run is safe — cp overwrites. Always diff before applying:
#   diff -u /Users/jtek/Documents/Claude/Scheduled/<name>/SKILL.md \
#           automation/scheduled-task-patches/<name>.SKILL.md

set -euo pipefail

PATCH_DIR="$(cd "$(dirname "$0")" && pwd)"
SCHED_DIR="$HOME/Documents/Claude/Scheduled"

if [ ! -d "$SCHED_DIR" ]; then
  echo "✘ Scheduled task directory not found: $SCHED_DIR" >&2
  exit 1
fi

apply_one() {
  local name="$1"
  local src="$PATCH_DIR/${name}.SKILL.md"
  local dst="$SCHED_DIR/${name}/SKILL.md"

  if [ ! -f "$src" ]; then
    echo "✘ No patch found for: $name (expected $src)" >&2
    return 1
  fi
  if [ ! -f "$dst" ]; then
    echo "✘ Target SKILL.md not found: $dst" >&2
    echo "  (Is the scheduled task name correct? Check: ls $SCHED_DIR)" >&2
    return 1
  fi

  if cmp -s "$src" "$dst"; then
    echo "= $name (already in sync)"
    return 0
  fi

  cp "$dst" "${dst}.bak.$(date +%Y%m%d-%H%M%S)"
  cp "$src" "$dst"
  echo "✓ $name (backup written to ${dst}.bak.*)"
}

if [ $# -eq 1 ]; then
  apply_one "$1"
else
  for patch in "$PATCH_DIR"/*.SKILL.md; do
    [ -f "$patch" ] || continue
    name="$(basename "$patch" .SKILL.md)"
    apply_one "$name"
  done
fi
