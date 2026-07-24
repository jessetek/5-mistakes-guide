# Skills — the editable how-to (EVOLVE rewrites this)

These are the Brain's working procedures. They are meant to be **edited every cycle** as we
learn faster/cheaper ways to do each step. Version notes at the bottom.

---

## SKILL 1 — MEASURE
**Goal:** know exactly where we stand, reach-weighted.
1. Read `../automation/.state/rank-history.json` + newest `../automation/.state/gsc-harvest-*.json`.
2. For each tracked query, record: avg position, impressions, clicks, Δ vs last snapshot.
3. Flag "near-miss" queries (position 8–20 with impressions) — cheapest wins live here.
4. Write `state/rank-snapshot.json` with the deltas + a 5-line summary.
**Cost rule:** read-only. Never re-harvest GSC here — the launchd job already does.
**Pipeline-liveness guard (v5):** if MEASURE has been FLAT for ≥2 consecutive runs, do NOT just report
FLAT again — first confirm the harvester is actually alive: check the newest `gsc-harvest-*.json` date
(stale if older than ~8 days) AND `launchctl list | grep net.jessetek.weekly-rank-watch`. A stalled
data pipeline masquerades as a stable rank. (Run 05 found the harvester dead for 27 days — see E5.)
**Frozen-tally liveness re-check (v12):** a frozen IDLE tally (SKILLS v11) may NOT assert "MEASURE dark /
pipeline still absent" from memory or a stale ledger note. Before ticking the tally, run the two cheap
liveness probes AND check the newest date actually present in `rank-history.json` (`max date across
queries`), not just `gsc-harvest-*.json`. The two GSC surfaces are INDEPENDENT: `weekly-rank-watch` →
`rank-history.json` (per-query monitor) and `weekly-gsc-harvest` → `gsc-harvest-*.json` (aggregate reach
KPI) can be alive/dark separately. If EITHER produced a date newer than the last `rank-snapshot.json`,
that is NEW data ⇒ MEASURE, do not IDLE. (Run 55: runs 53/54 tallied "weekly-rank-watch still absent"
AFTER it had been restored 2026-07-13 and had written fresh entries — the fast-path had stopped
re-verifying `launchctl`. This guard closes that blind spot.)
**Anchor-vs-commit-message guard (v12.1):** on the SAFE-FIX side of the fast-path, the authority is
`git rev-parse HEAD:public` vs `last-qc.json` public_tree_hash — NOT the commit subject line and NOT
run-log prose. If the tree hash EQUALS the anchor and the tree is clean, no new content shipped, full
stop: do NOT re-investigate a scary-looking `git show`/diff just because the newest public/ commit
message reads like a big change (e.g. "Rates page redesign"). A matching tree hash already proves the
bytes are identical to what passed full QC. Only a DIFFERENT hash unlocks the full-QC → re-anchor
branch. (Run 57 nearly burned a diff-read chasing 0c61b1e's redesign subject before confirming its
tree was still the QC-passed anchor 77a6330.)
**SAFE-FIX-eligibility over blind-tick (v12.2):** a frozen-anchor IDLE run must still spend one cheap
pass confirming NO whitelisted fix is actually shippable — do not just re-read `launchctl` and tick.
Cheapest high-signal check: walk the ledger's open items against the SAFE-FIX whitelist, then reality-
check the tempting one against two failure modes: (a) SCOPE — "author block on every money page" =
75-file sweep, NOT a small step; (b) FABRICATION — if the item's own note wants a fact you can't verify
(years/closings, review counts, which sameAs profiles exist), it's Jesse-owned. A whitelisted *category*
(e.g. E-E-A-T author block) does not make a specific *instance* shippable. When a scan comes back clean,
that negative result IS the run's value — record the number (run59: `Person` schema already on about.html
+ all case-studies, headshot assets exist, and a site-wide BreadcrumbList scan = 373/373 items resolve /
0 phantom, retiring C7's 'phantom breadcrumbs' sub-concern). Prefer verifying a backlog worry dead over
manufacturing a low-value edit.
**Provable-idle-window horizon (v12.3):** when the anchor is frozen, the whole on-page backlog gates on
Jesse's local facts, all off-page items are owner=jesse, AND the next MEASURE date is known and future,
the run can name the explicit date range through which NO autonomous non-IDLE action is even possible —
a horizon, not a vibe. As of run60 that window is 2026-07-14 → ~2026-07-20 (next weekly `rank-watch` fire
against a settled GSC window; `weekly-gsc-harvest` still owner=jesse). Every hourly Opus run inside that
window is provably IDLE before it starts, which is the concrete, dated form of the E6 cost-throttle case
(≈6 more idle Opus fires/day until then). State the horizon once per streak; don't re-raise E6 each run.
**Idle-streak token thrift (v12.4):** once a provable-idle horizon (v12.3) is named and unchanged, an
IDLE run inside it should still DO the cheap liveness re-verify (launchctl exit 0, newest `rank-history`
date vs `rank-snapshot.json`, `git rev-parse HEAD:public` == anchor + clean tree) — that is the guard
that catches a mid-horizon state change (the run55 lesson) — but LOG it as a one-line tally entry, not a
fresh multi-line paragraph restating the whole horizon. Re-derive & restate the full horizon only when a
liveness input actually changes (anchor moves, new rank-history date, launchctl drops) or the named end
date passes. Near-identical idle paragraphs are pure Opus token burn against the "idle runs near-free"
mandate; the verify is what matters, not the prose.

