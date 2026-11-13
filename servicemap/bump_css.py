#!/usr/bin/env python3
"""Point the map and city guide pages at the current kb.css. Run after build_guides.py.  python3 servicemap/bump_css.py 18"""
import glob, os, re, sys
PUB = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'public'); v = sys.argv[1]; n = 0
for f in glob.glob(PUB + '/neighborhoods/*.html') + [PUB + '/service-areas.html']:
    s = open(f).read(); t = re.sub(r'kb\.css\?v=\d+', 'kb.css?v=' + v, s)
    if t != s: open(f, 'w').write(t); n += 1
print('kb.css v=%s on %d pages' % (v, n))
