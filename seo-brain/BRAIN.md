# 🧠 jessetek.net SEO Brain

**Target query:** _"real estate agent in Downey and surrounding cities"_ — Downey + South Gate,
Montebello, Pico Rivera, Norwalk, Whittier, Bell Gardens, Bellflower, Lakewood, Long Beach (the
LA/OC cities Jesse actually serves). Exact query set lives in `goal.json → target_queries`.
**Site:** jessetek.net · **GSC property:** `https://jessetek.net/` (fallback `sc-domain:jessetek.net`).

> This Brain is the local-real-estate sibling of the **Jtek** SEO Brain
> (`../../../Jtek website/seo-brain/`, target = "real estate crm"). Same learn→act→evolve
> discipline, different target surface (local map pack + qualified-organic vs. a SaaS head term).

A self-improving operator whose single job is to move jessetek.net up Google for
**"real estate agent" in/around Downey, CA**. It runs as a loop: every cycle it
**measures** reality, **researches** what's working now, **diagnoses** the gap,
**acts** on what it can, **learns** from results, and **evolves its own skills**.

It is **not** a replacement for `../automation/` (the launchd jobs that already
harvest GSC data, watch rank, and run QC). The Brain *sits on top* of that data
and turns it into prioritized action toward one goal.

---

## The prime directive

Read `goal.json`. Note the **honest reframe**: ranking #1 organically for the bare
head term "real estate agent" is not winnable for a solo site — the SERP is owned
by the Google Map pack (GBP) + Zillow/Realtor.com. So the Brain optimizes the three
**winnable surfaces**: the **local pack** (GBP), **qualified organic** (Downey agent
long-tail), and **branded**. Always spend effort where impact/effort is highest, and
be honest about which levers only Jesse can pull (off-page) vs. which the Brain can
pull itself (on-page).

---

## The loop — one cycle = six skills, in order

Each run executes skills 1→6. Skills read/write the files noted. Keep each run
**cheap and incremental** (Jesse hits usage limits) — a cycle should do a *little*
real work and leave a clean trail, not boil the ocean.

### 1. MEASURE  → updates `state/rank-snapshot.json`
- Read the freshest GSC data already on disk:
  `../automation/.state/rank-history.json` and the newest
  `../automation/.state/gsc-harvest-*.json`.
- Pull, per tracked query: avg position, impressions, clicks, trend vs last run.
- Recompute the KPIs in `goal.json.baseline_kpis_*` → write a new dated snapshot.
- **Output:** a 5-line "state of the world" delta (what moved since last run).

### 2. RESEARCH  → updates `knowledge/best-practices-2026.md`
- Only when knowledge is stale (> ~30 days) or a new question arises. Don't re-research every run.
- Fan out web research on current local-real-estate SEO (GBP factors, review velocity,
  citations, AI Overviews, on-page) and synthesize into the knowledge base.
- The canonical way to run this: the `jessetek-seo-research` workflow
  (`Workflow` tool) — 6 research agents + 1 synthesizer. Re-run by editing the
  saved script and resuming.
- **Output:** refreshed `knowledge/best-practices-2026.md` + new `top_actions` merged into the ledger.

### 3. DIAGNOSE  → appends to current `runs/<date>.md`
- Compare MEASURE (where we are) against `knowledge/` (where best practice says we should be)
  and `goal.json` (where we want to be).
