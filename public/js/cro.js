/* CRO utilities — A/B test framework, form auto-save, Text Jesse widget,
   live booking ticker. Loaded on conversion pages.
   ============================================================ */
(function () {
  'use strict';

  /* ---------- A/B test framework ----------
     Usage: window.JtekAB.assign('test-name', ['A','B']) returns a stable
     variant for this user (cookie persistence) and fires a GA4 event
     `ab_assign` so you can segment funnel data per variant.
  ------------------------------------------- */
  function getCookie(name) {
    var m = document.cookie.match('(^|;)\\s*' + name + '\\s*=\\s*([^;]+)');
    return m ? decodeURIComponent(m[2]) : null;
  }
  function setCookie(name, val, days) {
    var d = new Date();
    d.setTime(d.getTime() + (days || 90) * 86400000);
    document.cookie = name + '=' + encodeURIComponent(val) + ';expires=' + d.toUTCString() + ';path=/;SameSite=Lax';
  }
  window.JtekAB = {
    assign: function (testName, variants) {
      if (!Array.isArray(variants) || variants.length < 2) return null;
      var key = 'ab_' + testName.replace(/[^a-z0-9_-]/gi, '');
      var existing = getCookie(key);
      if (existing && variants.indexOf(existing) !== -1) return existing;
      var pick = variants[Math.floor(Math.random() * variants.length)];
      setCookie(key, pick, 90);
      if (window.trackEvent) {
        window.trackEvent('ab_assign', { test: testName, variant: pick });
      }
      return pick;
    },
    get: function (testName) {
      var key = 'ab_' + testName.replace(/[^a-z0-9_-]/gi, '');
      return getCookie(key);
    },
  };

  /* ---------- Form auto-save ----------
     Usage: <form data-autosave="form-name"> — fields auto-persist to
     localStorage on blur, restore on next visit within 7 days.
     Skips password, file, hidden, honeypot, and credit-card inputs.
  ------------------------------------- */
  function autoSaveForm(form) {
    var name = form.getAttribute('data-autosave');
    if (!name) return;
    var key = 'fs_' + name;
    var maxAgeMs = 7 * 86400000;
    var skipTypes = ['password', 'file', 'hidden', 'submit', 'button', 'reset'];

    function fields() {
      return Array.prototype.slice.call(form.querySelectorAll('input,textarea,select'))
        .filter(function (el) {
          if (skipTypes.indexOf(el.type) !== -1) return false;
          if (el.getAttribute('autocomplete') === 'cc-number') return false;
          if (el.getAttribute('autocomplete') === 'cc-csc') return false;
          if (/website|honeypot/i.test(el.name)) return false; // honeypots
          return el.name && !el.disabled;
        });
    }

    // Restore
    try {
      var saved = JSON.parse(localStorage.getItem(key) || 'null');
      if (saved && saved.ts && Date.now() - saved.ts < maxAgeMs && saved.values) {
        fields().forEach(function (el) {
          if (saved.values[el.name] != null && !el.value) {
            if (el.type === 'checkbox' || el.type === 'radio') {
              if (el.value === saved.values[el.name]) el.checked = true;
            } else {
              el.value = saved.values[el.name];
            }
          }
        });
        // Show a soft notice
        if (saved.shownToast !== true && saved.values.address || saved.values.email) {
          var toast = document.createElement('div');
          toast.style.cssText = 'position:fixed;top:80px;right:14px;z-index:9994;' +
            'background:rgba(14,16,20,.96);color:#fff;padding:10px 14px;border-radius:12px;' +
            'font-size:13px;line-height:1.4;max-width:280px;box-shadow:0 8px 28px rgba(0,0,0,.3);' +
            'animation:fsToastIn .3s ease both';
          toast.innerHTML = 'Welcome back — picking up where you left off. <button style="background:none;border:0;color:#0a84ff;cursor:pointer;font-size:13px;font-weight:500;padding:0 0 0 6px">Clear</button>';
          var st = document.createElement('style');
          st.textContent = '@keyframes fsToastIn{from{opacity:0;transform:translateY(-10px)}to{opacity:1;transform:translateY(0)}}';
          document.head.appendChild(st);
          document.body.appendChild(toast);
          toast.querySelector('button').addEventListener('click', function () {
            localStorage.removeItem(key);
            fields().forEach(function (el) { if (el.type !== 'checkbox' && el.type !== 'radio') el.value = ''; });
            toast.remove();
          });
          setTimeout(function () { toast.remove(); }, 8000);
        }
      }
    } catch (e) {}

    // Save on input
    var save = function () {
      try {
        var values = {};
        fields().forEach(function (el) {
          if (el.type === 'checkbox' || el.type === 'radio') {
            if (el.checked) values[el.name] = el.value;
          } else if (el.value) {
            values[el.name] = el.value;
          }
        });
        localStorage.setItem(key, JSON.stringify({ ts: Date.now(), values: values }));
      } catch (e) {}
    };
    form.addEventListener('input', debounce(save, 400), { passive: true });

    // Clear on successful submit
    form.addEventListener('submit', function () {
      setTimeout(function () { localStorage.removeItem(key); }, 1500);
    });
  }
  function debounce(fn, ms) {
    var t;
    return function () {
      var ctx = this, args = arguments;
      clearTimeout(t);
      t = setTimeout(function () { fn.apply(ctx, args); }, ms);
    };
  }

  function initAutoSave() {
    document.querySelectorAll('form[data-autosave]').forEach(autoSaveForm);
  }

  /* ---------- Sticky mobile CTA — auto-attach per page ----------
     If a page doesn't already have a hand-rolled .sticky-mobile-cta
     (some pages have customized ones), inject a sensible default.
     The CTA target is chosen by URL pattern so each page funnels to
     its highest-intent next action.
  ----------------------------------------------------------------- */
  function initStickyMobileCta() {
    if (document.querySelector('.sticky-mobile-cta')) return; // hand-rolled exists
    if (/\/(privacy|terms|accessibility|404|offline)(\.html)?$/.test(location.pathname)) return;

    var path = location.pathname;
    // Decide CTA per page intent
    var ctaTitle, ctaSub, ctaText, ctaHref;
    if (/\/valuation/.test(path)) {
      ctaTitle = 'Home value report';
      ctaSub = 'Real comps · 24h delivery.';
      ctaText = 'Get it →';
      ctaHref = '#vfForm';
    } else if (/\/guide/.test(path)) {
      ctaTitle = '5-Mistakes guide';
      ctaSub = 'Sent in under 60 seconds.';
      ctaText = 'Send it →';
      ctaHref = '#guideForm';
    } else if (/\/buyer-quiz/.test(path)) {
      ctaTitle = '60-sec readiness quiz';
      ctaSub = 'No email required.';
      ctaText = 'Start →';
      ctaHref = '#qzShell';
    } else if (/\/seller-net/.test(path)) {
      ctaTitle = 'Net proceeds calculator';
      ctaSub = 'Live · No email needed.';
      ctaText = 'Try it →';
      ctaHref = '#nx-tool';
    } else if (/\/rates/.test(path)) {
      // /rates already has form-first layout — skip sticky to avoid CTA conflict
      return;
    } else if (/\/zoom/.test(path)) {
      ctaTitle = 'Prefer to text or call?';
      ctaSub = '(562) 609-4200';
      ctaText = 'Call →';
      ctaHref = 'tel:5626094200';
    } else if (/\/seller|\/sellers/.test(path)) {
      ctaTitle = "What's your home worth?";
      ctaSub = 'CMA · 24h.';
      ctaText = 'Find out →';
      ctaHref = '/valuation';
    } else if (/\/buyer|\/checklist|\/calculator|\/rent-vs-buy|\/listings/.test(path)) {
      ctaTitle = '15-min strategy call';
      ctaSub = 'No pressure. No pitch.';
      ctaText = 'Book →';
      ctaHref = '/zoom';
    } else {
      // Default — homepage, about, neighborhoods, insights, etc.
      ctaTitle = '15-min strategy call';
      ctaSub = 'No pressure. No pitch.';
      ctaText = 'Book →';
      ctaHref = '/zoom';
    }

    var sc = document.createElement('div');
    sc.className = 'sticky-mobile-cta';
    sc.id = 'stickyMobileCta';
    sc.setAttribute('aria-label', 'Quick contact');
    sc.innerHTML =
      '<div class="sticky-mobile-cta-row">' +
        '<div class="sticky-mobile-cta-text">' +
          '<strong>' + ctaTitle + '</strong>' +
          '<span>' + ctaSub + '</span>' +
        '</div>' +
        '<a href="' + ctaHref + '" class="sticky-mobile-cta-btn">' + ctaText + '</a>' +
      '</div>';
    document.body.appendChild(sc);
    document.body.classList.add('has-sticky-cta');

    var lastY = 0, ticking = false;
    window.addEventListener('scroll', function () {
      if (ticking) return;
      window.requestAnimationFrame(function () {
        var y = window.scrollY || window.pageYOffset;
        if (y > 200 && y > lastY) sc.classList.add('sticky-cta-hidden');
        else if (y < lastY || y <= 200) sc.classList.remove('sticky-cta-hidden');
        lastY = y; ticking = false;
      });
      ticking = true;
    }, { passive: true });

    sc.querySelector('.sticky-mobile-cta-btn').addEventListener('click', function () {
      if (window.trackEvent) window.trackEvent('sticky_cta_click', { page: path, target: ctaHref });
    });
  }

  /* ---------- Live booking ticker (rotating recent activity) ----------
     Each item gets a stable "minutes ago" assigned at boot — rotation
     just changes which item is visible, not the timestamp. Times spread
     across 8min - 4h range so it reads as believable recent activity,
     not a refresh-every-6s loop. Smooth fade transition between items.
  --------------------------------------------------------------------- */
  
  /* ---------- UTM tracking — persist source/medium/campaign across the funnel ----------
     Captures incoming UTM parameters into a 30-day cookie so attribution
     survives the form-fill journey. When a form submits, the latest values
     are auto-injected as hidden fields if not already present. Also fires
     a GA4 `utm_capture` event on first hit so you can build acquisition
     audiences without waiting for the conversion event.
  ---------------------------------------------------------------------------------- */
  function initUtmCapture() {
    var params = new URLSearchParams(location.search);
    var keys = ['utm_source', 'utm_medium', 'utm_campaign', 'utm_term', 'utm_content', 'gclid', 'fbclid'];
    var captured = {};
    var hasNew = false;
    keys.forEach(function (k) {
      var v = params.get(k);
      if (v) {
        captured[k] = v;
        hasNew = true;
      }
    });
    if (hasNew) {
      try {
        var existing = JSON.parse(getCookie('utm') || '{}');
        // Merge — new values overwrite, but unset keys persist
        var merged = Object.assign(existing, captured, { ts: Date.now(), landing: location.pathname });
        setCookie('utm', JSON.stringify(merged), 30);
        if (window.trackEvent) window.trackEvent('utm_capture', captured);
      } catch (e) {}
    }
    // Auto-inject UTM as hidden fields on form submit (so they POST with form data)
    var stored;
    try { stored = JSON.parse(getCookie('utm') || 'null'); } catch (e) {}
    if (!stored) return;
    document.querySelectorAll('form').forEach(function (form) {
      // Skip iframe-embedded forms — they won't see our DOM injection
      if (form.querySelector('iframe')) return;
      keys.forEach(function (k) {
        if (!stored[k]) return;
        if (form.querySelector('input[name="' + k + '"]')) return; // already has it
        var input = document.createElement('input');
        input.type = 'hidden';
        input.name = k;
        input.value = stored[k];
        form.appendChild(input);
      });
      // Also include the landing page
      if (stored.landing && !form.querySelector('input[name="utm_landing"]')) {
        var inp = document.createElement('input');
        inp.type = 'hidden';
        inp.name = 'utm_landing';
        inp.value = stored.landing;
        form.appendChild(inp);
      }
    });
  }

  // Boot
  function boot() {
    initUtmCapture();
    initAutoSave();
      }
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', boot);
  } else {
    boot();
  }
})();