**Schema-agnostic rank-history read (v12.5):** the newest-`rank-history` liveness check must NOT guess at
the JSON key layout (list vs `readings` vs `history`) — that key-guessing missed on run65 (`parse-check`
fallback). Canonical read: dump the file to JSON text and regex-scan `20\d\d-\d\d-\d\d`, take max; do the
same on `rank-snapshot.json`. If newest rank-history date ⊆ snapshot dates ⇒ MEASURE dark. One-liner,
schema-independent, never silently wrong when the harvester changes its output shape.
**Ledger-note compaction over infinite append (v12.6):** the `actions-ledger.json` `updated` field is a
state marker, NOT a run journal. Do NOT append a full prose note each idle run — that grew it to ~20.8 KB
of 50 near-identical run48→run97 notes (run98), which every hourly run then re-read, taxing the
"idle runs near-free" mandate the same way v12.4 targets. Keep `updated` to a compact frozen-state tally
(horizon, MEASURE-dark cause, E5/E6 status, anchor, last MILESTONE run) + a pointer to the dated
`runs/*.md` logs, where per-run detail already lives. When it exceeds ~2–3 KB again, re-compact: surgical
line-replace + `json.loads` validate before write. The dated `runs/` log is the append-only surface; the
ledger is the current-state surface.
**Run-log append anchoring (v12.7):** appending the new run entry to the dated `runs/*.md` log costs
extra Edit round-trips when you anchor on the boilerplate `**Did NOT do…**` / `RESULT: IDLE` tail — by
mid-day that string repeats 10+ times (once per idle run) and the Edit tool refuses the ambiguous match
(hit run124: 14 identical blocks). GUARD: append by anchoring on the CURRENT-newest entry's UNIQUE `**Did:**`
sentence (it carries a distinct anchor hash / date), and paste the whole new `## runNNN … + Did + Did NOT +
RESULT` block after that entry's `RESULT: IDLE`. One Edit, no ambiguity. Never anchor an append on text
that boilerplate-repeats across entries.
**Latency-artifact honesty (v12):** if a fresh per-query pull returns 0 impr / null rank on ALL queries
INCLUDING the branded term (baseline ~2.5), treat it as a GSC ~2–3d finalization-lag empty-window
artifact, NOT a real reach collapse. Record it as pipeline-alive-but-window-empty; never write those
zeros into `goal.json` baseline_kpis (that would fabricate a regression).

