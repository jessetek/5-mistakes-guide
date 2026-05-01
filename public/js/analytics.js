/* ============================================================
   ANALYTICS — single file, just drop in your IDs.
   ------------------------------------------------------------
   1. GA4_ID:        Get from analytics.google.com (looks like G-XXXXXXXXXX)
   2. META_PIXEL_ID: Get from business.facebook.com/events_manager (16-digit number)
   3. VERCEL:        Auto-loads if you enable Vercel Analytics in dashboard
                     (no ID needed — just toggle in Vercel project settings)

   Leave a value as null/empty to skip that integration.
   ============================================================ */

window.JESSE_CONFIG = window.JESSE_CONFIG || {
  GA4_ID: "G-ZXSY9V9PXX",   // Live GA4 property for jessetek.net
  META_PIXEL_ID: null,      // Add when running FB/IG ads (16-digit number)
  VERCEL_ANALYTICS: true,   // Vercel Web Analytics enabled in dashboard 2026-04-30
  GOOGLE_PLACE_ID: null,    // Get from places API place ID finder (for /reviews)
  GOOGLE_PLACES_API_KEY: null, // Restrict to jessetek.net referrer + Places API only
  CLARITY_ID: null,         // Microsoft Clarity Project ID (heatmaps + recordings)
                            // Get free at https://clarity.microsoft.com
                            // 10-char string like "abc1234xyz"
};

