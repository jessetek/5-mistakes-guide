#!/usr/bin/env python3
"""Official city and CDP boundaries for the service area map, from the U.S. Census Bureau
TIGER/Line Shapefiles, 2026 edition (boundaries as of January 1, 2026, Boundary and Annexation Survey).

Why this replaced fetch_tiger.py (TIGERweb, simplified one city at a time): simplifying each city on its own
moved shared borders differently on each side, which left 239 hairline overlaps between neighbors. Here the
135 places are simplified together with mapshaper, which keeps every shared border as one line (0 overlaps).

Simplification: Douglas-Peucker, 6 metre tolerance (about one screen pixel at the map's closest zoom).
Check: every simplified outline matches the full-resolution Census outline at 99.4% or better (area overlap).

Run:  python3 servicemap/fetch_tiger_line.py      (needs node + npx; downloads about 10 MB into servicemap/_cache/)
Out:  servicemap/tiger2026_outlines.json, same format as tiger_outlines.json
"""
import json, os, subprocess, urllib.request, zipfile
HERE = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(HERE, '_cache'); os.makedirs(CACHE, exist_ok=True)
YEAR = 2026
URL = f'https://www2.census.gov/geo/tiger/TIGER{YEAR}/PLACE/tl_{YEAR}_06_place.zip'
TOL = 6
M = json.load(open(os.path.join(HERE, 'master.json')))
zp = os.path.join(CACHE, os.path.basename(URL))
if not os.path.exists(zp):
    urllib.request.urlretrieve(URL, zp)
zipfile.ZipFile(zp).extractall(CACHE)
shp = os.path.join(CACHE, f'tl_{YEAR}_06_place.shp')
ids = ','.join(repr(c['geoid']) for c in M.values() if c['kind'] in ('city', 'cdp'))
tmp = os.path.join(CACHE, 'places.json')
subprocess.run(['npx', '--yes', 'mapshaper', shp, '-filter', f'[{ids}].indexOf(GEOID) > -1',
                '-filter-fields', 'GEOID,NAMELSAD,ALAND,AWATER,INTPTLAT,INTPTLON',
                '-simplify', 'dp', f'interval={TOL}', 'keep-shapes',
                '-o', 'format=geojson', 'precision=0.00001', tmp], check=True)
by = {f['properties']['GEOID']: f for f in json.load(open(tmp))['features']}
T = {}; missing = []
for s, c in M.items():
    if c['kind'] not in ('city', 'cdp'): continue
    f = by.get(c['geoid'])
    if not f: missing.append(s); continue
    p = f['properties']
    T[s] = {'geo': f['geometry'], 'lat': float(p['INTPTLAT']), 'lon': float(p['INTPTLON']), 'aland': p['ALAND'], 'awater': p['AWATER'],
            'geoid': p['GEOID'], 'census_name': p['NAMELSAD'], 'kind': c['kind'], 'source': f'census-tiger-line-{YEAR}'}
json.dump(T, open(os.path.join(HERE, 'tiger2026_outlines.json'), 'w'), separators=(',', ':'))
print(len(T), 'outlines | missing:', missing)
