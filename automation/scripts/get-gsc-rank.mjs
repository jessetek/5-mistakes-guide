#!/usr/bin/env node
// get-gsc-rank.mjs — Fetch jessetek.net's average position from Google Search
// Console for a single query.
//
// Why this exists: direct google.com scraping is reliably blocked by Google's
// SG (search-guard) JS challenge, so the prior weekly-rank-watch task was
// recording all-null bootstrap data. GSC's `searchanalytics.query` endpoint
// gives us the average position Google itself reported for our pages on a
// query, which is more trustworthy than scraping anyway and free.
//
// Caveats:
//   • GSC reports "average position" across impressions, not literal SERP rank
//     for a single moment. It rounds to one decimal. We round to nearest int
//     and treat it as the weekly rank.
//   • If we got zero impressions for a query in the window, GSC returns no
//     row → we report rank=null (treated as "not in top 50" by the watcher).
//   • Default window is the last 8 days, ending 3 days ago, because GSC has
//     a ~2-3 day reporting lag. Tunable via --start-days / --end-days.
//
// Usage:
//   node get-gsc-rank.mjs "downey realtor"
//   node get-gsc-rank.mjs --start-days=10 --end-days=3 "mello roos guide"
//
// Output (single line of JSON, always valid even on error):
//   {"query":"downey realtor","rank":7,"page":"https://jessetek.net/neighborhoods/downey","impressions":42,"clicks":3,"source":"gsc","window":"2026-04-23..2026-04-30"}
//   {"query":"foo","rank":null,"page":null,"impressions":0,"clicks":0,"source":"gsc","window":"...","note":"no impressions"}
//   {"query":"foo","rank":null,"page":null,"source":"gsc","error":"GSC creds missing"}
//
// Exit codes:
//   0  always — even on credentialed/API errors (caller parses JSON.error).
//      Rationale: this is invoked from inside a Claude prompt and we'd rather
//      let the prompt see a well-formed error than hit a non-zero shell exit.

