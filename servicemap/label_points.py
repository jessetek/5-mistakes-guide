"""Tap points for small or oddly shaped places. Run with a Python that has shapely:  python servicemap/label_points.py

The Census internal point can sit a few hundred meters from a city's edge (Bell, Cerritos, South San Jose Hills).
At the zoom a phone opens on, that is one or two pixels, so a finger on the name could land in the neighbor.
For those places the label goes to the point deepest inside the city (pole of inaccessibility of its biggest piece).
Writes label_points.json, which build.py reads. Cities with a hand-placed label (frame edge) are left alone."""
import json, os
from shapely.geometry import shape, Point
from shapely.ops import polylabel
HERE = os.path.dirname(os.path.abspath(__file__))
D = json.load(open(os.path.join(HERE, '..', 'public', 'data', 'service-area.json')))
M = json.load(open(os.path.join(HERE, 'master.json')))
T = json.load(open(os.path.join(HERE, 'tiger2026_outlines.json')))   # the Census internal points
KM = 100   # degrees to km, close enough at this latitude for a threshold
out = {}
for f in D['features']:
    p = f['properties']; s = p['slug']
    if M.get(s, {}).get('label') or s not in T: continue
    census = Point(T[s]['lon'], T[s]['lat'])
    g = shape(f['geometry']); g = max(g.geoms, key=lambda x: x.area) if g.geom_type == 'MultiPolygon' else g
    d = g.boundary.distance(census) * KM
    if d >= 0.4: continue
    pl = polylabel(g, 0.0003); dp = g.boundary.distance(pl) * KM
    if dp > d * 1.5: out[s] = [round(pl.x, 5), round(pl.y, 5)]
json.dump(out, open(os.path.join(HERE, 'label_points.json'), 'w'), indent=1, sort_keys=True)
print(len(out), 'labels moved inward:', ' '.join(sorted(out)))
