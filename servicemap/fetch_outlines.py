#!/usr/bin/env python3
"""Fetch precise outlines for every city in servicemap/master.json. Source: OpenStreetMap (Nominatim), ODbL.
Writes servicemap/outlines.json. Run rarely: python3 servicemap/fetch_outlines.py"""
import json, os, time, urllib.request, urllib.parse
HERE = os.path.dirname(os.path.abspath(__file__))
C = json.load(open(os.path.join(HERE, 'master.json')))   # every city on the map
Q = {'sherman-oaks': {'q': 'Sherman Oaks, Los Angeles, California'}, 'hacienda-heights': {'q': 'Hacienda Heights, California'},
     'rowland-heights': {'q': 'Rowland Heights, California'}, 'la-canada-flintridge': {'q': 'La Cañada Flintridge, California'},
     'east-los-angeles': {'q': 'East Los Angeles, California'}, 'south-whittier': {'q': 'South Whittier, California'},
     'industry': {'q': 'City of Industry, California'}, 'commerce': {'q': 'Commerce, Los Angeles County, California'},
     'orange': {'q': 'Orange, Orange County, California'}, 'bell': {'q': 'Bell, Los Angeles County, California'}}
out = {}; P = os.path.join(HERE, 'outlines.json')
if os.path.exists(P): out = json.load(open(P))
for slug, c in C.items():
    if slug in out: continue
    q = {'format': 'jsonv2', 'polygon_geojson': 1, 'polygon_threshold': 0.0003, 'limit': 5}
    q.update(Q.get(slug) or {'city': c['name'], 'state': 'California', 'country': 'USA'})
    for attempt in range(4):
        try:
            r = json.load(urllib.request.urlopen(urllib.request.Request('https://nominatim.openstreetmap.org/search?' + urllib.parse.urlencode(q), headers={'User-Agent': 'city-outline-map-build/1.0'}), timeout=40))
            g = next((x for x in r if x.get('geojson', {}).get('type') in ('Polygon', 'MultiPolygon') and -119.2 < float(x['lon']) < -116.8 and 33.3 < float(x['lat']) < 34.5), None)
            if g: out[slug] = {'geo': g['geojson'], 'lat': float(g['lat']), 'lon': float(g['lon'])}; print('ok', slug, flush=True)
            else: print('NO POLY', slug, [x.get('type') for x in r], flush=True)
            break
        except Exception as e:
            print('retry', slug, e, flush=True); time.sleep(8 + attempt * 10)
    json.dump(out, open(P, 'w')); time.sleep(1.2)
print('done', len(out), 'of', len(C))
