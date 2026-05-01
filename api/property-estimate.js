// Instant property value estimate via RentCast AVM
// https://developers.rentcast.io/reference/value-estimate
//
// Required env var: RENTCAST_API_KEY
//
// Used by /valuation page — seller types address, we ping this endpoint to
// show a rough automated estimate while they fill out the rest of the form.
// Real CMA still happens via LeadConnector workflow + Jesse's manual comps.

export default async function handler(req, res) {
  res.setHeader('Access-Control-Allow-Origin', '*');

  if (req.method === 'OPTIONS') return res.status(200).end();
  if (req.method !== 'GET') return res.status(405).json({ error: 'Method not allowed' });

  const address = (req.query.address || '').trim();
  if (!address || address.length < 8) {
    return res.status(400).json({ error: 'Address too short' });
  }

  // Edge cache 1 hour — same address → same estimate, no need to re-bill RentCast
  res.setHeader('Cache-Control', 'public, s-maxage=3600, stale-while-revalidate=86400');

  const apiKey = process.env.RENTCAST_API_KEY;
  if (!apiKey) {
    return res.status(503).json({ error: 'Estimate service not configured' });
  }

  try {
    const url = `https://api.rentcast.io/v1/avm/value?address=${encodeURIComponent(address)}`;
    const r = await fetch(url, {
      headers: { 'X-Api-Key': apiKey, Accept: 'application/json' },
    });

    if (r.status === 404) {
      return res.status(200).json({ found: false, reason: 'no_match' });
    }
    if (!r.ok) {
      const errText = await r.text().catch(() => '');
      // Don't leak the upstream body — could include rate limit details
      return res.status(200).json({
        found: false,
        reason: r.status === 429 ? 'rate_limit' : 'upstream_error',
      });
    }

    const data = await r.json();
    if (!data || typeof data.price !== 'number') {
      return res.status(200).json({ found: false, reason: 'no_estimate' });
    }

    // Trim comparables to keep response light — only what the UI uses
    const comps = (data.comparables || []).slice(0, 5).map((c) => ({
      address: c.formattedAddress,
      price: c.price,
      bedrooms: c.bedrooms,
      bathrooms: c.bathrooms,
      sqft: c.squareFootage,
      yearBuilt: c.yearBuilt,
      daysOnMarket: c.daysOnMarket,
      distance: c.distance ? Math.round(c.distance * 100) / 100 : null,
      correlation: c.correlation,
    }));

    return res.status(200).json({
      found: true,
      price: data.price,
      priceRangeLow: data.priceRangeLow,
      priceRangeHigh: data.priceRangeHigh,
      formattedAddress: data.subjectProperty?.formattedAddress || address,
      city: data.subjectProperty?.city,
      zipCode: data.subjectProperty?.zipCode,
      compsCount: (data.comparables || []).length,
      comps,
      source: 'rentcast',
    });
  } catch (err) {
    return res.status(200).json({ found: false, reason: 'fetch_error' });
  }
}
