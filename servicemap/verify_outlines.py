#!/usr/bin/env python3
"""One check per city: is the outline on the map the city's real boundary?
For each place it compares the map's outline (Census Bureau) with
  1. the Census Bureau's published land + water area for that place, and
  2. OpenStreetMap's independently drawn boundary for the same place (osm_check.json),
     as "overlap": the share of the combined area that both outlines agree on (100% = identical).
Writes outline_check.csv and prints anything under 97% overlap. Run: python3 servicemap/verify_outlines.py"""
import csv, json, math, os, random
HERE = os.path.dirname(os.path.abspath(__file__))
M = json.load(open(os.path.join(HERE, 'master.json'))); T = json.load(open(os.path.join(HERE, 'tiger_outlines.json')))
OSM = json.load(open(os.path.join(HERE, 'osm_check.json')))
D = {f['properties']['slug']: f for f in json.load(open(os.path.join(HERE, '..', 'public', 'data', 'service-area.json')))['features']}
def inring(x, y, r):
    hit = False; j = len(r) - 1
    for i in range(len(r)):
        xi, yi = r[i]; xj, yj = r[j]
        if (yi > y) != (yj > y) and x < (xj - xi) * (y - yi) / (yj - yi) + xi: hit = not hit
        j = i
    return hit
def polys(g): return g['coordinates'] if g['type'] == 'MultiPolygon' else [g['coordinates']]
def inside(x, y, g): return any(inring(x, y, p[0]) and not any(inring(x, y, h) for h in p[1:]) for p in polys(g))
def ra(r):
    k = math.cos(math.radians(sum(p[1] for p in r) / len(r))) * 111320.0
    pts = [(p[0] * k, p[1] * 110540.0) for p in r]
    return abs(sum(pts[i][0] * pts[i + 1][1] - pts[i + 1][0] * pts[i][1] for i in range(len(pts) - 1))) / 2
def area(g): return sum(ra(p[0]) - sum(ra(h) for h in p[1:]) for p in polys(g))
def bbox(g):
    xs = [p[0] for pl in polys(g) for p in pl[0]]; ys = [p[1] for pl in polys(g) for p in pl[0]]
    return min(xs), min(ys), max(xs), max(ys)
rows = []
for s in sorted(M):
    g = D[s]['geometry']; t = T[s]
    a_diff = (area(g) - (t['aland'] + t['awater'])) / (t['aland'] + t['awater']) * 100
    o = OSM.get(s); iou = land_iou = None
    if o:
        b1 = bbox(g); b2 = bbox(o['geo']); b = (min(b1[0], b2[0]), min(b1[1], b2[1]), max(b1[2], b2[2]), max(b1[3], b2[3]))
        random.seed(s); both = either = 0
        for _ in range(6000):
            x = random.uniform(b[0], b[2]); y = random.uniform(b[1], b[3])
            i1 = inside(x, y, g); i2 = inside(x, y, o['geo'])
            both += i1 and i2; either += i1 or i2
        iou = both / either * 100 if either else 0
    rows.append({'city': M[s]['name'], 'slug': s, 'kind': M[s]['kind'], 'points_in_outline': sum(len(r) for p in polys(g) for r in p),
                 'area_sq_mi': round(area(g) / 2.59e6, 2), 'census_area_sq_mi': round((t['aland'] + t['awater']) / 2.59e6, 2),
                 'area_diff_pct': round(a_diff, 2), 'overlap_with_openstreetmap_pct': round(iou, 1) if iou is not None else '',
                 'water_share_pct': round(t['awater'] / (t['aland'] + t['awater']) * 100, 1)})
w = csv.DictWriter(open(os.path.join(HERE, 'outline_check.csv'), 'w', newline=''), fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
have = [r for r in rows if r['overlap_with_openstreetmap_pct'] != '']
print(len(rows), 'cities checked | worst area difference vs Census: %.2f%%' % max(abs(r['area_diff_pct']) for r in rows))
print('compared with OpenStreetMap:', len(have), '| 99%+ overlap:', sum(1 for r in have if r['overlap_with_openstreetmap_pct'] >= 99), '| 97 to 99:', sum(1 for r in have if 97 <= r['overlap_with_openstreetmap_pct'] < 99), '| under 97:', sum(1 for r in have if r['overlap_with_openstreetmap_pct'] < 97))
print('under 97% (city, overlap, water share):', [(r['city'], r['overlap_with_openstreetmap_pct'], r['water_share_pct']) for r in sorted(have, key=lambda r: r['overlap_with_openstreetmap_pct']) if r['overlap_with_openstreetmap_pct'] < 97])
print('no OpenStreetMap outline to compare:', [r['city'] for r in rows if r['overlap_with_openstreetmap_pct'] == ''])
