#!/usr/bin/env python3
"""Second-source outlines for verification only: OpenStreetMap's boundary for every place on the map.
Writes osm_check.json. The map itself uses the Census boundaries; this file exists to check them."""
import json, os, time, urllib.parse, urllib.request
HERE = os.path.dirname(os.path.abspath(__file__))
M = json.load(open(os.path.join(HERE, 'master.json')))
P = os.path.join(HERE, 'osm_check.json'); out = json.load(open(P)) if os.path.exists(P) else {}
T = json.load(open(os.path.join(HERE, 'tiger_outlines.json')))
for slug, c in M.items():
    if slug in out: continue
    t = T[slug]
    for q in ({'city': c['name'], 'state': 'California', 'country': 'USA'}, {'q': c['name'] + ', California'}, {'q': c['name'] + ', ' + c['county'].replace('LA ', 'Los Angeles ') + ', California'}):
        q = dict(q, format='jsonv2', polygon_geojson=1, polygon_threshold=0.00008, limit=6)
        g = None
        for attempt in range(4):
            try:
                r = json.load(urllib.request.urlopen(urllib.request.Request('https://nominatim.openstreetmap.org/search?' + urllib.parse.urlencode(q), headers={'User-Agent': 'city-outline-map-build/1.0'}), timeout=40))
                cands = [x for x in r if x.get('geojson', {}).get('type') in ('Polygon', 'MultiPolygon') and abs(float(x['lon']) - t['lon']) < 0.12 and abs(float(x['lat']) - t['lat']) < 0.12]
                g = cands[0] if cands else None; break
            except Exception as e: time.sleep(8 + attempt * 8)
        time.sleep(1.15)
        if g: break
    out[slug] = {'geo': g['geojson'], 'osm': g.get('osm_type', '') + str(g.get('osm_id', ''))} if g else None
    print('ok' if g else 'NONE', slug, flush=True); json.dump(out, open(P, 'w'))
print('done', sum(1 for v in out.values() if v), 'of', len(M))
