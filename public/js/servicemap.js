/* Service area map: a real, zoomable map of Southern California. Every city with a guide
   lights up in its own color on hover and opens its guide on click.

   <div class="svc-map" data-servicemap></div>

   Map engine: MapLibre GL (loaded only when the map scrolls near the screen).
   Base map: OpenFreeMap (free, no key), recolored below to the Jessetek paper look.
   Cities: /data/service-area.json, built by servicemap/build.py.
*/
(function () {
  var LIB = 'https://cdnjs.cloudflare.com/ajax/libs/maplibre-gl/4.7.1/maplibre-gl.min.js';
  var CSS = 'https://cdnjs.cloudflare.com/ajax/libs/maplibre-gl/4.7.1/maplibre-gl.min.css';
  var STYLE = 'https://tiles.openfreemap.org/styles/positron';
  var DATA = '/data/service-area.json?v=10';

  // The look: warm paper land, soft blue water, quiet roads.
  var LAND = '#F7F3EC', WATER = '#BFE1F3', PARK = '#D9EBCF', WOOD = '#E3EDD6', ROAD = '#FFFFFF',
      ROAD_EDGE = '#E6DFD3', HIGHWAY = '#FBEFD2', HIGHWAY_EDGE = '#EFDDB0', INK = '#030302', MUTE = '#8A8780';

  function load(src, css) {
    return new Promise(function (ok, bad) {
      if (css) { var l = document.createElement('link'); l.rel = 'stylesheet'; l.href = css; document.head.appendChild(l); }
      if (window.maplibregl) return ok();
      var s = document.createElement('script'); s.src = src; s.onload = ok; s.onerror = bad; document.head.appendChild(s);
    });
  }

  // Recolor the stock base map and drop the layers that add noise at city scale.
  function restyle(style, names) {
    var keep = [];
    style.layers.forEach(function (l) {
      var id = l.id, p = l.paint = l.paint || {};
      var key = l.type === 'fill' ? 'fill-color' : 'line-color';
      if (/^(building|boundary_|railway|aeroway|highway-shield|road_shield|highway-name-path|highway-name-minor|waterway_line_label|label_other|label_village|tunnel_|landuse_residential)/.test(id)) return;
      if (l.type === 'background') p['background-color'] = LAND;
      else if (id === 'water') p['fill-color'] = WATER;
      else if (id === 'waterway') p[key] = WATER;
      else if (id === 'park') { p['fill-color'] = PARK; p['fill-opacity'] = 0.75; }
      else if (id === 'landcover_wood') { p['fill-color'] = WOOD; p['fill-opacity'] = 0.7; }
      else if (id === 'landuse_residential') { p['fill-color'] = LAND; }
      else if (/^highway_motorway.*casing$/.test(id)) p[key] = HIGHWAY_EDGE;
      else if (/^highway_motorway/.test(id)) p[key] = HIGHWAY;
      else if (/^highway_major_casing$/.test(id)) p[key] = ROAD_EDGE;
      else if (/^highway_(major|minor|path)/.test(id) || /^road_/.test(id)) p[key] = ROAD;
      else if (l.type === 'symbol') {
        p['text-color'] = /water/.test(id) ? '#6FA6C4' : MUTE;
        p['text-halo-color'] = /water/.test(id) ? WATER : LAND; p['text-halo-width'] = 1.2;
        // our own city labels replace the stock ones for cities we serve
        if (/^label_(city|town)/.test(id)) {
          var f = ['!', ['in', ['get', 'name'], ['literal', names]]];
          l.filter = l.filter ? ['all', l.filter, f] : f;
        }
      }
      keep.push(l);
    });
    style.layers = keep;
    return style;
  }

  function build(box, data, style) {
    var gl = window.maplibregl;
    var feats = data.features;
    var names = feats.map(function (f) { return f.properties.name; });
    var bySlug = {}; feats.forEach(function (f) { bySlug[f.properties.slug] = f; });

    // frame + chrome
    box.innerHTML =
      '<div class="svc-canvas"></div>' +
      '<div class="svc-ctrl" role="group" aria-label="Map zoom">' +
        '<button type="button" class="svc-btn" data-z="in" aria-label="Zoom in">+</button>' +
        '<button type="button" class="svc-btn" data-z="out" aria-label="Zoom out">&minus;</button>' +
      '</div>' +
      '<button type="button" class="svc-btn svc-home" aria-label="Show the whole service area" title="Whole service area">' +
        '<svg viewBox="0 0 24 24" width="18" height="18" aria-hidden="true"><path d="M20.5 3.5 3.8 10.3c-.6.25-.55 1.1.07 1.28l6.3 1.85 1.85 6.3c.18.62 1.03.67 1.28.07L20.5 3.5Z" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linejoin="round"/></svg>' +
      '</button>' +
      '<a class="svc-card" hidden>' +
        '<span class="svc-card-swatch"></span>' +
        '<span class="svc-card-body"><span class="svc-card-name"></span><span class="svc-card-meta"></span></span>' +
        '<span class="svc-card-go">Open guide <i aria-hidden="true">&rarr;</i></span>' +
      '</a>' +
      '<div class="svc-hint">Pick a city</div>' +
      '<div class="svc-credit">' + (data.credit || '') + ' · Map: OpenFreeMap © OpenMapTiles, OpenStreetMap</div>';

    // The map is one fixed area: the frame saved in the data file. Nothing outside it can be reached.
    var FR = data.frame;
    var all = new gl.LngLatBounds();
    if (FR) { all.extend([FR[0], FR[1]]); all.extend([FR[2], FR[3]]); }
    else feats.forEach(function (f) { var b = f.properties.bbox; all.extend([b[0], b[1]]); all.extend([b[2], b[3]]); });
    var pad = function () { return 0; };
    var limit = FR ? [[FR[0] - 0.012, FR[1] - 0.01], [FR[2] + 0.012, FR[3] + 0.01]] : [[-120.2, 32.4], [-115.6, 35.3]];
    var map = new gl.Map({
      container: box.querySelector('.svc-canvas'), style: restyle(style, names),
      bounds: all, fitBoundsOptions: { padding: pad() },
      minZoom: 7.2, maxZoom: 14.5, maxBounds: limit,
      dragRotate: false, pitchWithRotate: false, touchPitch: false, attributionControl: false,
      cooperativeGestures: true, fadeDuration: 150
    });
    map.touchZoomRotate.disableRotation();
    map.keyboard.disableRotation();

    var card = box.querySelector('.svc-card'), hint = box.querySelector('.svc-hint');
    var cName = card.querySelector('.svc-card-name'), cMeta = card.querySelector('.svc-card-meta'), cSw = card.querySelector('.svc-card-swatch');
    var active = null;
    // touch screens (phones, tablets): no hover, so a tap picks a city and the card opens its guide
    var touch = !!(window.matchMedia && window.matchMedia('(hover: none)').matches);
    if (touch) hint.textContent = 'Tap a city';

    function setActive(f) {
      if (active && (!f || f.id !== active.id)) map.setFeatureState({ source: 'cities', id: active.id }, { on: false });
      active = f || null;
      if (!f) { card.hidden = true; hint.hidden = false; map.getCanvas().style.cursor = ''; document.querySelectorAll('.svc-side-row.on').forEach(function (r) { r.classList.remove('on'); }); return; }
      map.setFeatureState({ source: 'cities', id: f.id }, { on: true });
      var p = f.properties;
      // on a city's own guide, its card is a label, not a link back to the same page
      var here = box._svc_focus && box._svc_focus.id === f.id && box.getAttribute('data-focus');
      cName.textContent = p.name;
      // unincorporated communities (Census CDPs) say so, so nobody mistakes them for a city hall
      cMeta.textContent = [p.kind === 'cdp' ? 'Unincorporated ' + p.county : p.county, p.value].filter(Boolean).join(' · ');
      card.setAttribute('aria-label', here ? p.name : 'Open the ' + p.name + ' guide');
      cSw.style.background = p.color;
      if (here) card.removeAttribute('href'); else card.href = p.url;
      card.classList.toggle('svc-card-here', !!here);
      card.hidden = false; hint.hidden = true;
      map.getCanvas().style.cursor = 'pointer';
      document.querySelectorAll('.svc-side-row.on').forEach(function (r) { r.classList.remove('on'); });
      var row = document.querySelector('.svc-side-row[data-svc-city="' + p.slug + '"]');
      if (row) row.classList.add('on');
    }

    map.on('load', function () {
      map.addSource('cities', { type: 'geojson', data: data });
      // City color sits under the water, roads and labels, the way a highlighted region does on a real map.
      // That also hides the part of a coastal city's legal boundary that runs out into the ocean.
      var first = map.getLayer('water') ? 'water' : undefined;
      var firstLabel = (map.getStyle().layers.filter(function (l) { return l.type === 'symbol'; })[0] || {}).id;   // outline rides above the roads
      // resting: a faint wash so the service area reads as one region. on: the city's own color.
      map.addLayer({ id: 'city-fill', type: 'fill', source: 'cities', paint: {
        'fill-color': ['case', ['boolean', ['feature-state', 'on'], false], ['get', 'color'], '#FFFFFF'],
        'fill-opacity': ['case', ['boolean', ['feature-state', 'on'], false], 1, 0.55] } }, first);
      // Outlines. Inland cities: above the roads, so the edge is one clean line. Coastal cities: under the
      // water, so the part of the legal boundary that runs out to sea is hidden and the shore is the edge.
      var linePaint = { 'line-color': INK,
        'line-opacity': ['case', ['boolean', ['feature-state', 'on'], false], 0.9, 0.16],
        'line-width': ['case', ['boolean', ['feature-state', 'on'], false], 2.2, 1] };
      map.addLayer({ id: 'city-line-coast', type: 'line', source: 'cities', filter: ['==', ['get', 'coastal'], true], layout: { 'line-join': 'round' }, paint: linePaint }, first);
      map.addLayer({ id: 'city-line', type: 'line', source: 'cities', filter: ['!=', ['get', 'coastal'], true], layout: { 'line-join': 'round' }, paint: linePaint }, firstLabel);
      map.addSource('city-labels', { type: 'geojson', data: { type: 'FeatureCollection', features: feats.map(function (f) {
        return { type: 'Feature', id: f.id, properties: { slug: f.properties.slug, name: f.properties.name, rank: -(f.properties.pop || 0), anchor: f.properties.anchor || 'center' }, geometry: { type: 'Point', coordinates: f.properties.center } };
      }) } });
      map.addLayer({ id: 'city-name', type: 'symbol', source: 'city-labels', layout: {
        'text-field': ['get', 'name'], 'text-font': ['Noto Sans Bold'],
        'text-size': ['interpolate', ['linear'], ['zoom'], 8, 10.5, 11, 13.5, 13, 17],
        'symbol-sort-key': ['get', 'rank'], 'text-padding': 6, 'text-max-width': 7, 'text-letter-spacing': 0.01,
        'text-anchor': ['get', 'anchor'], 'text-justify': 'auto' },
        paint: { 'text-color': INK, 'text-halo-color': 'rgba(255,255,255,.92)', 'text-halo-width': 1.6 } });

      map.on('mousemove', 'city-fill', function (e) { if (!touch && e.features.length) setActive(bySlug[e.features[0].properties.slug]); });
      // leaving a city: on a city's own guide the map falls back to that city, elsewhere to nothing
      map.on('mouseleave', 'city-fill', function () { if (!touch) setActive(box.getAttribute('data-focus') && box._svc_focus ? box._svc_focus : null); });
      // What a tap or click means: the outline under the finger (small cities sit on top of big ones), then a
      // city name under the finger, then on touch the closest city within a finger's width.
      function pick(pt) {
        var hit = map.queryRenderedFeatures(pt, { layers: ['city-fill'] })[0];
        if (hit) return bySlug[hit.properties.slug];
        var lab = map.queryRenderedFeatures(pt, { layers: ['city-name'] })[0];
        if (lab && bySlug[lab.properties.slug]) return bySlug[lab.properties.slug];
        if (!touch) return null;
        var near = map.queryRenderedFeatures([[pt.x - 22, pt.y - 22], [pt.x + 22, pt.y + 22]], { layers: ['city-fill'] });
        return near.length ? bySlug[near[0].properties.slug] : null;
      }
      map.on('click', function (e) {
        if (map.getLayer('dots') && map.queryRenderedFeatures(e.point, { layers: ['dots'] }).length) return;
        var f = pick(e.point);
        if (!f) { setActive(null); return; }
        // mouse: click goes straight to the guide. touch: first tap picks, second tap (or the card) opens.
        if (box._svc_focus && f.id === box._svc_focus.id) { setActive(f); return; }   // already on this city's page
        if (!touch || (active && active.id === f.id)) { window.location.href = f.properties.url; return; }
        // touch: the first tap also zooms to the city, so a small city is easy to see and tap again
        if (touch && map.getZoom() < 10.2) goTo(f); else setActive(f);
      });
      box.classList.add('ready');
    });
    box.addEventListener('touchstart', function () { touch = true; }, { passive: true });

    box.querySelector('[data-z="in"]').addEventListener('click', function () { map.zoomIn({ duration: 320 }); });
    box.querySelector('[data-z="out"]').addEventListener('click', function () { map.zoomOut({ duration: 320 }); });
    box.querySelector('.svc-home').addEventListener('click', function () { setActive(null); map.fitBounds(all, { padding: pad(), duration: 700 }); });

    // ---- go to one city: used by focus mode, the search box and ?city= links ----
    function cityBounds(f) { var b = f.properties.bbox; return [[b[0], b[1]], [b[2], b[3]]]; }
    function goTo(f, opts) {
      var w = box.clientWidth, side = Math.round(w * (opts && opts.wide ? 0.30 : 0.16));
      map.fitBounds(cityBounds(f), { padding: { top: 70, bottom: 120, left: Math.max(40, side), right: Math.max(40, side) }, maxZoom: 12.6, duration: opts && opts.instant ? 0 : 900 });
      setActive(f);
    }
    // focus mode (city guides): open on that city and keep it lit when the pointer leaves the map
    var focus = box._svc_focus = bySlug[box.getAttribute('data-focus') || new URLSearchParams(location.search).get('city') || ''] || null;
    if (focus) {
      map.once('load', function () { goTo(focus, { instant: true, wide: true }); });
      map.on('mouseleave', 'city-fill', function () { if (!touch) setActive(focus); });
    }
    // search box: typing a city flies the map to it
    var search = document.querySelector('#saSearch');
    if (search && !box.getAttribute('data-focus')) {
      var plain = function (t) { return t.normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase().trim(); };
      var timer;
      search.addEventListener('input', function () {
        clearTimeout(timer);
        timer = setTimeout(function () {
          if (!box.classList.contains('ready')) return;
          var q = plain(search.value);
          if (!q) { setActive(null); map.fitBounds(all, { padding: pad(), duration: 700 }); return; }
          var exact = feats.filter(function (f) { return plain(f.properties.name) === q; });
          var starts = feats.filter(function (f) { return plain(f.properties.name).indexOf(q) === 0; });
          var hit = exact[0] || (starts.length === 1 ? starts[0] : null);
          if (hit) goTo(hit);
        }, 280);
      });
    }

    // ---- side panel: every city on the map, searchable. Hover lights the city, click opens its guide. ----
    var panel = document.querySelector('[data-svc-list]');
    if (panel && !box.getAttribute('data-focus')) {
      var sorted = feats.slice().sort(function (a, b) { return a.properties.name.localeCompare(b.properties.name); });
      panel.innerHTML =
        '<div class="svc-side-head"><div class="svc-side-title"><span>' + feats.length + '</span> cities on the map</div>' +
        '<input type="search" class="svc-side-search" data-svc-search placeholder="Find a city" autocomplete="off" aria-label="Find a city on the map"></div>' +
        '<div class="svc-side-list" role="list">' + sorted.map(function (f) {
          var p = f.properties;
          return '<a role="listitem" class="svc-side-row" href="' + p.url + '" data-svc-city="' + p.slug + '"><i style="background:' + p.color + '"></i><span>' + p.name + '</span><em>' + p.county.replace(' County', '') + '</em></a>';
        }).join('') + '</div><div class="svc-side-empty" hidden>No city by that name on the map.</div>';
      var sideSearch = panel.querySelector('.svc-side-search'), rows = panel.querySelectorAll('.svc-side-row'), empty = panel.querySelector('.svc-side-empty');
      var plain2 = function (t) { return t.normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase().trim(); };
      var t2;
      sideSearch.addEventListener('input', function () {
        var q = plain2(sideSearch.value), shown = [];
        rows.forEach(function (r) { var ok = !q || plain2(r.textContent).indexOf(q) !== -1; r.hidden = !ok; if (ok) shown.push(r); });
        empty.hidden = shown.length > 0;
        clearTimeout(t2);
        t2 = setTimeout(function () {
          if (!box.classList.contains('ready')) return;
          if (!q) { setActive(null); map.fitBounds(all, { padding: 0, duration: 700 }); return; }
          var starts = shown.filter(function (r) { return plain2(r.querySelector('span').textContent).indexOf(q) === 0; });
          var pick = shown.length === 1 ? shown[0] : (starts.length === 1 ? starts[0] : null);
          if (pick) goTo(bySlug[pick.getAttribute('data-svc-city')]);
        }, 300);
      });
      sideSearch.addEventListener('keydown', function (e) {
        if (e.key !== 'Enter') return;
        var first = panel.querySelector('.svc-side-row:not([hidden])');
        if (first) window.location.href = first.getAttribute('href');
      });
    }

    // outside list: hovering or focusing a city link lights it on the map
    document.querySelectorAll('[data-svc-city]').forEach(function (a) {
      var f = bySlug[a.getAttribute('data-svc-city')];
      if (!f) return;
      a.addEventListener('mouseenter', function () { if (box.classList.contains('ready')) setActive(f); });
      a.addEventListener('focus', function () { if (box.classList.contains('ready')) setActive(f); });
    });
    // ---- places as dots (city guides): public schools, parks, things to do, local food.
    // Data sits in <script id="hubSchools"> and <script id="hubPlaces">, written by servicemap/hub.py. ----
    var schEl = box.getAttribute('data-focus') ? document.getElementById('hubSchools') : null;
    var plEl = box.getAttribute('data-focus') ? document.getElementById('hubPlaces') : null;
    if (schEl || plEl) {
      var LEVEL = { elementary: 'Elementary school', middle: 'Middle school', high: 'High school', k12: 'K to 12 school' };
      var dots = [];
      try { (schEl ? JSON.parse(schEl.textContent) : []).forEach(function (p) { dots.push({ c: [p[0], p[1]], name: p[2], layer: 'school', sub: p[3], label: LEVEL[p[3]] || 'School' }); }); } catch (err) {}
      try { (plEl ? JSON.parse(plEl.textContent) : []).forEach(function (p) { dots.push({ c: [p[0], p[1]], name: p[2], layer: p[3], sub: p[3], label: p[4] }); }); } catch (err) {}
      var LAYERS = [['school', 'Schools', '#030302'], ['park', 'Parks', '#2F9E63'], ['fun', 'Things to do', '#6A5BD6'], ['eat', 'Food', '#E0722F']];
      var on = {}, count = {};
      dots.forEach(function (d) { count[d.layer] = (count[d.layer] || 0) + 1; });
      var tip = document.createElement('div'); tip.className = 'svc-tip'; tip.hidden = true; box.appendChild(tip);
      var lg = document.createElement('div'); lg.className = 'svc-legend';
      LAYERS.forEach(function (L) {
        if (!count[L[0]]) return;
        on[L[0]] = true;
        var b = document.createElement('button'); b.type = 'button'; b.className = 'svc-chip on'; b.setAttribute('data-layer', L[0]); b.setAttribute('aria-pressed', 'true');
        b.innerHTML = '<i style="background:' + L[2] + '"></i>' + L[1] + ' <em>' + count[L[0]] + '</em>';
        lg.appendChild(b);
      });
      box.appendChild(lg);
      function applyFilter() {
        var keep = Object.keys(on).filter(function (k) { return on[k]; });
        if (map.getLayer('dots')) map.setFilter('dots', ['in', ['get', 'layer'], ['literal', keep]]);
      }
      lg.addEventListener('click', function (e) {
        var b = e.target.closest('.svc-chip'); if (!b) return;
        var k = b.getAttribute('data-layer'); on[k] = !on[k];
        b.classList.toggle('on', on[k]); b.setAttribute('aria-pressed', on[k] ? 'true' : 'false'); tip.hidden = true; applyFilter();
      });
      map.on('load', function () {
        map.addSource('dots', { type: 'geojson', data: { type: 'FeatureCollection', features: dots.map(function (d, i) {
          return { type: 'Feature', id: i + 1, properties: { name: d.name, layer: d.layer, sub: d.sub, label: d.label }, geometry: { type: 'Point', coordinates: d.c } };
        }) } });
        map.addLayer({ id: 'dots', type: 'circle', source: 'dots', paint: {
          'circle-radius': ['interpolate', ['linear'], ['zoom'], 9, 2.2, 11.5, 4.4, 14, 7],
          'circle-color': ['match', ['get', 'layer'], 'park', '#2F9E63', 'fun', '#6A5BD6', 'eat', '#E0722F',
            ['match', ['get', 'sub'], 'elementary', '#FFFFFF', 'middle', '#9A9A9A', INK]],
          'circle-stroke-color': ['match', ['get', 'layer'], 'school', INK, '#FFFFFF'],
          'circle-stroke-width': ['interpolate', ['linear'], ['zoom'], 9, 1, 12, 1.6] } }, 'city-name');
        function showTip(f) {
          var pt = map.project(f.geometry.coordinates);
          tip.textContent = f.properties.name + ' · ' + f.properties.label;
          tip.style.left = pt.x + 'px'; tip.style.top = pt.y + 'px'; tip.hidden = false;
        }
        map.on('mousemove', 'dots', function (e) { showTip(e.features[0]); map.getCanvas().style.cursor = 'default'; });
        map.on('mouseleave', 'dots', function () { tip.hidden = true; });
        map.on('click', 'dots', function (e) { showTip(e.features[0]); });   // touch: a tap names the place instead of leaving the page
        var hold = false;
        map.on('movestart', function () { if (!hold) tip.hidden = true; });
        // a park, place or restaurant named on the page: tap it and the map goes there
        function goSpot(el) {
          var c = el.getAttribute('data-spot').split(',').map(Number), hit = null;
          dots.forEach(function (d, i) { if (Math.abs(d.c[0] - c[0]) < 1e-6 && Math.abs(d.c[1] - c[1]) < 1e-6) hit = i; });
          var name = hit !== null ? dots[hit].name : (el.querySelector('b') || el).textContent.trim();
          var label = hit !== null ? dots[hit].label : '';
          if (hit !== null && !on[dots[hit].layer]) { var chip = lg.querySelector('[data-layer="' + dots[hit].layer + '"]'); if (chip) chip.click(); }
          box.scrollIntoView({ behavior: 'smooth', block: 'center' });
          hold = true; tip.hidden = true;
          map.flyTo({ center: c, zoom: Math.max(map.getZoom(), 14.2), duration: 1400, essential: true });
          map.once('moveend', function () {
            hold = false; var pt = map.project(c);
            tip.textContent = name + (label ? ' \u00b7 ' + label : ''); tip.style.left = pt.x + 'px'; tip.style.top = pt.y + 'px'; tip.hidden = false;
            tip.classList.remove('pin'); void tip.offsetWidth; tip.classList.add('pin');
          });
        }
        document.addEventListener('click', function (e) { var el = e.target.closest && e.target.closest('[data-spot]'); if (el) goSpot(el); });
        document.addEventListener('keydown', function (e) { if ((e.key === 'Enter' || e.key === ' ') && e.target.matches && e.target.matches('[data-spot]')) { e.preventDefault(); goSpot(e.target); } });
      });
    }

    box._svc = { map: map, setActive: setActive, bySlug: bySlug };
  }

  function start(box) {
    Promise.all([
      load(LIB, CSS),
      fetch(DATA).then(function (r) { return r.json(); }),
      fetch(STYLE).then(function (r) { return r.json(); })
    ]).then(function (r) { build(box, r[1], r[2]); })
      .catch(function () { box.classList.add('failed'); });
  }

  function init() {
    var boxes = document.querySelectorAll('[data-servicemap]');
    if (!boxes.length) return;
    if (!('IntersectionObserver' in window)) { boxes.forEach(start); return; }
    var io = new IntersectionObserver(function (en) {
      en.forEach(function (e) { if (e.isIntersecting) { io.unobserve(e.target); start(e.target); } });
    }, { rootMargin: '500px' });
    boxes.forEach(function (b) { io.observe(b); });
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init);
  else init();
})();
