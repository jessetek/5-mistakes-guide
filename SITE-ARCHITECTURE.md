# jessetek.net — Architecture Reference

This is the senior-dev reference for how the site is built. Update this file when architecture changes.

## Stack

| Layer | Tool | Notes |
|---|---|---|
| Hosting | Vercel | Static + serverless functions; Hobby tier |
| Source | GitHub `jessetek/5-mistakes-guide` | Auto-deploys `main` branch |
| Server | None (static HTML) | Plus 4 `/api/*.js` Vercel functions |
| Styles | Hand-written CSS | `main.css` source, `main.min.css` shipped |
| JS | Vanilla, no framework | `analytics.js` + `reviews-api.js` |
| CRM | LeadConnector / GHL (Jtek) | Form submissions, SMS workflows |
| Live data | FRED + RentCast | Mortgage rates + property AVM |
| Analytics | GA4 + Vercel Web + Web Vitals | Plus Microsoft Clarity slot (not active) |

## File structure

```
public/                       # Static + HTML site root (Vercel publishes this)
├── home.html                 # Main entry (rewrites `/` → `/home`)
├── *.html                    # Top-level pages (~30)
├── neighborhoods/            # 47 city pages
├── insights/                 # Blog (14 posts + index + RSS feed)
├── es/                       # Spanish pages (6 + index)
├── img/                      # Images + OG images per page
├── css/main.css              # Source CSS (4500 lines)
├── css/main.min.css          # Production CSS (minified, ~150KB)
├── js/analytics.js           # GA4 + Web Vitals + cookie consent + SW reg
├── js/reviews-api.js         # Google Places review embed (scaffold)
├── sw.js                     # Service worker (PWA + offline fallback)
├── manifest.json             # PWA manifest
├── 404.html                  # Custom 404
├── offline.html              # SW offline fallback
├── sitemap.xml               # Main sitemap (~100 URLs)
├── sitemap-images.xml        # Image sitemap (Google Image search)
├── sitemap-index.xml         # Sitemap index
└── robots.txt                # Sitemap pointers + AI bot blocks

api/                          # Vercel serverless functions (Node 20)
├── submit.js                 # 5-mistakes guide form → LeadConnector
├── valuation.js              # Valuation form → LeadConnector
├── property-estimate.js      # RentCast AVM proxy
└── rates.js                  # FRED MORTGAGE30US proxy + cron warm

vercel.json                   # cleanUrls, rewrites, headers, daily cron
```

## Deploy flow

1. `git push origin main` to GitHub
2. Vercel webhook triggers a build
3. Vercel uploads `public/` + spins up `/api/*` as edge functions
4. CDN propagates to all regions in ~30-60s

Cache busting via query string on stylesheet (`?v=N`). Bump on every CSS change.

## Environment variables (Vercel dashboard)

| Var | Used by | Notes |
|---|---|---|
| `JTEK_API_KEY` | `submit.js`, `valuation.js` | LeadConnector API token |
| `JTEK_LOCATION_ID` | `submit.js`, `valuation.js` | LeadConnector location |
| `FRED_API_KEY` | `rates.js` | Federal Reserve API key |
| `RENTCAST_API_KEY` | `property-estimate.js` | RentCast AVM key |

All set in Vercel → Project → Settings → Environment Variables. Production + Development scopes.

## Caching strategy

| Asset type | Strategy | Header |
|---|---|---|
| Images (jpg/png/webp/svg) | 1 year immutable | `public, max-age=31536000, immutable` |
| CSS | 30 days | `public, max-age=2592000` (cache-bust via `?v=N`) |
| HTML | Default Vercel | Revalidates per ETag |
| `/api/rates` | 12h fresh + 7d SWR | Edge cached + daily cron warm |
| `/api/property-estimate` | 1h fresh + 24h SWR | Per-address cached |
| `/sitemap*.xml`, `/robots.txt` | 1 day | `public, max-age=86400` |
| Service worker runtime | Stale-while-revalidate | Browser-side |

## Performance targets

- LCP < 2.5s (mobile)
- CLS < 0.1
- INP < 200ms
- TTFB < 600ms

Real-user data flows to GA4 via `analytics.js` PerformanceObserver. Audit periodically via:
- https://pagespeed.web.dev/ (PSI Lighthouse mobile + desktop)
- Vercel Speed Insights (real-user)

## Image optimization audit

