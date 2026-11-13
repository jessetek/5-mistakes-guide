#!/usr/bin/env python3
"""Turns the raw OpenStreetMap download (places_raw/) into a tidy list of real places per city.
A place belongs to a city when its location falls inside the city's official boundary.
Groups: parks (with size in acres), outdoors (beaches, nature reserves, golf), fun (museums, attractions,
theaters, cinemas, malls, markets), learn (libraries, colleges), historic (only landmarks with a Wikipedia or
Wikidata entry), eat (restaurants, cafes, bars, bakeries; chains are told apart from local spots by their brand tag).
Writes places.json.  Run:  python3 servicemap/places.py"""
import collections, json, math, os, re
HERE = os.path.dirname(os.path.abspath(__file__))
ALL = dict(json.load(open(os.path.join(HERE, 'master_v2_192.json')))); ALL.update(json.load(open(os.path.join(HERE, 'master.json'))))
T = json.load(open(os.path.join(HERE, 'tiger_outlines.json')))
GUIDES = {f[:-5] for f in os.listdir(os.path.join(HERE, '..', 'public', 'neighborhoods')) if f.endswith('.html')}
CITIES = [s for s in ALL if s in T and (s in GUIDES or s in json.load(open(os.path.join(HERE, 'master.json'))))]

def inring(x, y, r):
    hit = False; j = len(r) - 1
    for i in range(len(r)):
        xi, yi = r[i]; xj, yj = r[j]
        if (yi > y) != (yj > y) and x < (xj - xi) * (y - yi) / (yj - yi) + xi: hit = not hit
        j = i
    return hit
def polys(g): return g['coordinates'] if g['type'] == 'MultiPolygon' else [g['coordinates']]
def inside(x, y, g): return any(inring(x, y, p[0]) and not any(inring(x, y, h) for h in p[1:]) for p in polys(g))
def ring_acres(pts):
    if len(pts) < 4: return 0.0
    k = math.cos(math.radians(sum(p['lat'] for p in pts) / len(pts))) * 111320.0
    xy = [(p['lon'] * k, p['lat'] * 110540.0) for p in pts]
    return abs(sum(xy[i][0] * xy[i + 1][1] - xy[i + 1][0] * xy[i][1] for i in range(len(xy) - 1))) / 2 / 4046.86

GONE = re.compile(r'\bclosed\b|\bformer\b|\bvacant\b|coming soon|http', re.I)
def clean(n):
    n = re.sub(r'\s+', ' ', n.replace('–', '-').replace('—', '-').replace('’', "'")).strip()
    if GONE.search(n): return ''                                        # mapped as closed or former: leave it out
    n = re.sub(r'\s*[\(\[]?[\u1100-\u11FF\u2E80-\u9FFF\uAC00-\uD7AF\u0E00-\u0E7F\u0600-\u06FF][^\)\]]*[\)\]]?\s*$', '', n).strip()   # keep the English half of a two-language name
    if re.search(r'[\u1100-\u11FF\u2E80-\u9FFF\uAC00-\uD7AF\u0E00-\u0E7F\u0600-\u06FF]', n): return ''
    n = re.sub(r'^(.+?) Branch County of Los Angeles Public Library$', r'\1 Library', n)
    n = re.sub(r'^County of Los Angeles Public Library - (.+)$', r'\1 Library', n)
    if n.isupper() and len(n) > 5: n = ' '.join(w if len(w) <= 2 else w.capitalize() for w in n.split())
    n = n.replace('\u2018', "'").replace('\u00AE', '').replace('\u2026', '').replace(' \u00B7 ', ' ').strip()
    if re.search(r'[^\x20-\x7E\u00C0-\u024F\u1E00-\u1EFF\u00B0\u02BB]', n) or re.search(r'^Department |Graduate School|Building \d', n): return ''
    n = re.sub(r'^(.+?) Branch (City of \w+|Orange County|San Bernardino County|Riverside County) (Public )?Library$', r'\1 Library', n)
    if n[:1].islower() and n[1:2].islower() and '.' not in n.split()[0]: n = n[0].upper() + n[1:]
    return n if len(n) <= 60 else ''
