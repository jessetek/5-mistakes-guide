// Move Up Quiz handler (jessetek.net/move, the Instagram bio link)
// Pushes the lead into LeadConnector / Jtek with quiz tags so GHL workflows can
// fire (text the lead, notify Jesse). Every answer is attached as a contact note.
//
// Required env vars (already set for /api/submit and /api/valuation):
//   - JTEK_API_KEY
//   - JTEK_LOCATION_ID

const PATHS = { buyer: 'buyer', seller: 'seller', moveup: 'move-up' };

const LABELS = {
  move: 'Next move', own: 'Owns a home', county: 'Home county', city: 'Home city', years: 'Years in home',
  why: 'Why moving', work: 'Home needs work', next: 'Headed after', sellFirst: 'Needs to sell first',
  whereCounty: 'Wants county', where: 'Wants cities', timeline: 'Timeline', rent: 'Current rent', lender: 'Talked to lender',
  saved: 'Saved for move', matters: 'Matters most', type: 'Home type', beds: 'Bedrooms',
  bedsNeed: 'Bedrooms needed', worth: 'Owner thinks it is worth', address: 'Property address',
};

const clean = (v, max = 120) => String(v == null ? '' : v).replace(/[\u0000-\u001f]/g, ' ').trim().slice(0, max);

export default async function handler(req, res) {
  if (req.method === 'OPTIONS') {
    res.setHeader('Access-Control-Allow-Origin', '*');
    res.setHeader('Access-Control-Allow-Methods', 'POST, OPTIONS');
    res.setHeader('Access-Control-Allow-Headers', 'Content-Type');
    return res.status(200).end();
  }
  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }
  res.setHeader('Access-Control-Allow-Origin', '*');

  const { name, phone, path, answers, utm, website, elapsed } = req.body || {};

  // Honeypot + time-trap, same as submit.js. A real person needs well over 5s for the quiz.
  if (website || (typeof elapsed === 'number' && elapsed < 5000)) {
    return res.status(200).json({ success: true });
  }

  const digits = String(phone || '').replace(/\D/g, '').replace(/^1(?=\d{10}$)/, '');
  if (!clean(name) || digits.length !== 10) {
    return res.status(400).json({ error: 'Name and a 10 digit phone are required' });
  }

  const a = answers && typeof answers === 'object' ? answers : {};
  const pathTag = PATHS[path] || 'buyer';

  // One tag only (Jesse, 2026-10-02). Path, timeline and source live in the contact note.
  const tags = ['move-up-quiz'];

  const nameParts = clean(name, 80).split(/\s+/);
  const firstName = nameParts[0];
  const lastName = nameParts.slice(1).join(' ');

  const apiKey = process.env.JTEK_API_KEY || '';
  const locationId = process.env.JTEK_LOCATION_ID || '';
  if (!apiKey || !locationId) {
    return res.status(500).json({ error: 'Server not configured' });
  }

  const noteLines = [`Move Up Quiz (${pathTag})`];
  Object.keys(LABELS).forEach((k) => {
    if (a[k]) noteLines.push(`${LABELS[k]}: ${clean(a[k], 300)}`);
  });
  if (utm && typeof utm === 'object') {
    const u = ['utm_source', 'utm_medium', 'utm_campaign', 'utm_content']
      .filter((k) => utm[k]).map((k) => `${k}=${clean(utm[k], 80)}`);
    if (u.length) noteLines.push(`Came from: ${u.join(' ')}`);
  }
  const notes = noteLines.join('\n');

  const contactData = {
    firstName,
    lastName: lastName || undefined,
    phone: `+1${digits}`,
    locationId,
    source: 'Move Up Quiz',
    tags,
    city: a.city && a.city !== 'Not on the list' ? clean(a.city, 60) : undefined,
    address1: a.address ? clean(a.address, 160) : undefined,
  };

  const ghlHeaders = {
    Authorization: `Bearer ${apiKey}`,
    'Content-Type': 'application/json',
    Version: '2021-04-15',
  };

  async function attachNote(contactId) {
    if (!contactId) return;
    try {
      await fetch(`https://services.leadconnectorhq.com/contacts/${contactId}/notes`, {
        method: 'POST',
        headers: ghlHeaders,
        body: JSON.stringify({ body: notes }),
      });
    } catch (_) {
      // Best-effort. The contact and tags already landed, so workflows still fire.
    }
  }

  try {
    const response = await fetch('https://services.leadconnectorhq.com/contacts/', {
      method: 'POST',
      headers: ghlHeaders,
      body: JSON.stringify(contactData),
    });

    if (response.ok) {
      const result = await response.json();
      const contactId = result?.contact?.id || '';
      await attachNote(contactId);
      return res.status(200).json({ success: true });
    }

    const errorBody = await response.text();
    if (/duplicate/i.test(errorBody)) {
      // Upsert keeps the existing contact and adds the quiz tags.
      const upsertResponse = await fetch('https://services.leadconnectorhq.com/contacts/upsert', {
        method: 'POST',
        headers: ghlHeaders,
        body: JSON.stringify(contactData),
      });
      const upsertResult = await upsertResponse.json();
      await attachNote(upsertResult?.contact?.id || '');
      return res.status(200).json({ success: true });
    }

    return res.status(500).json({ error: 'Failed to create contact' });
  } catch (err) {
    return res.status(500).json({ error: 'Server error' });
  }
}
