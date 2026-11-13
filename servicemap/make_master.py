#!/usr/bin/env python3
"""Decide which places are on the map.

Rule (Jesse, 2026-11-13): the map is the area of his original Google Maps screenshot, nothing beyond it.
FRAME below was measured from that screenshot (Burbank and Glendale at the top left, Gardena on the left edge,
Corona and Jurupa Valley on the right edge, San Clemente at the bottom).
A place is on the map when:
  - it is an incorporated city, or an unincorporated community with 15,000+ people (2020 Census), AND
  - its Census internal point is inside the frame, OR at least 35% of its area is inside the frame
    (this keeps Los Angeles and cities the screenshot's edge cuts through, like Jurupa Valley).
Candidates and their outlines come from the wider survey (master_v2_192.json + tiger_outlines.json).
Output: master.json"""
import json, os, random
HERE = os.path.dirname(os.path.abspath(__file__))
FRAME = (-118.365, 33.402, -117.478, 34.291)   # west, south, east, north
CAND = json.load(open(os.path.join(HERE, 'master_v2_192.json')))
T = json.load(open(os.path.join(HERE, 'tiger_outlines.json')))
def inring(x, y, r):
    hit = False; j = len(r) - 1
    for i in range(len(r)):
        xi, yi = r[i]; xj, yj = r[j]
        if (yi > y) != (yj > y) and x < (xj - xi) * (y - yi) / (yj - yi) + xi: hit = not hit
        j = i
    return hit
def polys(g): return g['coordinates'] if g['type'] == 'MultiPolygon' else [g['coordinates']]
def inside(x, y, g): return any(inring(x, y, p[0]) and not any(inring(x, y, h) for h in p[1:]) for p in polys(g))
def inframe(x, y): return FRAME[0] <= x <= FRAME[2] and FRAME[1] <= y <= FRAME[3]
M = {}; cut = []
for s, c in CAND.items():
    if s not in T: cut.append(c['name']); continue          # Sherman Oaks: outside the frame anyway
    o = T[s]; g = o['geo']
    xs = [p[0] for pl in polys(g) for p in pl[0]]; ys = [p[1] for pl in polys(g) for p in pl[0]]
    random.seed(s); pts = []
    while len(pts) < 400:
        x = random.uniform(min(xs), max(xs)); y = random.uniform(min(ys), max(ys))
        if inside(x, y, g): pts.append((x, y))
    inn = [p for p in pts if inframe(*p)]; frac = len(inn) / len(pts)
    if not (inframe(o['lon'], o['lat']) or frac >= 0.35): cut.append(c['name']); continue
    c = dict(c); c['in_frame'] = round(frac, 2)
    if not inframe(o['lon'], o['lat']):                      # label goes where the city actually shows on the map
        c['label'] = [round(sum(p[0] for p in inn) / len(inn), 5), round(sum(p[1] for p in inn) / len(inn), 5)]
    M[s] = c
json.dump(M, open(os.path.join(HERE, 'master.json'), 'w'), indent=1, ensure_ascii=False)
json.dump({'frame': FRAME}, open(os.path.join(HERE, 'frame.json'), 'w'))
import collections
print(len(M), 'places on the map |', dict(collections.Counter(v['kind'] for v in M.values())), '|', dict(collections.Counter(v['county'] for v in M.values())))
print('edge places kept by the 35% rule:', sorted((v['name'], v['in_frame']) for v in M.values() if 'label' in v))
print('cut off (%d):' % len(cut), sorted(cut))
