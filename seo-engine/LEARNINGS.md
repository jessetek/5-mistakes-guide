# Learnings (read first, write last)

Newest entry at the top. Six lines max per entry. When a lesson keeps coming back, move it into SKILL.md
and delete it here, so this file stays short.

## Standing lessons (from building the engine, 2026-11-12)
- The old SEO brain died because it waited on data. Always ship the article and the site task, even with no Search Console data.
- Articles were orphaned: most had 0 or 1 inbound links, and 3 never made the sitemap or the index. `wire` plus the 2 manual links fix this every week.
- Three April posts were pre-dated with future months and noindexed. Never write future-dated content or numbers for a month that has not happened.
- Old articles say "Bilingual SoCal Realtor" in the author box. New articles use the template author box. Site task `author-box-bilingual` cleans up the old ones.
- 10 of 11 farm cities had no "Real Estate Agent in <City>" page. Those are the money queries, so site tasks build them one per week.

## Log
### 2026-11-12 (sitewide improvements, by hand, Jesse approved the list)
- All 10 farm-city agent pages are live, linked from their city guides and a new Service Areas directory; their bilingual redirects were repointed.
- Bilingual and dashes are gone sitewide (copy and schema). QC should stay green on any page you touch; if an old page fails, fix it as part of the run.
- New /insights/socal-mortgage-rate-history holds every monthly PMMS average. When you write a monthly rate watch, ALSO add that month's row to the history table, rebuild it, and link it from the new watch.
- April and June 2026 rate watches now redirect to the history page. Next site task: sitemap-lastmod, then refresh-oldest.

### 2026-11-12 (second run, automated)
- Article: downey-vs-whittier-where-to-buy (topic 2, compare intent). About 1,050 body words, 6 sources; linked from the Whittier guide and the living-in-downey article.
- Site task predated-drafts done. The old drafts invented a rate cut and 6.3% rates; real PMMS rose to 7.40% in October. The official history CSV at freddiemac.com/pmms/docs/PMMS_history.csv works with curl and gives every weekly number.
- Hard: QC wants 1,000+ words, so rewrites with only real data needed extra sourced-math sections (payments, 15 vs 30, break-even).
- Whittier guide had a bilingual FAQ in its schema; removed. Pages april, june and may rate pages still FAIL QC for bilingual and dashes, so fix them via author-box-bilingual.
- Next: author-box-bilingual (include those 3 rate pages), then best-neighborhoods-in-downey. Aim for 1,200 words.

### 2026-11-12 (built by hand, Jesse approved weekly auto-publish)
- Article: living-in-downey-ca (topic 1, Downey head target). 1,082 body words, 6 sources, linked from /neighborhoods/downey and the Mello-Roos article.
- Linking from old pages surfaced old copy violations (bilingual in schema FAQ and og tags, en dashes). Fix them in any page you touch, so every run leaves the site cleaner.
- (Resolved 2026-11-12) Jesse retired the bilingual-realtor-downey article. It 301s to /real-estate-agent-downey. Never recreate a bilingual article or topic.
- (2026-11-12) Jesse also retired the 15 best-bilingual-realtor-<city> pages. Downey 301s to /real-estate-agent-downey, the rest to /neighborhoods/<city>. After building a city's agent page, run `engine.py repoint <city>`.
- Next: site task predated-drafts, then the topic downey-vs-whittier-where-to-buy.
