#!/usr/bin/env python3
"""City photos picked by eye from commons_candidates.json, each one checked against its Commons title and description
to confirm it really shows that city. Saves to public/img/cities/<slug>-1.webp and records the credit.
Run:  python3 servicemap/pick_commons.py"""
import io, json, os, re, time, urllib.request
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__)); OUT = os.path.join(HERE, '..', 'public', 'img', 'cities')
C = json.load(open(os.path.join(HERE, 'commons_candidates.json'))); CP = os.path.join(HERE, 'photo_credits.json'); CR = json.load(open(CP))
ALL = dict(json.load(open(os.path.join(HERE, 'master_v2_192.json')))); ALL.update(json.load(open(os.path.join(HERE, 'master.json'))))
PICKS = {  # slug: (candidate number, caption, alt text)
    'irwindale': (2, 'Our Lady of Guadalupe Mission', 'The stone Our Lady of Guadalupe Mission church in Irwindale.'),
    'laguna-beach': (1, 'Laguna Beach', 'The beach and bluffs at Laguna Beach.'),
    'hawaiian-gardens': (2, 'The Gardens Casino', 'The outside of the Gardens Casino in Hawaiian Gardens.'),
    'lennox': (2, 'Lennox', 'A vintage Lennox sign on a building in Lennox.'),
    'villa-park': (0, 'Villa Park Civic Center', 'City Hall at the Villa Park Civic Center.'),
    'westmont': (4, 'Woodcrest School', 'Woodcrest School on 109th Street in Westmont.'),
    'south-el-monte': (2, 'San Gabriel River', 'The San Gabriel River from the Peck Road bridge at South El Monte.'),
    'temescal-valley': (0, 'Temescal Valley', 'Homes in Temescal Valley with the Santa Ana Mountains behind them.'),
    'gardena': (2, 'Gardena', 'A Japanese style building in Gardena.'),
    'bell-gardens': (4, 'Veterans Park', 'Veterans Park in Bell Gardens.'),
}
UA = {'User-Agent': 'CityGuideBuild/1.0 (static site build; low volume)'}
def raw(u):
    for i in range(3):
        try: return urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=60).read()
        except Exception as e: print('  retry', str(e)[:60]); time.sleep(6 + i * 6)
    return None
for slug, (k, cap, alt) in PICKS.items():
    dst = os.path.join(OUT, slug + '-1.webp')
    if os.path.exists(dst): continue
    c = C[slug][k]; time.sleep(1.2)
    b = raw(re.sub(r'/\d+px-', '/1920px-', c['thumb'])) if c['w'] > 1920 else None
    b = b or raw(c['thumb'])
    if not b: print('FAIL', slug); continue
    img = Image.open(io.BytesIO(b)).convert('RGB'); w0, h0 = img.size; tw = min(w0, int(h0 * 1.6)); th = min(h0, int(w0 / 1.6))
    img = img.crop(((w0 - tw) // 2, (h0 - th) // 2, (w0 - tw) // 2 + tw, (h0 - th) // 2 + th))
    big = img.copy(); big.thumbnail((1600, 1000)); big.save(dst, 'WEBP', quality=80, method=6)
    sm = img.copy(); sm.thumbnail((800, 500)); sm.save(dst.replace('.webp', '-sm.webp'), 'WEBP', quality=78, method=6)
    CR[slug] = [{'file': slug + '-1.webp', 'caption': cap, 'alt': alt, 'title': c['file'][5:], 'author': c['author'] or 'Unknown', 'license': c['license'], 'licurl': c['licurl'], 'page': c['page'], 'desc': c['desc']}]
    json.dump(CR, open(CP, 'w'), indent=1, ensure_ascii=False); print('ok', slug, big.size)
