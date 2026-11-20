---
name: jessetek-weekly-rate-sms
description: Monday 10:00 — adds qualifying LeadConnector contacts (excluding humboldtfarm + opt-outs) to the existing "Mortgage Rate Weekly Texts" workflow. Throttled, dedup'd, email summary.
---

Re-engage Jesse's LeadConnector contacts via the existing weekly mortgage SMS workflow. This task feeds qualifying contacts INTO the workflow he built — it does not author or send the SMS itself. The workflow handles the message + opt-out + deliverability.

CRITICAL — phone-number filter is the most important safeguard:
~83% of contacts in this LeadConnector have no phone number (most are Instagram "hometour" leads who only gave email/IG handle). Adding a contact without a phone to an SMS workflow is wasteful (workflow either silently drops it or attempts and fails) and clutters the audit. Verify the phone field is non-empty AND looks like a phone number BEFORE adding to the workflow. Do not rely on the workflow to filter — filter here.

Read creds from one of these files (in order):
  1. /Users/jtek/Library/Mobile Documents/com~apple~CloudDocs/Documents/Documents - JtekMac/Claude Code/Jessetek/tools/.env.local  ← canonical (holds Clarity, FRED, GitHub, GSC, and JTEK/LeadConnector creds for all sibling scheduled tasks)
  2. /Users/jtek/Library/Mobile Documents/com~apple~CloudDocs/Documents/Documents - JtekMac/Claude Code/Jessetek/.env  ← partial mirror (GSC + JTEK_* only) for sessions where /Jessetek/tools isn't reachable
  3. /Users/jtek/Library/Mobile Documents/com~apple~CloudDocs/Documents/Documents - JtekMac/Claude Code/Jtek/instagram-stories/.env.local  ← legacy location, kept honored for un-migrated setups

If none is reachable, request the Jessetek folder via request_cowork_directory before failing.

