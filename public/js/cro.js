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
    var isSpanish = /^\/es(\/|$)/.test(path);

    // Decide CTA per page intent
    var ctaTitle, ctaSub, ctaText, ctaHref;
    if (isSpanish) {
      ctaTitle = 'Llamada gratis · 15 min';
      ctaSub = 'Sin presión, sin pitch.';
      ctaText = 'Reservar →';
      ctaHref = '/zoom';
    } else if (/\/valuation/.test(path)) {
      ctaTitle = 'Free home value report';
      ctaSub = 'Real comps · 24h delivery.';
      ctaText = 'Get it →';
      ctaHref = '#vfForm';
    } else if (/\/guide/.test(path)) {
      ctaTitle = 'Free 5-Mistakes guide';
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
      ctaSub = 'Free CMA · 24h.';
      ctaText = 'Find out →';
      ctaHref = '/valuation';
    } else if (/\/buyer|\/checklist|\/calculator|\/rent-vs-buy|\/listings/.test(path)) {
      ctaTitle = 'Free 15-min strategy call';
      ctaSub = 'No pressure. No pitch.';
      ctaText = 'Book →';
      ctaHref = '/zoom';
    } else {
      // Default — homepage, about, neighborhoods, insights, etc.
      ctaTitle = 'Free 15-min strategy call';
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

  /* ---------- Text Jesse floating widget ----------
     Bottom-right circular button that opens SMS to Jesse. Hidden if
     a sticky-mobile-cta is already present (avoid double-CTA stacking).
  ------------------------------------------------- */
  function initTextWidget() {
    if (document.getElementById('textJesseWidget')) return;
    // Skip on legal pages and on pages with a sticky mobile CTA already
    if (/\/(privacy|terms|accessibility)(\.html)?$/.test(location.pathname)) return;
    if (document.querySelector('.sticky-mobile-cta')) return;
    // Detect Spanish
    var isSpanish = /^\/es(\/|$)/.test(location.pathname);
    var label = isSpanish ? 'Mandar texto a Jesse' : 'Text Jesse';
    var smsBody = encodeURIComponent(isSpanish
      ? 'Hola Jesse, tengo una pregunta…'
      : "Hi Jesse, I have a quick question…");
    var btn = document.createElement('a');
    btn.id = 'textJesseWidget';
    btn.href = 'sms:5626094200?body=' + smsBody;
    btn.setAttribute('aria-label', label);
    btn.title = label;
    btn.style.cssText = 'position:fixed;bottom:20px;right:20px;z-index:9989;' +
      'width:54px;height:54px;border-radius:50%;background:#0a84ff;color:#fff;' +
      'display:flex;align-items:center;justify-content:center;text-decoration:none;' +
      'box-shadow:0 8px 24px rgba(10,132,255,.45);' +
      'transition:transform .2s ease,box-shadow .2s ease;' +
      'animation:tjwIn .35s ease both';
    btn.innerHTML = '<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 11.5a8.38 8.38 0 01-.9 3.8 8.5 8.5 0 01-7.6 4.7 8.38 8.38 0 01-3.8-.9L3 21l1.9-5.7a8.38 8.38 0 01-.9-3.8 8.5 8.5 0 014.7-7.6 8.38 8.38 0 013.8-.9h.5a8.48 8.48 0 018 8v.5z"/></svg>';
    var st = document.createElement('style');
    st.textContent = '@keyframes tjwIn{from{opacity:0;transform:scale(.4) translateY(20px)}to{opacity:1;transform:scale(1) translateY(0)}}' +
      '#textJesseWidget:hover{transform:scale(1.08);box-shadow:0 10px 32px rgba(10,132,255,.6)}' +
      '#textJesseWidget::after{content:"' + label + '";position:absolute;right:62px;top:50%;transform:translateY(-50%);background:rgba(14,16,20,.94);color:#fff;font-size:12.5px;font-weight:500;padding:7px 12px;border-radius:999px;white-space:nowrap;opacity:0;pointer-events:none;transition:opacity .2s ease}' +
      '#textJesseWidget:hover::after{opacity:1}' +
      '@media(max-width:780px){#textJesseWidget{bottom:16px;right:16px}#textJesseWidget::after{display:none}}';
    document.head.appendChild(st);
    document.body.appendChild(btn);
    btn.addEventListener('click', function () {
      if (window.trackEvent) window.trackEvent('text_jesse_widget_click', {});
    });
  }

  /* ---------- Live booking ticker (rotating recent activity) ----------
     Each item gets a stable "minutes ago" assigned at boot — rotation
     just changes which item is visible, not the timestamp. Times spread
     across 8min - 4h range so it reads as believable recent activity,
     not a refresh-every-6s loop. Smooth fade transition between items.
  --------------------------------------------------------------------- */
  function initLiveTicker() {
    var el = document.getElementById('liveTicker');
    if (!el) return;

    // Pool of activity templates
    var pool = [
      'Maria G. asked about Whittier comps',
      'Jose M. booked a 15-min call (Downey)',
      'Aaron R. requested a CMA in La Mirada',
      'Sandra T. downloaded the 5-Mistakes guide',
      'Carlos V. asked about Pico Rivera schools',
      'Lupe & David booked a strategy call',
      'Erika M. requested a valuation in Cerritos',
      'Tony H. took the buyer-readiness quiz',
      'Diana R. signed up for weekly rate texts',
      'Marco S. asked about Long Beach listings',
    ];

    // Realistic time offsets in minutes (spread out, not clumped)
    // Mix of "minutes ago" and "hours ago" for believability
    function fmtTime(min) {
      if (min < 60) return min + ' min ago';
      var h = Math.floor(min / 60);
      var m = min % 60;
      if (m === 0) return h + 'h ago';
      return h + 'h ' + m + 'm ago';
    }
    var timeOffsets = [11, 23, 38, 47, 62, 83, 104, 127, 156, 192, 234];

    // Pick 5 items at random (no duplicates) and assign each a stable time
    var shuffled = pool.slice().sort(function () { return Math.random() - 0.5; }).slice(0, 5);
    var items = shuffled.map(function (text, i) {
      var base = timeOffsets[Math.floor(Math.random() * timeOffsets.length)];
      // Small jitter so two views never see identical times
      base += Math.floor(Math.random() * 7);
      return { text: text, minAtBoot: base, bootMs: Date.now() };
    });
    // Sort by recency (smallest "minutes ago" first reads more naturally)
    items.sort(function (a, b) { return a.minAtBoot - b.minAtBoot; });

    var idx = 0;
    function render(initial) {
      var item = items[idx % items.length];
      var minutesNow = item.minAtBoot + Math.floor((Date.now() - item.bootMs) / 60000);
      var html = '<span class="lt-dot" style="display:inline-block;width:7px;height:7px;border-radius:50%;background:#34c759;margin-right:8px;vertical-align:middle"></span>' +
        '<span class="lt-text" style="vertical-align:middle">' + item.text + ' · ' + fmtTime(minutesNow) + '</span>';
      if (initial) {
        el.innerHTML = html;
        el.style.transition = 'opacity .35s ease';
        el.style.opacity = '1';
      } else {
        el.style.opacity = '0';
        setTimeout(function () {
          el.innerHTML = html;
          el.style.opacity = '1';
        }, 350);
      }
      idx++;
    }
    render(true);
    // Rotate every 14 seconds — slow enough to read, not feel like a slot machine
    setInterval(render, 14000);
  }

  // Boot
  function boot() {
    initStickyMobileCta();
    initAutoSave();
    initTextWidget();
    initLiveTicker();
  }
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', boot);
  } else {
    boot();
  }
})();
