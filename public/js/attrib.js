/* _attrib.js: remembers where a visitor came from (an ad, a search, social, a UTM link, a
   referral, or direct) and the page they landed on, so the site forms can save it on the
   contact (Web Source, Web Campaign, Landing Page, Form Page, First Visit).
   This visit: sessionStorage. First visit across visits: localStorage, only with consent
   (jtek.app: the cookie banner said yes; jessetek.net: not opted out to essential only).
   Forms read it with window.siteAttribution(). Same file on jtek.app and jessetek.net. */
(function () {
  'use strict';
  var S = 'jt_attr_visit', F = 'jt_attr_first';
  function get(store, k) { try { return JSON.parse(store.getItem(k) || 'null'); } catch (e) { return null; } }
  function put(store, k, v) { try { store.setItem(k, JSON.stringify(v)); } catch (e) {} }
  function host(u) { try { return new URL(u).hostname.replace(/^www\./, ''); } catch (e) { return ''; } }
  function consent() {
    try {
      if (/jessetek/.test(location.hostname)) {
        var c = JSON.parse(localStorage.getItem('jt_cookie_consent_v1') || 'null');
        return !(c && c.choice === 'essential');
      }
      return localStorage.getItem('jtek_consent') === 'granted';
    } catch (e) { return false; }
  }

  var q = new URLSearchParams(location.search), self = location.hostname.replace(/^www\./, ''), ref = host(document.referrer);
  var p = function (k) { return (q.get(k) || '').slice(0, 120); };
  var touch = {
    src: p('utm_source'), med: p('utm_medium'), cmp: p('utm_campaign'), cnt: p('utm_content'), term: p('utm_term'),
    gclid: !!q.get('gclid'), fbclid: !!q.get('fbclid'), msclkid: !!q.get('msclkid'),
    ref: ref && ref !== self ? ref : '',
    land: (location.pathname + (function () { var k = new URLSearchParams(location.search); ['gclid', 'fbclid', 'msclkid', 'gbraid', 'wbraid', '_gl'].forEach(function (x) { k.delete(x); }); var t = k.toString(); return t ? '?' + t : ''; })()).slice(0, 300),
    at: new Date().toISOString()
  };
  var signal = touch.src || touch.gclid || touch.fbclid || touch.msclkid || touch.ref;

  // This visit: its first page, replaced only when the visitor comes in again from an ad,
  // a UTM link or another site (moving between our own pages changes nothing).
  var visit = get(sessionStorage, S);
  if (!visit || signal) { visit = touch; put(sessionStorage, S, visit); }
  if (consent() && !get(localStorage, F)) put(localStorage, F, visit);

  window.siteAttribution = function () {
    var first = consent() ? get(localStorage, F) : null;
    return { first: first || visit, last: visit, page: location.pathname.slice(0, 200) };
  };
})();
