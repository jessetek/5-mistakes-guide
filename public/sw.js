// Lightweight service worker for jessetek.net
// - Offline fallback page
// - Stale-while-revalidate for static assets (CSS/images/fonts)
// - Network-first for HTML (always get freshest content if online)
// - No background sync, no push (out of scope for a real-estate site)

const CACHE_VERSION = 'jt-v1-2026-05-01';
const STATIC_CACHE = `${CACHE_VERSION}-static`;
const RUNTIME_CACHE = `${CACHE_VERSION}-runtime`;

// Pages worth pre-caching for instant repeat visits + offline fallback
const PRECACHE = [
  '/',
  '/home.html',
  '/offline.html',
  '/css/main.min.css?v=19',
  '/img/jesse-headshot.webp',
  '/img/og-home.jpg',
  '/favicon.ico',
];

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(STATIC_CACHE).then((cache) => cache.addAll(PRECACHE))
      .then(() => self.skipWaiting())
  );
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(
        keys
          .filter((k) => !k.startsWith(CACHE_VERSION))
          .map((k) => caches.delete(k))
      )
    ).then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', (event) => {
  const req = event.request;
  if (req.method !== 'GET') return;

  const url = new URL(req.url);

  // Don't intercept API calls — they need to hit network for live data
  if (url.pathname.startsWith('/api/')) return;

  // Don't intercept third-party (LeadConnector form, Google Maps, etc.)
  if (url.origin !== self.location.origin) return;

  // HTML pages: network-first with offline fallback
  if (req.mode === 'navigate' || (req.headers.get('accept') || '').includes('text/html')) {
    event.respondWith(
      fetch(req)
        .then((res) => {
          // Cache the fresh page for offline use
          const copy = res.clone();
          caches.open(RUNTIME_CACHE).then((cache) => cache.put(req, copy));
          return res;
        })
        .catch(() => caches.match(req).then((hit) => hit || caches.match('/offline.html')))
    );
    return;
  }

  // Static assets (CSS, JS, images, fonts): stale-while-revalidate
  if (/\.(css|js|jpg|jpeg|png|webp|svg|woff2|ico)(\?.*)?$/.test(url.pathname)) {
    event.respondWith(
      caches.match(req).then((cached) => {
        const fetchPromise = fetch(req).then((res) => {
          const copy = res.clone();
          caches.open(RUNTIME_CACHE).then((cache) => cache.put(req, copy));
          return res;
        }).catch(() => cached); // network failed, return cache if any
        return cached || fetchPromise;
      })
    );
    return;
  }

  // Default: network with cache fallback
  event.respondWith(
    fetch(req).catch(() => caches.match(req))
  );
});
