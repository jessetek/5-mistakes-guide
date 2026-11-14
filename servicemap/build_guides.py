#!/usr/bin/env python3
"""City guides.

1. Builds a full guide for every place on the map that has no hand-written guide.
2. Adds the same data blocks ("the hub", see hub.py) to the hand-written guides, between
   <!-- cityhub:start --> and <!-- cityhub:end --> markers, so every city page carries the same tools.
   The hand-written copy on those pages is never touched.

Every number comes from citydata.py (public sources only). Generated pages carry
<meta name="generator" content="servicemap/build_guides.py"> and are the only pages this script overwrites whole.

Run:  python3 servicemap/build_guides.py
"""
import math, html, json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import citydata as CD
import hub as H

PUB = os.path.join(HERE, '..', 'public')
GDIR = os.path.join(PUB, 'neighborhoods')
M = CD.M
COUNTY_Z = CD.COUNTY_Z
HUES = [('#FDE99B', '#F7C9B6'), ('#D1EEF9', '#9ED4EF'), ('#9BD8A9', '#FDE99B'), ('#B8CAF5', '#D1EEF9'),
        ('#9ED4EF', '#9BD8A9'), ('#F7C9B6', '#FDE99B')]
MARK = '<meta name="generator" content="servicemap/build_guides.py">'
VER = {'map': 12, 'pay': 3, 'hub': 2}     # bump when the script files change
e = lambda s: html.escape(str(s), quote=True)
money, short, pct, signed, month, join = H.money, H.short, H.pct, H.signed, H.month, H.join


def people(n): return '{:.1f}M'.format(n / 1e6) if n >= 1e6 else ('{:.0f}K'.format(n / 1e3) if n >= 10000 else '{:,}'.format(n))


# ---- small wrappers other scripts use (build.py, wire.py, qc.py) ----
def zhvi(slug):
    r = CD.get(slug)
    return {'now': r['value'], 'date': r['value_date'], 'y1': r['y1'], 'y5': r['y5']} if r['value'] else None
def pop(slug):
    p = CD.get(slug)['pop']
    return {'est': p['n'], 'label': p['label'], 'year': int(p['label'][:4])} if p else None
def neighbors(slug, n=4): return CD.near(slug, n)
def is_generated(path): return os.path.exists(path) and MARK in open(path).read()


COAST = set('malibu santa-monica los-angeles el-segundo manhattan-beach hermosa-beach redondo-beach torrance palos-verdes-estates rancho-palos-verdes long-beach seal-beach huntington-beach newport-beach laguna-beach dana-point san-clemente'.split())
def map_colors():
    """Each city's own color on the service area map (public/data/service-area.json, written by build.py)."""
    global _MC
    if _MC is None:
        f = os.path.join(PUB, 'data', 'service-area.json')
        _MC = {x['properties']['slug']: x['properties']['color'] for x in json.load(open(f))['features']} if os.path.exists(f) else {}
    return _MC
_MC = None
def lighten(hexc, t):
    r_, g_, b_ = (int(hexc[i:i + 2], 16) for i in (1, 3, 5)); return '#%02X%02X%02X' % tuple(round(v + (255 - v) * t) for v in (r_, g_, b_))


def shape(slug):
    """The city's real outline as a small drawing for the top of its page (official Census boundary).
    Ocean cities are left out: their legal boundary runs out to sea and would not look like the city."""
    d = shape_path(slug)
    if not d: return ''
    kind = 'city limit' if CD.ALL[slug]['kind'] == 'city' else 'community boundary'
    return f'''<a class="hero-shape" href="#map" aria-label="The outline of {e(CD.ALL[slug]['name'])}. Jump to the map.">
      <svg viewBox="0 0 100 100" aria-hidden="true"><path d="{d}" fill-rule="evenodd"/></svg>
      <span>The real {kind}</span>
    </a>'''


