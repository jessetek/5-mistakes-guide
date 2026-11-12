# Jessetek weekly SEO engine

Runs once a week in the cloud with nobody watching. The goal: make jessetek.net the page Google,
Maps and AI answers trust for "realtor" and "real estate agent" in Downey and the surrounding cities,
so Jesse reads as the obvious local choice.

Each run ships three things:
1. **One new article** for a local search people actually make.
2. **One site upgrade**: a new city agent page, a fix, internal links, or a refresh of an old page.
3. **A Google Business Profile post** that Jesse pastes into GBP himself. The local map pack is the
   biggest lever, and only Jesse can post there.

Why it is built this way: the old SEO brain (`../seo-brain/`, retired 2026-08-05) depended on Search
Console data. When that feed died it logged "IDLE" for weeks and published nothing. This engine
**always ships**. Data makes it smarter, but it never blocks the work.

The current directory is the repo root (`jessetek/5-mistakes-guide`). Vercel deploys `main`
automatically, serving `public/`. The engine lives in `seo-engine/`, which is not published.

---

## Step 0: Orient (cheap)
1. `git pull --rebase --autostash origin main`
2. Read `seo-engine/LEARNINGS.md` first. It is what last week taught you; follow it.
3. Read `seo-engine/POSITIONING.md` (facts you may state, things you must never say, voice).
4. `python3 seo-engine/tools/engine.py status`
5. If `seo-engine/data/gsc-latest.json` exists and is under 21 days old, read it. Queries in positions
   5 to 20 with impressions are the best targets. A topic that serves one of them jumps the queue.
   If the file is missing or stale, continue without it.

## Step 1: Pick the article topic
- Default: the first `status: "queued"` topic in `seo-engine/topic-queue.json`.
- **Monthly rate watch:** if this run falls in the first 7 days of the month and no
  `socal-rate-watch-<month>-<year>` article exists for this month, write that instead. Use the real
  Freddie Mac PMMS 30-year and 15-year numbers for the latest Thursday (search the web, cite freddiemac.com).
  If you cannot source the real number, skip the rate watch and use the queue.
- Do not cannibalize. Before writing, check that no existing page targets the same keyword:
  `grep -ril "<keyword words>" public --include=*.html`. City pages already exist for first-time buyers
  (`/first-time-buyer-<city>`), selling (`/sell-over-asking-<city>`) and city guides (`/neighborhoods/<city>`).
  An article must serve a different intent and link to those pages instead of repeating them.
- If the topic would only work with numbers you cannot source, skip it (mark `skipped` with the reason) and take the next one.

## Step 2: Research (real facts only)
- City numbers (median price, days on market, residents, ZIPs, schools, neighbors) come from
  `seo-engine/data/cities.json`. That is the site's own data. Never contradict it. Write "around $926K"
  and name the source as "my Downey market guide" with a link to `/neighborhoods/<city>`.
- Anything else (programs, tax rules, rates, insurance, laws, landmarks, transit) must come from a page
  you fetch this run. Prefer .gov, county, city, Freddie Mac, CAR and school district sites. Put each one
  in the spec's `sources`. If you cannot verify it, leave it out.
- Spend no more than about 15 web lookups. Depth beats breadth.

## Step 3: Write the spec
Create `seo-engine/drafts/<slug>.json` (format documented at the top of `seo-engine/tools/engine.py`).

Rules for the article:
- 1,200 to 1,800 words in `body_html`. Semantic HTML only: `<h2>`, `<h3>`, `<p>`, `<ul>`, `<ol>`,
  `<table>`, `<strong>`, `<a>`. No inline styles, no images you did not verify exist in `public/img/`.
- The first 2 paragraphs answer the search question directly, with the primary keyword in the first 100 words.
- Use `<h2>` headings phrased the way people search ("How much are property taxes in Downey?").
- A table where comparison helps (prices, timelines, costs).
- At least 4 in-sentence links to other site pages: the city guide (`/neighborhoods/<city>`), one tool or
  guide (`/calculator`, `/buyer`, `/seller`, `/valuation`, `/checklist`, `/rent-vs-buy`, `/seller-net`),
  one related article (`/insights/<slug>`), and a case study or `/reviews` where it fits.
