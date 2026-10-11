// api/_form-guard.js (the underscore keeps Vercel from serving it as an endpoint)
// Spam screen shared by /api/submit, /api/valuation and /api/quiz. Same rules as
// the Jtek site (jtekpro lib/form-guard.js, 2026-10-11).
//
// Two kinds of verdict:
//   hard  - honeypot filled, timer missing or too fast, bad or throwaway email.
//           One is enough to drop.
//   soft  - signals a real person rarely trips (random name, Gmail dot trick,
//           impossible US phone). Any ONE alone passes; two or more drop, so a
//           real lead with one oddity still gets through.

const EMAIL = /^[^\s@]+@[^\s@]+\.[a-z]{2,}$/i;

// Throwaway inbox domains. A match is a hard drop, so only list domains no
// buyer or seller would use.
const DISPOSABLE = new Set([
  'mailinator.com', 'guerrillamail.com', '10minutemail.com', 'tempmail.com',
  'temp-mail.org', 'yopmail.com', 'trashmail.com', 'sharklasers.com',
  'getnada.com', 'dispostable.com', 'maildrop.cc', 'throwawaymail.com',
]);

const GMAIL = new Set(['gmail.com', 'googlemail.com']);

// "uvxfl" has v-x-f-l. h and y count as vowels here so "Schwartz" stays clean.
const CONSONANT_RUN = /[bcdfgjklmnpqrstvwxz]{4,}/i;

export function gibberishName(first, last) {
  const parts = [first, last].map((s) => String(s || '').replace(/[^a-z]/gi, '')).filter(Boolean);
  if (parts.some((p) => p.length >= 4 && !/[aeiouy]/i.test(p))) return true;
  return parts.some((p) => CONSONANT_RUN.test(p));
}

export function gmailDotTrick(email) {
  const [local, domain] = String(email || '').toLowerCase().split('@');
  if (!local || !GMAIL.has(domain)) return false;
  return (local.match(/\./g) || []).length >= 3;
}

// US and Canada numbers only. Area codes and exchanges cannot start with 0 or
// 1, N11 is reserved, and 37x / 96x / 555 area codes are reserved or unused.
// Soft signal only, so a stale entry never costs a real lead on its own.
// Numbers starting with another country code are left alone.
const UNASSIGNED_NPA = /^(37\d|96\d|555|\d11)$/;
const UNUSED_9XX = new Set(['922', '923', '924', '926', '927', '932', '933', '944', '953', '955', '957', '958', '977', '981', '987', '988']);

export function badUsPhone(phone) {
  const raw = String(phone || '').trim();
  if (!raw) return false;
  if (raw.startsWith('+') && !raw.startsWith('+1')) return false;
  let d = raw.replace(/\D/g, '');
  if (d.length === 11 && d[0] === '1') d = d.slice(1);
  if (d.length !== 10) return true;
  const npa = d.slice(0, 3);
  const nxx = d.slice(3, 6);
  if (/^[01]/.test(npa) || /^[01]/.test(nxx)) return true;
  return UNASSIGNED_NPA.test(npa) || UNUSED_9XX.has(npa);
}

// fields: { firstName, lastName, email, phone } (email or phone may be empty).
// meta:   { honeypot, elapsed, minMs }.
// Returns { ok, reasons } where reasons names every signal that fired.
export function screen(fields, meta = {}) {
  const reasons = [];
  const email = String(fields.email || '').trim();

  if (String(meta.honeypot || '').trim()) reasons.push('honeypot');
  const ms = Number(meta.elapsed);
  if (!Number.isFinite(ms) || ms < (meta.minMs || 2000)) reasons.push('too-fast');
  if (email) {
    if (!EMAIL.test(email)) reasons.push('bad-email');
    else if (DISPOSABLE.has(email.split('@')[1].toLowerCase())) reasons.push('disposable-email');
  }
  const hard = reasons.length > 0;

  const soft = [];
  if (gibberishName(fields.firstName, fields.lastName)) soft.push('gibberish-name');
  if (gmailDotTrick(email)) soft.push('gmail-dots');
  if (badUsPhone(fields.phone)) soft.push('bad-phone');
  reasons.push(...soft);

  return { ok: !hard && soft.length < 2, reasons };
}
