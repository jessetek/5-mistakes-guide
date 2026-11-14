"""One place that says where each city outline comes from.
Cities and unincorporated communities (CDPs): U.S. Census Bureau TIGER/Line 2026 boundaries (tiger2026_outlines.json,
built by fetch_tiger_line.py with shared borders kept as one line). Older TIGERweb set: tiger_outlines.json (fallback only).
Sherman Oaks is a Los Angeles neighborhood, which the Census does not draw, so it comes from OpenStreetMap (outlines.json)."""
import json, os
HERE = os.path.dirname(os.path.abspath(__file__))
def load():
    O = json.load(open(os.path.join(HERE, 'tiger_outlines.json')))
    new = os.path.join(HERE, 'tiger2026_outlines.json')
    if os.path.exists(new): O.update(json.load(open(new)))
    osm = json.load(open(os.path.join(HERE, 'outlines.json')))
    for slug in ('sherman-oaks',):
        if slug in osm: O[slug] = dict(osm[slug], source='openstreetmap')
    return O
