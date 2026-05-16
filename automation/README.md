# jessetek.net — Pure Automation

Zero-touch scheduler for the four autonomous tasks in `OPERATOR-PLAYBOOK.md`. Each one runs on a launchd schedule on the Mac mini, pipes a self-contained prompt into the `claude` CLI, logs the run, and (where applicable) commits + pushes its own changes.

You don't paste prompts. You don't open Claude Code. You just `bash install.sh` once, and the Mac mini does the rest.

## What's automated

### Scheduled (launchd)

| Task | When | Modifies repo? |
|---|---|---|
| Daily health check | every day, 08:00 | no — read-only report |
| Weekly QC sweep | Mondays, 09:00 | yes — auto-fixes broken links/images |
| Weekly Clarity / UX review | Fridays, 14:00 | yes — writes UX-AUDIT-{date}.md |
| Monthly Rate Watch post | 1st of month, 10:00 | yes — publishes new insights post |
| Monthly date refresh | 15th of month, 11:00 | yes — updates "as of" dates |
| Quarterly performance audit | Jan/Apr/Jul/Oct 1, 13:00 | yes — writes PERF-AUDIT-{date}.md |
| Quarterly city stats refresh | Jan/Apr/Jul/Oct 5, 13:00 | yes — refreshes neighborhood stats |
| Quarterly SEO opportunity scan | Jan/Apr/Jul/Oct 10, 13:00 | yes — writes SEO-OPPORTUNITIES-{date}.md |

### Event-driven (manual wrappers)

These don't have schedules — you run them when something happens. Same lock/log/notify plumbing as the scheduled tasks; the only difference is *you* trigger them.

| Wrapper | When you run it | What it does |
|---|---|---|
| `run-new-review.sh` | New Google review came in | Adds card to `public/reviews.html`, commits + pushes |
| `run-new-city-page.sh` | Adding a new SoCal city | Creates neighborhood page + sitemap + service-areas tile + OG image |
| `run-sentry-error.sh` | Sentry alert email landed | Diagnoses + patches our code OR logs as third-party in `SENTRY-LOG.md` |

All times are the Mac mini's local time. Schedules live in `launchd/*.plist.template` — edit those if you want different hours.

## Layout

```
automation/
├── README.md                      ← you are here
├── install.sh                     ← run once on the Mac mini
├── uninstall.sh                   ← reverse it
├── config.local.example.sh        ← copy to config.local.sh for per-machine overrides
├── prompts/                       ← self-contained prompts piped into `claude -p`
│   ├── daily-health-check.txt
│   ├── weekly-qc-sweep.txt
│   ├── monthly-rate-watch.txt
│   └── monthly-date-refresh.txt
├── scripts/                       ← shell wrappers launchd actually invokes
│   ├── _common.sh                 ← shared logging, locking, claude invocation
│   ├── run-daily-health-check.sh
│   ├── run-weekly-qc-sweep.sh
│   ├── run-monthly-rate-watch.sh
│   └── run-monthly-date-refresh.sh
├── launchd/                       ← plist templates (committed)
│   ├── net.jessetek.daily-health-check.plist.template
│   ├── net.jessetek.weekly-qc-sweep.plist.template
│   ├── net.jessetek.monthly-rate-watch.plist.template
│   └── net.jessetek.monthly-date-refresh.plist.template
└── logs/                          ← run logs (gitignored, kept 30 days)
```

## One-time install on the Mac mini

```bash
# 1. Make sure the repo is cloned and on main
cd "/Users/jesseonate/Documents/Documents - JtekMac/Claude Code/Jessetek/landing-page"
git pull

# 2. Make sure claude CLI is installed and authenticated
npm install -g @anthropic-ai/claude-code   # if not already
claude                                      # complete login if first time
# also confirm git push works without prompting (SSH key configured for jessetek github)

# 3. Install the schedules
bash automation/install.sh
```

That's it. The four jobs are now registered with launchd and will fire on schedule.

To verify they're loaded:

```bash
launchctl list | grep jessetek
```

You should see four lines with PID `-` (not yet running) and last-exit `0`.

## Per-machine overrides

If `claude` lives somewhere unusual, or you want a different model, copy the example config and edit it:

```bash
cp automation/config.local.example.sh automation/config.local.sh
$EDITOR automation/config.local.sh
```

`config.local.sh` is gitignored — each Mac can have its own.

Common reason to edit: launchd's PATH is minimal. If `which claude` returns something like `/Users/jesseonate/.npm-global/bin/claude`, set `CLAUDE_BIN` to that exact path so the launchd-spawned shell doesn't have to guess.

## Manual triggers

### Scheduled tasks — fire them now

