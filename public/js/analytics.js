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

  // ----- PWA install nudge (mobile only, dismissible, /rates only) -----
  // Catches the beforeinstallprompt event and surfaces a small bottom-sheet
  // CTA on mobile. Only on /rates so we don't get in the way of the rest of
  // the site. Dismissed state persists in localStorage for 30 days.
  try {
    var path = location.pathname.replace(/\/$/, '');
    var allow = /\/rates(\.html)?$/.test(path);
    var dismissed = +(localStorage.getItem('pwa_nudge_dismissed') || 0);
    var alreadyInstalled = window.matchMedia('(display-mode: standalone)').matches || window.navigator.standalone === true;
    var isMobile = window.matchMedia('(max-width: 760px)').matches;
    var isFresh = (Date.now() - dismissed) > (30 * 24 * 60 * 60 * 1000);

    if (allow && isMobile && !alreadyInstalled && isFresh) {
      var deferred = null;
      window.addEventListener('beforeinstallprompt', function (e) {
        e.preventDefault();
        deferred = e;
        // Wait until user has been on page for 25s before nudging
        setTimeout(showNudge, 25000);
      });
      // iOS Safari fires no beforeinstallprompt — show static nudge anyway after 25s
      var isIOS = /iPhone|iPad|iPod/.test(navigator.userAgent) && !window.MSStream;
      if (isIOS) setTimeout(showNudge, 25000);

      function showNudge() {
        if (document.getElementById('pwa-nudge')) return;
        var nudge = document.createElement('div');
        nudge.id = 'pwa-nudge';
        nudge.setAttribute('role', 'dialog');
        nudge.setAttribute('aria-label', 'Install Jesse Oñate Real Estate app');
        nudge.style.cssText = 'position:fixed;left:12px;right:12px;bottom:14px;z-index:9999;background:#0E1014;color:#fff;border-radius:18px;padding:14px 16px;box-shadow:0 14px 40px rgba(0,0,0,.30);display:flex;align-items:center;gap:12px;font-family:inherit;font-size:14px;line-height:1.4;animation:pwaUp .35s ease both';
        var msg = isIOS
          ? '<strong>Save Rate Alerts to your phone</strong><br><span style="color:rgba(255,255,255,.7);font-size:12.5px">Tap Share → Add to Home Screen</span>'
          : '<strong>Save Rate Alerts to your phone</strong><br><span style="color:rgba(255,255,255,.7);font-size:12.5px">Tap Install for one-tap weekly access</span>';
        nudge.innerHTML =
          '<div style="flex:1;min-width:0">' + msg + '</div>' +
          (isIOS
            ? ''
            : '<button id="pwa-install" style="background:#0071E3;color:#fff;border:0;padding:9px 14px;border-radius:999px;font-weight:600;font-size:13px;cursor:pointer">Install</button>'
          ) +
          '<button id="pwa-dismiss" aria-label="Dismiss" style="background:transparent;color:rgba(255,255,255,.55);border:0;font-size:20px;cursor:pointer;padding:4px 6px">×</button>';
        document.body.appendChild(nudge);

        if (!document.getElementById('pwa-nudge-style')) {
          var st = document.createElement('style');
          st.id = 'pwa-nudge-style';
          st.textContent = '@keyframes pwaUp{from{transform:translateY(40px);opacity:0}to{transform:translateY(0);opacity:1}}';
          document.head.appendChild(st);
        }

        var dismiss = function () {
          localStorage.setItem('pwa_nudge_dismissed', String(Date.now()));
          nudge.remove();
        };
        document.getElementById('pwa-dismiss').addEventListener('click', dismiss);
        var install = document.getElementById('pwa-install');
        if (install) {
          install.addEventListener('click', function () {
            if (!deferred) { dismiss(); return; }
            deferred.prompt();
            deferred.userChoice.then(function (choice) {
              if (window.trackEvent) trackEvent('pwa_install_choice', { outcome: choice.outcome });
              dismiss();
            });
          });
        }
        if (window.trackEvent) trackEvent('pwa_nudge_shown', { ios: isIOS });
      }
    }
  } catch (e) {}
})();
