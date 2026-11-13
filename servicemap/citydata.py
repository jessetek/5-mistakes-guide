#!/usr/bin/env python3
"""Everything we know about each city, from public sources only. Used by build_guides.py and hub.py.

Sources (all files in this folder):
  zillow_zhvi.json     Zillow Home Value Index, typical value, all homes, monthly, 10 years
  zillow_extra.json    Zillow: value by bedroom count, houses vs condos, lower and upper price tiers, and observed rents
  census_pop.json      U.S. Census Bureau population estimates (cities)
  census_2020_pop.json 2020 Census counts of people and homes (cities and unincorporated communities)
  cde_schools.json     California Department of Education public school directory (active schools, with coordinates)
  tiger_outlines.json  official Census boundaries (used to decide which schools sit inside which city)
Nothing here is estimated or invented. A city with no figure for something simply has None.
"""
import json, math, os

HERE = os.path.dirname(os.path.abspath(__file__))
def _j(n): return json.load(open(os.path.join(HERE, n)))
M = _j('master.json')                      # places on the map
ALL = dict(_j('master_v2_192.json')); ALL.update(M)   # also the hand-written guides just west of the map
Z = _j('zillow_zhvi.json'); ZX = _j('zillow_extra.json'); P = _j('census_pop.json'); C20 = _j('census_2020_pop.json')
T = _j('tiger_outlines.json'); SCH = _j('cde_schools.json')
PLACES = _j('places.json') if os.path.exists(os.path.join(HERE, 'places.json')) else {}
WIKI = _j('wiki.json') if os.path.exists(os.path.join(HERE, 'wiki.json')) else {}
COUNTY_Z = {'LA County': 'Los Angeles County', 'Orange County': 'Orange County', 'Ventura County': 'Ventura County',
            'San Bernardino County': 'San Bernardino County', 'Riverside County': 'Riverside County'}


def _key(slug):
    c = ALL[slug]
    return c['name'].replace('ñ', 'n') + '|' + COUNTY_Z[c['county']]


def history(slug):
    """Monthly typical home value, oldest first: [(date, value), ...] or []."""
    if ALL[slug]['kind'] == 'neighborhood': return []
    s = Z['cities'].get(_key(slug)) or {}
    return sorted(s.items())


def extra(slug, k):
    if ALL[slug]['kind'] == 'neighborhood': return None
    return (ZX.get(k, {}).get('cities', {}) or {}).get(_key(slug))


def population(slug):
    c = ALL[slug]
    for k in (c['name'] + ' city', c['name'] + ' town'):
        if k in P and c['kind'] == 'city': return {'n': P[k]['est'], 'label': '%d estimate' % P[k]['year']}
    if c.get('pop2020'): return {'n': c['pop2020'], 'label': '2020 Census'}
    return None


GAZ = _j('census_gazetteer.json')
def land_m2(slug):
    """Land area in square meters, from the U.S. Census Gazetteer."""
    n = ALL[slug]['name']
    for k in (n + ' city', n + ' town', n + ' CDP'):
        if k in GAZ and GAZ[k].get('aland'): return GAZ[k]['aland']
    return None


def homes2020(slug):
    g = ALL[slug].get('geoid'); return (C20.get(g) or {}).get('homes2020') if g else None


# ---------- schools: a school belongs to a city when its coordinates fall inside the city's official boundary ----------
def _inring(x, y, r):
    hit = False; j = len(r) - 1
    for i in range(len(r)):
        xi, yi = r[i]; xj, yj = r[j]
        if (yi > y) != (yj > y) and x < (xj - xi) * (y - yi) / (yj - yi) + xi: hit = not hit
        j = i
    return hit
def _polys(g): return g['coordinates'] if g['type'] == 'MultiPolygon' else [g['coordinates']]
def _inside(x, y, g): return any(_inring(x, y, p[0]) and not any(_inring(x, y, h) for h in p[1:]) for p in _polys(g))

LEVELS = {'Elementary Schools (Public)': 'elementary', 'Intermediate/Middle Schools (Public)': 'middle', 'Junior High Schools (Public)': 'middle',
          'High Schools (Public)': 'high', 'K-12 Schools (Public)': 'k12'}