def shape_path(slug, step=0.5):
    if slug not in CD.T or slug in COAST: return ''
    geo = CD.T[slug]['geo']; polys = geo['coordinates'] if geo['type'] == 'MultiPolygon' else [geo['coordinates']]
    k = math.cos(math.radians(CD.T[slug]['lat']))
    pts = [(x * k, -y) for pl in polys for x, y in pl[0]]
    x0 = min(p[0] for p in pts); x1 = max(p[0] for p in pts); y0 = min(p[1] for p in pts); y1 = max(p[1] for p in pts)
    sc = 96 / max(x1 - x0, y1 - y0); ox = (100 - (x1 - x0) * sc) / 2; oy = (100 - (y1 - y0) * sc) / 2
    d = []
    for pl in polys:
        for ring in pl:                                   # outer ring and any holes, so enclaves show as gaps
            out = []
            for x, y in ring:
                q = (round((x * k - x0) * sc + ox, 1), round((-y - y0) * sc + oy, 1))
                if not out or abs(q[0] - out[-1][0]) + abs(q[1] - out[-1][1]) >= step: out.append(q)
            if len(out) >= 4: d.append('M' + ' '.join(f'{a:g},{b:g}' for a, b in out) + 'Z')
    return ''.join(d)


JUMP = [('story', 'Story'), ('photos', 'Photos'), ('prices', 'Prices'), ('buy', 'What money buys'), ('payment', 'Monthly cost'), ('rank', 'Ranking'), ('parks', 'Parks'), ('todo', 'Things to do'), ('food', 'Food'), ('map', 'Map and schools')]
IDS = {'story': 'story', 'gallery': 'photos', 'price history': 'prices', 'what your money buys': 'buy', 'where it ranks': 'rank', 'parks': 'parks', 'things to do': 'todo', 'food': 'food'}
def anchors(h):
    """Give each data section an id so the jump bar can link to it."""
    for k, v in IDS.items(): h = h.replace(f'<!-- hub: {k} -->\n<section class="', f'<!-- hub: {k} -->\n<section id="{v}" class="')
    return h
def jump(h):
    links = ''.join(f'<a href="#{i}">{t}</a>' for i, t in sorted((x for x in JUMP if f'id="{x[0]}"' in h), key=lambda x: h.index(f'id="{x[0]}"')))
    return f'<nav class="hub-jump" aria-label="On this page"><div class="hub-jump-in">{links}</div></nav>\n\n'


CREDITS = os.path.join(HERE, 'photo_credits.json')
def photo(slug):
    """The city's own photo, if a freely licensed one has been saved to public/img/cities/ (see fetch_wiki_photos.py)."""
    c = json.load(open(CREDITS)) if os.path.exists(CREDITS) else {}
    for p in c.get(slug, []):
        f = os.path.join(PUB, 'img', 'cities', p['file'])
        if os.path.exists(f):
            return {'src': '/img/cities/' + p['file'], 'sm': '/img/cities/' + p['file'].replace('.webp', '-sm.webp'), 'alt': p['alt'], 'caption': p['caption']}
    return None


def scripts(r, with_map):
    out = []
    if r['value']: out.append(f'<script src="/js/citypay.js?v={VER["pay"]}" defer></script>')
    if with_map: out.append(f'<script src="/js/servicemap.js?v={VER["map"]}" defer></script>')
    out.append(f'<script src="/js/cityhub.js?v={VER["hub"]}" defer></script>')
    out.append('<script src="/js/header.js?v=1" defer></script>')   # hide-on-scroll header, on every page with the nav
    return '\n'.join(out) + '\n'


def pay_tool(r):
    if not r['value']: return ''
    prices = [v for v in list(r['beds'].values()) + [r['low'], r['high']] if v]
    lim = f' data-min="{min(prices)}" data-max="{max(prices)}"' if prices else ''
    return f'''<!-- ===================== PAYMENT TOOL ===================== -->
<section class="cp-section" id="payment">
  <div class="cp-head reveal">
    <h2>What {'an' if r['name'][0] in 'AEIOU' else 'a'} {e(r['name'])} Home<br>Costs Per Month.</h2>
    <p>Move the sliders. The rate is this week's average, so the number is honest.</p>
  </div>
  <div class="cp-card" data-citypay data-city="{e(r['name'])}" data-median="{r['value']}" data-label="typical home value"{lim}></div>
</section>

'''


