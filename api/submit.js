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

  const { firstName, email, phone, website, elapsed, source, quizScore, quizBand, quizAnswers } = req.body;

  // Honeypot: real users never see this field, so any value means a bot.
  // Time-trap: humans take longer than 2s to fill the form.
  // Silently return 200 so bots think they succeeded and stop retrying.
  if (website || typeof elapsed !== 'number' || elapsed < 2000) {
    return res.status(200).json({ success: true });
  }

  // firstName + email are always required. Phone is required for the guide form
  // (sent as a non-empty string) but optional for the buyer quiz (email-only capture).
  if (!firstName || !email) {
    return res.status(400).json({ error: 'firstName and email are required' });
  }

  const isBuyerQuiz = source === 'buyer-quiz';
  if (!isBuyerQuiz && !phone) {
    return res.status(400).json({ error: 'phone is required' });
  }

  // Quiz bands look like "READY · 80+" — slugify cleanly so GHL workflows can
  // filter by tag name (ready, strong-start, building, early, exploring).
  function slugifyBand(band) {
    if (!band) return 'unknown';
    return String(band)
      .split(/[·•|–\-]/)[0]      // drop the score range after the divider
      .toLowerCase()
      .replace(/[^a-z0-9]+/g, '-') // anything non-alphanumeric → dash
      .replace(/^-+|-+$/g, '');    // trim leading/trailing dashes
  }

  const apiKey = process.env.JTEK_API_KEY || '';
  const locationId = process.env.JTEK_LOCATION_ID || '';

  const contactData = {
    firstName,
    email,
    phone: phone || undefined,
    locationId,
    source: isBuyerQuiz ? 'Buyer Readiness Quiz' : '5 Mistakes Guide Lead Magnet',
    tags: isBuyerQuiz
      ? ['buyer-quiz', `quiz-band-${slugifyBand(quizBand)}`]
      : ['lead-magnet', '5-mistakes-guide'],
  };

  const ghlHeaders = {
    Authorization: `Bearer ${apiKey}`,
    'Content-Type': 'application/json',
    Version: '2021-04-15',
  };

  // Buyer-quiz contacts get a note with their score and answers so Jesse can
  // see context inside the contact (and workflows can email the right plan).
  let notes = '';
  if (isBuyerQuiz) {
    const lines = [`Buyer Readiness Quiz result`];
    if (quizScore !== undefined && quizScore !== null) lines.push(`Score: ${quizScore}`);
    if (quizBand) lines.push(`Band: ${quizBand}`);
    if (quizAnswers && typeof quizAnswers === 'object') {
      lines.push('Answers:');
      Object.entries(quizAnswers).forEach(([q, a]) => lines.push(`  ${q}: ${a}`));
    }
    notes = lines.join('\n');
  }

  async function attachNote(contactId) {
    if (!contactId || !notes) return;
    try {
      await fetch(`https://services.leadconnectorhq.com/contacts/${contactId}/notes`, {
        method: 'POST',
        headers: ghlHeaders,
        body: JSON.stringify({ body: notes }),
      });
    } catch (_) {
      // Best-effort — contact already exists, workflows still fire on tags.
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
      return res.status(200).json({ success: true, contactId });
    }

    const errorBody = await response.text();
    const isDuplicate = errorBody.toLowerCase().includes('duplicate') || errorBody.toLowerCase().includes('duplicated');

    if (isDuplicate) {
      // Upsert existing contact
      const upsertResponse = await fetch('https://services.leadconnectorhq.com/contacts/upsert', {
        method: 'POST',
        headers: ghlHeaders,
        body: JSON.stringify(contactData),
      });
      const upsertResult = await upsertResponse.json();
      const contactId = upsertResult?.contact?.id || '';
      await attachNote(contactId);
      return res.status(200).json({ success: true, contactId });
    }

    return res.status(500).json({ error: 'Failed to create contact', details: errorBody });
  } catch (err) {
    return res.status(500).json({ error: 'Server error', details: err.message });
  }
}
