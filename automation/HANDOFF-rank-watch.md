# weekly-rank-watch — handoff (2026-05-04)

The Monday-morning rank watcher is now wired into the standard automation
structure (same shape as the other 8 launchd jobs). It pulls average position
from **Google Search Console** instead of scraping google.com, which was the
root cause of last week's all-`n/a` bootstrap output.

## What changed

```
automation/
├── prompts/weekly-rank-watch.txt              NEW — main prompt
├── scripts/
│   ├── run-weekly-rank-watch.sh               NEW — _common.sh standard_run wrapper
│   └── get-gsc-rank.mjs                       NEW — GSC reader (returns {rank,page,...} JSON)
├── launchd/net.jessetek.weekly-rank-watch.plist.template   NEW — Mondays 07:30
├── install.sh                                 EDITED — registers the new label
├── setup-gsc-oauth.mjs                        EDITED — env path is now portable
│                                              (was hardcoded to /Jtek website/...)
└── .state/rank-history.json                   RESET to clean { "queries": {} }
                                               (the bootstrap row I wrote earlier
                                                used a `websearch_fallback` source
                                                that doesn't match the format —
                                                let the first GSC run lay baseline)
```

## To make it live (one-time, ~2 minutes)

1. **Move GSC creds into `/Jessetek/.env`** (canonical location all scheduled
   tasks now read from). If you already have a `.env.local` over in
   `/Jtek website/instagram-stories/`, copy the four `GSC_*` vars over:

   ```sh
   grep '^GSC_' "$HOME/Library/Mobile Documents/com~apple~CloudDocs/Documents/Documents - JtekMac/Claude Code/Jtek website/instagram-stories/.env.local" \
     >> "$HOME/Library/Mobile Documents/com~apple~CloudDocs/Documents/Documents - JtekMac/Claude Code/Jessetek/.env"
   ```

   If you've never set up GSC OAuth yet, run the setup script — it now reads
   from `/Jessetek/.env`:

   ```sh
   cd "$HOME/Library/Mobile Documents/com~apple~CloudDocs/Documents/Documents - JtekMac/Claude Code/Jessetek/landing-page/automation"
   node setup-gsc-oauth.mjs
   ```

2. **Re-run install.sh** to register the new launchd job:

   ```sh
   ./install.sh
   ```

   You should see `✓ net.jessetek.weekly-rank-watch` in the registered list.

3. **Smoke-test the GSC reader** (should print one line of JSON):

   ```sh
   node scripts/get-gsc-rank.mjs "downey realtor"
   ```

   - Healthy: `{"query":"downey realtor","rank":12,"page":"https://jessetek.net/...","impressions":34,...}`
   - No GSC creds yet: `{"query":"downey realtor","rank":null,...,"error":"missing GSC creds (...)"}`
   - No impressions in the window (long-tail query): `{"query":"...","rank":null,"impressions":0,"note":"no impressions in window"}`

4. **Force a real run on demand** (don't wait for Monday 07:30):

   ```sh
   launchctl kickstart -k "gui/$(id -u)/net.jessetek.weekly-rank-watch"
   tail -f logs/weekly-rank-watch-*.log
   ```

   The first real run will lay a baseline in `.state/rank-history.json` and
   stay silent (no Telegram alert — there's nothing to compare against yet).

## What the existing scheduled task is doing

The Cowork scheduled task `jessetek-weekly-rank-watch` (the one that fired this
morning) is still registered with its old SKILL.md that points at the broken
Telegram path and the blocked Google scrape. **Two clean options:**

- **(Recommended) Deactivate the Cowork scheduled task** — the launchd job
  now covers the same Monday-morning slot with the better data source.
  Open Cowork → Scheduled sidebar → `jessetek-weekly-rank-watch` → disable.
- **Or keep both running** — they don't conflict (different code paths,
  separate state files would clobber each other; right now they share
  `.state/rank-history.json` so whichever runs second wins). Not recommended.

## Caveats worth knowing

- **GSC reports "average position" rounded to one decimal**, not literal SERP
  rank for a single moment. The reader rounds to the nearest int. For a query
  where Jesse jumps between rank 7 and 9 across the week, GSC would report
  ~8.0. This is more stable than scraping (which catches one moment) but
  smaller real movements may take a couple weeks to surface.
- **Queries with zero impressions report rank=null.** This is expected for
  long-tail terms ("mello roos guide", "first time buyer downey") where Jesse
  doesn't get clicked through often. Once those pages start ranking and
  getting impressions, GSC will populate them.
- **The GSC date window is the last 8 days, ending 3 days ago** — GSC has a
  ~2-3 day reporting lag. Tunable via `--start-days=N --end-days=N` flags
  if you ever want a different window.

## Files I left alone

- The Cowork scheduled task SKILL.md uploaded at `/uploads/SKILL.md` — that's
  outside this repo and managed by the scheduler. Update it via Cowork's UI
  if you want to keep that path active (point it at `bash run-weekly-rank-watch.sh`
  if you want it to drive the same code).
- The previous run's log at `logs/jessetek-weekly-rank-watch-2026-05-04.log` —
  kept as an audit record of why this rebuild happened.