def map_block(r):
    """Our own map opened on this city, with its public schools as dots, plus the schools card."""
    pts = H.school_points(r); pls = H.place_points(r)
    kind = 'city limit' if r['kind'] == 'city' else 'community boundary'
    sub = f'The outline is the official {kind}.' + (' The dots are its public schools, parks, things to do and local food. Tap the chips to show or hide each kind. ' if (pts or pls) else ' ') + 'Pick any nearby city to open its guide.'
    data = (f'<script type="application/json" id="hubSchools">{json.dumps(pts, separators=(",", ":"), ensure_ascii=False)}</script>\n    ' if pts else '') + \
           (f'<script type="application/json" id="hubPlaces">{json.dumps(pls, separators=(",", ":"), ensure_ascii=False).replace("</", "<\\/")}</script>\n    ' if pls else '')
    return f'''<!-- ===================== MAP + SCHOOLS ===================== -->
<section id="map" class="nbhd-mapsection">
  <div class="nbhd-mapsection-inner">
    <div class="sec-head reveal">
      <h2 class="sec-title">{e(r['name'])} on the Map.</h2>
      <p class="sec-sub">{e(sub)}</p>
    </div>
    {data}<div class="svc-map svc-map-mini" data-servicemap data-focus="{r['slug']}" aria-label="Map of {e(r['name'])}: schools, parks, places and nearby cities"></div>
    {H.schools(r)}
  </div>
</section>

'''


def faq_items(r, nbn):
    name = r['name']; faq = []
    if r['value']:
        faq.append((f'What is the typical home value in {name}, CA?',
                    f'As of {month(r["value_date"])}, the typical home in {name} is worth about {money(r["value"])}, based on the Zillow Home Value Index. Prices vary a lot by street, lot size and condition, so ask for a valuation of your specific home.'))
        if r['y1']:
            ch = pct(r['value'], r['y1']); word = 'up' if ch > 0.05 else 'down' if ch < -0.05 else 'flat'
            faq.append((f'Are home values in {name} going up or down?',
                        (f'The typical home value in {name} is {word} {abs(ch):.1f}% over the past year, from about {money(r["y1"])} to about {money(r["value"])}.' if word != 'flat'
                         else f'The typical home value in {name} is about the same as a year ago, near {money(r["value"])}.') +
                        (f' Over ten years it is up {pct(r["value"], r["y10"]):.0f}%.' if r['y10'] and r['value'] > r['y10'] else '')))
    if len(r['beds']) >= 3:
        b = sorted(r['beds'].items())
        faq.append((f'How much is a 3-bedroom home in {name}?' if 3 in r['beds'] else f'How much do homes cost by size in {name}?',
                    'Typical values in ' + name + ' by bedroom count: ' + ', '.join(f'{n}{"+" if n == 5 else ""} bedroom about {money(v)}' for n, v in b) + f'. Source: Zillow Home Value Index, {month(r["value_date"])}.'))
    if r['rent']:
        faq.append((f'What is the typical rent in {name}?',
                    f'The typical asking rent in {name} is about {money(r["rent"])} a month as of {month(r["rent_date"])}, based on the Zillow Observed Rent Index.'))
    if r['schools']:
        lv = {}
        for s in r['schools']: lv[s['level']] = lv.get(s['level'], 0) + 1
        parts = [f'{lv[k]} {H.LEVEL_NAME[k].lower()}' for k in ('elementary', 'middle', 'high', 'k12') if k in lv]
        faq.append((f'How many public schools are in {name}?',
                    f'{len(r["schools"])} public schools sit inside the {name} boundary: {join(parts)}. ' + (f'They belong to {join(r["districts"][:6])}. ' if r['districts'] else '') + 'School assignment depends on the home address, so confirm with the district.'))
    ps = [p for p in r['places'].get('parks', []) if p['acres'] >= 0.5]
    if len(ps) >= 2:
        faq.append((f'What are the biggest parks in {name}?',
                    f'{name} has {len(ps)} parks. The largest are ' + join([f'{p["name"]} (about {H.acres(p["acres"])} acres)' for p in ps[:3]]) + '. Sizes are measured from OpenStreetMap.'))
    if nbn: faq.append((f'What cities are near {name}?', f'{name} is in {COUNTY_Z[r["county"]]}. The closest cities I cover are {join(nbn)}.'))
    faq.append((f'How do I find out what my {name} home is worth?',
                'Enter your address on the home valuation form at jessetek.net/valuation. You get an automated estimate right away and a Comparative Market Analysis from Jesse within 24 hours, with no obligation.'))
    return faq


def img_size(src):
    """Real pixel size of a site image, for og:image:width/height."""
    from PIL import Image
    return Image.open(os.path.join(PUB, src.lstrip('/'))).size


