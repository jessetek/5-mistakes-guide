#!/usr/bin/env node
// list-gsc-properties.mjs — Diagnostic. Refreshes the GSC OAuth token and
// lists every Search Console property the authorized user can see, with
// permission level. For each, also probes a no-op searchanalytics.query so we
// know whether analytics-read actually works (HTTP 200) or is forbidden (403)
// or some other error.
//
// Why: a 403 on searchanalytics.query while sites.list happily returns the
// property usually means the OAuth account is "associated" / "restricted" on
// that property — they can see it exists but can't read its data. The fix is
// either (a) point GSC_PROPERTY at a different property the same account does
// have full access to, or (b) ask the verified owner to grant Full or
// Restricted permission to the OAuth account.
//
// Usage:
//   node list-gsc-properties.mjs
//
// Output: human-readable table; exits 0.

import { readFileSync, existsSync } from 'node:fs';
import { dirname, resolve, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { homedir } from 'node:os';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

function findEnvFile() {
  const candidates = [
    process.env.JTEK_ENV,
    // Canonical location used by jessetek-weekly-gsc-harvest scheduled task.
    join(homedir(), 'Library/Mobile Documents/com~apple~CloudDocs/Documents/Documents - JtekMac/Claude Code/Jessetek/tools/.env.local'),
    resolve(__dirname, '../../../tools/.env.local'),
    resolve(__dirname, '../../../.env'),
    join(homedir(), 'Library/Mobile Documents/com~apple~CloudDocs/Documents/Documents - JtekMac/Claude Code/Jessetek/.env'),
    resolve(__dirname, '../.env'),
    join(homedir(), 'Library/Mobile Documents/com~apple~CloudDocs/Documents/Documents - JtekMac/Claude Code/Jtek website/instagram-stories/.env.local'),
  ].filter(Boolean);
  for (const c of candidates) if (existsSync(c)) return c;
  return null;
}
function loadEnv(path) {
  const env = {};
  if (!path) return env;
  for (const line of readFileSync(path, 'utf8').split('\n')) {
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
const currentProperty = env.GSC_PROPERTY || process.env.GSC_PROPERTY;

console.log('GSC diagnostic');
console.log('  env file:        ', envFile || '(none found)');
console.log('  GSC_PROPERTY now:', currentProperty || '(unset)');
console.log('');

if (!clientId || !clientSecret || !refreshToken) {
  console.error('Missing GSC creds. Run: node automation/setup-gsc-oauth.mjs');
  process.exit(0);
}

// Refresh access token
const tokenResp = await fetch('https://oauth2.googleapis.com/token', {
  method: 'POST',
  headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
  body: new URLSearchParams({
    client_id: clientId,
    client_secret: clientSecret,
    refresh_token: refreshToken,
    grant_type: 'refresh_token',
  }),
});
const tokenData = await tokenResp.json();
if (!tokenResp.ok) {
  console.error('Token refresh failed:', JSON.stringify(tokenData, null, 2));
  process.exit(0);
}
const accessToken = tokenData.access_token;

// List sites
const sitesResp = await fetch('https://searchconsole.googleapis.com/webmasters/v3/sites', {
  headers: { Authorization: `Bearer ${accessToken}` },
});
const sitesData = await sitesResp.json();
const sites = sitesData.siteEntry || [];

if (sites.length === 0) {
  console.log('No GSC properties visible to this OAuth account.');
  console.log('Verify jessetek.net at https://search.google.com/search-console first.');
  process.exit(0);
}

console.log(`Found ${sites.length} property/properties:`);
console.log('');

// Probe each with a tiny searchanalytics.query (1 day window) and report status.
const today = new Date().toISOString().slice(0, 10);
const yesterday = new Date(Date.now() - 86400 * 1000).toISOString().slice(0, 10);

for (const s of sites) {
  const url = `https://searchconsole.googleapis.com/webmasters/v3/sites/${encodeURIComponent(s.siteUrl)}/searchAnalytics/query`;
  const resp = await fetch(url, {
    method: 'POST',
    headers: { Authorization: `Bearer ${accessToken}`, 'Content-Type': 'application/json' },
    body: JSON.stringify({ startDate: yesterday, endDate: today, rowLimit: 1 }),
  });
  let status = `HTTP ${resp.status}`;
  if (resp.status === 200) status = '[32mOK (analytics-read works)[0m';
  else if (resp.status === 403) status = '[31mFORBIDDEN (no analytics-read)[0m';
  else {
    const body = await resp.text();
    status = `HTTP ${resp.status} ${body.slice(0, 80)}`;
  }
  const isCurrent = s.siteUrl === currentProperty ? ' ← current GSC_PROPERTY' : '';
  console.log(`  • ${s.siteUrl}`);
  console.log(`      perm:      ${s.permissionLevel}`);
  console.log(`      analytics: ${status}${isCurrent}`);
}

console.log('');
console.log('Recommended fix:');
const usable = sites.filter(async (s) => false); // placeholder, we report below
// We can't easily filter async — just tell the user.
console.log('  • Pick the property above whose `analytics: OK` line is green.');
console.log('  • Edit /Jessetek/.env and set GSC_PROPERTY=<that-siteUrl> exactly as printed.');
console.log("  • If NONE are green, the OAuth account doesn't have analytics-read on any");
console.log('    property. Either re-run setup-gsc-oauth.mjs while signed into Google as');
console.log('    the verified owner, OR have the verified owner add this account in GSC');
console.log('    (Settings → Users and permissions → Add user → Full).');