- `tldr`: 3 to 5 plain takeaways. `faq`: 4 to 6 real questions with 2 to 4 sentence answers.
- `cta`: match the intent. Buyers go to `/zoom` ("Book my 15-min call"), sellers to `/valuation`
  ("Get my home value"), and people who are curious to `/move` ("Take the Move Up Quiz").
- `h1` may italicize the key phrase with `<i>`, like the rest of the site. Keep it under 60 characters.
- `title` 45 to 65 characters, with the keyword and the city. `description` 140 to 160 characters, written for a human.
- Follow POSITIONING.md: Jesse's first-person voice, local detail, an honest recommendation, no bilingual, no dashes.

## Step 4: Build, wire, QC
```
python3 seo-engine/tools/engine.py build seo-engine/drafts/<slug>.json
python3 seo-engine/tools/engine.py wire <slug>
```
Then add **2 in-sentence links to the new article** from the most related existing pages (the city guide
for that city and one related article). Edit those pages by hand with a natural sentence, then run
`engine.py touch` on them.

QC, every file you created or edited, must pass with 0 FAIL:
```
python3 seo-engine/tools/engine.py qc public/insights/<slug>.html <every other page you edited>
```
Fix every FAIL and re-run. Warnings: fix them if they are quick.

## Step 5: One site upgrade
Take the first `open` task in `seo-engine/site-tasks.json` and do it completely. If it is too big for one
run (it should not be), do a clean subset and leave a note in the task. Then:
- Run QC on every page you touched. New pages need the same kb look: `/css/kb.css` link, a `--th` page
  color on `<body>` from the palette in engine.py (`HUES`), a headline-only hero, and one `<h1>`.
- Add new pages to `public/sitemap.xml`. Run `engine.py touch` on refreshed pages.
- Mark the task `done` with the date and a one-line note (or for `refresh-oldest`, log what you refreshed).

## Step 6: Publish
```
git add public seo-engine
git commit -m "SEO engine <YYYY-MM-DD>: <article title> + <site task>"
git push origin main
```
If the push is rejected: `git pull --rebase --autostash origin main`, re-run QC on your files, push once more.
Report the commit SHA. If it still fails, report the exact error and do NOT claim anything shipped.

## Step 7: Learn (do not skip)
Append this week's entry to `seo-engine/LEARNINGS.md` (top of the log, newest first, 6 lines max):
topic and why, the site task, what was hard, one thing to do differently next week. If the same problem
shows up twice, fix the cause: edit this SKILL.md, the queue or the tools, and say so in the entry.
Commit LEARNINGS.md with the same push (or a second push right after).

## Hard rules
- Only touch: `public/insights/*`, `public/sitemap.xml`, the city guides, the city landing pages, new
  `public/real-estate-agent-*.html` pages, `public/service-areas.html` (links only), and `seo-engine/*`.
  **Never** modify `api/`, `public/js/`, `public/css/`, `home.html`, `guide.html`, `move.html`, forms, or
  tracking. `vercel.json` may only be changed by `engine.py repoint <city>` after building that city's agent page.
- One article per run. Never publish more than one new article in a run.
- Never invent numbers, people, quotes or reviews. If the honest version is weaker, publish the honest version.
- No em or en dashes. No "bilingual". No address. QC enforces this, so do not bypass it.
- Do not try to reach Telegram or email. The report below is the output.

## Report (under 15 lines)
- Article: title, URL, primary keyword, words, why this topic (one line)
- Linked from: the 2 pages
- Site upgrade: task id and what changed
- QC: pass (counts)
- Commit SHA
- **Google Business Profile post for Jesse** (paste-ready, about 120 words, no dashes, ends with a link
  to the new article or the upgraded page, and suggests one photo he should attach)
- One thing Jesse could do this week that only he can do (for example ask a named recent client for a
  Google review, or answer a GBP question)
