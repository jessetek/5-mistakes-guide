/* Header: hides on scroll down, slides back on scroll up.
   Always shown at the top of the page, while the mobile menu or a dropdown is open, and when it has keyboard focus.
   The nav is position:fixed, so hiding it moves nothing else on the page. Uses the CSS `translate` property so it
   stacks with each page's own nav transform, and keeps each page's own transitions. */
(function () {
  'use strict';
  var nav = document.getElementById('nav');
  if (!nav || !window.requestAnimationFrame) return;
  var THRESHOLD = 8, TOP = 8;
  var reduce = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)');
  var st = document.createElement('style');
  st.textContent = '.nav.nav-autohide{translate:0 calc(-100% - 40px);pointer-events:none}' +
    '@media (prefers-reduced-motion: reduce){.nav.nav-autohide{translate:none;opacity:0;visibility:hidden}}';   // no sliding: it just goes away and comes back
  document.head.appendChild(st);
  function setTransition() {
    var base = (getComputedStyle(nav).transition || '').replace(/,?\s*translate [^,]*/g, '');
    if (!base || /^all 0s/.test(base)) base = '';
    nav.style.transition = (reduce && reduce.matches) ? base : (base ? base + ', ' : '') + 'translate .32s cubic-bezier(.2,.8,.2,1)';
  }
  setTransition();
  if (reduce && reduce.addEventListener) reduce.addEventListener('change', setTransition);
  function menuOpen() {
    var m = document.getElementById('mobNav');
    return (m && m.classList.contains('open')) || !!nav.querySelector('.nav-dropdown.open') || nav.contains(document.activeElement) && document.activeElement !== document.body;
  }
  var last = window.pageYOffset || 0, ticking = false;
  var root = document.documentElement;
  function show() { nav.classList.remove('nav-autohide'); root.classList.remove('nav-hidden'); }
  function hide() { nav.classList.add('nav-autohide'); root.classList.add('nav-hidden'); }
  function update() {
    ticking = false;
    var y = Math.max(window.pageYOffset || document.documentElement.scrollTop || 0, 0);
    if (y <= TOP || menuOpen()) { show(); last = y; return; }
    var d = y - last;
    if (Math.abs(d) < THRESHOLD) return;          // ignore jitter, keep measuring from the last real move
    if (d > 0 && y > nav.offsetHeight + 24) hide();
    else if (d < 0) show();
    last = y;
  }
  window.addEventListener('scroll', function () {
    if (!ticking) { ticking = true; window.requestAnimationFrame(update); }
  }, { passive: true });
  nav.addEventListener('focusin', show);
  var m = document.getElementById('mobNav');
  if (m && window.MutationObserver) new MutationObserver(function () { if (m.classList.contains('open')) show(); }).observe(m, { attributes: true, attributeFilter: ['class'] });
})();