CUISINE = {'mexican': 'Mexican', 'pizza': 'Pizza', 'burger': 'Burgers', 'chinese': 'Chinese', 'japanese': 'Japanese', 'sushi': 'Sushi', 'thai': 'Thai', 'vietnamese': 'Vietnamese',
           'korean': 'Korean', 'italian': 'Italian', 'american': 'American', 'sandwich': 'Sandwiches', 'chicken': 'Chicken', 'coffee_shop': 'Coffee', 'indian': 'Indian',
           'mediterranean': 'Mediterranean', 'seafood': 'Seafood', 'barbecue': 'Barbecue', 'bbq': 'Barbecue', 'ramen': 'Ramen', 'breakfast': 'Breakfast', 'steak_house': 'Steakhouse',
           'ice_cream': 'Ice cream', 'donut': 'Donuts', 'bubble_tea': 'Boba tea', 'tacos': 'Tacos', 'peruvian': 'Peruvian', 'salvadoran': 'Salvadoran', 'cuban': 'Cuban',
           'filipino': 'Filipino', 'greek': 'Greek', 'french': 'French', 'hawaiian': 'Hawaiian', 'asian': 'Asian', 'noodle': 'Noodles', 'bakery': 'Bakery', 'dessert': 'Dessert',
           'middle_eastern': 'Middle Eastern', 'lebanese': 'Lebanese', 'persian': 'Persian', 'armenian': 'Armenian', 'taiwanese': 'Taiwanese', 'hot_pot': 'Hot pot', 'juice': 'Juice',
           'poke': 'Poke', 'wings': 'Wings', 'latin_american': 'Latin American', 'spanish': 'Spanish', 'german': 'German', 'vegan': 'Vegan', 'vegetarian': 'Vegetarian', 'diner': 'Diner',
           'brunch': 'Brunch', 'tex-mex': 'Tex-Mex', 'hot_dog': 'Hot dogs', 'fish_and_chips': 'Fish and chips', 'cajun': 'Cajun', 'soul_food': 'Soul food', 'guatemalan': 'Guatemalan',
           'argentinian': 'Argentinian', 'brazilian': 'Brazilian', 'caribbean': 'Caribbean', 'ethiopian': 'Ethiopian', 'indonesian': 'Indonesian', 'cambodian': 'Cambodian', 'tea': 'Tea'}

def classify(t):
    le, am, to, sh = t.get('leisure'), t.get('amenity'), t.get('tourism'), t.get('shop')
    if le in ('park', 'garden', 'dog_park'): return 'parks', {'park': 'Park', 'garden': 'Garden', 'dog_park': 'Dog park'}[le]
    if le == 'nature_reserve' or t.get('boundary') == 'protected_area': return 'outdoors', 'Nature area'
    if t.get('natural') == 'beach': return 'outdoors', 'Beach'
    if le == 'golf_course': return 'outdoors', 'Golf course'
    if le == 'marina': return 'outdoors', 'Marina'
    if le in ('stadium', 'water_park'): return 'fun', {'stadium': 'Stadium', 'water_park': 'Water park'}[le]
    if to in ('museum', 'zoo', 'theme_park', 'gallery', 'aquarium', 'attraction', 'viewpoint'):
        return 'fun', {'museum': 'Museum', 'zoo': 'Zoo', 'theme_park': 'Theme park', 'gallery': 'Gallery', 'aquarium': 'Aquarium', 'attraction': 'Attraction', 'viewpoint': 'Viewpoint'}[to]
    if am in ('theatre', 'cinema', 'arts_centre', 'marketplace'): return 'fun', {'theatre': 'Theater', 'cinema': 'Movie theater', 'arts_centre': 'Arts center', 'marketplace': 'Market'}[am]
    if sh == 'mall': return 'fun', 'Shopping center'
    if am == 'library': return 'learn', 'Library'
    if am in ('college', 'university'): return 'learn', 'College'
    if am in ('restaurant', 'cafe', 'ice_cream', 'bar', 'pub', 'brewery', 'food_court') or sh in ('bakery', 'coffee') or t.get('craft') == 'brewery':
        kind = {'cafe': 'Cafe', 'ice_cream': 'Ice cream', 'bar': 'Bar', 'pub': 'Pub', 'brewery': 'Brewery', 'food_court': 'Food court'}.get(am) or {'bakery': 'Bakery', 'coffee': 'Coffee'}.get(sh) or ('Brewery' if t.get('craft') == 'brewery' else 'Restaurant')
        return 'eat', kind
    if t.get('historic') and (t.get('wikidata') or t.get('wikipedia')) and t['historic'] not in ('memorial', 'wayside_cross', 'boundary_stone', 'milestone'): return 'historic', 'Landmark'
    return None, None

