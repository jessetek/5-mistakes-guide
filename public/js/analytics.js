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
})();
