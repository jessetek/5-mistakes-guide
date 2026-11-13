/* Real Google reviews, pulled from the Jessetek account.
   Tries /api/reviews (live), falls back to /data/reviews.json (snapshot).

   Markup hooks:
     [data-reviews="mini"]   small looping cards (home bento). Needs .gr-scroll inside.
     [data-reviews="wall"]   full cards in a grid. Optional data-limit="6".
     [data-reviews-rating]   text becomes "5.0"
     [data-reviews-total]    text becomes "20"
*/
(function () {
  var GBP = 'https://www.google.com/maps?cid=9817183126910437877';
  var MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];

  function esc(s) {
    return String(s).replace(/[&<>"']/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c];
    });
  }
  function when(d) {
    var p = String(d || '').split('-');
    if (p.length < 2) return '';
    return MONTHS[parseInt(p[1], 10) - 1] + ' ' + p[0];
  }
  function stars(n) { return new Array((n || 5) + 1).join('★'); }
  // Site rule: no long dashes in anything a visitor reads, reviews included.
  function tidy(t) { return String(t).replace(/\s*[\u2014\u2013]\s*/g, ', '); }

  // Shorten at a sentence end when possible, so a card never cuts mid-thought.
  function clip(text, max) {
    var t = String(text).replace(/\s+/g, ' ').trim();
    if (t.length <= max) return t;
    var cut = t.slice(0, max);
    var end = Math.max(cut.lastIndexOf('. '), cut.lastIndexOf('! '), cut.lastIndexOf('? '));
    if (end > max * 0.45) return cut.slice(0, end + 1);
    return cut.slice(0, cut.lastIndexOf(' ')) + '…';
  }

  function miniCard(r) {
    return '<div class="gr-mini">' +
      '<div class="gr-mini-stars">' + stars(r.stars) + '</div>' +
      '<div class="gr-mini-quote">"' + esc(clip(r.text, 150)) + '"</div>' +
      '<div class="gr-mini-name">' + esc(r.name) + ' <span class="gr-mini-date">· ' + when(r.date) + '</span></div>' +
      '</div>';
  }
  function wallCard(r) {
    var long = r.text.length > 300;
    return '<article class="rv-card">' +
      '<div class="rv-stars" aria-label="' + r.stars + ' out of 5 stars">' + stars(r.stars) + '</div>' +
      '<p class="rv-text"' + (long ? ' data-full="' + esc(r.text) + '"' : '') + '>' + esc(long ? clip(r.text, 300) : r.text) + '</p>' +
      (long ? '<button type="button" class="rv-more">Read more</button>' : '') +
      '<div class="rv-foot"><span class="rv-name">' + esc(r.name) + '</span><span class="rv-date">' + when(r.date) + ' · Google</span></div>' +
      '</article>';
  }

  function render(data) {
    var list = (data.reviews || []).filter(function (r) { return r.text; })
      .map(function (r) { r.text = tidy(r.text); return r; });
    if (!list.length) return;

    document.querySelectorAll('[data-reviews-rating]').forEach(function (el) {
      el.textContent = Number(data.rating).toFixed(1);
    });
    document.querySelectorAll('[data-reviews-total]').forEach(function (el) {
      el.textContent = data.total;
    });

    document.querySelectorAll('[data-reviews="mini"]').forEach(function (box) {
      var scroll = box.querySelector('.gr-scroll');
      if (!scroll) return;
      var pick = list.slice(0, 8).map(miniCard).join('');
      scroll.innerHTML = pick + pick; // two sets for the seamless loop
      scroll.style.animationDuration = '72s';
    });

    document.querySelectorAll('[data-reviews="wall"]').forEach(function (box) {
      var limit = parseInt(box.getAttribute('data-limit'), 10) || list.length;
      box.innerHTML = list.slice(0, limit).map(wallCard).join('');
      if (!box.nextElementSibling || !box.nextElementSibling.classList.contains('rv-all')) {
        var a = document.createElement('a');
        a.className = 'rv-all'; a.href = GBP; a.target = '_blank'; a.rel = 'noopener';
        a.textContent = 'Read all ' + data.total + ' reviews on Google';
        box.parentNode.insertBefore(a, box.nextSibling);
      }
    });
  }

  document.addEventListener('click', function (e) {
    var b = e.target.closest && e.target.closest('.rv-more');
    if (!b) return;
    var p = b.previousElementSibling;
    if (p && p.getAttribute('data-full')) { p.textContent = p.getAttribute('data-full'); b.remove(); }
  });

  function get(url) {
    return fetch(url).then(function (r) {
      if (!r.ok) throw new Error(r.status);
      return r.json();
    });
  }
  function start() {
    if (!document.querySelector('[data-reviews]')) return;
    get('/api/reviews')
      .then(function (d) { if (!d.reviews || !d.reviews.length) throw new Error('empty'); return d; })
      .catch(function () { return get('/data/reviews.json'); })
      .then(render)
      .catch(function () { /* leave the page as is */ });
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', start);
  else start();
})();