def og_size(head, src):
    w, h = img_size(src)
    return re.sub(r'<meta property="og:image:width" content="\d+">\n<meta property="og:image:height" content="\d+">',
                  f'<meta property="og:image:width" content="{w}">\n<meta property="og:image:height" content="{h}">', head, count=1)


SITE_PAGES = set(f[:-5] for f in os.listdir(PUB) if f.endswith('.html'))
def more_links(slug, name):
    """Other pages on the site about this same city (agent page, first-time buyer, selling over asking)."""
    out = []
    for pre, label in (('real-estate-agent-', f'Real estate agent in {name}'), ('first-time-buyer-', f'First-time buyer guide for {name}'), ('sell-over-asking-', f'Selling over asking in {name}')):
        if pre + slug in SITE_PAGES: out.append(f'<a href="/{pre}{slug}">{e(label)}</a>')
    return out


def city_cta(slug, name):
    """One clear next step near the end of every city guide. Same block on generated and hand-written guides."""
    links = more_links(slug, name) + ['<a href="/rates">Weekly mortgage rate texts</a>', '<a href="/insights/">SoCal market insights</a>']
    return f'''<!-- citycta:start -->
<section class="city-cta" aria-labelledby="cityCtaTitle">
  <div class="city-cta-card reveal">
    <h2 class="sec-title" id="cityCtaTitle">Thinking About<br><span class="g">{e(name)}?</span></h2>
    <p class="city-cta-sub">Find out what your home is worth, see which move fits your budget, or talk it through with Jesse.</p>
    <div class="city-cta-btns">
      <a href="/valuation" class="btn-primary">What&#39;s My Home Worth?</a>
      <a href="/move" class="btn-ghost">Take the Move Up Quiz</a>
      <a href="/zoom" class="btn-ghost">Talk to Jesse</a>
    </div>
    <p class="city-cta-links">{' <span aria-hidden="true">·</span> '.join(links)}</p>
  </div>
</section>
<!-- citycta:end -->

'''


def mid_cta(r):
    """A short nudge halfway down the page, where people finish reading the prices."""
    name = e(r['name'])
    return f'''<!-- hub: mid cta -->
<section class="hub-section hub-tight city-mid">
  <div class="hub-inner"><div class="city-mid-card">
    <p><b>Own in {name}?</b> These are citywide numbers. Get a value for your street and your home.</p>
    <a href="/valuation" class="btn-primary">Get My Home Value</a>
  </div></div>
</section>

'''


def schema_graph(r, slug, desc, pic):
    """Breadcrumbs plus the page and the place it is about (Census point, county). No street address anywhere."""
    url = f'https://jessetek.net/neighborhoods/{slug}'; t = CD.T.get(slug, {})
    place = {'@type': 'City' if r['kind'] == 'city' else 'Place', 'name': f"{r['name']}, California",
             'containedInPlace': {'@type': 'AdministrativeArea', 'name': COUNTY_Z[r['county']] + ', California'}}
    if r['kind'] == 'cdp': place['description'] = f"Unincorporated community (Census designated place) in {COUNTY_Z[r['county']]}."
    if t.get('lat'): place['geo'] = {'@type': 'GeoCoordinates', 'latitude': round(t['lat'], 5), 'longitude': round(t['lon'], 5)}
    page = {'@type': 'WebPage', '@id': url, 'url': url, 'name': f"{r['name']} Real Estate Guide", 'description': desc, 'inLanguage': 'en',
            'isPartOf': {'@id': 'https://jessetek.net/'}, 'about': place, 'author': {'@id': 'https://jessetek.net/about#jesse'},
            'breadcrumb': {'@id': url + '#breadcrumb'}, 'dateModified': '2026-11-13'}
    if pic: page['primaryImageOfPage'] = {'@type': 'ImageObject', 'url': 'https://jessetek.net' + pic['src']}
    crumbs = {'@type': 'BreadcrumbList', '@id': url + '#breadcrumb', 'itemListElement': [
        {'@type': 'ListItem', 'position': 1, 'name': 'Home', 'item': 'https://jessetek.net/'},
        {'@type': 'ListItem', 'position': 2, 'name': 'Service Areas', 'item': 'https://jessetek.net/service-areas'},
        {'@type': 'ListItem', 'position': 3, 'name': r['name'], 'item': url}]}
    return '<script type="application/ld+json">\n' + json.dumps({'@context': 'https://schema.org', '@graph': [page, crumbs]}, indent=2, ensure_ascii=False) + '\n</script>\n'