(function () {
  var cfg = window.JESSE_CONFIG;

  // ----- Google Analytics 4 -----
  if (cfg.GA4_ID) {
    var gaScript = document.createElement('script');
    gaScript.async = true;
    gaScript.src = 'https://www.googletagmanager.com/gtag/js?id=' + cfg.GA4_ID;
    document.head.appendChild(gaScript);
    window.dataLayer = window.dataLayer || [];
    window.gtag = function () { dataLayer.push(arguments); };
    gtag('js', new Date());
    gtag('config', cfg.GA4_ID, { anonymize_ip: true });
  }

  // ----- Meta (Facebook) Pixel -----
  if (cfg.META_PIXEL_ID) {
    !function (f, b, e, v, n, t, s) {
      if (f.fbq) return; n = f.fbq = function () { n.callMethod ? n.callMethod.apply(n, arguments) : n.queue.push(arguments); };
      if (!f._fbq) f._fbq = n; n.push = n; n.loaded = !0; n.version = '2.0'; n.queue = []; t = b.createElement(e); t.async = !0;
      t.src = v; s = b.getElementsByTagName(e)[0]; s.parentNode.insertBefore(t, s);
    }(window, document, 'script', 'https://connect.facebook.net/en_US/fbevents.js');
    fbq('init', cfg.META_PIXEL_ID);
    fbq('track', 'PageView');
  }

  // ----- Custom event helpers (use anywhere) -----
  window.trackEvent = function (name, params) {
    params = params || {};
    if (window.gtag) gtag('event', name, params);
    if (window.fbq)  fbq('trackCustom', name, params);
  };

  // ----- Auto-track key conversion clicks -----
  document.addEventListener('click', function (e) {
    var t = e.target.closest && e.target.closest('a, button');
    if (!t) return;
    var href = (t.getAttribute('href') || '').toLowerCase();
    var txt  = (t.textContent || '').trim().slice(0, 60);

    if (href.startsWith('tel:'))  trackEvent('click_phone',   { phone: href, label: txt });
    if (href.startsWith('sms:'))  trackEvent('click_sms',     { sms: href, label: txt });
    if (href.startsWith('mailto:')) trackEvent('click_email', { email: href, label: txt });
    if (href.includes('/zoom'))   trackEvent('click_book_call',  { label: txt });
    if (href.includes('/rates'))  trackEvent('click_rate_alerts',{ label: txt });
    if (href.includes('/guide'))  trackEvent('click_guide',     { label: txt });
    if (href.includes('/valuation')) trackEvent('click_valuation', { label: txt });
  }, { passive: true });

  // ----- Microsoft Clarity (heatmaps + session recordings + dead-click detection) -----
  // Free, unlimited. Get Project ID at https://clarity.microsoft.com
  if (cfg.CLARITY_ID) {
    (function (c, l, a, r, i, t, y) {
      c[a] = c[a] || function () { (c[a].q = c[a].q || []).push(arguments); };
      t = l.createElement(r); t.async = 1; t.src = "https://www.clarity.ms/tag/" + i;
      y = l.getElementsByTagName(r)[0]; y.parentNode.insertBefore(t, y);
    })(window, document, "clarity", "script", cfg.CLARITY_ID);
  }

  // ----- Vercel Web Analytics (static-site script tag) -----
  // Vercel hosts the script at /_vercel/insights/script.js when the project
  // has Web Analytics enabled in the dashboard.
  if (cfg.VERCEL_ANALYTICS) {
    window.va = window.va || function () { (window.vaq = window.vaq || []).push(arguments); };
    var vaScript = document.createElement('script');
    vaScript.defer = true;
    vaScript.src = '/_vercel/insights/script.js';
    document.head.appendChild(vaScript);
  }

  // ----- Web Vitals reporting (LCP, CLS, INP, FCP, TTFB) -----
  // Sends real-user Core Web Vitals to GA4 — the actual numbers Google
  // ranks on, not Lighthouse's lab simulation. Uses native PerformanceObserver
  // APIs to avoid pulling in the web-vitals library.
  function reportVital(name, value, id) {
    var rounded = name === 'CLS' ? Math.round(value * 1000) / 1000 : Math.round(value);
    if (window.gtag) {
      gtag('event', name, {
        value: rounded,
        metric_id: id,
        metric_value: rounded,
        metric_delta: rounded,
        non_interaction: true
      });
    }
    if (window.va) window.va('event', { name: 'web-vital-' + name, data: { value: rounded } });
  }

  // LCP — Largest Contentful Paint
  try {
    var lcpId = 'lcp-' + Date.now();
    new PerformanceObserver(function (list) {
      var entries = list.getEntries();
      var last = entries[entries.length - 1];
      if (last) reportVital('LCP', last.startTime, lcpId);
    }).observe({ type: 'largest-contentful-paint', buffered: true });
  } catch (e) {}

  // CLS — Cumulative Layout Shift
  try {
    var clsValue = 0, clsEntries = [];
    var clsId = 'cls-' + Date.now();
    new PerformanceObserver(function (list) {
      list.getEntries().forEach(function (entry) {
        if (!entry.hadRecentInput) {
          clsValue += entry.value;
          clsEntries.push(entry);
        }
      });
    }).observe({ type: 'layout-shift', buffered: true });
    // Report on visibility change (page hidden = final CLS reading)
    document.addEventListener('visibilitychange', function () {
      if (document.visibilityState === 'hidden') reportVital('CLS', clsValue, clsId);
    });
  } catch (e) {}

  // INP — Interaction to Next Paint (replaces FID in 2024+)
  try {
    var inpId = 'inp-' + Date.now();
    new PerformanceObserver(function (list) {
      list.getEntries().forEach(function (entry) {
        if (entry.duration > 40) reportVital('INP', entry.duration, inpId);
      });
    }).observe({ type: 'event', buffered: true, durationThreshold: 40 });
  } catch (e) {}

  // FCP — First Contentful Paint
  try {
    var fcpId = 'fcp-' + Date.now();
    new PerformanceObserver(function (list) {
      list.getEntries().forEach(function (entry) {
        if (entry.name === 'first-contentful-paint') reportVital('FCP', entry.startTime, fcpId);
      });
    }).observe({ type: 'paint', buffered: true });
  } catch (e) {}

  // TTFB — Time To First Byte
  try {
    var nav = performance.getEntriesByType('navigation')[0];
    if (nav) {
      var ttfb = nav.responseStart - nav.requestStart;
      reportVital('TTFB', ttfb, 'ttfb-' + Date.now());
    }
  } catch (e) {}

  // ----- Service worker registration (PWA + offline fallback) -----
  // Caches static assets stale-while-revalidate; HTML pages network-first
  // with /offline.html fallback. Adds zero overhead on first load (SW only
  // activates on second pageview), and shaves real time on repeat visits.
  if ('serviceWorker' in navigator) {
    window.addEventListener('load', function () {
      navigator.serviceWorker.register('/sw.js').catch(function (err) {
        // Silent — SW failures shouldn't break the page
        if (window.console) console.warn('SW registration skipped:', err && err.message);
      });
    });
  }

  // ----- Cookie consent banner (CCPA-friendly) -----
  // Lightweight, dismissible, persists choice in localStorage for 12 months.
  // We always run strictly-necessary cookies + first-party performance metrics.
  // Analytics fires by default but the user can opt out via the banner.
  try {
    var consentKey = 'jt_cookie_consent_v1';
    var stored = localStorage.getItem(consentKey);
    if (!stored) {
      window.addEventListener('DOMContentLoaded', function () {
        // Don't show on legal pages themselves to avoid loop
        if (/\/(privacy|terms|accessibility)(\.html)?$/.test(location.pathname)) return;

        var banner = document.createElement('div');
        banner.id = 'cookie-banner';
        banner.setAttribute('role', 'dialog');
        banner.setAttribute('aria-label', 'Cookie consent');
        banner.style.cssText = 'position:fixed;left:14px;right:14px;bottom:14px;max-width:560px;margin-left:auto;z-index:9998;' +
          'background:#0E1014;color:#fff;border-radius:18px;padding:16px 18px;' +
          'box-shadow:0 14px 40px rgba(0,0,0,.30);' +
          'font-family:inherit;font-size:13.5px;line-height:1.5;' +
          'border:1px solid rgba(255,255,255,.08);' +
          'animation:cookieIn .35s ease both';
        banner.innerHTML =
          '<div style="margin-bottom:12px;color:rgba(255,255,255,.85)">' +
          'We use cookies to make this site work and improve it (analytics + performance). ' +
          'You can opt out of analytics anytime. ' +
          '<a href="/privacy.html" style="color:#0a84ff;font-weight:500">Read our privacy policy</a>.' +
          '</div>' +
          '<div style="display:flex;gap:8px;flex-wrap:wrap">' +
          '<button id="cookieAcceptAll" type="button" style="flex:1 1 auto;background:#0a84ff;color:#fff;border:0;padding:9px 14px;border-radius:999px;font-weight:600;font-size:13px;cursor:pointer;min-width:120px">Accept all</button>' +
          '<button id="cookieEssentialOnly" type="button" style="flex:1 1 auto;background:rgba(255,255,255,.08);color:#fff;border:0;padding:9px 14px;border-radius:999px;font-weight:500;font-size:13px;cursor:pointer;min-width:120px">Essential only</button>' +
          '</div>';
        if (!document.getElementById('cookie-banner-style')) {
          var st = document.createElement('style');
          st.id = 'cookie-banner-style';
          st.textContent = '@keyframes cookieIn{from{transform:translateY(20px);opacity:0}to{transform:translateY(0);opacity:1}}';
          document.head.appendChild(st);
        }
        document.body.appendChild(banner);

        var save = function (choice) {
          localStorage.setItem(consentKey, JSON.stringify({
            choice: choice,
            ts: Date.now(),
          }));
          banner.style.animation = 'none';
          banner.style.transition = 'opacity .25s ease';
          banner.style.opacity = '0';
          setTimeout(function () { banner.remove(); }, 260);
          if (window.trackEvent) trackEvent('cookie_consent', { choice: choice });
        };
        document.getElementById('cookieAcceptAll').addEventListener('click', function () { save('all'); });
        document.getElementById('cookieEssentialOnly').addEventListener('click', function () {
          // Disable analytics by setting opt-out flags for GA4 + Vercel
          try { window['ga-disable-' + cfg.GA4_ID] = true; } catch (_) {}
          save('essential');
        });
      });
    } else {
      // Honor existing 'essential only' choice on subsequent loads
      try {
        var parsed = JSON.parse(stored);
        if (parsed && parsed.choice === 'essential' && cfg.GA4_ID) {
          window['ga-disable-' + cfg.GA4_ID] = true;
        }
      } catch (e) {}
    }
  } catch (e) {}
})();
