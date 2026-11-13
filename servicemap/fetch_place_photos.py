#!/usr/bin/env python3
"""Real photos of the parks, museums and landmarks named on each city guide.
A place qualifies only when OpenStreetMap links it to a Wikidata item, that item has a photo (P18),
and Wikimedia Commons says the photo is freely licensed. Up to 6 per city.
Saves public/img/places/<city>-<n>.webp and place_photos.json (file, author, license, source page). Resumable.
Run:  python3 servicemap/fetch_place_photos.py"""
import io, json, os, re, time, urllib.parse, urllib.request
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__)); OUT = os.path.join(HERE, '..', 'public', 'img', 'places'); os.makedirs(OUT, exist_ok=True)
PL = json.load(open(os.path.join(HERE, 'places.json')))
P = os.path.join(HERE, 'place_photos.json'); done = json.load(open(P)) if os.path.exists(P) else {}
UA = {'User-Agent': 'city-guide-research/1.0'}
OKLIC = re.compile(r'^(cc0|public domain|pd|cc by(-sa)? [1-4]\.\d)', re.I)
BAD = re.compile(r'map|logo|seal|sign\b|plaque|diagram|\b1[89]\d\d\b|\.svg|\.png|\.tif', re.I)
def raw(u, t=60):
    for i in range(6):
        try: return urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=t).read()
        except urllib.error.HTTPError as e:
            if e.code == 404: return None
            time.sleep((int(e.headers.get('Retry-After') or 15) if e.code == 429 else 4) + i * 6)
        except Exception: time.sleep(3 + i * 4)
    return None
def api(u):
    time.sleep(0.6); b = raw(u); return json.loads(b) if b else {}
def clean(s): return re.sub(r'\s+', ' ', re.sub('<[^>]+>', '', s or '')).strip()

# 1. which places: the ones the page names first
want = {}
for slug, c in PL.items():
    picks = []
    for g, n in (('fun', 5), ('historic', 3), ('parks', 4), ('outdoors', 2), ('learn', 2)):
        picks += [p for p in c.get(g, [])[:12] if p.get('wd')][:n]
    seen = set(); want[slug] = [p for p in picks if not (p['wd'] in seen or seen.add(p['wd']))][:9]
ids = sorted({p['wd'] for v in want.values() for p in v})
CP = os.path.join(HERE, 'place_photos_lookup.json'); look = json.load(open(CP)) if os.path.exists(CP) else {}
todo = [q for q in ids if q not in look]
for i in range(0, len(todo), 50):
    d = api('https://www.wikidata.org/w/api.php?action=wbgetentities&format=json&props=claims&ids=' + '|'.join(todo[i:i + 50]))
    for q in todo[i:i + 50]:
        try: look[q] = {'file': d['entities'][q]['claims']['P18'][0]['mainsnak']['datavalue']['value']}
        except Exception: look[q] = {}
    json.dump(look, open(CP, 'w'))
files = sorted({v['file'] for v in look.values() if v.get('file') and 'lic' not in v})
for i in range(0, len(files), 40):
    d = api('https://commons.wikimedia.org/w/api.php?action=query&format=json&prop=imageinfo&iiprop=url|size|extmetadata|mime&iiurlwidth=960&titles=' + urllib.parse.quote('|'.join('File:' + f for f in files[i:i + 40])))
    norm = {n['to']: n['from'] for n in d.get('query', {}).get('normalized', [])}
    for pg in d.get('query', {}).get('pages', {}).values():
        src = norm.get(pg['title'], pg['title'])[5:]
        try:
            info = pg['imageinfo'][0]; m = info.get('extmetadata', {})
            rec = {'lic': clean(m.get('LicenseShortName', {}).get('value', '')), 'licurl': m.get('LicenseUrl', {}).get('value', ''), 'author': clean(m.get('Artist', {}).get('value', ''))[:80],
                   'thumb': info.get('thumburl'), 'w': info['width'], 'h': info['height'], 'mime': info.get('mime'), 'page': info.get('descriptionurl')}
        except Exception: rec = {'lic': ''}
        for v in look.values():
            if v.get('file') in (src, src.replace('_', ' ')): v.update(rec)
    json.dump(look, open(CP, 'w'))
# 2. download
n = 0
for slug, picks in sorted(want.items()):
    if slug in done: continue
    got = []
    for p in picks:
        v = look.get(p['wd'], {})
        if len(got) >= 6: break
        if not v.get('thumb') or not OKLIC.match(v.get('lic', '')) or v.get('mime') != 'image/jpeg' or v['w'] < 900 or v['w'] < v['h'] or BAD.search(v['file']): continue
        time.sleep(1.0); b = raw(v['thumb'])
        if not b: continue
        try: img = Image.open(io.BytesIO(b)).convert('RGB')
        except Exception: continue
        w0, h0 = img.size; tw = min(w0, int(h0 * 1.5)); th = min(h0, int(w0 / 1.5))
        img = img.crop(((w0 - tw) // 2, (h0 - th) // 2, (w0 - tw) // 2 + tw, (h0 - th) // 2 + th)); img.thumbnail((720, 480))
        fn = '%s-%d.webp' % (slug, len(got) + 1); img.save(os.path.join(OUT, fn), 'WEBP', quality=76, method=6)
        got.append({'name': p['name'], 'kind': p['kind'], 'file': fn, 'title': v['file'], 'author': v.get('author') or 'Unknown', 'license': v['lic'], 'licurl': v.get('licurl', ''), 'page': v.get('page', '')}); n += 1
    done[slug] = got; json.dump(done, open(P, 'w'), indent=1, ensure_ascii=False); print(slug, len(got), [g['name'] for g in got], flush=True)
print('saved', n, 'photos |', sum(1 for v in done.values() if v), 'cities have at least one')
