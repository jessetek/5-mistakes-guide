// Where a website lead came from, saved on the contact after it is created (2026-10-24):
// Web Source, Web Campaign, Landing Page, Form Page, First Visit (text fields in the Jessetek
// sub-account). The browser side is /js/attrib.js (window.siteAttribution()), the same file
// jtek.app uses; the labels match Jtek/lib/web-attribution.js.
// Best effort and separate from creating the contact, so it can never cost a lead.

const FIELD_IDS = {
  source: 'TCwo4WdEDW51edibvHat', campaign: 'toMG3IRCychrIpsalLvX', landing: 'YafSdZclfdqeCD9BJc6J',
  form: 'SMuRXgrXjMwyHESyk0fT', firstVisit: 's9dNIC7W5W0W0eZrG8Ot',
};

const clean = (v, n) => String(v == null ? '' : v).replace(/[\u0000-\u001f<>]/g, '').trim().slice(0, n || 200);

function cleanTouch(t) {
  if (!t || typeof t !== 'object') return null;
  return {
    src: clean(t.src, 120), med: clean(t.med, 120), cmp: clean(t.cmp, 120), cnt: clean(t.cnt, 120), term: clean(t.term, 120),
    gclid: t.gclid === true, fbclid: t.fbclid === true, msclkid: t.msclkid === true,
    ref: clean(t.ref, 120).toLowerCase(), land: clean(t.land, 300), at: clean(t.at, 40),
  };
}

const SEARCH = [[/(^|\.)google\./, 'Google search'], [/(^|\.)bing\.com$/, 'Bing search'], [/duckduckgo\.com$/, 'DuckDuckGo'], [/(^|\.)yahoo\./, 'Yahoo search'], [/chatgpt\.com$|openai\.com$/, 'ChatGPT'], [/perplexity\.ai$/, 'Perplexity']];
const SOCIAL = [[/instagram\.com$/, 'Instagram'], [/facebook\.com$|fb\.com$|fb\.me$/, 'Facebook'], [/tiktok\.com$/, 'TikTok'], [/youtube\.com$|youtu\.be$/, 'YouTube'], [/linkedin\.com$|lnkd\.in$/, 'LinkedIn'], [/^t\.co$|(^|\.)x\.com$|twitter\.com$/, 'X'], [/reddit\.com$/, 'Reddit'], [/threads\.net$/, 'Threads'], [/zillow\.com$/, 'Zillow'], [/realtor\.com$/, 'Realtor.com'], [/yelp\.com$/, 'Yelp']];
const cap = (s) => s.charAt(0).toUpperCase() + s.slice(1);

export function sourceLabel(t) {
  if (!t) return '';
  const src = t.src.toLowerCase(), med = t.med.toLowerCase(), paid = /cpc|ppc|paid|ads?$|display|cpm/.test(med);
  if (t.gclid || (/google/.test(src) && paid)) return 'Google Ads';
  if (t.msclkid || (/bing|microsoft/.test(src) && paid)) return 'Microsoft Ads';
  if (/facebook|^fb$|instagram|^ig$|meta/.test(src) && paid) return 'Meta Ads';
  if (src) return med ? `${t.src} / ${t.med}` : cap(t.src);
  if (t.fbclid) return 'Facebook';
  if (t.ref) {
    for (const [re, name] of SEARCH) if (re.test(t.ref)) return name;
    for (const [re, name] of SOCIAL) if (re.test(t.ref)) return name;
    return `Referral: ${t.ref}`;
  }
  return 'Direct';
}

function dayLabel(iso) {
  const d = new Date(iso);
  return Number.isFinite(d.getTime()) ? d.toLocaleDateString('en-US', { timeZone: 'America/Los_Angeles', month: 'short', day: 'numeric', year: 'numeric' }) : '';
}

export function attributionValues(raw) {
  if (!raw || typeof raw !== 'object') return null;
  const first = cleanTouch(raw.first) || cleanTouch(raw.last);
  if (!first) return null;
  return {
    source: sourceLabel(first),
    campaign: [first.cmp, first.cnt, first.term].filter(Boolean).join(' / '),
    landing: first.land ? `jessetek.net${first.land}` : '',
    form: raw.page ? `jessetek.net${clean(raw.page, 200)}` : '',
    firstVisit: dayLabel(first.at),
  };
}

// Fills in the five fields on a contact that already exists. Never throws.
export async function saveAttribution(contactId, raw, headers) {
  try {
    const values = attributionValues(raw);
    if (!contactId || !values) return;
    const customFields = Object.keys(FIELD_IDS).filter((k) => values[k]).map((k) => ({ id: FIELD_IDS[k], field_value: values[k] }));
    const r = await fetch(`https://services.leadconnectorhq.com/contacts/${contactId}`, {
      method: 'PUT',
      headers: { ...headers, Version: '2021-07-28' },
      body: JSON.stringify({ customFields }),
    });
    if (!r.ok) console.warn('attribution not saved:', r.status, (await r.text()).slice(0, 160));
  } catch (e) {
    console.warn('attribution not saved:', e.message);
  }
}