Required keys:
  JTEK_API_KEY
  JTEK_LOCATION_ID
  JTEK_API_BASE             (https://services.leadconnectorhq.com)
  JTEK_RATE_WORKFLOW_ID     (9a97c2ae-97cb-46e0-a759-cd6e0d500b6b)
  JTEK_RATE_SMS_MAX_PER_WEEK (default 200)

If JTEK_API_KEY is missing or starts with "PASTE_": email jesse@jtek.pro with the Resend connector (from Jtek Command Center <alerts@updates.jtek.pro>): "Rate SMS task skipped — JTEK_API_KEY not set in .env" and stop.

Audience filtering (apply ALL — TCPA-safe per Jesse's policy):
1. PHONE PRESENCE — contact's `phone` field exists, is non-empty after stripping whitespace, and matches /^[+]?[0-9 ()\-]{7,}$/. Skip silently if no phone. This is the primary filter — most contacts will fail here.
2. TAGS INCLUDE — contact has at least one of: buyer, seller, hometour, lead-magnet, 5-mistakes-guide (case-insensitive)
3. TAGS EXCLUDE — contact has NONE of: humboldtfarm, stop, unsubscribed, do-not-contact, dnd, opt-out (case-insensitive). Note the spelling is humboldtfarm with a 't' — this is the actual tag in the data; older versions of this skill said "humboldfarm" which never matched anything.
4. DND BOOLEAN — contact's top-level `dnd` field must NOT be true. This is independent of the dnd tag check above; honor both.
5. RECENCY — contact created (dateAdded) within last 18 months.
6. DEDUP — not in state file's last 14 days (every 2 weeks per contact, not weekly — small audience).

Sort qualifying contacts by dateAdded DESC (newest/warmest first). Cap at JTEK_RATE_SMS_MAX_PER_WEEK.

State file:
/Users/jtek/Library/Mobile Documents/com~apple~CloudDocs/Documents/Documents - JtekMac/Claude Code/Jessetek/landing-page/automation/.state/rate-sms-sent.json
Format: { "history": [ {"date":"2026-05-04","contactId":"...","phone":"+15551234567","name":"..."}, ... ], "last_run": {...} }
Trim history entries older than 60 days at start of each run.

Summary delivery: email jesse@jtek.pro with the Resend connector (from Jtek Command Center <alerts@updates.jtek.pro>).

Steps:

1. Page through ALL contacts using the LeadConnector pagination (limit=100 per call, follow meta.nextPageUrl).
   GET $JTEK_API_BASE/contacts/?locationId=$LOCATION_ID&limit=100[&startAfterId=...&startAfter=...]
   Headers: Authorization: Bearer $JTEK_API_KEY, Version: 2021-07-28
   Pagination cursor: meta.nextPageUrl, or build manually with meta.startAfter (epoch ms) + meta.startAfterId.

2. As you stream through pages, count totals:
   total_scanned, has_phone, has_engagement_tag, in_18mo, qualifying (passes all filters), excluded_humboldtfarm, excluded_optout, dnd_excluded, in_dedup_window

3. Apply filters in order. Track exclusion reasons for the summary.

4. If qualifying count is 0: email the summary (counts breakdown) and STOP. Don't fire workflow.

5. If qualifying ≥ 1, take the top JTEK_RATE_SMS_MAX_PER_WEEK by dateAdded DESC, then for each:
   POST $JTEK_API_BASE/contacts/{contactId}/workflow/$JTEK_RATE_WORKFLOW_ID
   Headers: Authorization: Bearer $JTEK_API_KEY, Version: 2021-07-28
   Empty body. Expected: 200 or 201.
   On 429 (rate limit), back off 30s and retry up to 3 times.
   On other errors, log + continue. Don't abort the run.

6. Append all successfully-added contactIds + phone + date to state file. Also write a `last_run` block with funnel counts + run timestamp.

7. Pull current rate context for the summary:
   curl -s https://jessetek.net/api/rates → current, delta

8. Email the summary: email jesse@jtek.pro with the Resend connector (from Jtek Command Center <alerts@updates.jtek.pro>).

   Summary format (target 9-12 lines, terse):

Rate SMS · week of {Mon DD}
Added: {N} contacts to "Mortgage Rate Weekly Texts"
Failed: {failed_count} (if >0)

Audience funnel:
  Scanned: {total_scanned}
  Has phone: {has_phone}
  Active tags + last 18mo: {qualifying_pre_dedup}
  After 14d dedup: {final_pool}
  Sent (cap {MAX}): {N}

Rate this week: {current}% ({delta})

9. Output a one-line summary to stdout.

Constraints:
- Phone filter is paramount. If a contact has no valid phone, skip them — never add them to the workflow.
- Honor `dnd: true` on the contact in addition to the dnd tag.
- Never bypass JTEK_RATE_SMS_MAX_PER_WEEK.
- If JTEK_RATE_WORKFLOW_ID is empty, email "rate workflow ID missing" and stop.
- Don't modify contacts in any way other than adding them to the workflow. No tag changes, no field edits.

Changelog:
- 2026-05-04 #1: token rotated to pit-014b8a07-... (saved to both .env.local and /Jessetek/.env); humboldfarm typo fixed to humboldtfarm; dnd boolean check added.
- 2026-05-04 #2: Jtek website folder remounted in Cowork → original .env.local restored as canonical. Mirror at /Jessetek/.env kept as fallback for sessions where Jtek website isn't mounted.
- 2026-05-04 #3: Verified end-to-end — 60 contacts added to workflow, summary delivered.
- 2026-05-12: canonical creds moved to /Jessetek/tools/.env.local (consolidated: Clarity + FRED + GitHub + GSC + JTEK all in one file). /Jtek/instagram-stories/.env.local demoted to legacy (still honored by env resolvers). Triggered by gsc-harvest re-auth — the new account's refresh token writes to /Jessetek/tools/.env.local and the env path resolvers across setup-gsc.sh, setup-gsc-oauth.mjs, get-gsc-rank.mjs, list-gsc-properties.mjs, fetch-fred-key.sh were all updated to find it there. Old paths kept as fallbacks for un-migrated setups.
