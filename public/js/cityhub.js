/* City guide data blocks: the price chart you can read month by month, bedroom rows that load a price
   into the payment tool, and the rent comparison that follows the tool's settings. Markup comes from
   servicemap/hub.py. */
(function () {
  var MONTHS = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December'];
  function money(n) { return '$' + Math.round(n).toLocaleString('en-US'); }

  // ---- price chart: move across it to read any month ----
  document.querySelectorAll('[data-hub-chart]').forEach(function (box) {
    var d; try { d = JSON.parse(box.getAttribute('data-hub-chart')); } catch (e) { return; }
    var v = d.v, y0 = +d.start.slice(0, 4), m0 = +d.start.slice(5, 7) - 1;
    var plot = box.querySelector('.hub-plot'), cur = box.querySelector('[data-hc="cursor"]'), dot = cur.querySelector('i');
    var val = box.querySelector('[data-hc="val"]'), date = box.querySelector('[data-hc="date"]');
    var lo = Math.min.apply(null, v), hi = Math.max.apply(null, v), span = (hi - lo) || 1; lo -= span * 0.08; hi += span * 0.08;
    var last = v.length - 1, restVal = val.textContent, restDate = date.textContent;
    function show(i) {
      i = Math.max(0, Math.min(last, i));
      var m = m0 + i, x = i / last * 100, y = (1 - (v[i] - lo) / (hi - lo)) * 100;
      cur.hidden = false; cur.style.left = x + '%'; dot.style.top = y + '%';
      val.textContent = money(v[i]); date.textContent = MONTHS[m % 12] + ' ' + (y0 + Math.floor(m / 12));
    }
    function at(e) {
      var r = plot.getBoundingClientRect(), cx = (e.touches ? e.touches[0].clientX : e.clientX);
      show(Math.round((cx - r.left) / r.width * last));
    }
    function rest() { cur.hidden = true; val.textContent = restVal; date.textContent = restDate; }
    plot.addEventListener('mousemove', at);
    plot.addEventListener('mouseleave', rest);
    plot.addEventListener('touchstart', at, { passive: true });
    plot.addEventListener('touchmove', at, { passive: true });
    plot.addEventListener('touchend', rest);
    // keyboard: arrow keys step month by month
    plot.tabIndex = 0; var k = last;
    plot.addEventListener('keydown', function (e) {
      if (e.key === 'ArrowLeft') k--; else if (e.key === 'ArrowRight') k++; else return;
      e.preventDefault(); k = Math.max(0, Math.min(last, k)); show(k);
    });
    plot.addEventListener('blur', rest);
  });

  // ---- bedroom rows: tap one to load that price into the payment tool ----
  var tool = document.querySelector('[data-citypay]');
  document.querySelectorAll('[data-hub-price]').forEach(function (b) {
    if (!tool) { b.disabled = true; return; }
    b.addEventListener('click', function () {
      document.querySelectorAll('.hub-bed.on').forEach(function (x) { x.classList.remove('on'); });
      b.classList.add('on');
      tool.dispatchEvent(new CustomEvent('citypay:set', { detail: { price: +b.getAttribute('data-hub-price') } }));
      var sec = tool.closest('section') || tool;
      var r = sec.getBoundingClientRect();
      if (r.top < 60 || r.top > innerHeight * 0.6) window.scrollTo({ top: r.top + scrollY - 90, behavior: 'smooth' });
    });
  });

  // ---- rent vs own: follows whatever the payment tool is set to ----
  var rent = document.querySelector('[data-hub-rent]');
  if (rent) {
    var r0 = +rent.getAttribute('data-hub-rent'), own = rent.querySelector('[data-hr="own"]'), line = rent.querySelector('[data-hr="line"]');
    document.addEventListener('citypay:update', function (e) {
      var t = e.detail.total, diff = t - r0;
      own.innerHTML = money(t) + '<small>/mo</small>';
      line.textContent = (diff >= 0
        ? 'That is ' + money(diff) + ' more a month than the typical rent'
        : 'That is ' + money(-diff) + ' less a month than the typical rent') +
        ', for a ' + money(e.detail.price) + ' home with ' + e.detail.down + '% down at ' + e.detail.rate.toFixed(2) + '%. Owning also builds equity; renting does not.';
    });
  }
  // ---- fact tiles count up the first time they come into view ----
  var calm = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  if (!calm && 'IntersectionObserver' in window) {
    var io = new IntersectionObserver(function (es) {
      es.forEach(function (en) {
        if (!en.isIntersecting) return;
        var el = en.target; io.unobserve(el);
        var m = /^(\$?)([\d,]*\.?\d+)([KM%]?)$/.exec(el.textContent.trim()); if (!m) return;
        var end = parseFloat(m[2].replace(/,/g, '')), dec = (m[2].split('.')[1] || '').length, t0 = null, final = el.textContent;
        if (!(end > 0)) return;
        function step(ts) {
          if (!t0) t0 = ts;
          var p = Math.min(1, (ts - t0) / 900), v = end * (1 - Math.pow(1 - p, 3));
          el.textContent = p === 1 ? final : m[1] + v.toLocaleString('en-US', { minimumFractionDigits: dec, maximumFractionDigits: dec }) + m[3];
          if (p < 1) requestAnimationFrame(step);
        }
        requestAnimationFrame(step);
      });
    }, { threshold: 0.6 });
    document.querySelectorAll('[data-count]').forEach(function (el) { io.observe(el); });
  }

  // ---- jump bar: mark the section you are reading; a thin bar shows how far down the page you are ----
  var jump = document.querySelector('.hub-jump');
  if (jump) {
    var links = [].slice.call(jump.querySelectorAll('a')), secs = links.map(function (a) { return document.getElementById(a.getAttribute('href').slice(1)); });
    var bar = document.createElement('div'); bar.className = 'hub-progress'; bar.setAttribute('aria-hidden', 'true'); document.body.appendChild(bar);
    var cur = -1, tick = false;
    function spy() {
      tick = false;
      var d = document.documentElement, max = d.scrollHeight - window.innerHeight;
      bar.style.transform = 'scaleX(' + (max > 0 ? Math.min(1, window.scrollY / max) : 0) + ')';
      var now = -1, line = window.innerHeight * 0.35, lastBottom = 0;
      var best = -1e9;
      secs.forEach(function (s, i) { if (!s) return; var r = s.getBoundingClientRect(); if (r.top <= line && r.top > best) { best = r.top; now = i; } lastBottom = Math.max(lastBottom, r.bottom); });
      jump.classList.toggle('gone', lastBottom < 140);
      if (now === cur) return; cur = now;
      links.forEach(function (a, i) { a.classList.toggle('on', i === now); });
      if (now >= 0) { var a = links[now], box = a.parentNode; box.scrollTo({ left: a.offsetLeft - (box.clientWidth - a.offsetWidth) / 2, behavior: calm ? 'auto' : 'smooth' }); }
    }
    window.addEventListener('scroll', function () { if (!tick) { tick = true; requestAnimationFrame(spy); } }, { passive: true });
    spy();
  }
})();