- Produce the gap list, ranked by **impact ÷ effort**. Tag each gap's **owner**
  (`jesse` = off-page/account work the Brain can't do; `claude` = on-page/code).
- **Output:** ranked gap list → feeds the ledger.

### 4. ACT  → edits the site + updates `state/actions-ledger.json`
- Take the top **claude-owned** actions and actually do them (edit `../public/*.html`,
  schema, internal links, sitemap, new pages). Verify locally (preview server / QC sweep).
  **Never `git push` without Jesse's explicit OK** — this is a live lead-gen site.
- For top **jesse-owned** actions, write a crisp, do-this-now task (exact steps, links,
  copy-paste text) into the run log and mark `status: awaiting-jesse` in the ledger.
- **Output:** shipped on-page changes (staged) + a short punch-list for Jesse.

### 5. LEARN  → updates `knowledge/` + `goal.json`
- Did last cycle's actions move anything in MEASURE? Record cause→effect.
- Promote things that worked into `knowledge/` as durable lessons; demote things that didn't.
- Update `goal.json` status/run_count and target statuses.
- **Output:** durable lessons captured, not just activity logged.

### 6. EVOLVE  → edits **this file** and `skills/`
- The Brain improves its *own* method. Ask: what made this cycle slow, wrong, or wasteful?
  Tighten a skill, add a check, retire a dead tactic, sharpen a prompt.
- Append a dated line to the **Changelog** at the bottom describing the self-edit.
- **Output:** a measurably better Brain next run. This is what "gets better every run" means.

---

## How to run it

**Hourly autonomous job (Opus/max by default):**
`automation/scripts/run-hourly-seo-brain.sh` runs this loop unattended via launchd. It auto-deploys
only whitelisted safe fixes and drafts anything bigger to `seo-brain/drafts/`.

> ⚠️ **Host changed (2026-06): the always-on Mac mini is GONE.** This now runs on Jesse's
> **MacBook Pro M1 Pro**, which is **NOT always-on** — launchd fires the job only while the laptop
> is awake. Missed hours simply run the next time it wakes; the loop self-throttles (idle = near-free).
> The `claude` CLI lives at `~/.claude-cli-global/bin/` (NOT on the default PATH), so the launchd
> plist must add that dir to `PATH` (see `~/Library/LaunchAgents/net.jessetek.seo-brain.plist`).

- Activate: `launchctl load -w ~/Library/LaunchAgents/net.jessetek.seo-brain.plist`
- Force a run now: `launchctl kickstart -k "gui/$(id -u)/net.jessetek.seo-brain"`
- Kill switch: `launchctl unload ~/Library/LaunchAgents/net.jessetek.seo-brain.plist`
- Cheaper: set `HOURLY_SEO_MODEL=sonnet` in `automation/config.local.sh`
- Companion job `net.jessetek.hourly-autopush` pushes any local SEO-brain commits to origin
  (Vercel auto-builds main) whenever the laptop is awake.
> Note: hourly is for **execution velocity**. Rank **measurement** still only matters weekly
> (GSC refresh) — the loop skips MEASURE when there's no new data, so most hours are cheap no-ops.

**Manual single cycle:** "Run the SEO brain" → execute skills 1→6 once, stop.

**Stop condition:** `goal.json.definition_of_done_overall` is met for 2 straight GSC weeks,
or Jesse says stop.

---

## File map

```
seo-brain/
├── BRAIN.md                      ← you are here: the loop + self-improvement protocol
├── goal.json                     ← the target, honest reframe, KPIs, winnable surfaces, status
├── knowledge/                    ← the "research brain" (durable, improves over time)
│   ├── diagnosis.md              ← current data-driven diagnosis (what's actually wrong)
│   ├── ranking-strategy.md       ← the strategic framework (3 winnable surfaces, lever priority)
│   └── best-practices-2026.md    ← synthesized from the research workflow (refreshed when stale)
├── state/
│   ├── actions-ledger.json       ← every action: owner, impact, effort, status, result
│   └── rank-snapshot.json        ← latest MEASURE output (delta vs prior run)
├── runs/
│   └── <date>.md                 ← one log per cycle: measured / diagnosed / did / learned
└── skills/
    └── SKILLS.md                 ← the editable how-to for each of the 6 skills (EVOLVE edits this)
```

---

## Operating principles (hard-won, edit as we learn)

1. **Reach before rank.** This site already ranks; it isn't *seen*. Prioritize levers that
   grow impressions (GBP, reviews, citations, links) over micro on-page tweaks.
2. **Honesty over vanity.** A position-3.9 on 7 impressions is not "ranking #4 for real estate
   agent." Report reach-weighted reality.
3. **Owner-tag everything.** The biggest levers are off-page and only Jesse can pull them. The
   Brain's job there is to make his next action frictionless, not to pretend it did the work.
4. **Cheap, incremental cycles.** Small verifiable steps with a clean trail beat marathon runs.
5. **Never auto-deploy.** Stage on-page changes; Jesse approves the push.
6. **Compound, don't churn.** Every cycle should leave the knowledge base and the skills sharper
   than it found them.

---

## Changelog (EVOLVE writes here)

- **2026-06-11 — run 01 (genesis):** Brain created. Diagnosis: reach, not rank, is the blocker
  (169 impressions/28d). Reframed the goal into 3 winnable surfaces. Seeded knowledge + ledger.
  Launched the `jessetek-seo-research` workflow for the 2026 best-practices knowledge base.
- **2026-06-29 — run 06 (NAP-consistency):** Used the two preceding NAP commits (`ebe2343`/`62e6676`,
  which reverted phone to (562) 609-4200 and standardized email to jessetek.net) as a QC trigger and
  swept phone + email across the whole site. Phone fully consistent (old 688-5214 = 0 files); the only
  stragglers were 2 RSS contact fields in `insights/feed.xml` still on the OLD `jesse@jesseonate.com`.
  **Shipped C12: repointed both to canonical `jesse@jessetek.net`** (2-line diff, feed.xml still valid
  XML, 0 `jesseonate.com` refs remain in public/), pushed live. MEASURE re-confirmed DARK via the v5
  guard (harvester still absent from `launchctl list`, harvest 28d stale — E5 still owner=jesse).
  EVOLVE: SKILL 4 v6 NAP-straggler sweep across non-HTML surfaces after any NAP commit. RESULT: SHIPPED.
- **2026-06-28 — run 05 (measure-pipeline root-cause):** QC surfaces all verified CLEAN this run
  (sitemap: no phantoms/orphans, flagship Downey page present; vercel.json valid + homepage canonical
  consistent; Person/RealEstateAgent schema well-formed). No whitelisted SAFE FIX genuinely pending →
  instead of manufacturing a low-value edit, diagnosed the elephant 3 runs ignored: **MEASURE has been
  dark for 27 days because the GSC harvester + QC launchd jobs were never re-installed after the
  Mac-mini→MacBook host migration** (their generated plists still point at the dead `/Users/jtek`
  iCloud path; only `seo-brain` + `hourly-autopush` were migrated). Logged **E5 (awaiting-jesse,
  priority 0)** with a one-command fix. EVOLVE: SKILL 1 pipeline-liveness guard (≥2 FLAT runs ⇒ verify
  the harvester is alive, don't just re-report FLAT). RESULT: DRAFTED (no on-page commit — nothing broken).
- **2026-06-28 — run 04 (compliance):** Site-wide QC sweep: anchors, images, internal links,
  breadcrumb URLs, and `aggregateRating` all CLEAN. But found 12 fabricated `Review` JSON-LD nodes on
  `reviews.html`, each falsely tagged `publisher: "Google"` — the S1 aggregateRating strip missed
  these. **Stripped them (S3, schema-only 206-line removal, 0 visible content changed, 380/380
  JSON-LD valid), pushed live.** EVOLVE: extended the S1 fake-rating guard to per-`Review` markup
  (SKILL 4 v4) + added a "verify QC-script missing-asset hits before acting" guard after a
  broken-image false alarm. Flagged C10 (visible-testimonial authenticity + dormant live Google
  widget) + C11 (seller buyer-guide CTA) to Jesse.
- **2026-06-11 — run 01 (ship):** Research returned → `knowledge/best-practices-2026.md`. It read the
  code and verified two structural issues: fabricated `aggregateRating` (105 files) + ~97%-identical
  doorway city pages. **Built `tools/strip-fake-aggregate-rating.py`, stripped all 105 (compliance),
  opened robots.txt to AI crawlers, shipped `e7f4443` to production.** EVOLVE lesson: the research
  agents' raw file *counts* were off (said 74 pages, actually 153) — so the Brain now **re-verifies any
  numeric claim with its own grep before acting on it** (already applied this run; codified in SKILL 4).
