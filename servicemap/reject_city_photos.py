#!/usr/bin/env python3
"""City lead photos reviewed by eye and turned down (hazy aerials, intersections, parking lots). Safe to rerun."""
import json, os
HERE = os.path.dirname(os.path.abspath(__file__)); P = os.path.join(HERE, 'photo_credits.json'); C = json.load(open(P))
REJECT = 'baldwin-park chino duarte fountain-valley hawthorne inglewood lawndale monterey-park north-tustin rowland-heights la-palma eastvale la-habra maywood sherman-oaks'.split()
for s in REJECT:
    if s in C: C[s] = []
    for f in (s + '-1.webp', s + '-1-sm.webp'):
        f = os.path.join(HERE, '..', 'public', 'img', 'cities', f)
        if os.path.exists(f): os.remove(f)
json.dump(C, open(P, 'w'), indent=1, ensure_ascii=False); print('kept', sum(1 for v in C.values() if v))