## SKILL 2 — RESEARCH (the research brain)
**Goal:** keep `knowledge/best-practices-2026.md` current; don't repeat stale advice.
**Two tiers — do NOT conflate them (v13 fix):**
- **Tier A — one-question VERIFY (cheap, the ~30d gate).** When knowledge > ~30 days old AND no
  SAFE FIX is pending, run a SINGLE targeted verify: 2–4 web searches + ≤1 fetch on ONE open
  question, then APPEND a dated, source-cited refresh section to `knowledge/best-practices-2026.md`
  (don't rewrite the file) and sharpen the affected ledger `why` fields. This is what the hourly
  prompt's priority-2 "RESEARCH/VERIFY one open best-practice question" means. Costs a few searches,
  not a workflow. This IS the operative ~30d trigger.
- **Tier B — full workflow (expensive, ~quarterly).** Re-run the `jessetek-seo-research` workflow
  (Workflow tool): 6 facet agents (SERP structure, GBP, reviews, citations/links, on-page/content,
  solo-agent breakthroughs) → 1 synthesizer → rewrite the playbook + merge `top_actions` into the
  ledger (dedupe by title). Cap at ~quarterly. Reuse the saved workflow script.
**Threshold reconciliation (v13):** the file's `Refresh ~quarterly` header governs Tier B ONLY.
It does NOT license idling past 30d — a Tier-A verify is due at ~30d. Runs 42–47 wrongly read
"quarterly = fresh" and idled at 29–40d; run48 corrected this at 32d.

## SKILL 3 — DIAGNOSE
**Goal:** the ranked gap list.
1. Triangulate MEASURE (reality) × knowledge (best practice) × goal.json (target).
2. For each gap: estimate impact (reach it unlocks) and effort; compute impact÷effort; tag owner.
3. Write the ranked list into today's `runs/<date>.md`. Keep it to the top ~8 — focus beats breadth.

## SKILL 4 — ACT
**Goal:** ship the cheap, high-impact things; tee up the rest for Jesse.
- **claude-owned:** edit `../public/*.html`, schema, internal links, sitemap, new pages. Match the
  site's exact template (clone an existing page; keep nav/footer/CSS version/OG image consistent).
  Run the QC sweep from `../SITE-ARCHITECTURE.md`. Verify locally (preview server). **No git push
  without Jesse's OK.** Update the ledger entry to `done-staged`.
- **jesse-owned:** write a copy-paste-ready task (exact steps + links + the NAP/description text +
  any scripts) into the run log; set ledger `status: awaiting-jesse`.
**Cost rule:** 1–3 on-page actions per cycle. Small, verifiable, reversible.

## SKILL 5 — LEARN
**Goal:** capture cause→effect, not activity.
1. Cross-reference: did a prior `done`/`awaiting-jesse` action move its target query in MEASURE?
2. Write durable lessons into `knowledge/` (what worked → keep; what didn't → stop). Date them.
3. Update `goal.json` (run_count, status, per-target status).

## SKILL 6 — EVOLVE
**Goal:** make the Brain better than it was this morning.
1. Name the cycle's biggest friction/waste/error.
2. Make ONE concrete improvement: tighten a skill above, add a guard, retire a dead tactic,
   sharpen the research workflow prompt, or improve the ledger schema.
3. Append a dated line to `BRAIN.md` Changelog AND the version notes below.
**Rule:** every run must leave the Brain at least as sharp as it found it — but a *verified frozen-IDLE*
run (public/ hash == `last-qc.json`, harvester dark, knowledge <30d) has nothing genuine left to sharpen,
and manufacturing a self-edit anyway is churn, not improvement (v6→v10 burned five version bumps doing
exactly this). On such runs the contract is satisfied by appending ONE LINE to the rolling idle-streak
tally in `runs/<date>.md` — no new verbose run section, no forced SKILLS version bump, no public/ commit.
Only spend a real EVOLVE (and a version bump) when something actually changed or broke. "Gets better
every run" means *compounding*, which on a frozen clean site means staying quiet and cheap.

---

## Version notes
- **v14.9 (2026-07-20):** Run 170. **Long idle streaks must run a latent-defect sweep, not only re-check the anchor.**
  The single-probe fast-path (v14.5-14.8) proved a clean tree by `HEAD:public == last-qc anchor`. That is a
  correct test of ONE thing: *no un-QC'd NEW content slipped in since the anchor.* It says NOTHING about latent
  defects sitting in already-committed files — the anchor moved to those files at commit time and never got
  re-audited. Runs 152-169 (18 consecutive IDLE) rode that blind spot while `public/sitemap.xml` carried 5
  future-dated `<lastmod>` values (a real crawl-signal loss). **Rule added to SKILL 4/EVOLVE:** after a run of
  ≥~6 consecutive frozen-IDLE probes, one run must spend a *single* cheap latent-defect sweep over the
  zero-Jesse-input whitelist surfaces instead of a 7th blind anchor re-check — concretely: (1) sitemap
  `<lastmod>` sanity (no future dates; parses; loc count plausible), (2) JSON-LD still valid on a sampled money
  page, (3) robots/canonical unchanged-and-correct. Anchor-equality is necessary but not sufficient for
  "nothing shippable." A found defect breaks the streak with a real SHIPPED fix (C13); a clean sweep re-arms
  the fast-path for another ~6 runs. Keeps idle cheap WITHOUT going structurally blind to pre-existing rot.
- **v14.7 (2026-07-20):** Run 157. **Repeat same-day frozen-IDLE runs collapse to a one-line log entry.**
  v14.6 fixed *which files* a frozen IDLE touches (run-log + ledger-header only); v14.7 fixes *how much*
  gets written to the run-log itself. `runs/2026-07-20.md` accumulated FIVE full IDLE blocks (runs 152-156)
  in a single day — each re-stating the same probe tuple in ~6 lines. That is same-day bloat, not compounding.
  **Rule:** the FIRST frozen-IDLE run of a given day writes a full block (establishes the day's anchor tuple);
  every SUBSEQUENT frozen-IDLE run the same day, where the probe tuple is byte-identical to the prior run,
  appends a SINGLE line — probe result + verdict + the one EVOLVE/Did-NOT delta — instead of a new block.
  A full block returns only when a probe field actually moves (anchor/mtime/knowledge). Keeps the hourly
  idle cadence near-free on the disk-write axis too, not just the tool-call axis.
- **v14.6 (2026-07-20):** Run 156. **Single-probe fast-path is the steady-state default; minimize per-run
  writes while frozen.** v14.5 established the one-probe IDLE check; v14.6 codifies what mutations a frozen
  IDLE run should make afterward. When the probe returns the unchanged frozen tuple (tree==anchor + clean +
  newest-rank-date==snapshot + knowledge <30d), the ONLY required writes are: (1) a compact run-log entry in
  `runs/<today>.md` and (2) the ledger `updated` header field. Do NOT edit individual ledger action-objects,
  re-touch state/*.json, or re-narrate the horizon — nothing about the actions changed, so editing them is
  churn that taxes the "idle near-free" mandate. A ledger action-object edit is warranted ONLY when a probe
  field actually changes: the anchor moves (content shipped/QC'd), rank-history mtime advances (MEASURE
  candidate), or knowledge ages past 30d (RESEARCH due). **Rule:** frozen IDLE = run-log + ledger-header
  only; touch nothing else.
- **v14.5 (2026-07-20):** Run 155. **Idle fast-path = ONE deterministic probe.** First run under the v14.4
  "frozen-state re-verify" label. Codifies the cheapest sufficient IDLE check so the hourly loop honors the
  "idle runs near-free" mandate: a SINGLE Bash call that emits (1) `git rev-parse HEAD:public` tree hash vs
  the `last-qc.json` anchor, (2) the newest distinct date in `rank-history.json` (with its mtime), and
  (3) `best-practices-2026.md` mtime — plus `git status --porcelain` — is enough to reach the four-tier
  verdict. If tree-hash==anchor + clean + newest-rank-date==snapshot + knowledge <30d, the verdict is IDLE
  and no further probing, per-check narration, or full QC battery is warranted. **Rule:** don't fan the idle
  pre-check across many tool calls; one probe in, verdict out, log, exit.
- **v14.4 (2026-07-20):** Run 154. **Retire the "fire-day" framing once the estimate is falsified.** v14.3
  said don't re-estimate a new horizon; v14.4 goes one step further on the *labeling*: after a specific
  expected fire date (07-20) has passed across multiple runs with no mtime advance, STOP tagging runs as
  "fire-day re-verify #N" and STOP re-asserting "today IS the fire day." That framing is what pulled runs
  152→154 into narrating phantom precision about a date that carries no signal. **Rule:** revert to the plain
  "frozen-state re-verify" label; the next-fire is simply *unknown — whenever `rank-history.json` mtime moves
  past 07-13*. One line, re-scan mtime, IDLE. No calendar date belongs in an idle run's reasoning until the
  file itself moves.
- **v14.3 (2026-07-20):** Run 153. **HORIZON-DATE ≠ FIRE-SIGNAL corollary to v14.2(b).** Same fire-day,
  one hour later: 07-20 arrived and passed with `rank-history.json` mtime *still* unmoved at 07-13 15:06.
  The temptation on a "the estimate said it'd fire today" run is to treat the calendar horizon as evidence
  the job is broken and reach for a manual kickstart. It is not. The "~07-20 Mon" horizon was always an
  estimate; the ONLY authoritative fire-detector is the mtime/newest-distinct-date advancing (v14.2b).
  **Rule:** an expected fire date passing WITHOUT an mtime advance is a plain IDLE, not an anomaly and not
  grounds to intervene — the job fires on its own launchd calendar; keep re-scanning mtime each run and let
  the first genuine advance be the MEASURE trigger. Do not re-estimate a "new" horizon date each run either
  (that just re-arms the same false-anomaly next time); trust the file, not the calendar.
- **v14.2 (2026-07-20):** Run 152. Two things, discovered on the weekly-fire day itself.
  (a) **VERSION-CITATION DRIFT guard.** Ledger prose from runs ~148–151 repeatedly cited "per v14.3"
  / "v14.3 governs tomorrow's fire" as if it were a written rule — but SKILLS.md only ever reached
  **v14.1**; v14.2 and v14.3 were NEVER written. A run-log/ledger citation of a version that doesn't
  exist in this file is a phantom authority. **Rule:** before writing "per vX.Y" in a ledger/run note,
  confirm vX.Y actually exists here (`grep -n "vX.Y" SKILLS.md`); if the rule isn't written down, either
  write it or describe the behavior inline — never cite a version you didn't ship. This v14.2 now
  actually codifies the MEASURE-fire protocol those notes were gesturing at:
  (b) **FIRE-DAY MEASURE protocol (SKILL 1).** On/after an expected `weekly-rank-watch` fire, "the job
  is loaded" != "it fired." The authoritative freshness signal is `automation/.state/rank-history.json`
  **mtime** + its newest distinct date — NOT `launchctl list` (which only proves the plist is
  registered). If mtime hasn't advanced past the last-snapshot date, MEASURE is still dark → IDLE; do
  NOT manually `launchctl kickstart` the job to force data (that's E5, owner=jesse, outside the
  SAFE-FIX whitelist, and a GSC ~2-3d finalization-lag empty window is the likely result anyway). The
  MEASURE candidate is the first hourly run where rank-history mtime/date has genuinely advanced.
- **v14.1 (2026-07-18):** Run 127. Fast-path FALSE-ALARM guard. This run's opening probe used
  `git log -1 --format='%H %s' -- public/` and read its result (`0c61b1e` "Rates redesign") as a NEW
  post-anchor public/ change → briefly treated a frozen run as a state change. That command returns the
  **last commit id that touched public/**, which is NOT the fast-path comparand. **Rule reinforced in
  SKILL 4:** the ONLY valid anchor comparand is the subtree **tree hash** from
  `git rev-parse HEAD:public` vs `last-qc.json.public_tree_hash` — never a commit id, commit subject, or
  `git log -- public/` output. A commit can touch public/ and still leave the tree byte-identical to the
  anchor (e.g. an already-QC'd commit like `0c61b1e`, re-anchored at run41). One clean `git rev-parse`
  settles it; don't spin up a diff/QC sweep off a commit-log misread.
- **v14 (2026-07-14):** Run 55. Broke the run53/54 frozen-IDLE tally by re-checking pipeline liveness
  and finding **E5 partially resolved**: `net.jessetek.weekly-rank-watch` was re-installed 2026-07-13
  (correct MacBook path) and had written fresh 2026-07-13 GSC data into `rank-history.json` — while
  runs 53/54 were still asserting "weekly-rank-watch still absent" from the stale ledger note. **Added
  the SKILL 1 frozen-tally liveness re-check + latency-artifact honesty guards (v12 tags):** a frozen
  tally must probe `launchctl` + `max(rank-history date)` before claiming MEASURE-dark, treating the two
  GSC surfaces (rank-history monitor vs gsc-harvest aggregate) as independent; and all-zero pulls that
  include the branded term are logged as GSC finalization-lag artifacts, never written to baseline_kpis.
  Wrote the first `state/rank-snapshot.json`. Result: MEASURED, not IDLE.
- **v13 (2026-07-13):** Run 48. Broke a 7-run frozen-IDLE streak (42–47) that idled 29–40d while
  citing the knowledge file's `Refresh ~quarterly` header as "fresh" — but the hourly prompt's
  priority order triggers RESEARCH at **~30d stale**. **Split SKILL 2 into two tiers:** Tier A =
  cheap one-question VERIFY (the real ~30d gate; a few searches, append a cited section) vs Tier B =
  the ~quarterly full 6-agent workflow. "Quarterly" governs Tier B only and does NOT license idling
  past 30d. Run48 fired Tier A at 32d: appended a 7-source-cited post-March-2026-Core-Update refresh
  (43% packs w/ AI Overviews; review recency ~2.3×; on-page now #1 local-organic factor; entity
  authority > keyword match; FAQPage must mirror visible Q&A) → sharpened C2/C6/J1/J2 in the ledger.
- **v12 (2026-07-09):** Run 41. The 30-run frozen streak (11–40) broke: Jesse shipped the Rates page
  redesign (`0c61b1e`), moving `HEAD:public` `09a40ce`→`77a6330`. **First real firing of the fast-path's
  DIFFERENT-hash → full-QC → re-anchor branch** — it worked exactly as designed (v9–v11 machinery
  compounds, doesn't churn). Full QC passed clean (380/380 JSON-LD, 0 broken img/OG, 0 em-dash-as-punctuation
  in visible prose, rates.html carries no aggregateRating/Review nodes and a truthful un-inflated
  "5.0★ Google"); re-anchored `last-qc.json` to `77a6330`. **Codified a known-acceptable QC exception:**
  the canonical check will ALWAYS flag `404.html` + `offline.html` as "missing canonical" — that is CORRECT
  (error + service-worker-offline utility pages should omit `rel=canonical`), so full-QC runs treat exactly
  those two as expected, not a regression. Do NOT "fix" them. Also confirmed the human-voice grep must strip
  HTML comments (`<!-- NAV — DESKTOP -->`) and JS placeholder `>—<` spans and ignore numeric/currency/grade
  en-dash ranges (`$10K–$30K`, `K–5`) before counting violations — the raw grep's ~280 hits are ~99% these
  false positives; the real signal is em-dash (`—`) inside visible text nodes, which was 0.
- **v11 (2026-06-29):** Run 11 (6th run today, 5th consecutive frozen IDLE). **Retired the forced-self-edit
  tactic.** v6→v10 each bumped a SKILLS version on a frozen, clean, harvester-dark site — five increasingly
  marginal tweaks to the same fast-path, which is the "churn, don't compound" anti-pattern the Brain is
  supposed to avoid (BRAIN.md principle 6). The fast-path is now mature and anchored in `last-qc.json`;
  there is nothing left to genuinely sharpen until the site changes or GSC wakes up. **Fix: relaxed SKILL 6's
  "every run must self-edit" rule** so a verified frozen-IDLE collapses to a one-line tally — no new verbose
  run section, no version bump, no commit-for-bookkeeping's-sake. This is the last structural change the
  frozen state warrants; subsequent idle hours should just tick the tally and exit near-free.
- **v10 (2026-06-29):** Run 10 (5th run today). 4th consecutive frozen IDLE. **Persisted the fast-path
  anchor out of prose and into state.** v9 keyed the fast-path off the `public/` subtree hash but the
  "validated-clean" value (`09a40ce`) lived only inside run-log/SKILLS prose — every future full-QC run
  would have had to remember to re-type the new hash in narrative text, and a fast-path that trusts a
  hand-copied string is one typo from skipping QC on a tree that actually changed. **Fix: write
  `seo-brain/state/last-qc.json`** recording `public_tree_hash` + which run/result last passed full QC.
  Protocol now: compare `git rev-parse HEAD:public` to `last-qc.json:public_tree_hash`; EQUAL + clean +
  knowledge <30d → trust the stored verdict, IDLE without re-QC; DIFFERENT → run the full QC battery and,
  when it passes, rewrite `last-qc.json` to the new hash. This run: `09a40ce` == stored hash → IDLE.
- **v9 (2026-06-29):** Run 09 (4th run today). 3rd consecutive frozen IDLE. **Fixed a latent bug in the
  v8 fast-path:** it keyed off whole-`HEAD` equality, but the Brain commits its own `seo-brain/`
  bookkeeping every idle run — so HEAD advances each hour while `public/` is byte-identical. After the
  first idle, "HEAD unchanged since last run" is therefore always FALSE, which would force a needless full
  QC battery every run (defeating the whole near-free goal). **Fix: key the fast-path off the `public/`
  subtree hash, not whole-HEAD — `git rev-parse HEAD:public`.** If that hash equals the value the last
  full-QC run recorded (run 07 validated tree `09a40ce` CLEAN) AND the tree is clean AND knowledge <30d,
  the QC verdict still holds regardless of how many bookkeeping commits landed on top. This run: public/
  tree `09a40ce` (last touched by `d74c8dd`, run06's feed.xml fix) == run07's validated-clean state →
  IDLE without re-running QC.
- **v8 (2026-06-29):** Run 08 (3rd run today). 2nd consecutive IDLE on a frozen HEAD. **Frozen-state
  fast-path added to SKILL 1 + SKILL 4:** the only state that changes hour-to-hour *without a new commit*
  is the data pipeline. So at the top of each run, do the 3 cheap checks first — `git status` (clean?),
  `git rev-parse HEAD` vs the HEAD the previous run logged, and the harvester liveness (newest
  `gsc-harvest-*.json` date + `launchctl list | grep weekly-rank-watch`). **If the tree is clean AND HEAD
  is unchanged since the last run AND knowledge <30d, the previous run's full QC verdict still holds
  (public/ is byte-identical) — skip re-running the expensive QC battery and decide IDLE/MEASURE off the
  liveness checks alone.** Only re-run the full QC sweep when HEAD has moved (a new commit could have
  introduced a regression) or knowledge has gone stale. Keeps idle runs genuinely near-free, which is the
  stated cost goal.
- **v7 (2026-06-29):** Run 07 (2nd run today, laptop re-woke). Full QC swept CLEAN — 380/380 JSON-LD
  valid, 0 broken img/og, 0 NAP stragglers (post-C12), vercel.json valid (2 rewrites / 21 redirects).
  IDLE was correct. **Guard added to SKILL 4 (sitemap QC) — two standing FALSE POSITIVES to ignore so
  future runs stop re-investigating them:** (1) a naive `*.html`-glob sitemap-drift check flags
  `/insights/feed.xml` as a "phantom" — it's the real RSS file, never an HTML page, intentionally not a
  sitemap `<loc>`. (2) The site has **NO `index.html`**; the homepage is `public/home.html`, served at
  `/` via the vercel.json rewrite `{"/" → "/home"}` and 301'd back with the redirect `{"/home" → "/"}`,
  and home.html canonicals to `https://jessetek.net/`. So `/home` will ALWAYS look like an "orphan
  not in sitemap" to a file-glob check — it is correct as-is; do NOT add `/home` to the sitemap (would
  create a duplicate of `/`). Net: treat feed.xml + home.html as known-good; only act on sitemap drift
  that is neither of these.
- **v1 (2026-06-11):** Genesis. Six skills defined. Open improvement targets for next run:
  (a) auto-pull GBP insights once Jesse grants access (would make SKILL 1 measure the #1 surface,
  which is currently a blind spot — we only see website GSC, not map-pack performance);
  (b) add a "near-miss harvester" that auto-drafts on-page tweaks for position 8–20 queries.
- **v3 (2026-06-28):** Run 03. Friction: nearly went to RESEARCH/IDLE before noticing the two
  `UX-AUDIT-*.md` files held a pre-vetted High-confidence broken-link finding. **Guard added to
  SKILL 2 (DIAGNOSE/ACT):** before declaring IDLE, mine `UX-AUDIT-*.md` and `seo-brain/drafts/` for
  High-confidence broken-link/markup items, re-verify each against LIVE code (audits go stale), then
  ship the whitelisted ones. Did exactly this → fixed 28 dead `#contact` anchors (C9, commit 559ef36).
- **v4 (2026-06-28):** Run 04. Two compounding lessons:
  (a) **COMPLIANCE GUARD — extend the S1 fake-rating sweep to per-`Review` schema, not just
  `aggregateRating`.** Found 12 hardcoded `Review` nodes on `reviews.html` each tagged
  `publisher: Organization "Google"` — a machine-readable claim that fabricated testimonials were
  Google-published. S1 (Jun-11) only stripped `aggregateRating` and missed these. **New standing QC
  in SKILL 4:** grep `"@type": "Review"` + `"aggregateRating"` + `"ratingValue"` site-wide; any
  self-hosted review markup attributing reviews to Google (or carrying a rating the site can't
  substantiate) is the same FTC/Google liability → strip the JSON-LD (schema-only, leave visible
  text for Jesse). Ineligible for rich results since 2019 anyway = zero ranking downside.
  Shipped S3 (206-line JSON-LD-only removal, 380/380 blocks valid, 0 visible content touched).
  (b) **QC-SCRIPT GUARD — verify "missing asset" findings before believing them.** A broken-image
  sweep this run reported ~50 "MISSING IMG" hits that were ALL a bash word-splitting artifact in the
  ref-extraction loop (the files existed; 206 img files tracked). Rule: when a QC script flags
  missing files/links, spot-check 2-3 with `ls`/`git ls-files` before acting — never ship a
  "fix broken X" change off an unverified script count. (Negative result is also a win: anchors,
  images, internal links, breadcrumb URLs, and aggregateRating are all CLEAN site-wide as of run 04.)
- **v6 (2026-06-29):** Run 06. A NAP commit is a QC trigger. Jesse's commits `ebe2343`/`62e6676` had
  just changed the site phone + email; sweeping for stragglers found the RSS feed (`insights/feed.xml`)
  still carried the OLD `jesse@jesseonate.com` in `<managingEditor>`/`<webMaster>` — a bulk
  find-replace had missed the non-HTML surface. **Guard added to SKILL 4:** after any NAP-touching
  commit (phone/email/address), grep the canonical value across ALL file types — `*.html` AND
  `*.xml` / `*.json` / `*.webmanifest` / `feed.*` — and reconcile stragglers to the canonical. Ignore
  reserved-fictional placeholders (`555-0123`, `you@email.com`) — those are intentional `<input>` hints,
  not NAP claims. Shipped C12 (2-line feed.xml fix, 0 old-domain refs remain, valid XML).
- **v5 (2026-06-28):** Run 05. Friction: 3 prior runs reported MEASURE "FLAT (harvester stalled,
  non-blocking)" without ever diagnosing it — the brain's core metric had been dead 27 days.
  Root cause: the Mac-mini→MacBook host migration only re-installed `seo-brain` + `hourly-autopush`;
  the GSC harvester + QC launchd jobs were left pointing at the dead `/Users/jtek` iCloud path and
  never re-loaded (E5, owner=jesse). **Guard added to SKILL 1:** treat ≥2 FLAT runs as a pipeline-
  liveness check, not a rank report. Also verified this run: sitemap, vercel.json routing/canonical,
  and the Person/RealEstateAgent schema are all clean — so a clean-QC run should DIAGNOSE the loop's
  own machinery (crons, creds, data freshness) rather than manufacture a low-value on-page edit.
- **v15 (2026-07-20):** Run 171. Two-part sharpening after run170's latent-sweep ship.
  (1) **Anchor rotation:** the frozen fast-path's `HEAD:public==anchor` check is only valid against the
  CURRENT committed public tree. When a SAFE FIX ships (like run170's sitemap), `public/` changes and the
  anchor MOVES — retired `77a63300` → now **`0012fbc7`**. Guard: after any push that touches `public/`,
  record the new `git rev-parse HEAD:public` as the anchor in the run log; do not compare later runs to a
  stale hash (a stale-anchor compare would false-positive "un-QC'd content" on a clean tree).
  (2) **Sweep cooldown:** the v14.9 latent-defect sweep is for LONG idle streaks, not every run. Do NOT
  re-run it in the run(s) immediately following a sweep-ship — the just-audited surfaces (sitemap, schema,
  OG, anchors, robots/canonical) don't re-rot in an hour. Only re-arm the sweep after the frozen streak has
  re-accumulated (≈≥8 idle runs, matching runs152-169), or when a public/ change lands from another source.

- **v16 (2026-07-21):** Run 178. The latent-defect sweep has now paid out on BOTH re-arms — run170 caught
  future-dated `<lastmod>`, run178 caught a **malformed image sitemap** (`sitemap-images.xml` had 5 bare
  unescaped `&` → whole file failed `xmlParseEntityRef`, so Google discarded every image entry). The
  ~8-run cadence is validated: keep it. **Standing sweep checklist (make these the first probes each re-arm,
  they are cheap and high-yield):** (1) `xmllint --noout` EVERY file in `public/**/*.xml` (not just
  `sitemap.xml` — the images sitemap and feed are separate files and were the ones that rotted); (2) bare-`&`
  / unescaped-entity grep across xml; (3) future-dated `<lastmod>` vs `date +%Y-%m-%d`; (4) regression greps
  for `aggregateRating` (must be 0) and false review-count claims (must be 0). A found defect ships and resets
  the cooldown (next re-arm ≈run186); a fully-clean sweep just re-arms and the run IDLEs. **Scope discipline
  reaffirmed:** the same sweep found 53 em-dashes in the image sitemap — logged as C15 (queued), NOT fixed in
  the same run. One structural QC fix per re-arm; copy-voice rewrites are a separate scoped pass.

- **v17 (2026-07-22):** Run 186. **Falsifies v16's "the sweep pays out on every re-arm."** The 3rd re-arm ran
  the full checklist and found the structural layer **fully clean** — no ship. This is the correct, expected
  outcome now, not a miss: run170's future-lastmod and run178's malformed-XML were both one-time
  *sitemap-generator artifacts*; once fixed they hold, so the structural surface is now well-covered and a
  **clean sweep = SUCCESS**. Guidance: (a) keep the ~8-run cooldown and the standing checklist (still cheap
  insurance against a generator regression), next re-arm ≈run194; (b) do NOT manufacture a "ship" from a clean
  sweep — IDLE is the right result; (c) the sweep's remaining frontier is *content/voice debt*, which is
  **out-of-whitelist** (owner=jesse), so future re-arms should expect clean structural results. **Two new
  sweep-hygiene rules learned this run:** (1) **Verify resolver false-positives before alarming** — a naive
  internal-href check flagged 149 "broken `/`" links + 1 `sms:`; both were artifacts (`/` is served by a
  `vercel.json` rewrite `/ → /home`, so the homepage is `home.html` not `index.html`; `sms:` is a valid URI
  scheme). Always reconcile a "broken link" finding against `vercel.json` rewrites/redirects + URI schemes
  before treating it as a defect. (2) **Don't hand-edit generated/derived files** — `sitemap-images.xml`
  captions are generated and DIVERGENT from live page OG (sitemap title used `·`/`—`; `home.html` uses `|`/`:`),
  so C15's dashes must be fixed at the page-source and the sitemap regenerated, never edited directly. C15 was
  re-scoped from "53 dashes in one file" to its true size: **296 em/en dashes across 140/154 HTML pages**
  (site-wide human-voice debt, owner=jesse, dedicated skill pass with the grep QC gate).

- **v18 (2026-07-22):** Run 187. **The v15 anchor is a git TREE hash, not a commit hash — never confuse them.**
  This run I first probed with `git log -1 --format=%H -- public/`, which returns the last *commit that touched
  public/* (`5bbc6e61`, run178's C14 ship) and momentarily false-read as "anchor rotated." The recorded anchor
  `bee60a73` comes from `git rev-parse HEAD:public` = the *tree object* of the public/ directory (its content),
  a different object class. Only the tree hash is the correct frozen-state probe: it stays constant across
  seo-brain-only commits (which don't touch public/) and changes iff public/ CONTENT changes — exactly the
  invariant we want. The commit hash, by contrast, moves whenever any public/ file is committed and would
  drift/mislead. **Guard:** always verify the anchor with `git rev-parse HEAD:public | cut -c1-8`; if a probe
  ever seems to show rotation, reconcile against THIS command before alarming, and never "correct" the recorded
  anchor to a commit hash. (Frozen-streak status unchanged: 9th clean re-verify, sweep re-arms ≈run194.)

- **v19 (2026-07-23):** Run 194, latent-sweep re-arm. **The sweep must examine the REMAINDER, not just tally
  the healthy majority.** Every prior sweep recorded "canonicals 151/151 jessetek.net 0 www" and moved on — but
  154 HTML pages exist, so "151/151" silently accepted 3 pages WITHOUT a canonical as if they didn't count. This
  run inverted the lens and inspected those 3: `offline.html` + `404.html` correctly carry `noindex`, but
  `img/og-generator.html` (a public dev tool, OG-card generator, no `<title>`, not in sitemap) had NEITHER
  canonical NOR noindex → a crawlable/indexable thin non-customer page diluting quality signals. Shipped C16
  (added `noindex, nofollow`, whitelisted robots/meta). **Guard added to the standing sweep:** after tallying the
  N pages that PASS a check, always enumerate the (total − N) that don't and classify each — a healthy-looking
  ratio is a hiding place, not an all-clear. Two grep lessons reconfirmed: (a) `grep -r --include=*.html` is
  UNRELIABLE in the ctx sandbox (returned 0 for canonicals that demonstrably exist) — verify HTML-content checks
  with a python glob, not recursive grep; (b) reconcile any zero-count against a known-present example before
  trusting it. 3rd real ship from re-arms (run170, run178, run194); structural layer otherwise clean. Next
  re-arm ≈run202.

- **v20 (2026-07-23):** Run 202, latent-sweep re-arm. **The structural sweep has CONVERGED — the remainder
  frontier is empty.** Ran the full v19 sweep: layer clean (4/4 XML well-formed, 0 future lastmod, 151+170 loc,
  0 aggregateRating/Review, 380/380 JSON-LD valid, 0 missing og targets, 0 www canonicals, 0 bare `&`). The v19
  remainder audit — the whole point of the last EVOLVE — now returns **hascanon=151, noindex=3, NEITHER=empty**:
  every one of the 154 pages is either canonical or noindex, because run194 closed the last neither-page. So the
  remainder hiding-place v19 warned about is exhausted at the structural layer; the only unswept frontier left is
  content/voice debt (C15, 296 site-wide dashes), which is out-of-whitelist owner=jesse. **Convergence rule:**
  after two consecutive clean re-arms (run186, run202) AND a proven-empty remainder, future re-arms can revert to
  the cheap single-probe UNLESS the `public/` HTML file-count OR the canonical/noindex tally changes — a NEW page
  is the only way a structural defect can re-enter, so gate the expensive full sweep on that delta instead of
  running it blind every 8 runs. The v19 grep-artifact lesson reconfirmed once more: raw `grep '<loc>'` reported
  0, xmllint xpath confirmed 151 — always cross-check zero-counts. Cooldown reset, next re-arm ≈run210.

- **v21 (2026-07-23):** Run 210, the ≈run210 re-arm point v20 predicted. **v20's sweep-gate got its first live
  test and HELD.** At the scheduled re-arm the gate fired: `public/` file-count = 380, unchanged from the recorded
  baseline, so no new page entered and no structural-defect vector could have re-appeared — the expensive full
  sweep was correctly SKIPPED and the cheap single-probe was sufficient. v20 is now validated end-to-end, not just
  theorized. **Rule change:** the latent-sweep no longer needs a fixed ~8-run cooldown cadence at all — retire the
  cooldown counter and make the sweep purely **event-triggered** on a `public/` file-count OR canonical/noindex-tally
  delta. Re-arm ONLY when the gate detects a structural change (a new/removed page); while the tree is frozen, idle
  runs stay near-free indefinitely with no scheduled "expensive" run looming. This closes the loop v14.9 opened:
  the latent-defect surface is fully covered by cheap structural anchors, and the full sweep is now demand-driven.
