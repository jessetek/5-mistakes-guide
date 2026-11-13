#!/usr/bin/env python3
"""For cities that still have no photo: search Wikimedia Commons for freely licensed landscape photos of the city
and save small previews for a person to review. Nothing goes on the site from here; pick_commons.py does that.
Run:  python3 servicemap/fetch_commons_candidates.py <preview folder>"""
import io, json, os, re, sys, time, urllib.parse, urllib.request
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__)); PUB = os.path.join(HERE, '..', 'public'); OUT = sys.argv[1]; os.makedirs(OUT, exist_ok=True)
ALL = dict(json.load(open(os.path.join(HERE, 'master_v2_192.json')))); ALL.update(json.load(open(os.path.join(HERE, 'master.json'))))
PP = json.load(open(os.path.join(HERE, 'place_photos.json')))
G = sorted(f[:-5] for f in os.listdir(os.path.join(PUB, 'neighborhoods')) if f.endswith('.html'))
need = [s for s in G if s in ALL and not os.path.exists(os.path.join(PUB, 'img', 'cities', s + '-1.webp')) and not any(os.path.exists(os.path.join(PUB, 'img', 'places', p['file'])) for p in PP.get(s, []))]
P = os.path.join(HERE, 'commons_candidates.json'); out = json.load(open(P)) if os.path.exists(P) else {}
UA = {'User-Agent': 'CityGuideBuild/1.0 (static site build; low volume)'}
OKLIC = re.compile(r'^(cc0|public domain|pd|cc by(-sa)? [1-4]\.\d)', re.I)
BAD = re.compile(r'map|logo|seal|flag|sign\b|plaque|diagram|locator|\b1[89]\d\d\b|\b19\d\ds?\b|station|metro|freeway|interstate|i-\d|aerial|historic|crime|fire|protest|police|grave|cemetery', re.I)
def raw(u):
    for i in range(3):
        try: return urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=40).read()
        except urllib.error.HTTPError as e: time.sleep((int(e.headers.get('Retry-After') or 12) if e.code == 429 else 4) + i * 5)
        except Exception: time.sleep(4)
    return None
def clean(s): return re.sub(r'\s+', ' ', re.sub('<[^>]+>', '', s or '')).strip()
for slug in need:
    if slug in out: continue
    name = ALL[slug]['name']; time.sleep(1.2)
    b = raw('https://commons.wikimedia.org/w/api.php?action=query&format=json&generator=search&gsrnamespace=6&gsrlimit=30&gsrsearch=' + urllib.parse.quote(f'"{name}" California filetype:bitmap') +
            '&prop=imageinfo&iiprop=url|size|extmetadata|mime&iiurlwidth=1600')
    cands = []
    for pg in sorted((json.loads(b) if b else {}).get('query', {}).get('pages', {}).values(), key=lambda p: p.get('index', 99)):
        try:
            i = pg['imageinfo'][0]; m = i.get('extmetadata', {}); lic = clean(m.get('LicenseShortName', {}).get('value', ''))
            if i.get('mime') != 'image/jpeg' or not OKLIC.match(lic) or i['width'] < 1400 or i['width'] < i['height'] * 1.25 or BAD.search(pg['title']): continue
            cands.append({'file': pg['title'], 'thumb': i['thumburl'], 'w': i['width'], 'h': i['height'], 'license': lic, 'licurl': m.get('LicenseUrl', {}).get('value', ''),
                          'author': clean(m.get('Artist', {}).get('value', ''))[:80], 'desc': clean(m.get('ImageDescription', {}).get('value', ''))[:160], 'page': i.get('descriptionurl')})
        except Exception: pass
    keep = []
    for k, c in enumerate(cands[:5]):
        time.sleep(1.0); im = raw(re.sub(r'/\d+px-', '/500px-', c['thumb']))
        if not im: continue
        try: Image.open(io.BytesIO(im)).convert('RGB').save(os.path.join(OUT, f'{slug}_{len(keep)}.jpg'), quality=80); keep.append(c)
        except Exception: pass
    out[slug] = keep; json.dump(out, open(P, 'w'), indent=1, ensure_ascii=False); print(slug, len(keep), flush=True)
print('done', sum(1 for v in out.values() if v), 'of', len(need), 'cities have candidates')
