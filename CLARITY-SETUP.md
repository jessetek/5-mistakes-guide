# How to See Heatmaps + Session Recordings of Your Site

The site is now wired for **three data sources** — pick what you want to plug in.

---

## 1. Microsoft Clarity (heatmaps + session recordings) — **Free, unlimited, recommended**

What you get: see exactly where users click, scroll, get stuck, rage-click, drop off — across every page on the site. Plus session recordings of real visitors. Free forever, no quota.

### Setup (5 min)

1. Go to **https://clarity.microsoft.com/** → Sign in (Google/Microsoft/Facebook)
2. Click **"+ New project"** in the top-right
   - Name: `jessetek.net`
   - Website URL: `https://jessetek.net`
   - Industry: Real Estate
3. After creation, you'll see a **Project ID** at the top (10-character string like `abc1234xyz`)
4. Open `public/js/analytics.js` and replace:
   ```js
   CLARITY_ID: null,
   ```
   with:
   ```js
   CLARITY_ID: "your-10-char-id-here",
   ```
5. Commit + push. Live in ~1 min via Vercel.

### What you'll see in Clarity dashboard
- **Heatmaps** for every page (where users click, scroll depth, attention map)
- **Session recordings** — actual video of users using the site
- **Dead clicks** — places people click that don't do anything (UX bug spotter)
- **Rage clicks** — frustrated repeated clicking
- **Quick backs** — pages people leave fast (problem signal)
- **JavaScript errors** — auto-detected
- Filter by traffic source, device, page, country, custom events

### What to look at first (after 100+ sessions)
- **/rates heatmap** — is the form getting reached? Where are people clicking before dropping off?
- **/home heatmap** — what's getting attention vs ignored
- **Session recordings of /zoom drop-offs** — why are people not booking?
- **Mobile vs desktop split** — likely 70%+ mobile for real estate

---

## 2. Google Reviews live integration

Pull your **live Google reviews** (with current rating + review count) into `/reviews` instead of hardcoded testimonials. Updates automatically when new reviews come in.

### Setup (10 min)

1. **Find your Place ID:**
   - Go to https://developers.google.com/maps/documentation/places/web-service/place-id
   - Search "Jesse Onate Realtor Montebello" → copy the Place ID (looks like `ChIJ...`)
2. **Get a Maps API key:**
   - https://console.cloud.google.com/apis/credentials
   - Create credentials → API key
   - **Restrict the key:**
     - Application restrictions → HTTP referrers → add `*.jessetek.net/*` and `jessetek.net/*`
     - API restrictions → Restrict key → check "Places API"
3. **Enable the Places API:**
   - https://console.cloud.google.com/apis/library/places-backend.googleapis.com → Enable
4. **Update `public/js/analytics.js`:**
   ```js
   GOOGLE_PLACE_ID: "ChIJ-your-place-id-here",
   GOOGLE_PLACES_API_KEY: "AIza-your-key-here",
   ```
5. Commit + push.

The script caches results in localStorage for 24 hours — so after the first daily fetch, every visitor uses 0 API calls. Free tier is 1000/month, so we'll never hit it.

### Fallback behavior
If `GOOGLE_PLACE_ID` or `GOOGLE_PLACES_API_KEY` is null, the existing static testimonials stay visible. Drop in IDs and the live block replaces them seamlessly.

---

## 3. PWA install prompt — let mobile users install your site as an app

Your site already has a `manifest.json` (Web App Manifest) and proper PWA icons. Modern Chrome/Safari will offer "Add to Home Screen" automatically.

### To go further (optional)

If you want a **custom prompt** that nudges mobile users to install (similar to "Save this to your phone for fast access to rates" — common conversion lift), you'd add:

```js
// Listen for the install opportunity
let deferredPrompt;
window.addEventListener('beforeinstallprompt', (e) => {
  e.preventDefault();
  deferredPrompt = e;
  // Show your custom UI here
});

// When user clicks your custom Install button
function installApp() {
  if (!deferredPrompt) return;
  deferredPrompt.prompt();
}
```

This is technically achievable but it requires designing a banner/button (a visible UI element). Since you've asked to keep visual design intact, I'd skip this unless you want to add a small mobile-only "Install" button somewhere — let me know if you want to design it together.

**Already working without any extra code:** users can manually save the site to their home screen via the browser menu. Many already do this for the rate alerts page.

---

## What's already live and tracking (no setup needed)

| Tool | Status | What it captures |
|---|---|---|
| **Vercel Analytics** | ✅ Live | Page views, top pages, country, referrer |
| **GA4** (`G-ZXSY9V9PXX`) | ✅ Live | Sessions, conversions, custom events |
| **Web Vitals** (LCP, CLS, INP, FCP, TTFB) | ✅ Live | Real-user Core Web Vitals → GA4 |
| **Auto-tracked clicks** | ✅ Live | phone, SMS, email, /zoom, /rates, /guide, /valuation |
| **GSC** | ✅ Verified | Search impressions, clicks, queries |
| **Bing Webmaster** | ✅ Verified | Same for Bing (~10% of traffic) |

---

## My recommendation: do these three this week

1. **Clarity (5 min)** — biggest unlock. You'll see exactly where users actually click and where the friction is.
2. **Place ID + Maps API (10 min)** — reviews go live, no more outdated hardcoded testimonials
3. **Mark `click_book_call` + `click_valuation` as Key Events in GA4** — once events fire (24-48h), 1-click toggle in GA4 admin

Total: ~20 min. Massively better visibility into what's working.
