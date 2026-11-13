"""One place that says where each city outline comes from.
Cities and unincorporated communities: U.S. Census Bureau TIGER boundaries (tiger_outlines.json), the official ones.
Sherman Oaks is a Los Angeles neighborhood, which the Census does not draw, so it comes from OpenStreetMap (outlines.json)."""
import json, os
HERE = os.path.dirname(os.path.abspath(__file__))
def load():
    O = json.load(open(os.path.join(HERE, 'tiger_outlines.json')))
    osm = json.load(open(os.path.join(HERE, 'outlines.json')))
    for slug in ('sherman-oaks',):
        if slug in osm: O[slug] = dict(osm[slug], source='openstreetmap')
    return O
