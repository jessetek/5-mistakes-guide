#!/usr/bin/env python3
"""Save one freely licensed photo per city (the lead photo of its Wikipedia article, license checked on
Wikimedia Commons in fetch_wiki.py) to public/img/cities/<slug>-1.webp, for cities that have no photo yet.
Records every photo in photo_credits.json, which build_credits.py turns into the /photo-credits page.
Run:  python3 servicemap/fetch_wiki_photos.py"""
import io, json, os, re, time, urllib.request
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__)); OUT = os.path.join(HERE, '..', 'public', 'img', 'cities')
W = {k: {'image': v} for k, v in json.load(open(os.path.join(HERE, 'wiki_images.json'))).items() if 'skip' not in v}
ALL = dict(json.load(open(os.path.join(HERE, 'master_v2_192.json')))); ALL.update(json.load(open(os.path.join(HERE, 'master.json'))))
CP = os.path.join(HERE, 'photo_credits.json'); C = json.load(open(CP)) if os.path.exists(CP) else {}
BAD = re.compile(r'map|seal|logo|flag|locator|montage|collage|aerial survey|\b1[89]\d\d\b', re.I)
def fetch(u):
    for i in range(3):
        try: return urllib.request.urlopen(urllib.request.Request(u, headers={'User-Agent': 'CityGuideBuild/1.0 (static site build; low volume)'}), timeout=40).read()
        except urllib.error.HTTPError as e:
            time.sleep((int(e.headers.get('Retry-After') or 20) if e.code == 429 else 4) + i * 5)
        except Exception: time.sleep(4 + i * 4)
    return None
made = 0
for slug, w in sorted(W.items()):
    im = w.get('image')
    dst = os.path.join(OUT, slug + '-1.webp')
    if not im or os.path.exists(dst) or slug in C: continue
    if BAD.search(im['file']) or im['w'] < im['h'] * 1.15 or slug in ('vernon', 'west-carson', 'willowbrook', 'south-san-jose-hills', 'south-pasadena'): continue      # no maps, seals, collages or tall photos
    u = im.get('thumb') or im['url']
    b = fetch(u) or fetch(im['url']); time.sleep(1.1)
    if not b: print('FAIL', slug); continue
    try: img = Image.open(io.BytesIO(b)).convert('RGB')
    except Exception: print('BAD IMAGE', slug); continue
    w0, h0 = img.size; tw = min(w0, int(h0 * 1.6)); th = min(h0, int(w0 / 1.6))
    img = img.crop(((w0 - tw) // 2, (h0 - th) // 2, (w0 - tw) // 2 + tw, (h0 - th) // 2 + th))
    big = img.copy(); big.thumbnail((1600, 1000)); big.save(dst, 'WEBP', quality=80, method=6)
    sm = img.copy(); sm.thumbnail((800, 500)); sm.save(dst.replace('.webp', '-sm.webp'), 'WEBP', quality=78, method=6)
    name = ALL[slug]['name']
    C[slug] = [{'file': slug + '-1.webp', 'caption': name, 'alt': 'A view of ' + name + ', California.', 'title': im['file'][5:], 'author': im['author'] or 'Unknown',
                'license': im['license'], 'licurl': im.get('licurl', ''), 'page': im['page'], 'desc': im.get('desc', '')}]
    json.dump(C, open(CP, 'w'), indent=1, ensure_ascii=False); made += 1; print('ok', slug, im['file'][:60], flush=True)
print('saved', made, 'new photos |', len(C), 'cities have a credited photo')
