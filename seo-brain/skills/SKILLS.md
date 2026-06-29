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
