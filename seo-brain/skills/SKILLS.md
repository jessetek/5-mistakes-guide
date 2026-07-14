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
