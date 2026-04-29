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

  const { firstName, email, phone, website, elapsed } = req.body;

  // Honeypot: real users never see this field, so any value means a bot.
  // Time-trap: humans take longer than 2s to fill the form.
  // Silently return 200 so bots think they succeeded and stop retrying.
  if (website || typeof elapsed !== 'number' || elapsed < 2000) {
    return res.status(200).json({ success: true });
  }

  if (!firstName || !email || !phone) {
    return res.status(400).json({ error: 'All fields are required' });
  }

  const apiKey = process.env.JTEK_API_KEY || '';
  const locationId = process.env.JTEK_LOCATION_ID || '';

  const contactData = {
    firstName,
    email,
    phone,
    locationId,
    source: '5 Mistakes Guide Lead Magnet',
    tags: ['lead-magnet', '5-mistakes-guide'],
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
    const isDuplicate = errorBody.toLowerCase().includes('duplicate') || errorBody.toLowerCase().includes('duplicated');

    if (isDuplicate) {
      // Upsert existing contact
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