TPL = None
def template():
    global TPL
    if TPL is None: TPL = open(os.path.join(GDIR, 'downey.html')).read()
    return TPL
def cut(src, a, b):
    i = src.index(a); j = src.index(b, i); return src[:i], src[i:j], src[j:]


def page(slug, i):
    r = CD.get(slug); name = r['name']; county = r['county']
    nb = neighbors(slug); nbn = [M[s]['name'] for s in nb]
    th, th2 = HUES[i % len(HUES)]
    if map_colors().get(slug): th = map_colors()[slug]; th2 = lighten(th, .25)     # the page wears the city's own color from the map
    place = {'city': 'a city', 'cdp': 'an unincorporated community', 'neighborhood': 'a neighborhood'}[r['kind']]
    about = f'{name} is {place} in {COUNTY_Z[county]}, near {join(nbn[:3])}.'
    if r['pop']: about = f'{name} is {place} of about {r["pop"]["n"]:,} people in {COUNTY_Z[county]}, near {join(nbn[:3])}.'
    desc = f'{name}, CA home values by bedroom, a 10-year price chart, rent vs own, public schools on the map and a live payment tool. By Realtor Jesse Oñate.'
    if not r['value']: desc = f'Buying or selling a home in {name}, CA? See its official boundary, public schools and nearby cities, then get a real valuation from Jesse Oñate.'
    if len(desc) > 165: desc = f'{name}, CA home values by bedroom, a 10-year price chart, rent vs own, schools on the map and a live payment tool.'
    if len(desc) < 112: desc = desc[:-1] + ', your SoCal Realtor.'
    title = f'{name} Real Estate Guide | Jesse Oñate Realtor'

    stats = []
    if r['value']:
        stats.append((short(r['value']), 'Typical Home Value'))
        if r['y1']: stats.append((signed(pct(r['value'], r['y1'])), 'Change in One Year'))
    if r['pop']: stats.append((people(r['pop']['n']), 'Residents'))
    if len(stats) < 3 and r['homes2020']: stats.append((people(r['homes2020']), 'Homes, 2020 Census'))
    if len(stats) < 3 and r['schools']: stats.append((str(len(r['schools'])), 'Public Schools'))
    if len(stats) < 3: stats.append((county.replace(' County', ''), 'County'))
    stats_html = '\n'.join(f'    <div class="nbhd-stat">\n      <div class="nbhd-stat-num">{e(v)}</div>\n      <div class="nbhd-stat-label">{e(l)}</div>\n    </div>' for v, l in stats[:3])

    faq = faq_items(r, nbn)
    faq_html = '\n'.join(f'      <details class="faq-item">\n        <summary>{e(q)}</summary>\n        <p>{e(a)}</p>\n      </details>' for q, a in faq)
    faq_ld = json.dumps({'@context': 'https://schema.org', '@type': 'FAQPage', 'mainEntity': [
        {'@type': 'Question', 'name': q, 'acceptedAnswer': {'@type': 'Answer', 'text': a}} for q, a in faq]}, indent=2, ensure_ascii=False)
    related = '\n'.join(f'        <a href="/neighborhoods/{s}" class="related-city-card">\n          <span class="related-city-sw" style="background:{map_colors().get(s, "#D1EEF9")}"></span>\n          <span class="related-city-name">{e(M[s]["name"])}</span>\n          {f"""<span class="related-city-val">{short(CD.get(s)["value"])}</span>""" if CD.get(s)["value"] else ""}\n        </a>' for s in nb)

    T = template()
    head, _, rest = cut(T, '<!-- ===================== PAGE HERO ===================== -->', '<section class="cta-section cta-section-cal">')
    _, booking, rest = cut(rest, '<section class="cta-section cta-section-cal">', '<!-- RELATED CITIES -->')
    _, _, rest = cut(rest, '<!-- RELATED CITIES -->', '<!-- ===================== FOOTER ===================== -->')
    footer_etc = rest[:rest.index('<script type="application/ld+json">')]

    head = re.sub(r'<title>.*?</title>', f'<title>{e(title)}</title>\n{MARK}', head, count=1)
    for pat, val in ((r'<meta name="description" content="[^"]*">', f'<meta name="description" content="{e(desc)}">'),
                     (r'<meta property="og:title" content="[^"]*">', f'<meta property="og:title" content="{e(title)}">'),
                     (r'<meta name="twitter:title" content="[^"]*">', f'<meta name="twitter:title" content="{e(title)}">'),
                     (r'<meta property="og:description" content="[^"]*">', f'<meta property="og:description" content="{e(desc)}">'),
                     (r'<meta name="twitter:description" content="[^"]*">', f'<meta name="twitter:description" content="{e(desc)}">'),
                     (r'<body style="[^"]*">', f'<body style="--th:{th};--th2:{th2}">')):
        head = re.sub(pat, val, head, count=1)
    head = head.replace('https://jessetek.net/neighborhoods/downey', f'https://jessetek.net/neighborhoods/{slug}')
    pic = photo(slug)
    if pic:   # share previews show the city's own (freely licensed) photo instead of the generic site image
        for pat in (r'(<meta property="og:image" content=")[^"]*(">)', r'(<meta name="twitter:image" content=")[^"]*(">)'):
            head = re.sub(pat, r'\g<1>https://jessetek.net' + pic['src'] + r'\g<2>', head, count=1)
        head = og_size(head, pic['src'])

    body = f'''<!-- ===================== PAGE HERO ===================== -->
<section class="page-hero">
  <div class="page-hero-inner">
    <div class="hero-badge">
      <span class="hero-badge-dot"></span>
      <span>California · {e(county)}</span>
    </div>
    <h1>{e(name)} Homes,<br><span class="g">By the Numbers.</span></h1>
    <p>{e(about)} I help buyers and sellers across Southern California, {e(name)} included.</p>
    <div class="hero-btns">
      <a href="/zoom" class="btn-primary">Talk to Jesse</a>
      <a href="/valuation" class="btn-ghost">Home Valuation</a>
    </div>
  </div>
  {shape(slug)}
</section>

<!-- ===================== STATS ===================== -->
<section class="nbhd-stats">
  <div class="nbhd-stats-inner">
{stats_html}
  </div>
</section>

''' + (lambda mid: jump(mid) + mid)(anchors(H.story(r, photo(slug)) + H.gallery(r, skip_first=not photo(slug)) + H.chart(r) + H.money_buys(r) + pay_tool(r) + H.rent(r) + H.ranks(r) + (mid_cta(r) if r['value'] else '') + H.parks(r) + H.things(r) + H.eat(r) + map_block(r))) + f'''<!-- ===================== FAQ ===================== -->
<section class="hv-section">
  <div class="hv-inner">
    <div class="sec-head reveal">
      <h2 class="sec-title">{e(name)} Questions,<br>Answered.</h2>
    </div>
    <div class="faq-list">
{faq_html}
    </div>
    <p class="hv-source">{e(H.sources(r))}</p>
  </div>
</section>

''' + city_cta(slug, name) + booking + f'''<!-- RELATED CITIES -->
<section class="related-cities">
  <div class="related-cities-inner">
    <div class="sec-head reveal">
      <span class="sec-label">Nearby Cities</span>
      <h2 class="sec-title">Also Considering<br>These Cities?</h2>
    </div>
    <div class="related-cities-grid">
{related}
    </div>
    <div style="text-align:center;margin-top:28px">
      <a href="/service-areas" style="font-size:14px;color:var(--blue);font-weight:500;text-decoration:none">See every city I cover on the map →</a>
    </div>
  </div>
</section>

''' + footer_etc + f'<script type="application/ld+json">\n{faq_ld}\n</script>\n' + schema_graph(r, slug, desc, pic) + '\n' + scripts(r, True) + '</body>\n</html>\n'
    return head + body


