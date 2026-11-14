#!/usr/bin/env python3
"""Second photo pass (2026-11-13): city photos taken from the images each city's own English Wikipedia
article uses, kept only when Wikimedia Commons lists a free license (CC BY, CC BY-SA, CC0 or public domain).
Candidates: wiki_lead_candidates.json (title, author, license and description as Commons lists them).
Every pick below was looked at by eye and its Commons description checked for the right place.
Saves public/img/cities/<slug>-1.webp (1600 px) and -sm.webp (800 px) and records the credit for /photo-credits.
Run:  python3 servicemap/pick_wiki_lead.py   then build_guides.py and build_credits.py"""
import io, json, os, re, time, urllib.request
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__)); OUT = os.path.join(HERE, '..', 'public', 'img', 'cities')
C = json.load(open(os.path.join(HERE, 'wiki_lead_candidates.json'))); CP = os.path.join(HERE, 'photo_credits.json'); CR = json.load(open(CP))
PICKS = {  # slug: (candidate number, caption, alt text, vertical focus 0 top .. 1 bottom)
    'altadena': (2, 'Lake Avenue', 'Lake Avenue running north through Altadena toward the San Gabriel Mountains.', .5),
    'arcadia': (2, 'Los Angeles County Arboretum', 'The central fountain at the Los Angeles County Arboretum in Arcadia, with the San Gabriel Mountains behind.', .5),
    'bell': (1, 'James George Bell House', 'The historic James George Bell House on Pine Avenue in Bell.', .5),
    'carson': (4, 'Leo F. Cain Library, CSU Dominguez Hills', 'The Leo F. Cain Library at California State University, Dominguez Hills in Carson.', .5),
    'chino': (4, 'Moyse Building', 'The historic Moyse Building in Chino.', .5),
    'claremont': (0, 'Claremont Station', 'The Claremont train station.', .5),
    'compton': (0, 'Compton High School', 'The Compton High School sign in front of the school building.', .5),
    'corona': (2, 'Santa Fe Depot', 'The 1937 Santa Fe train station in Corona.', .5),
    'duarte': (1, 'City of Hope', 'The Helford Clinical Research Hospital at City of Hope in Duarte.', .5),
    'east-los-angeles': (1, 'Whittier Boulevard', 'An old theater building on Whittier Boulevard in East Los Angeles.', .45),
    'eastvale': (1, 'Eastvale', 'Homes and a tree lined street in Eastvale.', .5),
    'inglewood': (1, "Randy's Donuts", "Randy's Donuts and its giant donut sign in Inglewood.", .35),
    'la-crescenta-montrose': (2, 'Holy Redeemer Catholic Church', 'Holy Redeemer Catholic Church in Montrose.', .55),
    'la-palma': (1, 'La Palma Civic Center', 'The La Palma Civic Center sign and City Hall.', .6),
    'la-verne': (1, 'University of La Verne', "Founders Hall at the University of La Verne.", .5),
    'maywood': (1, 'Maywood City Hall', 'Maywood City Hall.', .55),
    'monterey-park': (4, 'Monterey Park Civic Center', 'The Monterey Park Civic Center.', .55),
    'pomona': (6, 'Antique Row, Downtown Pomona', 'The Antique Row arch over a street in downtown Pomona.', .5),
    'seal-beach': (2, 'Red Car Museum', 'The restored Pacific Electric Red Car at the museum in Seal Beach.', .55),
    'sierra-madre': (2, 'Sierra Madre Wistaria', "The giant wisteria vine in Sierra Madre in bloom.", .45),
    'south-pasadena': (4, 'Mission Street', 'Historic storefronts on Mission Street in South Pasadena.', .5),
    'upland': (2, 'Upland Memorial Park', 'Oak trees and lawn at Upland Memorial Park.', .5),
    'vernon': (4, 'Vernon City Hall', 'Vernon City Hall.', .55),
    'west-carson': (1, 'Harbor-UCLA Medical Center', 'Harbor-UCLA Medical Center in West Carson.', .5),
    'willowbrook': (1, 'Willowbrook Station', 'The Metro station platform at Willowbrook.', .55),
}
UA = {'User-Agent': 'JessetekCityGuides/1.0 (jesse@jessetek.net; static site build, low volume)'}
def raw(u):
    for i in range(3):
        try: return urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=90).read()
        except Exception as e: print('  retry', str(e)[:60]); time.sleep(4 + i * 4)
    return None
for slug, (k, cap, alt, fy) in PICKS.items():
    dst = os.path.join(OUT, slug + '-1.webp')
    c = C[slug][k]
    if os.path.exists(dst) and CR.get(slug) and CR[slug][0].get('title') == c['file'][5:]: continue
    time.sleep(0.8)
    b = raw(re.sub(r'/\d+px-', '/1920px-', c['thumb'])) if c['w'] > 1920 else raw(c['url'])
    if not b: print('FAIL', slug); continue
    img = Image.open(io.BytesIO(b)).convert('RGB'); w0, h0 = img.size; tw = min(w0, int(h0 * 1.6)); th = min(h0, int(w0 / 1.6))
    x = (w0 - tw) // 2; y = int((h0 - th) * fy)
    img = img.crop((x, y, x + tw, y + th))
    big = img.copy(); big.thumbnail((1600, 1000)); big.save(dst, 'WEBP', quality=80, method=6)
    sm = img.copy(); sm.thumbnail((800, 500)); sm.save(dst.replace('.webp', '-sm.webp'), 'WEBP', quality=78, method=6)
    CR[slug] = [{'file': slug + '-1.webp', 'caption': cap, 'alt': alt, 'title': c['file'][5:], 'author': c['author'] or 'Unknown',
                 'license': c['license'], 'licurl': c['licurl'], 'page': c['page'], 'desc': c['desc'], 'source': 'wikipedia-lead-2026-11-13'}]
    json.dump(CR, open(CP, 'w'), indent=1, ensure_ascii=False); print('ok', slug, big.size)
