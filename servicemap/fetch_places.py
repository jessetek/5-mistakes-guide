#!/usr/bin/env python3
"""Real places for every city guide, from OpenStreetMap (Overpass API): parks, trails and nature, things to do,
places to eat and drink, shopping, libraries, colleges. Downloads the whole coverage area in tiles into
places_raw/ (resumable). places.py then keeps the ones that sit inside each city's official boundary.
Run:  python3 servicemap/fetch_places.py"""
import json, os, time, urllib.parse, urllib.request
HERE = os.path.dirname(os.path.abspath(__file__)); RAW = os.path.join(HERE, 'places_raw'); os.makedirs(RAW, exist_ok=True)
W, S, E, N = -118.72, 33.40, -117.46, 34.30     # the map frame plus the hand-written guides to its west
STEP = 0.105
ENDPOINTS = ['https://overpass.openstreetmap.fr/api/interpreter', 'https://overpass-api.de/api/interpreter']   # the French mirror is the fast one
# two lighter questions per tile: outdoor places with their outlines (to measure acres), then everything else as points
Q1 = '''[out:json][timeout:110];
(
  nwr["leisure"~"^(park|nature_reserve|golf_course|garden|dog_park|stadium|water_park|marina)$"]["name"]({b});
  nwr["natural"="beach"]["name"]({b});
);
out tags geom qt;'''
Q2 = '''[out:json][timeout:110];
(
  nwr["tourism"~"^(museum|attraction|zoo|theme_park|gallery|viewpoint|aquarium)$"]["name"]({b});
  nwr["amenity"~"^(restaurant|cafe|ice_cream|bar|pub|library|theatre|cinema|marketplace|arts_centre|college|university|brewery|food_court)$"]["name"]({b});
  nwr["shop"~"^(mall|bakery|coffee)$"]["name"]({b});
  nwr["craft"="brewery"]["name"]({b});
  nwr["historic"]["wikidata"]["name"]({b});
);
out tags center qt;'''
tiles = []
y = S
while y < N - 1e-9:
    x = W
    while x < E - 1e-9:
        tiles.append((round(y, 3), round(x, 3), round(min(y + STEP, N), 3), round(min(x + STEP, E), 3))); x += STEP
    y += STEP
jobs = [(i, k, q) for i in range(len(tiles)) for k, q in (('a', Q1), ('b', Q2))]
import threading, queue
todo = queue.Queue()
for j in jobs:
    if not os.path.exists(os.path.join(RAW, 'tile_%03d%s.json' % (j[0], j[1]))): todo.put(j)
print(todo.qsize(), 'requests to make,', len(jobs) - todo.qsize(), 'already saved', flush=True)
lock = threading.Lock(); bad = []
def work(ep):
    while True:
        try: i, k, q = todo.get_nowait()
        except queue.Empty: return
        f = os.path.join(RAW, 'tile_%03d%s.json' % (i, k)); ok = False
        for attempt in range(5):
            try:
                r = urllib.request.urlopen(urllib.request.Request(ep, data=urllib.parse.urlencode({'data': q.replace('{b}', '%s,%s,%s,%s' % tiles[i])}).encode(), headers={'User-Agent': 'city-guide-places-build/1.0'}), timeout=150)
                d = json.loads(r.read())
                if 'elements' not in d: raise ValueError('no elements')
                json.dump(d['elements'], open(f, 'w')); ok = True
                with lock: print('tile %d%s ok %d (%s)' % (i, k, len(d['elements']), ep.split('/')[2]), flush=True)
                break
            except Exception as ex:
                time.sleep(10 + attempt * 12)
        if not ok:
            with lock: bad.append((i, k)); print('tile %d%s FAILED on %s' % (i, k, ep.split('/')[2]), flush=True)
            todo.put((i, k, q)) if len(bad) < 400 else None
        time.sleep(2.5)
ts = [threading.Thread(target=work, args=(ep,)) for ep in ENDPOINTS]
[t.start() for t in ts]; [t.join() for t in ts]
print('done. files:', len(os.listdir(RAW)), 'of', len(jobs))