# ---------------------------------------------------------------- hand-written guides: add the hub
GOOGLE_MAP = re.compile(r'<!-- ===================== MAP ===================== -->.*?</section>\n*', re.S)
HUB = re.compile(r'<!-- cityhub:start -->.*?<!-- cityhub:end -->\n*', re.S)
CTA = re.compile(r'<!-- citycta:start -->.*?<!-- citycta:end -->\n*', re.S)
def add_hub(path, slug):
    h = open(path).read()
    if slug not in CD.ALL or slug not in CD.T: return False
    r = CD.get(slug); on_map = r['on_map']
    # first run: remember the page's original Google map section so a re-run starts from the same place
    side = os.path.join(HERE, 'original_map_sections.json')
    keep = json.load(open(side)) if os.path.exists(side) else {}
    m = GOOGLE_MAP.search(h)
    if m and slug not in keep: keep[slug] = m.group(0); json.dump(keep, open(side, 'w'), indent=1)
    h = HUB.sub('', h)
    h = CTA.sub('', h)
    h = re.sub(r'<script src="/js/(cityhub|servicemap)\.js\?v=\d+" defer></script>\n', '', h)
    prices = [v for v in list(r['beds'].values()) + [r['low'], r['high']] if v]
    if prices and 'data-citypay' in h and 'data-min=' not in h:
        h = h.replace('data-citypay ', f'data-citypay data-min="{min(prices)}" data-max="{max(prices)}" ', 1)
    # the hub goes right after the payment tool, which every hand-written guide has
    block = '<!-- cityhub:start -->\n' + H.story(r, photo(slug)) + H.gallery(r, skip_first=not photo(slug)) + H.chart(r) + H.money_buys(r) + H.rent(r) + H.ranks(r) + (mid_cta(r) if r['value'] else '') + H.parks(r) + H.things(r) + '<!-- cityhub:end -->\n\n'
    block = anchors(block)
    m = re.search(r'<section class="cp-section" id="payment">.*?</section>\n*', h, flags=re.S)
    if not m: return False
    h = h[:m.end()] + block + h[m.end():]
    eat = next((x for x in ('<!-- ===================== WHERE TO EAT ===================== -->', '<!-- ===================== CTA ===================== -->', '<section class="cta-section') if x in h), '</body>')
    if on_map:
        # our map with the school dots replaces the Google embed
        m = GOOGLE_MAP.search(h)
        new = '<!-- cityhub:start -->\n' + map_block(r) + '<!-- cityhub:end -->\n\n'
        if m: h = h[:m.start()] + new + h[m.end():]
        else: h = h.replace(eat, new + eat, 1)
    elif r['schools']:
        h = h.replace(eat, f'<!-- cityhub:start -->\n<section class="hub-section hub-tight"><div class="hub-inner">{H.schools(r)}</div></section>\n<!-- cityhub:end -->\n\n' + eat, 1)
    # jump bar above the payment tool, and the city's outline in the hero
    m = re.search(r'<section class="cp-section" id="payment">', h)
    h = h[:m.start()] + '<!-- cityhub:start -->\n' + jump(h) + '<!-- cityhub:end -->\n\n' + h[m.start():]
    hero = re.search(r'<section class="page-hero">.*?</section>', h, flags=re.S)
    if hero and on_map and shape(slug):
        k = hero.end() - len('</section>')
        h = h[:k] + '<!-- cityhub:start -->\n  ' + shape(slug) + '\n<!-- cityhub:end -->\n\n' + h[k:]
    anchor = '<section class="cta-section cta-section-cal">' if '<section class="cta-section cta-section-cal">' in h else '<!-- RELATED CITIES -->' if '<!-- RELATED CITIES -->' in h else '<section class="related-cities">'
    h = h.replace(anchor, city_cta(slug, r['name']) + anchor, 1)
    tags = (f'<script src="/js/servicemap.js?v={VER["map"]}" defer></script>\n' if on_map else '') + f'<script src="/js/cityhub.js?v={VER["hub"]}" defer></script>\n'
    h = re.sub(r'/js/citypay\.js\?v=\d+', f'/js/citypay.js?v={VER["pay"]}', h)
    h = h.replace('</body>', tags + '</body>', 1)
    open(path, 'w').write(h); return True


def main():
    made = hubbed = 0; nodata = []
    for i, slug in enumerate(sorted(M)):
        path = os.path.join(GDIR, slug + '.html')
        if os.path.exists(path) and not is_generated(path): continue
        if not CD.get(slug)['value']: nodata.append(slug)
        open(path, 'w').write(page(slug, i)); made += 1
    for f in sorted(os.listdir(GDIR)):
        path = os.path.join(GDIR, f)
        if f.endswith('.html') and f != 'index.html' and not is_generated(path):
            hubbed += add_hub(path, f[:-5])
    print(f'generated {made} guides | hub added to {hubbed} hand-written guides | no Zillow value: {len(nodata)}')


if __name__ == '__main__':
    main()
