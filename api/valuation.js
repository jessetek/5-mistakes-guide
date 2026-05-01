// Free home valuation form handler
// Pushes the lead into LeadConnector / Jtek with valuation-specific tags so
// the user's existing GHL workflows can fire (auto-text seller, notify Jesse).
//
// Required env vars (already set for /api/submit):
//   - JTEK_API_KEY
//   - JTEK_LOCATION_ID

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

  const { address, name, contact, bedrooms, timeline, website, elapsed } = req.body || {};

  // Honeypot + time-trap. Same as submit.js.
  // 'website' is hidden from real users — bots auto-fill it.
  // 'elapsed' under 2s = bot.
  if (website || (typeof elapsed === 'number' && elapsed < 2000)) {
    return res.status(200).json({ success: true });
  }

  if (!address || !name || !contact) {
    return res.status(400).json({ error: 'Address, name, and contact are required' });
  }

  // Split contact into phone vs email so LeadConnector treats it correctly.
  const isEmail = /\S+@\S+\.\S+/.test(contact);
  const phone = isEmail ? '' : contact.replace(/[^0-9+]/g, '');
  const email = isEmail ? contact : '';

  // Auto-tag by timeline so workflows can branch by urgency.
  const tags = ['valuation-request', 'seller'];
  const tl = (timeline || '').toLowerCase();
  if (tl.includes('asap')) tags.push('lead-hot', 'timeline-asap');
  else if (tl.includes('1-3')) tags.push('lead-hot', 'timeline-1-3-months');
  else if (tl.includes('3-6')) tags.push('lead-warm', 'timeline-3-6-months');
  else tags.push('lead-nurture', 'timeline-curious');

  // First/last name split — best effort.
  const nameParts = String(name).trim().split(/\s+/);
  const firstName = nameParts[0] || name;
  const lastName = nameParts.slice(1).join(' ') || '';

  const apiKey = process.env.JTEK_API_KEY || '';
  const locationId = process.env.JTEK_LOCATION_ID || '';

  if (!apiKey || !locationId) {
    return res.status(500).json({ error: 'Server not configured' });
  }

  // Custom field payload — these become visible inside the contact in LeadConnector.
  const contactData = {
    firstName,
    lastName,
    email: email || undefined,
    phone: phone || undefined,
    locationId,
    source: 'Free Home Valuation Request',
    tags,
    address1: address,
    customField: {
      property_address: address,
      bedrooms: bedrooms || '',
      sell_timeline: timeline || '',
    },
  };

  try {
    const response = await fetch('https://services.leadconnectorhq.com/contacts/', {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${apiKey}`,
        'Content-Type': 'application/json',
        Version: '2021-04-15',
      },
      body: JSON.stringify(contactData),
    });

    if (response.ok) {
      const result = await response.json();
      return res.status(200).json({ success: true, contactId: result?.contact?.id || '' });
    }

    const errorBody = await response.text();
    const isDuplicate =
      errorBody.toLowerCase().includes('duplicate') ||
      errorBody.toLowerCase().includes('duplicated');

    if (isDuplicate) {
      // Upsert — preserves existing contact, adds new tags + custom fields.
      const upsertResponse = await fetch('https://services.leadconnectorhq.com/contacts/upsert', {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${apiKey}`,
          'Content-Type': 'application/json',
          Version: '2021-04-15',
        },
        body: JSON.stringify(contactData),
      });
      const upsertResult = await upsertResponse.json();
      return res.status(200).json({ success: true, contactId: upsertResult?.contact?.id || '' });
    }

    return res.status(500).json({ error: 'Failed to create contact', details: errorBody });
  } catch (err) {
    return res.status(500).json({ error: 'Server error', details: err.message });
  }
}
