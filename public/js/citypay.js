/* City payment tool: "what does a home here cost per month?"
   <div class="cp-card" data-citypay data-city="Downey" data-median="926000"></div>
   Rate comes from /api/rates (Freddie Mac weekly average). Everything else is a
   stated estimate, listed under the result.
*/
(function () {
  var FALLBACK_RATE = 7.11;   // used only if /api/rates cannot be reached
  var TAX = 0.012;            // property tax, about 1.2% of price per year
  var INS = 0.0022;           // home insurance, about 0.22% of price per year
  var PMI = 0.005;            // mortgage insurance, about 0.5% of the loan per year under 20% down

  function money(n) { return '$' + Math.round(n).toLocaleString('en-US'); }
  function short(n) {
    return n >= 1e6 ? '$' + (n / 1e6).toFixed(2).replace(/0$/, '') + 'M' : '$' + Math.round(n / 1000) + 'K';
  }

  function build(box, live) {
    var city = box.getAttribute('data-city') || 'this city';
    var median = parseInt(box.getAttribute('data-median'), 10) || 800000;
    var rate = live && live.current ? live.current : FALLBACK_RATE;
    var lo = parseInt(box.getAttribute('data-min'), 10), hi = parseInt(box.getAttribute('data-max'), 10);
    var min = Math.round(Math.min(median * 0.55, lo || 1e12) * 0.97 / 1000) * 1000;
    var max = Math.round(Math.max(median * 1.6, hi || 0) * 1.03 / 1000) * 1000;

    box.innerHTML =
      '<div class="cp-controls">' +
        '<label class="cp-field"><span class="cp-label">Home price <b class="cp-val" data-o="price"></b></span>' +
          '<input type="range" class="cp-range" data-i="price" min="' + min + '" max="' + max + '" step="1000" value="' + median + '">' +
          '<span class="cp-hint">' + city + ' ' + (box.getAttribute('data-label') || 'median') + ' is ' + short(median) + '</span></label>' +
        '<label class="cp-field"><span class="cp-label">Down payment <b class="cp-val" data-o="down"></b></span>' +
          '<input type="range" class="cp-range" data-i="down" min="3" max="30" step="1" value="10">' +
          '<span class="cp-hint" data-o="downhint"></span></label>' +
        '<div class="cp-rate"><span class="cp-rate-num">' + rate.toFixed(2) + '%</span>' +
          '<span class="cp-rate-txt">30-year fixed, ' + (live && live.current ? 'this week\'s Freddie Mac average' : 'recent Freddie Mac average') + '</span></div>' +
      '</div>' +
      '<div class="cp-result">' +
        '<div class="cp-big"><span data-o="total"></span><small>/mo</small></div>' +
        '<div class="cp-bar" aria-hidden="true"><i data-b="pi"></i><i data-b="tax"></i><i data-b="ins"></i><i data-b="pmi"></i></div>' +
        '<ul class="cp-rows">' +
          '<li><i class="cp-k cp-k-pi"></i><span>Loan payment</span><b data-o="pi"></b></li>' +
          '<li><i class="cp-k cp-k-tax"></i><span>Property tax</span><b data-o="tax"></b></li>' +
          '<li><i class="cp-k cp-k-ins"></i><span>Home insurance</span><b data-o="ins"></b></li>' +
          '<li data-row="pmi"><i class="cp-k cp-k-pmi"></i><span>Mortgage insurance</span><b data-o="pmi"></b></li>' +
        '</ul>' +
        '<p class="cp-income" data-o="income"></p>' +
        '<a class="cp-cta" href="/zoom">Get my real number</a>' +
        '<p class="cp-fine">An estimate, not a quote. Tax about 1.2% and insurance about 0.22% of the price per year. Mortgage insurance about 0.5% of the loan per year under 20% down. No HOA or Mello-Roos.</p>' +
      '</div>';

    var o = {}, b = {};
    box.querySelectorAll('[data-o]').forEach(function (e) { o[e.getAttribute('data-o')] = e; });
    box.querySelectorAll('[data-b]').forEach(function (e) { b[e.getAttribute('data-b')] = e; });
    var iPrice = box.querySelector('[data-i="price"]'), iDown = box.querySelector('[data-i="down"]');
    var pmiRow = box.querySelector('[data-row="pmi"]');

    function fill(input) {
      var p = (input.value - input.min) / (input.max - input.min) * 100;
      input.style.setProperty('--p', p + '%');
    }
    function calc() {
      var price = +iPrice.value, pct = +iDown.value;
      var loan = price * (1 - pct / 100);
      var r = rate / 100 / 12, n = 360;
      var pi = loan * r / (1 - Math.pow(1 + r, -n));
      var tax = price * TAX / 12, ins = price * INS / 12;
      var pmi = pct < 20 ? loan * PMI / 12 : 0;
      var total = pi + tax + ins + pmi;
      o.price.textContent = money(price);
      o.down.textContent = pct + '%';
      o.downhint.textContent = money(price * pct / 100) + ' down';
      o.total.textContent = money(total);
      o.pi.textContent = money(pi); o.tax.textContent = money(tax); o.ins.textContent = money(ins); o.pmi.textContent = money(pmi);
      pmiRow.hidden = pmi === 0;
      b.pi.style.flexGrow = pi; b.tax.style.flexGrow = tax; b.ins.style.flexGrow = ins; b.pmi.style.flexGrow = pmi;
      b.pmi.style.display = pmi ? '' : 'none';
      fill(iPrice); fill(iDown);
      // plain arithmetic, no advice: the income at which this payment is 36% of gross pay
      o.income.textContent = 'This payment is 36% of a household income of about ' + money(total / 0.36 * 12 / 1000) + 'K a year.';
      box.dispatchEvent(new CustomEvent('citypay:update', { bubbles: true, detail: { total: total, price: price, down: pct, rate: rate } }));
    }
    // another block on the page can load a price into the tool (the bedroom rows do)
    box.addEventListener('citypay:set', function (e) {
      var v = Math.max(+iPrice.min, Math.min(+iPrice.max, Math.round(e.detail.price / 1000) * 1000));
      iPrice.value = v; calc();
    });
    iPrice.addEventListener('input', calc);
    iDown.addEventListener('input', calc);
    calc();
  }

  function start() {
    var boxes = document.querySelectorAll('[data-citypay]');
    if (!boxes.length) return;
    fetch('/api/rates').then(function (r) { if (!r.ok) throw 0; return r.json(); })
      .then(function (d) { return d && d.source !== 'fallback' ? d : null; })
      .catch(function () { return null; })
      .then(function (live) { boxes.forEach(function (bx) { build(bx, live); }); });
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', start);
  else start();
})();
