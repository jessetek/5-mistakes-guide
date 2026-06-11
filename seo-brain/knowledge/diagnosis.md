# Diagnosis — what's actually wrong (living doc)

_Last updated: 2026-06-11 (run 01). Update each MEASURE/DIAGNOSE cycle._

## TL;DR
**Reach, not rank, is the blocker.** The site ranks well for the handful of impressions
it gets, but Google barely surfaces it. Fixing this is ~80% off-page (Google Business
Profile, reviews, citations, links) and ~20% on-page.

## Evidence (GSC, 28 days ending 2026-06-01)
- **169 impressions, 4 clicks** total across all queries. That is the whole story.
- `real estate agent` → avg position **3.9**, but only **7 impressions**. A high average
  position on tiny impressions = personalized/hyper-local searches (Jesse, people near him),
  **not** real competitive ranking. If the site truly ranked #4 for a Downey searcher, it
  would log hundreds–thousands of impressions.
- `realtor` → pos 4.6 / 22 impressions. `jesse onate` (branded) → pos 2.5 / 25 impressions / 4 clicks.
- Branded search works; non-branded discovery barely exists.
- **www/non-www split:** GSC shows impressions on BOTH `https://jessetek.net/...` and
  `https://www.jessetek.net/...`. Canonicals point to apex (good), but confirm a hard 301
  www→apex at the Vercel domain level so authority isn't split.

## Why the head term can't be won organically (solo agent)
A 2026 SERP for "real estate agent [city]" is, top to bottom: AI Overview (sometimes) →
**local map 3-pack** (Google Business Profiles) → a few directory results
(Zillow, Realtor.com, Redfin, Homes.com) → maybe 2–3 organic spots left, usually also
directories. An individual agent's own domain is not structurally positioned to take #1
organic there. **So the goal is reframed** (see `ranking-strategy.md`).

## Off-page status (the real gap)
- **Google Business Profile:** UNCONFIRMED whether claimed/verified/optimized. This is the
  single highest-impact lever for everything "near Downey" and the Brain **cannot do it** —
  only Jesse can. _Top open question._
- **Citations:** `../automation/.state/citation-audit.json` says first run found **no claimed
  profiles to audit** → the LOCAL-CITATIONS.md playbook was written but **not executed**.
- **Reviews:** `../public/reviews.html` is hardcoded; no live Google reviews integration;
  review volume/velocity on GBP unknown.
- **Backlinks:** few/none. SEO-NEXT-STEPS.md backlink plan not yet executed.

## On-page gaps the Brain CAN close
1. **No page targets "real estate agent Downey" precisely.** Homepage H1 is "Confused by the
   market? You found the right agent." (no city, no "real estate agent"). Closest geo page is
   `neighborhoods/downey.html` ("Downey Real Estate, Done Right"). The `best-bilingual-realtor-*`
   and `first-time-buyer-*` page families exist, but **no `real-estate-agent-downey`**.
2. **Schema is missing `sameAs` and a site-wide `aggregateRating`** linking GBP/Zillow/Realtor.com —
   weakens entity consolidation for the branded knowledge panel.
3. **AI-crawler block:** `robots.txt` blocks Google-Extended, PerplexityBot, GPTBot, etc.
   This forfeits AI Overview / Perplexity visibility (a growing real-estate research surface).
   It does **not** hurt classic Google rank. Strategic call for Jesse.
4. **Internal linking** to a Downey-agent hub is thin.

## What is already excellent (don't re-do)
Compressed images + WebP, zero-CLS, canonical/hreflang en-es, ~100-URL sitemap + image sitemap,
RealEstateAgent + Breadcrumb + FAQ + Article JSON-LD, security headers, PWA, fast Core Web Vitals,
47 city pages, 14 insights posts, Spanish tree. Technically top-5% of realtor sites.
