# Jessetek.net — Operator Playbook

This is your handbook for running the site long-term. It separates **your duties as operator** from **what Mac mini Claude can run autonomously**, then gives you copy-paste prompts for every recurring task.

> **How to use this doc on your Mac mini Claude (always-on machine):**
> 1. Make sure the repo is cloned at the same path or know your Mac mini's path
> 2. Copy any prompt below verbatim (the prompts are self-contained — Mac mini Claude doesn't share memory with my conversation, so each prompt includes its own context)
> 3. Paste into a fresh Claude Code session
> 4. Walk away — most tasks finish in 5-30 min

---

## Part 1 — The operator/AI division of labor

### YOUR job (only you, never Claude)
| Task | Why |
|---|---|
| Reply to qualified leads (Zoom calls, real conversations) | Your voice is the brand |
| Approve LeadConnector workflow changes (SMS templates, email blasts) | TCPA + brand voice |
| Sign off on pricing/service/legal changes | Material business decisions |
| Authorize new paid services or add billing | Security boundary, financial control |
| Create new accounts on third-party platforms | Security boundary |
| Final review of any commit touching: home hero, /rates form, animation code, GBP listing | Protected design + critical conversion paths |
| Approve content drafts that require domain expertise (specific market commentary) | Real-estate accuracy |

### CLAUDE'S job (autonomous, no approval needed)
| Task | Cadence |
|---|---|
| Weekly QC sweep + auto-fix | Mondays |
| Monthly Rate Watch insights post | 1st of month |
| Refresh city median prices from public data | Quarterly |
| Internal link audit + repair | Monthly |
| Sitemap + image-sitemap regeneration | After every content change |
| Lighthouse audit + performance fix | Quarterly |
| Stale-date refresh on insights posts | Monthly |
| Schema markup expansion | Quarterly |
| Service worker cache version bump | After major asset changes |

### CLAUDE'S job (research + propose only, NO deploys)
| Task | Cadence |
|---|---|
| Clarity heatmap analysis | Weekly |
| GA4 top-page review + content suggestions | Weekly |
| Sentry error triage + diagnosis | Weekly |
| GSC query opportunity report | Monthly |
| Competitive analysis (other SoCal realtor sites) | Quarterly |

---

## Part 2 — Ready-to-paste prompts

Prompts are organized by cadence. Each is self-contained (no memory dependency). Each ends with explicit success criteria.

### 🔄 Daily — Health Check (5 min)

```
You are running a daily health check on jessetek.net.

Project root: /Users/jesseonate/Documents/Documents - JtekMac/Claude Code/Jessetek/landing-page

Run these checks and produce a one-page report. Don't change any files.

1. curl https://jessetek.net/api/rates → confirm source=fred and asOf is within last 7 days
2. curl -sI https://jessetek.net/home → confirm 200 status
3. cd to project, run `git log -3 --oneline` and report
4. cd to project, run `git status` and report
5. If any anomaly, propose specific fix steps but DO NOT execute them

Report under 200 words.
```

---

### 📅 Weekly — QC Sweep (10-20 min)

```
You are running a weekly quality control sweep on jessetek.net.

Project root: /Users/jesseonate/Documents/Documents - JtekMac/Claude Code/Jessetek/landing-page

Run this Python QC pass on all pages:

cd "$PROJECT_ROOT" && python3 << 'EOF'
import os, re, json, glob
PUB = "public"
files = sorted(glob.glob(f'{PUB}/**/*.html', recursive=True))
files = [f for f in files if 'og-generator' not in f]
issues = []
local = set()
for f in files:
    rel = os.path.relpath(f, PUB).replace(os.sep, '/')
    local.add('/' + rel); local.add('/' + rel.replace('.html', ''))
    if rel.endswith('/index.html'):
        local.add('/' + rel.replace('/index.html', '/'))
        local.add('/' + rel.replace('/index.html', ''))
LM = ('guide.html', 'guide-pdf.html', 'offline.html', '404.html')
for path in files:
    rel = os.path.relpath(path, PUB)
    with open(path) as fh: t = fh.read()
    for m in re.finditer(r'<script type="application/ld\+json">(.*?)</script>', t, re.DOTALL):
        try: json.loads(m.group(1))
        except: issues.append((rel, "BAD JSON-LD"))
    if rel not in LM and 'rel="canonical"' not in t:
        issues.append((rel, "no canonical"))
    for m in re.finditer(r'(?:src|href)="(/img/[^"]+\.(?:jpg|webp|png|svg))"', t):
        if not os.path.exists(PUB + m.group(1)):
            issues.append((rel, f"missing img: {m.group(1)}"))
    for m in re.finditer(r'href="(/[^"#?]*)"', t):
        url = m.group(1)
        if url.startswith(('/api/','/css/','/js/','/img/','/icons/','/favicon','/_vercel','/sw.js')): continue
        if url.endswith(('.xml','.ico','.json','.pdf')): continue
        if url not in local and url + '.html' not in local and url + '/index.html' not in local:
            for c in [PUB+url, PUB+url+'.html', PUB+url+'/index.html']:
                if os.path.exists(c): break
            else: issues.append((rel, f'broken: {url}'))
print(f'{len(files)} files, {len(set(issues))} issues')
for f,i in sorted(set(issues)): print(f'  {f}: {i}')
EOF

If issues found:
1. Fix each one (broken links → find correct path; missing images → check if it should be removed or fix the path; JSON-LD errors → fix the syntax)
2. Run the sweep again — must come back 0 issues
3. git add -A, commit with message "Weekly QC: fixed N broken links + M missing images"
4. git push

If 0 issues: just report "QC clean, no changes needed."
```

---

### 📅 Monthly (1st of month) — Rate Watch Insights Post

```
You are publishing the monthly SoCal Mortgage Rate Watch insights post on jessetek.net.

Project root: /Users/jesseonate/Documents/Documents - JtekMac/Claude Code/Jessetek/landing-page

Today is the 1st of the month. Steps:

1. Read public/insights/socal-rate-watch-october-2026.html as a template — match its tone, length (6 min read), structure, and CTA pattern.

2. Pull current FRED data: curl -s "https://jessetek.net/api/rates?weeks=13"
   Use the 'current' value as this month's rate.
   Compare to last month's rate (last point in the array vs first).

3. Write a new post for THIS MONTH:
   - File: public/insights/socal-rate-watch-{month}-{year}.html
   - Title: "SoCal Mortgage Rate Watch — {Month} {Year}"
   - Use the previous month's post as a structural template
   - Update: where rates landed, what's driving the move, buyer + seller takeaways, the play heading into next month
   - Keep it ~6 min read, real-talk voice, no fluff
   - Include the live-rate-banner snippet (id="liveRateBanner") at top
   - Include the standardized nav, footer (with EHO + DRE), schema markup

4. Generate OG image: public/img/og-rate-watch-{month}.jpg (and .webp).
   Use the same Python+PIL pattern from previous OG generation in OG image scripts (1200x630, gradient, "Jesse Oñate" header, "MARKET UPDATE · {MONTH} {YEAR}" badge).

5. Update:
   - public/insights/index.html (add new card at top)
   - public/sitemap.xml (add new URL with priority 0.7)
   - public/insights/feed.xml (add new <item>)

6. Run the QC sweep (see Weekly QC prompt) — must come back clean.

7. git commit with message describing the post, git push.

8. Verify live in production: curl -sI https://jessetek.net/insights/socal-rate-watch-{month}-{year} should return 200 within 90 seconds.

Don't fabricate market data — use only what the FRED API returns. Where commentary requires interpretation (Fed signaling, seasonal trends), keep it general and grounded in the rate movement itself.
```

---

### 📅 Monthly (15th) — Stale-content date refresh

```
You are refreshing date references on jessetek.net so the content reads as current.

Project root: /Users/jesseonate/Documents/Documents - JtekMac/Claude Code/Jessetek/landing-page

Tasks:

1. Find all blog posts with "As of" or "as of" date references in their body text:
   grep -rn "[Aa]s of [A-Z][a-z]\+ [0-9]" public/insights/*.html

2. For posts older than 60 days, do NOT change publish date — that's historic.
   For evergreen guide-style posts (refinance guide, DPA guide, mello-roos),
   update the "as of {date}" reference to today's month/year so the advice
   reads current.

3. Update the dateModified in JSON-LD on those evergreen posts to today's
   ISO date, but leave datePublished alone.

4. git diff to verify changes are minimal (just date strings, nothing structural).

5. git commit with message "Monthly date refresh on evergreen insights posts", git push.

Report: how many files updated, what date you changed to, and any post you
SKIPPED because the date felt load-bearing to the historical context.
```

---

### 📅 Quarterly — Performance audit

```
You are running a quarterly performance audit on jessetek.net.

Project root: /Users/jesseonate/Documents/Documents - JtekMac/Claude Code/Jessetek/landing-page

Tasks:

1. Hit https://pagespeed.web.dev/ via curl (PSI API):
   curl "https://www.googleapis.com/pagespeedonline/v5/runPagespeed?url=https://jessetek.net/home&strategy=mobile&category=performance"

   Extract LCP, CLS, INP, FCP, TTFB, overall score.

2. Repeat for /rates, /buyer-quiz, /seller-net, /valuation.

3. Identify the bottom 2 metrics (worst LCP or CLS).

4. Read the relevant page's source. Identify likely causes:
   - Hero image too large?
   - Too many synchronous scripts?
   - Layout shifts from late-loading content?
   - Custom font swap?

5. Propose specific fixes — do NOT deploy them. Write a report:
   - Current state per page (table of metrics)
   - Top 3 issues
   - Specific fixes with estimated impact

6. Save the report at PERF-AUDIT-{YYYY-MM}.md at project root.
   git add it, git commit, git push.

7. Tag me (the human operator) for review before any actual code changes.

Don't change any HTML/CSS/JS. Audit only.
```

---

### 📅 Quarterly — City stats refresh

```
You are refreshing the median home prices and days-on-market stats on
jessetek.net's neighborhood pages.

Project root: /Users/jesseonate/Documents/Documents - JtekMac/Claude Code/Jessetek/landing-page

For each city page in public/neighborhoods/*.html:

1. Read the current stats:
   - Median Home Price (e.g. "$1.45M")
   - Avg Days on Market
   - Residents (don't change — population doesn't move quarterly)

2. The stats live in <div class="nbhd-stat-num">VALUE</div> blocks.

3. For prices: I will NOT have you scrape Zillow or Redfin (TOS issues).
   Instead, look at https://www.car.org/marketdata for the latest published
   CAR median by region. Use the closest match. If unsure, leave the price
   alone and add a comment in the file noting "stat last verified {date}".

4. For days-on-market: same source, same caution.

5. Update only when CAR data clearly differs from current page by >5%.

6. Update the JSON-LD schema datePublished/dateModified accordingly.

7. git commit with message listing which cities updated, git push.

If you can't access fresh data, skip the update and report "stats appear
current vs CAR Q{N} data" — no commit needed.
```

---

### 📅 Weekly — Clarity heatmap review (research only, no deploy)

```
You are reviewing Microsoft Clarity heatmap data for jessetek.net.

Note: Clarity is at https://clarity.microsoft.com/projects/view/wke2elyrvc.
You can't directly browse it without auth, but you can pull insights from
the GA4 funnel data + the Web Vitals analytics that flow into GA4 from
analytics.js.

Tasks:

1. Identify the top 5 pages by traffic (from GA4 if accessible, or guess
   based on /home, /buyer, /seller, /valuation, /rates).

2. For each, read the current page in public/{slug}.html.

3. List any UX friction points YOU notice from a code/design review:
   - Forms with too many fields?
   - CTAs below the fold without anchor?
   - Long pages without subheadings?
   - Missing hover/active states?
   - Slow-loading images above the fold?

4. Save findings at UX-AUDIT-{YYYY-MM-DD}.md at project root with:
   - Page name
   - 1-3 friction points
   - Specific fix proposal
   - Confidence level (high/medium/low — was this from data or hunch?)

5. git add the markdown, commit, push.

Do NOT change any HTML/CSS/JS. This is a propose-only audit.
```

---

### 📅 Event-based — New review on Google

```
A new client review came in on Google. Update the static-fallback testimonials.

Project root: /Users/jesseonate/Documents/Documents - JtekMac/Claude Code/Jessetek/landing-page

Reviewer name: {NAME}
City: {CITY}
Time: {RELATIVE TIME — e.g. "1 month ago"}
Stars: {1-5}
Quote: "{REVIEW TEXT}"

Tasks:

1. Read public/reviews.html — find the .reviews-grid section.

2. Add a new <div class="review-card reveal-s"> for this client at the TOP
   of the grid, matching the existing pattern.

3. Use a unique avatar background color from the existing palette.

4. Trim the quote to 1-2 sentences max — pull the strongest line.

5. Mark it as `Google Review` source (existing pattern).

6. git commit with "Add review from {NAME}", git push.

Live widget on /reviews via Jtek pulls reviews automatically — this is
just the static-fallback in case the widget fails. Match the visual style.
```

---

### 📅 Event-based — New city page request

```
You are adding a new SoCal city page to jessetek.net.

Project root: /Users/jesseonate/Documents/Documents - JtekMac/Claude Code/Jessetek/landing-page

City: {CITY NAME}
County: {LA County | Orange County}
ZIP codes: {ZIPS}
Median: {VALUE}
DOM: {DAYS}
Population: {POP}

Tasks:

1. Use public/neighborhoods/irvine.html or downey.html as a template
   (whichever county matches). Match the structure exactly.

2. Write 4 unique "Why this city" features (research from Wikipedia or
   the city's own .gov site if needed — facts only, no fluff).

3. Pick 4 sub-areas with 1-sentence real-talk descriptions.

4. List 3 top schools with GreatSchools-style ratings (use rough public
   data — better to under-rate than over-rate).

5. Generate OG image at public/img/og-{slug}.jpg using the existing PIL
   script pattern (1200x630, gradient, county badge, city name).

6. Update:
   - public/sitemap.xml (priority 0.85)
   - public/sitemap-images.xml
   - public/service-areas.html (new tile in the grid + counter +1)
   - areaServed schema across all pages (the bulk-replace Python pattern
     from previous commits)

7. Run QC sweep — 0 issues required.

8. git commit, git push.

9. Verify https://jessetek.net/neighborhoods/{slug} returns 200.

Standards:
- Don't fabricate stats. If you can't verify, mark "stat est." in the page.
- Don't claim school ratings without basis — use under-promise framing.
- Match the structural template exactly so QC stays clean.
```

---

### 📅 Event-based — Sentry shows new errors

```
Sentry alerted on a new JS error from jessetek.net production.

Project root: /Users/jesseonate/Documents/Documents - JtekMac/Claude Code/Jessetek/landing-page

Error message: {PASTE FROM SENTRY}
Stack trace: {PASTE FROM SENTRY}
URL: {PASTE FROM SENTRY}
Sample browser/OS: {PASTE FROM SENTRY}

Tasks:

1. Identify the file in /public/ that triggered the error from the stack.

2. Diagnose the root cause:
   - Is it our code? (script in /js/ or inline)
   - Is it a third-party? (LeadConnector, Google Maps, Clarity, Sentry itself)
   - Is it a browser-specific edge case?

3. If it's our code:
   a. Propose a specific patch
   b. Apply the patch
   c. Run the QC sweep
   d. git commit + push
   e. Verify the fix is live

4. If it's third-party:
   - Just document the error in a SENTRY-LOG.md at root with date + summary
   - Do NOT modify our code unless the error is breaking us

5. If it's a one-off (script extension, weird browser): just log it. Don't act.

Report: what was the error, was it ours, what fix, did you deploy?
```

---

### 📅 Quarterly — SEO + content opportunity scan

```
You are scanning Google Search Console for content gap opportunities on jessetek.net.

Project root: /Users/jesseonate/Documents/Documents - JtekMac/Claude Code/Jessetek/landing-page

Note: GSC API requires auth that you don't have. Instead, do a content audit:

1. List top 10 pages on the site by sitemap priority.

2. For each, identify the primary keyword target:
   - Read the <title> and <h1>
   - Note what query that page is optimized for

3. Check if there are gaps:
   - Are there obvious related queries we don't have a page for?
   - Are there 2026-specific updates we're missing?

4. Suggest 3 new posts for the /insights/ blog with:
   - Title (SEO-optimized, 50-65 chars)
   - Target query
   - 5-bullet outline
   - Internal links it should hit

5. Save at SEO-OPPORTUNITIES-{YYYY-MM}.md at root.

6. git commit + push the markdown.

Do NOT write the new posts themselves — that's a separate task with the
operator's input on positioning. Just identify opportunities + outlines.
```

---

## Part 3 — How to set up the Mac mini Claude

### One-time setup
1. Clone the repo on your Mac mini if you haven't:
   ```bash
   cd ~
   git clone git@github.com:jessetek/5-mistakes-guide.git landing-page
   cd landing-page
   ```

2. Update `OPERATOR-PLAYBOOK.md` line referencing project root if your Mac mini path differs.

3. Make sure Mac mini Claude has:
   - Vercel CLI: `npm i -g vercel` (or use `npx vercel` like the laptop)
   - Python 3 + Pillow (for OG image gen): `pip3 install pillow`
   - Git credentials configured for `jessetek` GitHub account

### Workflow
1. Open Claude Code on Mac mini
2. `cd` to the project directory
3. Paste the prompt that matches the task you want done
4. Walk away
5. Review the auto-generated commit when you have a moment

### Don't do this
- Don't paste two prompts simultaneously — Claude can run only one task at a time without scope creep
- Don't run the same prompt twice in a row without checking the first one's output (it'll happily redo work)
- Don't authorize prompts that would do account creation or billing — Mac mini Claude has the same security boundaries as I do

### What to monitor

Once a week glance at:
- `git log` on the repo to see what auto-committed
- Vercel dashboard for failed deploys
- Sentry inbox for new error categories
- Clarity dashboard for unexpected user behavior (occasional weekend check)

If something looks off in a commit, just `git revert <hash>` and the change rolls back cleanly.

---

## Part 4 — Operator self-checklist

This is the human-only stuff. Do these yourself, weekly:

- [ ] Reply to every Zoom-call request within 4 hours
- [ ] Reply to every form submission within 24 hours (or sooner via Jtek workflow)
- [ ] Post at least 1 new IG/social piece weekly to drive /rates traffic
- [ ] Read the latest Clarity session recording with high friction
- [ ] Review GA4 conversions count vs last week
- [ ] Check Vercel Analytics for any country/source spikes
- [ ] Check Google Business Profile for any new reviews; reply within 48h

Monthly:
- [ ] Update Google Business Profile with one fresh photo or post
- [ ] Audit your local citations (Realtor.com, Zillow, Yelp profiles match jessetek.net)
- [ ] Review Search Console for new keyword wins
- [ ] Send a personal SMS check-in to 5 past clients (referral pipeline)

Quarterly:
- [ ] Site Lighthouse score check (Mac mini Claude can run, you review)
- [ ] Refresh the LinkedIn / Realtor profile bio to match site
- [ ] Test all 3 lead forms personally (valuation, /rates, /guide) end-to-end
- [ ] Review every active LeadConnector workflow

Yearly:
- [ ] Renew DRE license + update DRE# everywhere if changes
- [ ] Renew domain (jessetek.net)
- [ ] Renew Vercel plan if traffic warrants Pro tier
- [ ] Audit and rotate API keys (FRED, RentCast, JTek, Sentry, Clarity)

---

## Part 5 — Emergency procedures

### Site is down (Vercel showing 5xx)
1. Check Vercel dashboard: vercel.com/dashboard
2. Check most recent commit's deploy status
3. If deploy failed: rollback via `git revert HEAD && git push`
4. If domain issue: Vercel → Settings → Domains → check DNS

### A form just stopped working
1. Check `/api/submit.js`, `/api/valuation.js` Vercel function logs
2. Check JTEK_API_KEY hasn't expired
3. Check LeadConnector API status
4. Test the form manually with a test entry

### Reviews widget is empty
1. Open the Jtek reputation hub admin
2. Verify the widget URL hasn't changed
3. Check Google Business Profile is still linked

### A blog post or city page returns 404
1. Check sitemap.xml — is the URL there?
2. Check the file exists at public/{path}.html
3. Test with cache buster: `curl -sI "https://jessetek.net/{url}?cb=$(date +%s)"`
4. If file exists + sitemap correct: hard-purge Vercel cache or wait 5 min
