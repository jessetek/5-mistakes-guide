#!/usr/bin/env python3
"""Wire the generated guides into the site: Service Areas cards and counts, sitemap, and the
"all cities" link on every guide. Safe to run again. Run after build_guides.py."""
import datetime, html, json, os, re, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import build_guides as G
PUB = G.PUB; M = G.M
gen = sorted(s for s in M if G.is_generated(os.path.join(G.GDIR, s + '.html')))
N = len([f for f in os.listdir(G.GDIR) if f.endswith('.html') and f != 'index.html'])   # every guide page, on the map or not

# ---- Service Areas page ----
p = os.path.join(PUB, 'service-areas.html'); h = open(p).read()
h = re.sub(r'\n    <!-- generated cities: start -->.*?<!-- generated cities: end -->', '', h, flags=re.S)
cards = []
for s in gen:
    c = M[s]; z = G.zhvi(s); pp = G.pop(s)
    stats = ''
    if z: stats += f'<span><strong>{G.short(z["now"])}</strong>typical</span>'
    if pp: stats += f'<span><strong>{G.people(pp["est"])}</strong>residents</span>'
    key = (c['name'] + ' ' + c['county'] + (' la los angeles' if c['county'] == 'LA County' else ' oc' if c['county'] == 'Orange County' else ' ventura' if c['county'] == 'Ventura County' else ' inland empire')).lower().replace('ñ', 'n')
    cards.append(f'    <a href="/neighborhoods/{s}" class="sa-card" data-svc-city="{s}" data-city="{html.escape(key)}"><div class="sa-card-county">{html.escape(c["county"])}</div><div class="sa-card-name">{html.escape(c["name"])}</div><div class="sa-card-stats">{stats}</div></a>')
block = '\n    <!-- generated cities: start -->\n' + '\n'.join(cards) + '\n    <!-- generated cities: end -->'
i = h.index('<div class="sa-empty"'); j = h.rindex('</div>', 0, i)
h = h[:j].rstrip() + block + '\n  ' + h[j:]
# every card: the city's own outline in its map color (or a photo for ocean cities, whose legal boundary runs out to sea)
h = re.sub(r'<span class="sa-card-art".*?</span>', '', h, flags=re.S)
def art(m):
    slug = m.group(2); col = G.map_colors().get(slug, '#D1EEF9'); d = G.shape_path(slug, 1.2)
    if d: a = f'<span class="sa-card-art" aria-hidden="true"><svg viewBox="0 0 100 100"><path d="{d}" fill="{col}" fill-rule="evenodd"/></svg></span>'
    elif os.path.exists(os.path.join(PUB, 'img', 'cities', slug + '-1-sm.webp')): a = f'<span class="sa-card-art sa-card-photo" aria-hidden="true" style="background-image:url(/img/cities/{slug}-1-sm.webp)"></span>'
    else: a = f'<span class="sa-card-art" aria-hidden="true"><i style="background:{col}"></i></span>'
    return m.group(1) + a
h = re.sub(r'(<a href="/neighborhoods/([a-z-]+)" class="sa-card"[^>]*>)', art, h)
h = re.sub(r'All \d+ SoCal Cities', f'All {N} SoCal Cities', h)
h = re.sub(r'covers \d+ SoCal cities', f'covers {N} SoCal cities', h)
h = re.sub(r'<h1>\d+ SoCal Cities\.', f'<h1>{N} SoCal Cities.', h)
h = re.sub(r'id="saCounter">\d+ cities<', f'id="saCounter">{N} cities<', h)
h = h.replace('<p>Find your city below. Each page has real local market data, median prices, days on market, schools, top sub-areas, and what makes that specific city worth knowing.</p>',
              '<p>Pick your city on the map or search for it. Every city has its own page with real home values and a monthly payment estimate.</p>')
open(p, 'w').write(h)

# ---- sitemap ----
p = os.path.join(PUB, 'sitemap.xml'); x = open(p).read(); today = datetime.date.today().isoformat(); add = []
for s in gen:
    loc = f'https://jessetek.net/neighborhoods/{s}'
    if loc + '<' not in x: add.append(f'  <url><loc>{loc}</loc><lastmod>{today}</lastmod><changefreq>monthly</changefreq><priority>0.6</priority></url>')
if add:
    x = x.replace('</urlset>', '\n'.join(add) + '\n</urlset>'); open(p, 'w').write(x)

# ---- "all cities" link on the hand-written guides ----
fixed = 0
for s in M:
    f = os.path.join(G.GDIR, s + '.html')
    if not os.path.exists(f) or G.is_generated(f): continue
    t = open(f).read(); t2 = re.sub(r'View all \d+ SoCal cities I cover →', 'See every city I cover on the map →', t)
    if t2 != t: open(f, 'w').write(t2); fixed += 1
print(f'service areas: {len(cards)} cards added, {N} cities total | sitemap +{len(add)} | guide links fixed: {fixed}')
