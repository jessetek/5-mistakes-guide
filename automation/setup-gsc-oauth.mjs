// One-shot OAuth flow for Google Search Console.
//
// What this does:
//   1. Reads GSC_CLIENT_ID + GSC_CLIENT_SECRET from .env.local
//   2. Spins up a tiny local HTTP server on 127.0.0.1:8765
//   3. Opens your default browser to Google's consent screen
//   4. After you click Allow, Google redirects to http://localhost:8765
//      with the auth code; we capture it automatically
//   5. Exchanges the code for a refresh token
//   6. Verifies API access by listing your Search Console properties
//   7. Writes GSC_REFRESH_TOKEN + GSC_PROPERTY back to .env.local
//
// You only need to (a) sign in if not already, (b) click Allow.
// No copy-pasting auth codes.

import { readFileSync, writeFileSync, existsSync } from 'node:fs';
import { createServer } from 'node:http';
import { exec } from 'node:child_process';
import { dirname, resolve, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { homedir } from 'node:os';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

// Resolve the env file: same fallback chain as scripts/send-telegram-text.sh
// and scripts/get-gsc-rank.mjs. /Jessetek/.env is canonical; the legacy
// /Jtek website/instagram-stories/.env.local is honored last for users who
// haven't migrated yet. Override with JTEK_ENV=/some/path if you keep creds
// somewhere unusual.
function resolveEnvPath() {
  const candidates = [
    process.env.JTEK_ENV,
    // Canonical location used by jessetek-weekly-gsc-harvest and other tools.
    join(homedir(), 'Library/Mobile Documents/com~apple~CloudDocs/Documents/Documents - JtekMac/Claude Code/Jessetek/tools/.env.local'),
    resolve(__dirname, '../../tools/.env.local'),                                  // same file, relative to this script
    resolve(__dirname, '../.env'),                                                 // landing-page is inside Jessetek
    join(homedir(), 'Library/Mobile Documents/com~apple~CloudDocs/Documents/Documents - JtekMac/Claude Code/Jessetek/.env'),
    resolve(__dirname, '.env'),                                                    // copied next to setup script
    join(homedir(), 'Library/Mobile Documents/com~apple~CloudDocs/Documents/Documents - JtekMac/Claude Code/Jtek website/instagram-stories/.env.local'),
  ].filter(Boolean);
  for (const c of candidates) {
    if (existsSync(c)) return c;
  }
  // None exist yet — pick the canonical destination so first-run can create it.
  return candidates[1];
}

const ENV_PATH = resolveEnvPath();
const PORT = 8765;
const REDIRECT = `http://localhost:${PORT}`;
const SCOPE = 'https://www.googleapis.com/auth/webmasters.readonly';

const colors = {
  bold: (s) => `\x1b[1m${s}\x1b[0m`,
  ok: (s) => `\x1b[32m✓\x1b[0m ${s}`,
  warn: (s) => `\x1b[33m⚠\x1b[0m ${s}`,
  fail: (s) => `\x1b[31m✘\x1b[0m ${s}`,
  info: (s) => `\x1b[36m▸\x1b[0m ${s}`,
};

function readEnv() {
  if (!existsSync(ENV_PATH)) {
    console.error(colors.fail(`env file not found at ${ENV_PATH}`));
    console.error(colors.fail(`Create it with at minimum:`));
    console.error(`  GSC_CLIENT_ID=...`);
    console.error(`  GSC_CLIENT_SECRET=...`);
    console.error(`(Get these by creating an OAuth 2.0 client in https://console.cloud.google.com/apis/credentials → "Desktop app". Add http://localhost:8765 as an authorized redirect URI.)`);
    process.exit(1);
  }
  const raw = readFileSync(ENV_PATH, 'utf8');
  const env = {};
  for (const line of raw.split('\n')) {
    const m = line.match(/^([A-Z_][A-Z0-9_]*)=(.*)$/);
    if (m) env[m[1]] = m[2].trim().replace(/^["']|["']$/g, '');
  }
  return { env, raw };
}

function writeEnv({ raw }, updates) {
  let next = raw;
  for (const [k, v] of Object.entries(updates)) {
    const re = new RegExp(`^${k}=.*$`, 'm');
    if (re.test(next)) {
      next = next.replace(re, `${k}=${v}`);
    } else {
      next = next.replace(/\n*$/, '') + `\n${k}=${v}\n`;
    }
  }
  writeFileSync(ENV_PATH, next);
}

async function main() {
  const { env, raw } = readEnv();
  const clientId = env.GSC_CLIENT_ID;
  const clientSecret = env.GSC_CLIENT_SECRET;

  if (!clientId || !clientSecret) {
    console.error(colors.fail('GSC_CLIENT_ID or GSC_CLIENT_SECRET missing in .env.local'));
    process.exit(1);
  }

  console.log(colors.bold('\n╭─ GSC OAuth setup ───────────────────────────────╮'));
  console.log(colors.bold('│  Should take ~30 seconds. Browser will open.    │'));
  console.log(colors.bold('╰─────────────────────────────────────────────────╯\n'));

  // Start local server that catches the redirect
  let resolveCode, rejectCode;
  const codePromise = new Promise((res, rej) => { resolveCode = res; rejectCode = rej; });

  const server = createServer((req, res) => {
    const url = new URL(req.url, `http://localhost:${PORT}`);
    const code = url.searchParams.get('code');
    const error = url.searchParams.get('error');

    if (error) {
      res.writeHead(400, { 'Content-Type': 'text/html' });
      res.end(`<html><body style="font-family: -apple-system; padding: 40px; text-align: center;">
        <h2 style="color: #c00;">Authorization denied</h2>
        <p>${error}</p>
        <p>Close this tab and re-run the script.</p>
        </body></html>`);
      rejectCode(new Error(`OAuth error: ${error}`));
      return;
    }

    if (code) {
      res.writeHead(200, { 'Content-Type': 'text/html' });
      res.end(`<html><body style="font-family: -apple-system; padding: 40px; text-align: center;">
        <h2 style="color: #0a0;">✓ Authorized</h2>
        <p>You can close this tab and return to Terminal.</p>
        </body></html>`);
      resolveCode(code);
      return;
    }

    res.writeHead(404);
    res.end('Waiting for OAuth redirect…');
  });

  await new Promise((res) => server.listen(PORT, '127.0.0.1', res));
  console.log(colors.ok(`Local redirect server listening on ${REDIRECT}`));

  // Build auth URL
  const authUrl = new URL('https://accounts.google.com/o/oauth2/v2/auth');
  authUrl.searchParams.set('client_id', clientId);
  authUrl.searchParams.set('redirect_uri', REDIRECT);
  authUrl.searchParams.set('response_type', 'code');
  authUrl.searchParams.set('scope', SCOPE);
  authUrl.searchParams.set('access_type', 'offline');
  // Force the account picker AND consent screen every run, so the user can't
  // silently re-auth as the wrong Google account on a machine where multiple
  // accounts are signed in. Critical because jessetek.net's GSC property is
  // typically owned by Jesse's realtor Gmail, not his @jtek.* dev account.
  authUrl.searchParams.set('prompt', 'select_account consent');

  console.log(colors.info('Opening Google consent screen in your default browser…'));
  console.log(colors.info(`If it doesn't open automatically, paste this URL into Chrome:\n  ${authUrl.toString()}\n`));

  exec(`open "${authUrl.toString()}"`, (err) => {
    if (err) console.warn(colors.warn(`open failed: ${err.message} — paste the URL manually`));
  });

  // Wait for the code (up to 5 minutes)
  let code;
  try {
    code = await Promise.race([
      codePromise,
      new Promise((_, rej) => setTimeout(() => rej(new Error('timeout waiting for redirect (5 min)')), 5 * 60 * 1000)),
    ]);
  } finally {
    server.close();
  }

  console.log(colors.ok('Got auth code. Exchanging for refresh token…'));

  // Exchange code for tokens
  const tokenResp = await fetch('https://oauth2.googleapis.com/token', {
    method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body: new URLSearchParams({
      code,
      client_id: clientId,
      client_secret: clientSecret,
      redirect_uri: REDIRECT,
      grant_type: 'authorization_code',
    }),
  });
  const tokens = await tokenResp.json();

  if (!tokens.refresh_token) {
    console.error(colors.fail(`Token exchange failed:\n${JSON.stringify(tokens, null, 2)}`));
    process.exit(1);
  }

  console.log(colors.ok(`Got refresh token (${tokens.refresh_token.length} chars).`));

  // Verify by listing GSC properties
  console.log(colors.info('Verifying GSC API access…'));
  const sitesResp = await fetch('https://searchconsole.googleapis.com/webmasters/v3/sites', {
    headers: { 'Authorization': `Bearer ${tokens.access_token}` },
  });
  const sitesData = await sitesResp.json();

  if (!sitesResp.ok) {
    console.error(colors.fail(`GSC API call failed: ${JSON.stringify(sitesData)}`));
    process.exit(1);
  }

  const sites = (sitesData.siteEntry || []).map((s) => ({ url: s.siteUrl, perm: s.permissionLevel }));
  if (sites.length === 0) {
    console.error(colors.fail('No GSC properties found on this account.'));
    console.error(colors.fail('Verify jessetek.net at https://search.google.com/search-console first.'));
    process.exit(1);
  }

  console.log(colors.ok('GSC properties accessible:'));
  sites.forEach((s) => console.log(`    • ${s.url} (${s.perm})`));

  // Pick the jessetek.net property
  let property = sites.find((s) => s.url === 'https://jessetek.net/')?.url
              || sites.find((s) => s.url === 'sc-domain:jessetek.net')?.url
              || sites.find((s) => s.url.includes('jessetek.net'))?.url
              || sites[0].url;

  console.log(colors.ok(`Using property: ${property}`));

  // Write refresh token + property back to .env.local
  writeEnv({ raw }, {
    GSC_REFRESH_TOKEN: tokens.refresh_token,
    GSC_PROPERTY: property,
  });

  console.log(colors.ok(`Wrote GSC_REFRESH_TOKEN + GSC_PROPERTY to ${ENV_PATH}`));
  console.log('');
  console.log(colors.bold('All set. The weekly-gsc-harvest Cowork task fires every Sunday 21:00.'));
  console.log(colors.bold('Test it now without waiting:'));
  console.log('  Open Cowork → Scheduled sidebar → jessetek-weekly-gsc-harvest → "Run now"');
  console.log('');
}

main().catch((err) => {
  console.error(colors.fail(err.message));
  process.exit(1);
});
