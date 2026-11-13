#!/usr/bin/env python3
"""Download the official boundary of every place in master.json from the U.S. Census Bureau (TIGERweb),
by Census GEOID. Writes tiger_outlines.json. Run after make_master.py:  python3 servicemap/fetch_tiger.py"""
import json, os, urllib.parse, urllib.request
HERE = os.path.dirname(os.path.abspath(__file__))
M = json.load(open(os.path.join(HERE, 'master.json')))
BASE = 'https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/Places_CouSub_ConCity_SubMCD/MapServer'
TOL = 0.00006   # about 6 metres: fine enough that neighbors share the same edge
def query(layer, geoids):
    out = []
    for i in range(0, len(geoids), 20):
        w = "GEOID IN (" + ",".join("'%s'" % g for g in geoids[i:i + 20]) + ")"
        body = urllib.parse.urlencode({'where': w, 'outFields': 'NAME,BASENAME,GEOID,AREALAND,AREAWATER,INTPTLAT,INTPTLON', 'outSR': 4326,
                                       'f': 'geojson', 'geometryPrecision': 5, 'maxAllowableOffset': TOL}).encode()
        for attempt in range(4):
            try:
                r = json.loads(urllib.request.urlopen(urllib.request.Request(f'{BASE}/{layer}/query', data=body, headers={'User-Agent': 'Mozilla/5.0 (data build)'}), timeout=180).read())
                out += r['features']; break
            except Exception as e:
                if attempt == 3: raise
    return out
by = {}
for layer, kind in ((4, 'city'), (5, 'cdp')):
    for f in query(layer, [c['geoid'] for c in M.values() if c['kind'] == kind]): by[f['properties']['GEOID']] = f
T = {}; missing = []
for s, c in M.items():
    if c['kind'] == 'neighborhood': continue
    f = by.get(c['geoid'])
    if not f: missing.append(s); continue
    p = f['properties']
    T[s] = {'geo': f['geometry'], 'lat': float(p['INTPTLAT']), 'lon': float(p['INTPTLON']), 'aland': p['AREALAND'], 'awater': p['AREAWATER'],
            'geoid': p['GEOID'], 'census_name': p['NAME'], 'source': 'census-tiger'}
json.dump(T, open(os.path.join(HERE, 'tiger_outlines.json'), 'w'))
print(len(T), 'outlines | missing:', missing, '|', os.path.getsize(os.path.join(HERE, 'tiger_outlines.json')) // 1024, 'KB')