_SCHOOLS = None
def _schools():
    global _SCHOOLS
    if _SCHOOLS is not None: return _SCHOOLS
    out = {s: [] for s in ALL if s in T}
    boxes = {}
    for s in out:
        xs = [p[0] for pl in _polys(T[s]['geo']) for p in pl[0]]; ys = [p[1] for pl in _polys(T[s]['geo']) for p in pl[0]]
        boxes[s] = (min(xs), min(ys), max(xs), max(ys))
    # small cities first, so a school in a city surrounded by Los Angeles is not credited to Los Angeles
    order = sorted(out, key=lambda s: (boxes[s][2] - boxes[s][0]) * (boxes[s][3] - boxes[s][1]))
    for r in SCH:
        lev = LEVELS.get(r['SOCType'])
        if not lev or r.get('Virtual') in ('F', 'Exclusively Virtual') or r['School'] in ('', 'No Data'): continue
        try: x, y = float(r['Longitude']), float(r['Latitude'])
        except ValueError: continue
        for s in order:
            b = boxes[s]
            if b[0] <= x <= b[2] and b[1] <= y <= b[3] and _inside(x, y, T[s]['geo']):
                # official names sometimes carry a long dash; the site's copy rule allows only a plain hyphen
                nm = r['School'].replace('\u2013', '-').replace('\u2014', '-')
                out[s].append({'name': nm, 'level': lev, 'district': r['District'].replace('\u2013', '-').replace('\u2014', '-'), 'grades': r['GSoffered'],
                               'charter': r['Charter'] == 'Y', 'lon': round(x, 5), 'lat': round(y, 5)})
                break
    _SCHOOLS = out; return out


def schools(slug): return _schools().get(slug, [])


# ---------- one record per city ----------
def record(slug):
    h = history(slug)
    def back(months):
        return h[-1 - months][1] if len(h) > months else None
    val = h[-1][1] if h else None
    beds = {n: (extra(slug, 'bed%d' % n) or {}).get('now') for n in (1, 2, 3, 4, 5)}
    rent = extra(slug, 'rent')
    sc = schools(slug)
    return {'slug': slug, 'name': ALL[slug]['name'], 'county': ALL[slug]['county'], 'kind': ALL[slug]['kind'], 'on_map': slug in M,
            'value': val, 'value_date': h[-1][0] if h else None, 'y1': back(12), 'y5': back(60), 'y10': back(120), 'history': h,
            'beds': {n: v for n, v in beds.items() if v}, 'house': (extra(slug, 'house') or {}).get('now'), 'condo': (extra(slug, 'condo') or {}).get('now'),
            'low': (extra(slug, 'low') or {}).get('now'), 'high': (extra(slug, 'high') or {}).get('now'),
            'rent': rent.get('now') if rent else None, 'rent_y1': rent.get('y1') if rent else None, 'rent_date': rent.get('date') if rent else None,
            'places': PLACES.get(slug, {}), 'wiki': WIKI.get(slug, {}), 'cuisines': _cuisines(PLACES.get(slug, {})),
            'pop': population(slug), 'homes2020': homes2020(slug), 'schools': sc,
            'districts': _districts(sc)}


def _districts(sc):
    """Districts that run this city's schools, the one with the most campuses first.
    A charter school lists whoever authorized it, which can be a district far away, so charters do not count here."""
    import collections
    c = collections.Counter(x['district'] for x in sc if not x['charter'] and 'County Office' not in x['district'])
    if not c: c = collections.Counter(x['district'] for x in sc)
    rows = sorted(c.items(), key=lambda kv: (-kv[1], kv[0]))
    return [d for i, (d, n) in enumerate(rows) if i == 0 or n >= 2]      # one stray campus is not a district that serves the city


def _cuisines(pl):
    import collections
    c = collections.Counter()
    for p in pl.get('eat', []):
        for z in p['cuisine'][:1]: c[z] += 1
    return [(k, n) for k, n in c.most_common() if n >= 2]


_REC = {}
def get(slug):
    if slug not in _REC: _REC[slug] = record(slug)
    return _REC[slug]


def ranking(key='value'):
    """Cities on the map that have this figure, highest first: [(slug, value), ...]."""
    rows = [(s, get(s)[key]) for s in M if get(s)[key]]
    return sorted(rows, key=lambda r: -r[1])


def near(slug, n=4):
    if slug not in T: return []
    x, y = T[slug]['lon'], T[slug]['lat']; k = math.cos(math.radians(y))
    return [t for _, t in sorted((math.hypot((T[t]['lon'] - x) * k, T[t]['lat'] - y), t) for t in M if t != slug and t in T)[:n]]


if __name__ == '__main__':
    import collections
    recs = [get(s) for s in M]
    print(len(recs), 'cities on the map')
    for k in ('value', 'y10', 'house', 'condo', 'low', 'high', 'rent', 'homes2020'):
        print('  have %-9s' % k, sum(1 for r in recs if r[k]))
    print('  have bedrooms  ', sum(1 for r in recs if len(r['beds']) >= 3))
    print('  have schools   ', sum(1 for r in recs if r['schools']), '| schools placed:', sum(len(r['schools']) for r in recs))
    d = get('downey'); print('Downey:', d['value'], d['beds'], 'rent', d['rent'], 'schools', collections.Counter(s['level'] for s in d['schools']), d['districts'])
