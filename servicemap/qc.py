#!/usr/bin/env python3
"""One-shot QC for the service area map and its city guides. Exit 1 on any failure.
Run:  python3 servicemap/qc.py"""
import collections, glob, json, math, os, re, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import build_guides as G
from outlines_all import load
PUB = G.PUB; fails = []
def check(name, ok, detail=''):
    print(('PASS  ' if ok else 'FAIL  ') + name + (('  ' + str(detail)) if detail and not ok else ''))
    if not ok: fails.append(name)
D = json.load(open(os.path.join(PUB, 'data', 'service-area.json'))); F = D['features']; O = load(); M = G.M
slugs = [f['properties']['slug'] for f in F]
check('map has every city in the master list', sorted(slugs) == sorted(M), set(M) ^ set(slugs))
FR = D['frame']
def _infr(f):
    c = f['properties']['center']; return FR[0] <= c[0] <= FR[2] and FR[1] <= c[1] <= FR[3]
check('every label point is inside the screenshot frame', all(_infr(f) for f in F), [f['properties']['slug'] for f in F if not _infr(f)])
check('every map city has a guide page', all(os.path.exists(os.path.join(G.GDIR, s + '.html')) for s in slugs))
check('every city has its own color', len(set(f['properties']['color'] for f in F)) == len(F))
def ra(r):
    k = math.cos(math.radians(sum(p[1] for p in r) / len(r))) * 111320.0
    pts = [(p[0] * k, p[1] * 110540.0) for p in r]
    return abs(sum(pts[i][0] * pts[i + 1][1] - pts[i + 1][0] * pts[i][1] for i in range(len(pts) - 1))) / 2
def polys(g): return g['coordinates'] if g['type'] == 'MultiPolygon' else [g['coordinates']]
worst = 0; openr = 0
for f in F:
    o = O[f['properties']['slug']]
    for p in polys(f['geometry']):
        for r in p: openr += r[0] != r[-1]
    if 'aland' in o:
        got = sum(ra(p[0]) - sum(ra(h) for h in p[1:]) for p in polys(f['geometry']))
        worst = max(worst, abs(got - (o['aland'] + o['awater'])) / (o['aland'] + o['awater']) * 100)
check('outlines match the Census area within 2 percent (worst %.2f)' % worst, worst < 2)
check('all outline rings are closed', openr == 0)
def inring(x, y, r):
    hit = False; j = len(r) - 1
    for i in range(len(r)):
        xi, yi = r[i]; xj, yj = r[j]
        if (yi > y) != (yj > y) and x < (xj - xi) * (y - yi) / (yj - yi) + xi: hit = not hit
        j = i
    return hit
out = [f['properties']['slug'] for f in F if not any(inring(*f['properties']['center'], p[0]) and not any(inring(*f['properties']['center'], h) for h in p[1:]) for p in polys(f['geometry']))]
check('every label point sits inside its city', not out, out)
pages = sorted(glob.glob(os.path.join(G.GDIR, '*.html'))); gen = [p for p in pages if G.is_generated(p)]
offmap = [os.path.basename(p)[:-5] for p in pages if os.path.basename(p)[:-5] not in M]
check('%d guide pages (%d generated, %d hand-written, %d of those west of the map frame)' % (len(pages), len(gen), len(pages) - len(gen), len(offmap)), len(pages) == len(M) + len(offmap) and not any(G.is_generated(os.path.join(G.GDIR, s + '.html')) for s in offmap))
T = collections.Counter(); bad = []
for p in gen:
    h = open(p).read(); s = os.path.basename(p)[:-5]
    t = re.search(r'<title>(.*?)</title>', h).group(1); d = re.search(r'<meta name="description" content="([^"]*)"', h).group(1); T[t] += 1
    body = h[h.index('<!-- ===================== PAGE HERO'):h.index('<!-- ===================== FOOTER')]
    body_copy = re.sub(r'<a href="/neighborhoods/[a-z-]+" class="hub-dot[^>]*></a>', '', body)   # the ranking dots name every city
    if re.search(r'—|–|&mdash;|&ndash;|&#8212;|&#8211;', body): bad.append((s, 'dash'))
    if not 110 <= len(d) <= 165: bad.append((s, 'description length', len(d)))
    if not 30 <= len(t) <= 70: bad.append((s, 'title length', len(t)))
    if len(re.findall(r'<h1', h)) != 1: bad.append((s, 'h1'))
    if f'href="https://jessetek.net/neighborhoods/{s}"' not in h: bad.append((s, 'canonical'))
    if re.search(r'bilingual|guarantee|Spanish', body, re.I): bad.append((s, 'banned word'))
    if M[s]['name'] != 'Downey' and re.search(r'Downey(?! Rd)', body_copy) and 'downey' not in G.neighbors(s) and 'Downey Unified' not in body_copy: bad.append((s, 'template text'))
    for u in re.findall(r'(?:href|src)="(/[^"#?]*)', h):
        if u.startswith('//') or u == '/' or u.startswith('/api/'): continue
        fs = os.path.join(PUB, u.lstrip('/'))
        if not (os.path.exists(fs) or os.path.exists(fs + '.html') or os.path.exists(os.path.join(fs, 'index.html')) or u in ('/zoom', '/contact')): bad.append((s, 'broken link', u))
check('generated pages: copy rules, meta, canonical, links', not bad, bad[:6])
check('generated page titles are unique', max(T.values()) == 1)
sa = open(os.path.join(PUB, 'service-areas.html')).read()
check('Service Areas page has a card for every guide', len(re.findall(r'class="sa-card"', sa)) == len(pages) and all(f'data-svc-city="{s}"' in sa for s in M))
check('Service Areas headline count is right', f'<h1>{len(pages)} SoCal Cities.' in sa)
sm = open(os.path.join(PUB, 'sitemap.xml')).read()
check('sitemap lists every guide and nothing removed', all(f'/neighborhoods/{s}<' in sm for s in M) and len(re.findall(r'/neighborhoods/[a-z-]+<', sm)) == len(pages))
v = set(re.findall(r'kb\.css\?v=(\d+)', sa + ''.join(open(p).read() for p in pages)))
check('one stylesheet version on these pages', len(v) == 1, v)
vals = [G.zhvi(s) for s in M if G.zhvi(s)]
check('home values are plausible', all(250000 < z['now'] < 8000000 and (not z['y1'] or abs(G.pct(z['now'], z['y1'])) < 15) for z in vals))
print('\n%d failed' % len(fails)); sys.exit(1 if fails else 0)