def main():
    raw = {}
    d = os.path.join(HERE, 'places_raw')
    for f in sorted(os.listdir(d)):
        for e in json.load(open(os.path.join(d, f))): raw[(e['type'], e['id'])] = e
    boxes = {}
    for s in CITIES:
        xs = [p[0] for pl in polys(T[s]['geo']) for p in pl[0]]; ys = [p[1] for pl in polys(T[s]['geo']) for p in pl[0]]
        boxes[s] = (min(xs), min(ys), max(xs), max(ys))
    order = sorted(CITIES, key=lambda s: (boxes[s][2] - boxes[s][0]) * (boxes[s][3] - boxes[s][1]))
    out = {s: collections.defaultdict(dict) for s in CITIES}; skipped = collections.Counter()
    for e in raw.values():
        t = e.get('tags', {}); name = clean(t.get('name', ''))
        if not name or len(name) < 3 or t.get('disused') or t.get('abandoned') or t.get('access') == 'private' or any(k.startswith(('disused:', 'abandoned:', 'was:', 'razed:', 'demolished:')) for k in t): skipped['closed or unnamed'] += 1; continue
        group, kind = classify(t)
        if not group: continue
        acres = 0.0
        if 'geometry' in e: acres = ring_acres(e['geometry'])
        elif 'members' in e: acres = sum(ring_acres(m['geometry']) for m in e['members'] if m.get('role') in ('outer', '') and m.get('geometry'))
        if 'center' in e: lon, lat = e['center']['lon'], e['center']['lat']
        elif 'bounds' in e: lon, lat = (e['bounds']['minlon'] + e['bounds']['maxlon']) / 2, (e['bounds']['minlat'] + e['bounds']['maxlat']) / 2
        elif 'lon' in e: lon, lat = e['lon'], e['lat']
        else: continue
        for s in order:
            b = boxes[s]
            if b[0] <= lon <= b[2] and b[1] <= lat <= b[3] and inside(lon, lat, T[s]['geo']):
                key = name.lower()
                p = out[s][group].get(key)
                if p: p['acres'] = round(p['acres'] + acres, 1); break       # the same park drawn in several pieces
                cz = [CUISINE.get(c.strip().lower()) for c in t.get('cuisine', '').split(';')]
                out[s][group][key] = {'name': name, 'kind': kind, 'lon': round(lon, 5), 'lat': round(lat, 5), 'acres': round(acres, 1),
                                      'chain': bool(t.get('brand') or t.get('brand:wikidata')), 'cuisine': [c for c in cz if c][:2],
                                      'known': bool(t.get('wikidata') or t.get('wikipedia')), 'wd': t.get('wikidata', '') if group != 'eat' else '', 'commons': t.get('wikimedia_commons', '') if group != 'eat' else '',
                                      'detail': sum(1 for k in ('website', 'contact:website', 'phone', 'contact:phone', 'opening_hours', 'addr:street') if t.get(k))}
                break
    final = {s: {g: sorted(v.values(), key=lambda p: (-p['acres'], -p['known'], -p['detail'], p['name'])) for g, v in out[s].items()} for s in CITIES}
    json.dump(final, open(os.path.join(HERE, 'places.json'), 'w'), separators=(',', ':'), ensure_ascii=False)
    tot = collections.Counter()
    for s in final:
        for g, v in final[s].items(): tot[g] += len(v)
    print(len(raw), 'raw places |', dict(tot), '| cities with parks:', sum(1 for s in final if final[s].get('parks')), 'of', len(final), '| with places to eat:', sum(1 for s in final if final[s].get('eat')))
    return final

if __name__ == '__main__':
    f = main()
    d = f.get('downey', {})
    print('Downey parks:', [(p['name'], p['acres']) for p in d.get('parks', [])[:8]]); print('Downey fun:', [(p['name'], p['kind']) for p in d.get('fun', [])[:8]])
    print('Downey eat:', len(d.get('eat', [])), 'local', sum(1 for p in d.get('eat', []) if not p['chain']), [p['name'] for p in d.get('eat', []) if not p['chain']][:8])