Current state of image assets:
- **OG images**: 1200×630 JPG + WebP (60-90KB), one per page. Generated via Python+PIL.
- **Hero image** (`img/hero-bg.jpg/.webp`): 143KB WebP (preload + fetchpriority=high on home)
- **Headshot** (`img/jesse-headshot.jpeg/.webp`): ~80×80 displayed, sourced ~800×1200
- **Client photos** (`img/clients/c-*.jpg/.webp`): 34 files, marquee usage, ~50-150KB each

To-do for future image work:
- Audit client photos for srcset variants (currently single size — wastes bytes on mobile)
- Consider AVIF for hero (smaller than WebP, broad support in 2026)
- Build `<picture>` shortcode for any new images so WebP is always served first

## Error tracking

**Currently NOT enabled.** Recommendations when ready:

### Option A — Sentry (best for code errors)
1. Sign up at sentry.io (free tier: 5K errors/month)
2. Get DSN, add to `analytics.js`:
   ```js
   if (window.Sentry) {
     Sentry.init({
       dsn: '...',
       environment: 'production',
       tracesSampleRate: 0.1, // 10% transaction sampling
     });
   }
   ```
3. Add `<script src="https://browser.sentry-cdn.com/.../bundle.min.js"></script>` to head
4. Catches: JS exceptions, unhandled promise rejections, fetch failures
5. Cost: $0/mo at our traffic level for years

### Option B — Vercel Speed Insights + native Web Vitals (already on)
- Already capturing real-user LCP/CLS/INP/FCP/TTFB
- For JS exceptions, use `window.onerror` and post to a custom endpoint
- Cheaper ($0) but less rich than Sentry

### Recommended: skip Sentry for now
At current site complexity, real-user perf metrics + Vercel runtime logs are enough. Revisit when there's a real error problem.

## Adding a new page (checklist)

1. Create `public/{slug}.html` with standardized:
   - Mobile nav block
   - Desktop nav block
   - Footer with legal links + DRE + EHO
   - Canonical, OG tags, JSON-LD schema
2. Create OG image at 1200×630 → `public/img/og-{slug}.jpg/.webp`
3. Add to `public/sitemap.xml` with priority
4. Add to `public/sitemap-images.xml` (run the regen script)
5. Add nav/footer link if it's a primary page
6. Bump `main.min.css?v=N` if CSS changed
7. Run QC sweep (see below)

## Adding a new city

Same as above plus:
- Add to `service-areas.html` tile grid
- Add to `areaServed` schema array site-wide (sed/python script)
- Add to `RELATED` map in the related-cities script
- Custom sub-areas + schools data in the city template

## QC sweep (run before deploy)

```bash
python3 << 'EOF'
import os, re, json, glob
PUB = "public"
files = sorted(glob.glob(f'{PUB}/**/*.html', recursive=True))
files = [f for f in files if 'og-generator' not in f]
issues = []
local = set()
for f in files:
    rel = os.path.relpath(f, PUB).replace(os.sep, '/')
    local.add('/' + rel); local.add('/' + rel.replace('.html', ''))
    if rel.endswith('/index.html'):
        local.add('/' + rel.replace('/index.html', '/'))
        local.add('/' + rel.replace('/index.html', ''))
LM = ('guide.html', 'guide-pdf.html')
for path in files:
    rel = os.path.relpath(path, PUB)
    with open(path) as fh: t = fh.read()
    for m in re.finditer(r'<script type="application/ld\+json">(.*?)</script>', t, re.DOTALL):
        try: json.loads(m.group(1))
        except Exception as e: issues.append((rel, f"BAD JSON-LD"))
    if rel not in LM and 'rel="canonical"' not in t and '<head>' in t:
        issues.append((rel, "missing canonical"))
    for m in re.finditer(r'(?:src|href)="(/img/[^"]+\.(?:jpg|webp|png))"', t):
        if not os.path.exists(PUB + m.group(1)):
            issues.append((rel, f"missing img: {m.group(1)}"))
print(f'{len(files)} files, {len(set(issues))} issues')
PYEOF
```

## Where things break (from experience)

1. **Bulk regex replaces** can match more than intended. Always test on 2-3 files first.
2. **CSS specificity** with the `.scrolled` class on nav can override dropdown menu colors — use both selectors.
3. **JSON-LD scripts** with curly braces inside Python `.format()` strings break — use `+` concatenation.
4. **Vercel cron** uses UTC times, not PT. Set explicitly.
5. **Cache-busting** — bump `?v=N` on HTML when CSS/JS changes, otherwise visitors see stale.
6. **CDN cache** can serve stale 404s for new pages. Add `?cb={timestamp}` to verify.