import { readFileSync, existsSync } from 'node:fs';
import { dirname, resolve, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { homedir } from 'node:os';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

// --- Args ----------------------------------------------------------------
const argv = process.argv.slice(2);
let queryArg = null;
let startDaysAgo = 10;   // window starts 10d ago
let endDaysAgo = 3;      // window ends 3d ago (GSC lag)

for (const a of argv) {
  if (a.startsWith('--start-days=')) startDaysAgo = parseInt(a.slice(13), 10);
  else if (a.startsWith('--end-days=')) endDaysAgo = parseInt(a.slice(11), 10);
  else if (!a.startsWith('--')) queryArg = a;
}

function out(obj) {
  process.stdout.write(JSON.stringify(obj) + '\n');
  process.exit(0);
}

if (!queryArg) {
  out({ query: null, rank: null, page: null, source: 'gsc', error: 'usage: get-gsc-rank.mjs "<query>"' });
}

// --- Resolve env file: same fallback chain as send-telegram-text.sh ------
function findEnvFile() {
  const candidates = [
    process.env.JTEK_ENV,
    // Canonical location used by jessetek-weekly-gsc-harvest scheduled task.
    join(homedir(), 'Library/Mobile Documents/com~apple~CloudDocs/Documents/Documents - JtekMac/Claude Code/Jessetek/tools/.env.local'),
    resolve(__dirname, '../../../tools/.env.local'),                              // same file, relative to this script
    resolve(__dirname, '../../../.env'),                                          // landing-page is inside Jessetek
    join(homedir(), 'Library/Mobile Documents/com~apple~CloudDocs/Documents/Documents - JtekMac/Claude Code/Jessetek/.env'),
    resolve(__dirname, '../.env'),                                                // copied next to automation/
    // Legacy fallback — for users who haven't migrated creds yet.
    join(homedir(), 'Library/Mobile Documents/com~apple~CloudDocs/Documents/Documents - JtekMac/Claude Code/Jtek website/instagram-stories/.env.local'),
  ].filter(Boolean);
  for (const c of candidates) {
    if (existsSync(c)) return c;
  }
  return null;
}

function loadEnv(path) {
  const env = {};
  if (!path) return env;
  const raw = readFileSync(path, 'utf8');
  for (const line of raw.split('\n')) {
    const m = line.match(/^([A-Z_][A-Z0-9_]*)=(.*)$/);
    if (m) env[m[1]] = m[2].trim().replace(/^["']|["']$/g, '');
  }
  return env;
}

const envFile = findEnvFile();
const env = loadEnv(envFile);

const clientId = env.GSC_CLIENT_ID || process.env.GSC_CLIENT_ID;
const clientSecret = env.GSC_CLIENT_SECRET || process.env.GSC_CLIENT_SECRET;
const refreshToken = env.GSC_REFRESH_TOKEN || process.env.GSC_REFRESH_TOKEN;
const property = env.GSC_PROPERTY || process.env.GSC_PROPERTY;

if (!clientId || !clientSecret || !refreshToken || !property) {
  out({
    query: queryArg,
    rank: null,
    page: null,
    source: 'gsc',
    error: `missing GSC creds (env=${envFile || 'none-found'}; have client_id=${!!clientId} secret=${!!clientSecret} refresh=${!!refreshToken} property=${!!property})`,
  });
}

// --- Date window --------------------------------------------------------
function ymd(daysAgo) {
  const d = new Date(Date.now() - daysAgo * 86400 * 1000);
  return d.toISOString().slice(0, 10);
}
const startDate = ymd(startDaysAgo);
const endDate = ymd(endDaysAgo);
const windowStr = `${startDate}..${endDate}`;

// --- Token refresh ------------------------------------------------------
async function getAccessToken() {
  const resp = await fetch('https://oauth2.googleapis.com/token', {
    method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body: new URLSearchParams({
      client_id: clientId,
      client_secret: clientSecret,
      refresh_token: refreshToken,
      grant_type: 'refresh_token',
    }),
  });
  const data = await resp.json();
  if (!resp.ok) throw new Error(`token refresh failed: ${JSON.stringify(data)}`);
  return data.access_token;
}

// --- Search Console query -----------------------------------------------
async function querySearchAnalytics(accessToken) {
  const url = `https://searchconsole.googleapis.com/webmasters/v3/sites/${encodeURIComponent(property)}/searchAnalytics/query`;
  const body = {
    startDate,
    endDate,
    dimensions: ['query', 'page'],
    dimensionFilterGroups: [{
      filters: [{
        dimension: 'query',
        operator: 'equals',
        expression: queryArg,
      }],
    }],
    rowLimit: 25,
  };
  const resp = await fetch(url, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${accessToken}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(body),
  });
  const data = await resp.json();
  if (!resp.ok) throw new Error(`searchAnalytics.query failed: HTTP ${resp.status} ${JSON.stringify(data)}`);
  return data.rows || [];
}

// --- Main ---------------------------------------------------------------
try {
  const accessToken = await getAccessToken();
  const rows = await querySearchAnalytics(accessToken);

  if (rows.length === 0) {
    out({
      query: queryArg,
      rank: null,
      page: null,
      impressions: 0,
      clicks: 0,
      source: 'gsc',
      window: windowStr,
      note: 'no impressions in window',
    });
  }

  // Pick the row with the most impressions (the page Google actually ranked
  // most often for this query). Average its position; round to nearest int.
  rows.sort((a, b) => b.impressions - a.impressions);
  const top = rows[0];
  const rank = Math.round(top.position);
  const page = top.keys?.[1] || null;
  const totalImpressions = rows.reduce((s, r) => s + (r.impressions || 0), 0);
  const totalClicks = rows.reduce((s, r) => s + (r.clicks || 0), 0);

  out({
    query: queryArg,
    rank,
    page,
    impressions: totalImpressions,
    clicks: totalClicks,
    avg_position: top.position,
    source: 'gsc',
    window: windowStr,
  });
} catch (err) {
  out({
    query: queryArg,
    rank: null,
    page: null,
    source: 'gsc',
    window: windowStr,
    error: err.message || String(err),
  });
}
