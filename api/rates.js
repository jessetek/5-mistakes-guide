// Live MORTGAGE30US (Freddie Mac PMMS, weekly Thursday release) via FRED
// Public API — https://fred.stlouisfed.org/series/MORTGAGE30US
//
// Vercel env var required: FRED_API_KEY
// Set it in: Vercel dashboard → Project → Settings → Environment Variables
//
// Cron: /vercel.json fires this endpoint daily at 16:00 UTC (8am PT, 11am ET)
// — well after FRED's Thursday ~10am ET publish — to keep the edge cache hot
// even on days with zero organic traffic.

export default async function handler(req, res) {
  res.setHeader('Access-Control-Allow-Origin', '*');

  if (req.method === 'OPTIONS') return res.status(200).end();
  if (req.method !== 'GET') return res.status(405).json({ error: 'Method not allowed' });

  // Edge cache: 12 hours fresh, 7 days stale-while-revalidate.
  // - 12h fresh: cron fires daily at 16:00 UTC, so the cache is always fresh
  //   for at least the next 12 hours after a cron run
  // - 7d SWR: if FRED is unreachable, we keep serving the last good value
  //   for up to a week while a background revalidation tries to recover
  res.setHeader('Cache-Control', 'public, s-maxage=43200, stale-while-revalidate=604800');

  // Cron requests come from Vercel with this header — log them so we can
  // verify in Vercel logs that the daily warm-up actually ran
  const isCron = req.headers['user-agent']?.includes('vercel-cron') === true ||
                 req.headers['x-vercel-cron'] != null;
  if (isCron) console.log('[rates.js] cron warm-up firing');

  const apiKey = process.env.FRED_API_KEY;

  // Static fallback — used if FRED is down or env var is missing.
  // Keeps the page functional with sensible illustrative numbers.
  const fallback = {
    current: 6.42,
    delta: -0.08,
    asOf: null,
    points: [
      { date: '2026-01-30', value: 6.95 },
      { date: '2026-02-06', value: 6.88 },
      { date: '2026-02-13', value: 6.79 },
      { date: '2026-02-20', value: 6.71 },
      { date: '2026-02-27', value: 6.66 },
      { date: '2026-03-06', value: 6.58 },
      { date: '2026-03-13', value: 6.61 },
      { date: '2026-03-20', value: 6.55 },
      { date: '2026-03-27', value: 6.50 },
      { date: '2026-04-03', value: 6.48 },
      { date: '2026-04-10', value: 6.42 },
      { date: '2026-04-17', value: 6.50 },
      { date: '2026-04-24', value: 6.42 }
    ],
    source: 'fallback',
  };

  // Window: how many weekly observations to return. Default 13 (one quarter).
  // Cap at 60 weeks so the response stays small (~1.5KB).
  const requestedWeeks = Math.min(60, Math.max(13, parseInt(req.query.weeks, 10) || 13));

  if (!apiKey) {
    // Trim fallback to requested window to match shape
    const slice = fallback.points.slice(-requestedWeeks);
    return res.status(200).json({ ...fallback, points: slice });
  }

  try {
    const url =
      `https://api.stlouisfed.org/fred/series/observations` +
      `?series_id=MORTGAGE30US` +
      `&api_key=${apiKey}` +
      `&file_type=json` +
      `&sort_order=desc` +
      `&limit=${requestedWeeks + 5}`; // +5 buffer for missing values

    const r = await fetch(url, { headers: { Accept: 'application/json' } });
    if (!r.ok) return res.status(200).json(fallback);

    const data = await r.json();
    const obs = (data && data.observations) || [];

    // FRED returns descending. Filter out missing values (".") and reverse to ascending.
    const cleaned = obs
      .filter((o) => o && o.value && o.value !== '.')
      .map((o) => ({ date: o.date, value: parseFloat(o.value) }))
      .filter((o) => Number.isFinite(o.value));

    if (cleaned.length < 2) return res.status(200).json(fallback);

    const ascending = cleaned.slice(0, requestedWeeks).reverse();
    const last = ascending[ascending.length - 1];
    const prev = ascending[ascending.length - 2];

    return res.status(200).json({
      current: last.value,
      delta: Math.round((last.value - prev.value) * 100) / 100,
      asOf: last.date,
      points: ascending,
      source: 'fred',
    });
  } catch (err) {
    return res.status(200).json(fallback);
  }
}
