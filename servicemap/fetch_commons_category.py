#!/usr/bin/env python3
"""Third photo pass (2026-11-13): for cities that still have no photo, list freely licensed landscape photos in the
city's own Wikimedia Commons category (and its direct subcategories), and save previews + contact sheets for review.
Nothing goes on the site from here; pick_commons_category.py does that after a person looks at the sheets.
Run:  python3 servicemap/fetch_commons_category.py <preview folder> slug [slug ...]"""
import io, json, os, re, sys, time, urllib.parse, urllib.request
from PIL import Image, ImageDraw
HERE = os.path.dirname(os.path.abspath(__file__)); OUT = sys.argv[1]; os.makedirs(OUT, exist_ok=True)
ALL = dict(json.load(open(os.path.join(HERE, 'master_v2_192.json')))); ALL.update(json.load(open(os.path.join(HERE, 'master.json'))))
P = os.path.join(HERE, 'commons_category_candidates.json'); out = json.load(open(P)) if os.path.exists(P) else {}
UA = {'User-Agent': 'JessetekCityGuides/1.0 (jesse@jessetek.net; static site build, low volume)'}
OKLIC = re.compile(r'^(cc0|public domain|pd|cc by(-sa)? [1-4]\.\d)', re.I)
BAD = re.compile(r'\bmap\b|logo|seal|flag|diagram|locator|crime|protest|police|grave|cemetery|accident|crash|mugshot|portrait', re.I)
CATNAME = {'sherman-oaks': 'Sherman Oaks, Los Angeles', 'florence-graham': 'Florence-Graham, California', 'west-whittier-los-nietos': 'West Whittier-Los Nietos, California'}
API = 'https://commons.wikimedia.org/w/api.php?format=json&'
def get(q):
    for i in range(4):
        try: return json.loads(urllib.request.urlopen(urllib.request.Request(API + q, headers=UA), timeout=60).read())
        except Exception as e: time.sleep(5 + i * 5)
    return {}
def raw(u):
    for i in range(3):
        try: return urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=60).read()
        except Exception: time.sleep(5 + i * 5)
    return None
def clean(s): return re.sub(r'\s+', ' ', re.sub('<[^>]+>', '', s or '')).strip()
def members(cat, kind):
    r = get('action=query&list=categorymembers&cmlimit=200&cmtype=' + kind + '&cmtitle=' + urllib.parse.quote('Category:' + cat))
    return [m['title'] for m in r.get('query', {}).get('categorymembers', [])]
for slug in sys.argv[2:]:
    if slug in out: continue
    cat = CATNAME.get(slug, ALL[slug]['name'] + ', California')
    files = members(cat, 'file'); subs = members(cat, 'subcat')
    for sc in subs[:25]:
        if re.search(r'maps|logos|seals|flags|people|births|deaths', sc, re.I): continue
        time.sleep(0.3); files += [f for f in members(sc[9:], 'file') if f not in files]
    cands = []
    for k in range(0, len(files), 40):
        time.sleep(0.5)
        r = get('action=query&prop=imageinfo&iiprop=url|size|extmetadata|mime&iiurlwidth=1920&titles=' + urllib.parse.quote('|'.join(files[k:k + 40])))
        for pg in r.get('query', {}).get('pages', {}).values():
            try:
                i = pg['imageinfo'][0]; m = i.get('extmetadata', {}); lic = clean(m.get('LicenseShortName', {}).get('value', ''))
                if i.get('mime') != 'image/jpeg' or not OKLIC.match(lic) or i['width'] < 1200 or i['width'] < i['height'] * 1.2 or BAD.search(pg['title']): continue
                cands.append({'file': pg['title'], 'thumb': i['thumburl'], 'url': i['url'], 'w': i['width'], 'h': i['height'], 'license': lic, 'licurl': m.get('LicenseUrl', {}).get('value', ''),
                              'author': clean(m.get('Artist', {}).get('value', ''))[:80], 'desc': clean(m.get('ImageDescription', {}).get('value', ''))[:200],
                              'cats': clean(m.get('Categories', {}).get('value', ''))[:200], 'page': i.get('descriptionurl')})
            except Exception: pass
    nm = ALL[slug]['name'].lower()
    SKIP = re.compile(r'panoramio|unsplash|us navy|usda|earthquake damage|freeway|\bca[- ]?\d+\b|interstate|exit \d|council|mayor|cropped|\bjr\b', re.I)
    def score(c):   # the city's own name in the title or description first, then size
        t = c['file'].lower(); d = c['desc'].lower()
        return (-(nm in t) * 2 - (nm in d) + (1 if SKIP.search(c['file'] + ' ' + c['desc']) else 0) * 5, -c['w'])
    allc = sorted(cands, key=score); cands = allc[:16]
    thumbs = []
    for n, c in enumerate(cands):
        time.sleep(0.4); b = raw(re.sub(r'/\d+px-', '/330px-', c['thumb']))
        try: im = Image.open(io.BytesIO(b)).convert('RGB'); im.thumbnail((400, 260)); thumbs.append((n, im))
        except Exception: thumbs.append((n, None))
    if thumbs:
        cols = 4; rows = (len(thumbs) + cols - 1) // cols; sheet = Image.new('RGB', (cols * 410, rows * 280), 'white'); d = ImageDraw.Draw(sheet)
        for n, im in thumbs:
            x, y = (n % cols) * 410, (n // cols) * 280
            if im: sheet.paste(im, (x + 5, y + 18))
            d.rectangle([x + 5, y, x + 40, y + 16], fill='black'); d.text((x + 9, y + 2), str(n), fill='white')
        sheet.save(os.path.join(OUT, slug + '.jpg'), quality=82)
    out[slug] = {'category': cat, 'files_in_category': len(files), 'cands': cands, 'all': allc}
    json.dump(out, open(P, 'w'), indent=1, ensure_ascii=False); print(slug, cat, len(files), len(cands), flush=True)
