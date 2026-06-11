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

## SKILL 2 — RESEARCH (the research brain)
**Goal:** keep `knowledge/best-practices-2026.md` current; don't repeat stale advice.
1. Trigger only if knowledge > ~30 days old OR a new strategic question appeared in DIAGNOSE.
2. Run the `jessetek-seo-research` workflow (Workflow tool): 6 facet agents (SERP structure, GBP,
   reviews, citations/links, on-page/content, solo-agent breakthroughs) → 1 synthesizer.
3. Write the synthesized playbook to `knowledge/best-practices-2026.md`; merge its `top_actions`
   into the ledger (dedupe by title).
**Cost rule:** this is the most expensive skill. Cap at ~monthly. Reuse the saved workflow script.

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
**Rule:** every run must leave at least one self-edit here. That is the "gets better every run" contract.

---

## Version notes
- **v1 (2026-06-11):** Genesis. Six skills defined. Open improvement targets for next run:
  (a) auto-pull GBP insights once Jesse grants access (would make SKILL 1 measure the #1 surface,
  which is currently a blind spot — we only see website GSC, not map-pack performance);
  (b) add a "near-miss harvester" that auto-drafts on-page tweaks for position 8–20 queries.
