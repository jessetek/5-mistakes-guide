#!/usr/bin/env python3
"""Third photo pass (2026-11-13): city photos picked by eye from the city's own Wikimedia Commons category
(fetch_commons_category.py contact sheets) or, for two small communities, a Commons search for the place name.
Each pick's Commons title and description were checked for the right place; license must be CC BY, CC BY-SA, CC0 or PD.
Saves public/img/cities/<slug>-1.webp (1600 px) and -sm.webp (800 px) and records the credit for /photo-credits.
Run:  python3 servicemap/pick_commons_category.py   then build_guides.py, seo_pass.py and build_credits.py"""
import io, json, os, re, sys, time, urllib.parse, urllib.request
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__)); OUT = os.path.join(HERE, '..', 'public', 'img', 'cities')
CP = os.path.join(HERE, 'photo_credits.json'); CR = json.load(open(CP))
PICKS = {  # slug: (Commons file, caption, alt text, vertical focus 0 top .. 1 bottom)
    'baldwin-park': ('In-n-Out Burger Store 1 original replica - 3.jpg', 'In-N-Out Burger Store 1 replica', 'The replica of the first In-N-Out Burger stand in Baldwin Park.', .55),
    'bradbury': ('Bradbury CA sign.jpg', 'City of Bradbury', 'The City of Bradbury entrance sign with the foothills behind it.', .5),
    'chino-hills': ('Chino Hills Community Center 01.jpg', 'Chino Hills Community Center', 'The Chino Hills Community Center.', .55),
    'commerce': ('View of Los Angeles Skyline from Commerce, California (14517769445).jpg', 'Commerce', 'A view across the homes of Commerce toward downtown Los Angeles.', .6),
    'el-monte': ('Arroyo High School 2011.jpg', 'Arroyo High School', 'Pine trees and the front of Arroyo High School in El Monte.', .5),
    'florence-graham': ('Florence-Graham, California.jpg', 'Compton Avenue', 'Shops and parked cars along Compton Avenue in Florence-Graham.', .82),
    'fountain-valley': ('Mile Square Park.jpg', 'Mile Square Regional Park', 'The lake and trees at Mile Square Regional Park in Fountain Valley.', .5),
    'hawthorne': ('Chips Diner, April 2024.jpg', 'Chips', 'The Googie style Chips diner and its tall sign in Hawthorne.', .5),
    'la-habra': ('Photograph of Sonora High School in La Habra, California.jpg', 'Sonora High School', 'The Sonora High School gym building in La Habra.', .5),
    'lawndale': ('LawndaleLibrary1.jpg', 'Lawndale Library', 'The Lawndale Library with bird of paradise plants in front.', .5),
    'montclair': ('Montclair Transcenter, March 2025.jpg', 'Montclair Transcenter', 'The arch sculpture at the Montclair Transcenter.', .5),
    'rowland-heights': ('Schabarum Regional Park (Mar 2014) 01.JPG', 'Schabarum Regional Park', 'The entrance sign at Schabarum Regional Park in Rowland Heights.', .5),
    'sherman-oaks': ('La Reina Theater, Sherman Oaks.jpg', 'La Reina Theater', 'The streamline front of the old La Reina Theater on Ventura Boulevard in Sherman Oaks.', .5),
    'walnut': ('Mt. Sac Valley Pan.jpg', 'Mt. San Antonio College, Walnut', 'The Mt. San Antonio College campus and the hills of Walnut.', .5),
}
UA = {'User-Agent': 'JessetekCityGuides/1.0 (jesse@jessetek.net; static site build, low volume)'}
OKLIC = re.compile(r'^(cc0|public domain|pd|cc by(-sa)? [1-4]\.\d)', re.I)
def raw(u):
    for i in range(3):
        try: return urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=90).read()
        except Exception as e: print('  retry', str(e)[:60]); time.sleep(4 + i * 4)
    return None
def clean(s): return re.sub(r'\s+', ' ', re.sub('<[^>]+>', '', s or '')).strip()
only = sys.argv[1:]
for slug, (f, cap, alt, fy) in PICKS.items():
    if only and slug not in only: continue
    dst = os.path.join(OUT, slug + '-1.webp')
    if os.path.exists(dst) and CR.get(slug) and CR[slug][0].get('title') == f: continue
    r = json.loads(raw('https://commons.wikimedia.org/w/api.php?format=json&action=query&prop=imageinfo&iiprop=url|size|extmetadata&iiurlwidth=1920&titles=' + urllib.parse.quote('File:' + f)))
    i = list(r['query']['pages'].values())[0]['imageinfo'][0]; m = i['extmetadata']
    lic = clean(m.get('LicenseShortName', {}).get('value', '')); assert OKLIC.match(lic), (slug, lic)
    b = raw(i['thumburl']) if i['width'] > 1920 and i['width'] / i['height'] < 1.92 else raw(i['url'])  # wide panoramas: original so the crop keeps 1000 px height
    if not b: print('FAIL', slug); continue
    img = Image.open(io.BytesIO(b)).convert('RGB'); w0, h0 = img.size; tw = min(w0, int(h0 * 1.6)); th = min(h0, int(w0 / 1.6))
    x = (w0 - tw) // 2; y = int((h0 - th) * fy)
    img = img.crop((x, y, x + tw, y + th))
    big = img.copy(); big.thumbnail((1600, 1000)); big.save(dst, 'WEBP', quality=80, method=6)
    sm = img.copy(); sm.thumbnail((800, 500)); sm.save(dst.replace('.webp', '-sm.webp'), 'WEBP', quality=78, method=6)
    CR[slug] = [{'file': slug + '-1.webp', 'caption': cap, 'alt': alt, 'title': f, 'author': clean(m.get('Artist', {}).get('value', ''))[:80] or 'Unknown',
                 'license': lic, 'licurl': m.get('LicenseUrl', {}).get('value', ''), 'page': i['descriptionurl'], 'desc': clean(m.get('ImageDescription', {}).get('value', ''))[:200],
                 'source': 'commons-category-2026-11-13'}]
    json.dump(CR, open(CP, 'w'), indent=1, ensure_ascii=False); print('ok', slug, big.size, lic, '|', CR[slug][0]['author'], '|', CR[slug][0]['desc'][:110])
