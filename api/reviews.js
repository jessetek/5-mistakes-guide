// Live Google reviews for jessetek.net.
// Source: the public review widget of the Jessetek account (the same data the
// account's Reputation tab shows). No key is needed: the widget page is public.
//
// The page script (public/js/reviews.js) calls this first and falls back to the
// snapshot in public/data/reviews.json, so reviews always render.

const WIDGET = 'https://services.leadconnectorhq.com/reputation/widgets/review_widget/4IKcbmtpx3ZLuYU0uJzw';

// Pull the JSON array that follows `"reviews":` out of the widget's inline data.
function sliceArray(src, key) {
  const start = src.indexOf(key);
  if (start < 0) return null;
  let i = start + key.length - 1; // points at '['
  let depth = 0;
  for (; i < src.length; i++) {
    const c = src[i];
    if (c === '"') { // skip strings
      i++;
      while (i < src.length && src[i] !== '"') { if (src[i] === '\\') i++; i++; }
    } else if (c === '[') depth++;
    else if (c === ']') { depth--; if (depth === 0) break; }
  }
  return src.slice(start + key.length - 1, i + 1);
}

export default async function handler(req, res) {
  res.setHeader('Access-Control-Allow-Origin', '*');
  if (req.method === 'OPTIONS') return res.status(200).end();
  if (req.method !== 'GET') return res.status(405).json({ error: 'Method not allowed' });

  try {
    const r = await fetch(WIDGET, { headers: { 'User-Agent': 'Mozilla/5.0 (jessetek.net reviews)' } });
    if (!r.ok) throw new Error('widget ' + r.status);
    const html = await r.text();
    const raw = sliceArray(html, '"reviews":[');
    if (!raw) throw new Error('no reviews in widget');
    const list = JSON.parse(raw);

    const seen = new Set();
    const reviews = [];
    for (const x of list) {
      const text = String(x.comment || '').trim();
      const key = text ? text.slice(0, 80) : x.id;
      if (seen.has(key)) continue;
      seen.add(key);
      reviews.push({
        name: String(x.reviewerName || '').trim(),
        stars: Number(x.starRating) || 0,
        text,
        date: String(x.dateAdded || '').slice(0, 10),
      });
    }
    if (!reviews.length) throw new Error('empty');

    const agg = html.match(/"aggregateData":\{"totalReviews":(\d+),"totalRating":([\d.]+)\}/);
    const total = agg ? Number(agg[1]) : list.length;
    const rating = agg ? Number(agg[2]) : 5;

    // One day fresh, a week of stale-while-revalidate if the widget is down.
    res.setHeader('Cache-Control', 'public, s-maxage=86400, stale-while-revalidate=604800');
    return res.status(200).json({
      source: 'Google', rating, total,
      updated: new Date().toISOString().slice(0, 10),
      reviews,
    });
  } catch (err) {
    console.error('[reviews.js]', err.message);
    res.setHeader('Cache-Control', 'public, s-maxage=300');
    return res.status(502).json({ error: 'reviews unavailable' });
  }
}
