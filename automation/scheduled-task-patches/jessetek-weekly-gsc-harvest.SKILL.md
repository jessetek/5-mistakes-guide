---
name: jessetek-weekly-gsc-harvest
description: Sunday 21:00 — pulls GSC near-page-1 queries (rank 8-20), drafts content angles via Telegram. Handles low-data weeks gracefully. Requires GSC OAuth setup (run automation/setup-gsc-oauth.mjs once).
---

Pull last 28 days of Google Search Console data for jessetek.net, find queries ranking on positions 8-20 (near page 1 but not there), and draft a content angle to push them up.

Steps:

1. Read GSC credentials from /Users/jtek/Library/Mobile Documents/com~apple~CloudDocs/Documents/Documents - JtekMac/Claude Code/Jessetek/tools/.env.local — keys: GSC_CLIENT_ID, GSC_CLIENT_SECRET, GSC_REFRESH_TOKEN, GSC_PROPERTY.

   If any is missing or empty: send a one-time Telegram setup nudge:
   "GSC harvest skipped — run `node automation/setup-gsc-oauth.mjs` on the Mac mini once. Auto-resumes next Sunday."
   Then STOP.

2. Refresh the access token:
   curl -s -X POST https://oauth2.googleapis.com/token \
     -d "client_id=$GSC_CLIENT_ID" \
     -d "client_secret=$GSC_CLIENT_SECRET" \
     -d "refresh_token=$GSC_REFRESH_TOKEN" \
     -d "grant_type=refresh_token"

   Parse the access_token from the response.

3. Query the GSC Search Analytics API:
   curl -s -X POST "https://searchconsole.googleapis.com/webmasters/v3/sites/$(printf %s "$GSC_PROPERTY" | jq -sRr @uri)/searchAnalytics/query" \
     -H "Authorization: Bearer $ACCESS_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{
       "startDate": "<28 days ago YYYY-MM-DD>",
       "endDate": "<today YYYY-MM-DD>",
       "dimensions": ["query","page"],
       "rowLimit": 500
     }'

4. Filter the rows to: position between 8.0 and 20.0, impressions ≥ 50 (avoid noise).
   Compute:
   - qualifying = rows that pass the filter
   - total_rows = full row count from step 3
   - total_impressions = sum of impressions across ALL rows from step 3
   - top_query = the highest-impression row from step 3 (regardless of position)

5. Branch on `qualifying`:

   5a. If len(qualifying) >= 1 — proceed to the full opportunity report:
   - Sort qualifying by impressions × (1 / position).
   - Pick the top 5 — these are queries with real demand where you're 1-2 pages away from page 1.
   - Continue to step 6.

   5b. If len(qualifying) == 0 — site has no near-miss queries this week:
   - SKIP step 6 entirely (there's no #1 to propose an angle for).
   - In step 7, send the short "low-data" message format (see 7b below).
   - Still save the snapshot per step 9.

6. (Only on the 5a branch.) For the #1 opportunity, propose a concrete content angle:
   - Read the page that's currently ranking (from the GSC data) to see what it's missing.
   - Suggest one of: a 200-word section to add, an FAQ to insert, a sub-page to create, or an internal link to push from a higher-authority page.

7. Compose the Telegram message.

   7a. Full opportunity report (qualifying >= 1) — target 12-15 lines:

   GSC harvest · last 28 days

   Top 5 near-miss queries (rank 8-20):
   1. "downey property tax calculator" — pos 11, 230 impressions, 0.8% CTR
      → /tools/property-tax-estimator (currently ranking)
   2. "mello roos calculator" — pos 14, 180 impressions
   3. "first time buyer downey ca" — pos 9, 145 impressions
   4. "homes downey under 800k" — pos 13, 110 impressions
   5. "bilingual realtor whittier" — pos 16, 95 impressions

   This week's push:
   #1 query needs a calculator tool. The current page has rate context but no interactive estimator. Add a small JS calculator block to /tools/property-tax-estimator (input: home price, output: monthly tax incl. Mello-Roos). Estimated rank lift: 11→6.

   7b. Low-data message (qualifying == 0) — target 5-7 lines:

   GSC harvest · last 28 days
   0 near-miss queries this week (no rows at pos 8-20 with ≥50 impressions).

   Site landscape: {total_rows} queries indexed, {total_impressions} total impressions.
   Top query: "{top_query.query}" — pos {top_query.position}, {top_query.impressions} impressions.

   Pre-traction site — the harvest filter is calibrated for queries with real demand. Lift comes from upstream content work (weekly-clarity-review / quarterly-seo-scan), not from this report. Snapshot saved.

8. Send via Telegram:

   MSG=$(mktemp); cat > "$MSG" <<'EOF'
   <message>
   EOF
   cat "$MSG" | node "/Users/jtek/Library/Mobile Documents/com~apple~CloudDocs/Documents/Documents - JtekMac/Claude Code/Jessetek/tools/send-telegram-text.mjs" --plain --stdin
   rm -f "$MSG"

9. Save the harvest snapshot to:
   /Users/jtek/Library/Mobile Documents/com~apple~CloudDocs/Documents/Documents - JtekMac/Claude Code/Jessetek/landing-page/automation/.state/gsc-harvest-{YYYY-MM-DD}.json

   Snapshot schema (save regardless of branch):
   {
     "harvest_date": "YYYY-MM-DD",
     "range_start": "YYYY-MM-DD",
     "range_end": "YYYY-MM-DD",
     "property": "<GSC_PROPERTY value>",
     "total_rows": <int>,
     "total_impressions": <int>,
     "qualifying_rows": <int>,
     "opportunities": [<top 5 if any, else empty array>],
     "all_rows": [<full row list, query+page+pos+imp+clk+ctr, sorted by impressions desc>],
     "note": "<one-line summary of branch taken>"
   }

   So we can track which opportunities have been worked on AND watch site landscape grow week over week.

10. If GSC API call fails (auth expired, quota hit, etc.): send a Telegram with "GSC harvest failed: <error>. Re-run `node automation/setup-gsc-oauth.mjs` if auth expired." Don't fall back to scraping.

Constraints:
- Top 5 max in the full-report message — never overwhelm.
- One concrete push per week — pick the highest-impact one to recommend.
- Low-data weeks (qualifying == 0) get the 5-7 line message — never fabricate opportunities to fill 12 lines.
- Don't write the actual content; this is a research-only task. Repo changes happen via the existing weekly-clarity-review or quarterly-seo-scan.
- No Gmail drafts.
