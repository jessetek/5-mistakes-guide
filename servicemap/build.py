#!/usr/bin/env python3
"""Build public/data/service-area.json for the interactive service area map.

Inputs:  master.json (every city on the map), outlines (see outlines_all.py), Zillow + cities.json for the card.
Output:  one GeoJSON FeatureCollection, one feature per city, each with its guide URL and its own color.
Run:     python3 servicemap/build.py
"""
import colorsys, json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from outlines_all import load as load_outlines
OUT = os.path.join(HERE, '..', 'public', 'data', 'service-area.json')
M = json.load(open(os.path.join(HERE, 'master.json')))
O = load_outlines()
C = json.load(open(os.path.join(HERE, '..', 'seo-engine', 'data', 'cities.json')))
import build_guides as G
# cities on the ocean: their legal boundary runs out to sea
COAST = set('malibu santa-monica los-angeles el-segundo manhattan-beach hermosa-beach redondo-beach torrance palos-verdes-estates rancho-palos-verdes long-beach seal-beach huntington-beach newport-beach laguna-beach dana-point san-clemente'.split())
KB = ['#FDE99B', '#D1EEF9', '#9BD8A9', '#B8CAF5', '#9ED4EF', '#F7C9B6']   # the Jessetek guide colors

def pastel(i):
    h = (0.09 + i * 0.61803398875) % 1.0
    r, g, b = colorsys.hls_to_rgb(h, 0.80, 0.72)
    return '#%02X%02X%02X' % (round(r * 255), round(g * 255), round(b * 255))

def short(n): return ('$%.2fM' % (n / 1e6)).replace('0M', 'M') if n >= 1e6 else '$%.0fK' % (n / 1e3)
def rnd(c): return [round(c[0], 5), round(c[1], 5)] if isinstance(c[0], (int, float)) else [rnd(x) for x in c]
def rings(geo): return [p[0] for p in (geo['coordinates'] if geo['type'] == 'MultiPolygon' else [geo['coordinates']])]
def area(ring): return abs(sum(ring[i][0] * ring[i + 1][1] - ring[i + 1][0] * ring[i][1] for i in range(len(ring) - 1))) / 2

order = C.get('farm_order', []) + sorted(s for s in M if s not in C.get('farm_order', []))

# ---- colors: one per city, all in the Jessetek pastel family, and never close to a neighbor's ----
import math
def hue_of(hexc):
    r, g, b = (int(hexc[i:i + 2], 16) / 255 for i in (1, 3, 5)); return colorsys.rgb_to_hls(r, g, b)[0]
def palette(n):
    out = []
    for i in range(n):
        h = (0.09 + i * 0.61803398875) % 1.0
        l = (0.78, 0.84, 0.81)[i % 3]; sat = (0.74, 0.66, 0.82)[(i // 3) % 3]   # three tints so 190 pastels do not blur together
        r, g, b = colorsys.hls_to_rgb(h, l, sat); out.append('#%02X%02X%02X' % (round(r * 255), round(g * 255), round(b * 255)))
    return out
def near(slug, n=6):
    x, y = O[slug]['lon'], O[slug]['lat']; k = math.cos(math.radians(y))
    return [t for _, t in sorted((math.hypot((O[t]['lon'] - x) * k, O[t]['lat'] - y), t) for t in M if t != slug and t in O)[:n]]
def hdist(a, b): d = abs(hue_of(a) - hue_of(b)); return min(d, 1 - d)
pool = [c for c in palette(len(order) + 60) if c not in KB]
NB = {s: set(near(s)) for s in order if s in O}
for s in list(NB):                      # make "neighbor" mutual: if A is near B, B is near A
    for t in NB[s]: NB.setdefault(t, set()).add(s)
color = {s: KB[i] for i, s in enumerate(order[:len(KB)])}
for s in order[len(KB):]:
    taken = [color[t] for t in NB.get(s, ()) if t in color]
    best = max(pool, key=lambda c: (round(min([hdist(c, t) for t in taken] or [1]), 3), -pool.index(c)))
    color[s] = best; pool.remove(best)
FRAME = json.load(open(os.path.join(HERE, 'frame.json')))['frame']   # the area of Jesse's original screenshot
feats = []; missing = []
for slug in order:
    c = M[slug]
    if slug not in O: missing.append(slug); continue
    o = O[slug]; geo = o['geo']
    big = max(rings(geo), key=area)
    xs = [p[0] for r in rings(geo) for p in r]; ys = [p[1] for r in rings(geo) for p in r]
    # label point: the Census internal point when we have one, else the middle of the biggest piece
    if c.get('label'): center = c['label']                 # a city the frame cuts through: label where it shows
    elif o.get('source') == 'census-tiger': center = [round(o['lon'], 5), round(o['lat'], 5)]
    else: center = [round((min(p[0] for p in big) + max(p[0] for p in big)) / 2, 5), round((min(p[1] for p in big) + max(p[1] for p in big)) / 2, 5)]
    old = C['cities'].get(slug)
    z = G.zhvi(slug)
    if old and old.get('median_price'): value = 'Median ' + old['median_price']
    elif z: value = 'Typical value ' + short(z['now'])
    else: value = ''
    feats.append({'type': 'Feature', 'properties': {'slug': slug, 'name': c['name'], 'county': c['county'], 'value': value,
                  'url': '/neighborhoods/' + slug, 'color': color[slug], 'center': center,
                  'pop': (G.pop(slug) or {}).get('est', 0),
                  # labels beside the frame edge grow inward so the edge does not cut the name
                  'anchor': 'left' if center[0] - FRAME[0] < 0.05 else 'right' if FRAME[2] - center[0] < 0.05 else 'center',
                  'bbox': [round(min(xs), 5), round(min(ys), 5), round(max(xs), 5), round(max(ys), 5)],
                  'size': round(sum(area(r) for r in rings(geo)) * 1e4, 3),
                  # coastal = the legal boundary runs out to sea, so the map draws its outline under the water
                  'coastal': slug in COAST},
                  'geometry': {'type': geo['type'], 'coordinates': rnd(geo['coordinates'])}})
# big cities first, so a small city inside or beside a big one sits on top and stays clickable
feats.sort(key=lambda f: -f['properties']['size'])
for i, f in enumerate(feats): f['id'] = i + 1
out = {'type': 'FeatureCollection', 'credit': 'City boundaries: U.S. Census Bureau', 'frame': FRAME, 'features': feats}
json.dump(out, open(OUT, 'w'), separators=(',', ':'), ensure_ascii=False)
print('wrote', os.path.relpath(OUT), '|', len(feats), 'cities |', os.path.getsize(OUT) // 1024, 'KB | missing:', missing,
      '| unique colors:', len(set(f['properties']['color'] for f in feats)))