```bash
# Force a launchd-managed run (uses launchd/.out/.err logs too):
launchctl kickstart -k "gui/$(id -u)/net.jessetek.daily-health-check"
launchctl kickstart -k "gui/$(id -u)/net.jessetek.weekly-qc-sweep"
launchctl kickstart -k "gui/$(id -u)/net.jessetek.weekly-clarity-review"
launchctl kickstart -k "gui/$(id -u)/net.jessetek.monthly-rate-watch"
launchctl kickstart -k "gui/$(id -u)/net.jessetek.monthly-date-refresh"
launchctl kickstart -k "gui/$(id -u)/net.jessetek.quarterly-perf-audit"
launchctl kickstart -k "gui/$(id -u)/net.jessetek.quarterly-city-stats"
launchctl kickstart -k "gui/$(id -u)/net.jessetek.quarterly-seo-scan"

# Or run the script directly (faster feedback in your terminal):
automation/scripts/run-daily-health-check.sh

# Dry-run any task — renders the prompt + logs, skips claude invocation:
DRY_RUN=1 automation/scripts/run-weekly-qc-sweep.sh
```

### Event-driven wrappers

```bash
# New Google review arrived
automation/scripts/run-new-review.sh \
  "Maria S." "Long Beach" "2 weeks ago" 5 \
  "Jesse was patient with all our questions and got us into our dream home."

# Adding a new SoCal city page
automation/scripts/run-new-city-page.sh \
  "Tustin" "Orange County" "92780,92782" '$1.2M' 28 80000

# Sentry alert email landed — pipe whatever payload you have to stdin
pbpaste | automation/scripts/run-sentry-error.sh
# or
automation/scripts/run-sentry-error.sh < ~/Downloads/sentry-export.txt
```

Each event wrapper validates argv up front (so a typo fails fast instead of producing garbage) and uses the same `claude -p` + lock + log + notify pipeline. The result line at the end of the log tells you what happened: `RESULT: ADDED Maria S.`, `RESULT: PUBLISHED neighborhoods/tustin`, `RESULT: PATCHED public/js/widgets.js`, etc.

## Watching it work

```bash
# Latest log per task
ls -lt automation/logs/

# Tail an in-progress run
tail -f automation/logs/weekly-qc-sweep-*.log

# Just the failures, ever
cat automation/logs/_failures.log

# What launchd thinks
launchctl print "gui/$(id -u)/net.jessetek.weekly-qc-sweep" | head -50
```

Every run ends with a single line like:

```
RESULT: CLEAN
RESULT: FIXED 3
RESULT: PUBLISHED socal-rate-watch-may-2026
RESULT: BLOCKED git push rejected (non-fast-forward)
```

Grep that across logs for a quick week-in-review:

```bash
grep -h '^RESULT: ' automation/logs/*.log | tail -20
```

## How the autonomy works

Scripts invoke `claude -p --dangerously-skip-permissions` non-interactively. That flag is the price of unattended runs — there's no human present to approve tool calls. To keep that safe:

- The **daily health check** prompt explicitly says "do not modify, commit, or push" so even with the bypass flag it stays read-only.
- The other three are scoped tasks with verifiable outputs (QC must come back clean, posts must return 200, diffs must be date-only). Each prompt ends with a `RESULT:` line so the script can grep for success.
- A lock file in `.locks/` prevents overlapping runs of the same task.
- A failure (non-zero exit) triggers a macOS notification and an entry in `_failures.log`.

If you want to tighten the daily health check further, set `CLAUDE_EXTRA_ARGS="--allowedTools Bash,Read,Grep,Glob,WebFetch"` in `config.local.sh` to deny Edit/Write entirely on that task.

## Troubleshooting

**"claude: command not found" in the log.**
launchd's PATH doesn't include npm globals by default. Either:
- Set `CLAUDE_BIN` in `config.local.sh` to the absolute path (`which claude` shows you).
- Or add the directory to the `EnvironmentVariables/PATH` in the relevant `.plist.template` and re-run `install.sh`.

**Job is registered but never runs.**
- Mac mini must be awake at the scheduled time. In System Settings → Energy, enable "Prevent automatic sleeping when the display is off" or schedule it to wake at 07:55.
- launchd will fire a missed `StartCalendarInterval` job once when the mac wakes, but only the most recent one. Don't rely on a sleeping mac.
- Check `launchctl print "gui/$(id -u)/net.jessetek.weekly-qc-sweep"` for the next-fire time.

**git push fails inside the run.**
Confirm `ssh -T git@github.com` works as the same user. If you use HTTPS, install `gh` and run `gh auth login` so the helper supplies credentials non-interactively.

**iCloud Drive path on the Mac mini differs.**
`PROJECT_ROOT` is computed from each script's location (`$AUTOMATION_DIR/..`), so the absolute path doesn't matter as long as `automation/` lives next to `public/` inside the repo. After moving the project, just re-run `install.sh` so the LaunchAgents plists pick up the new path.

**Need to disable just one job temporarily.**
```bash
launchctl bootout "gui/$(id -u)/net.jessetek.weekly-qc-sweep"
# To re-enable:
launchctl bootstrap "gui/$(id -u)" "$HOME/Library/LaunchAgents/net.jessetek.weekly-qc-sweep.plist"
```

## Updating prompts or schedules

1. Edit `prompts/<task>.txt` or `launchd/<label>.plist.template`.
2. Commit + push.
3. On the Mac mini, `git pull` and re-run `bash automation/install.sh`. The install script is idempotent — it boots out the old jobs and bootstraps the new ones.

## Uninstall

```bash
bash automation/uninstall.sh
```

Removes the LaunchAgents plists. Keeps your prompts, scripts, and logs in the repo so you can re-install later.
