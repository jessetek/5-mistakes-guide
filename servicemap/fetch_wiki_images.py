#!/usr/bin/env python3
"""The lead photo of each city's Wikipedia article, kept only when Wikimedia Commons says it is freely licensed.
Writes wiki_images.json (resumable). Run after fetch_wiki.py:  python3 servicemap/fetch_wiki_images.py"""
import json, os, re, time, urllib.parse, urllib.request
HERE = os.path.dirname(os.path.abspath(__file__))
W = json.load(open(os.path.join(HERE, 'wiki.json')))
P = os.path.join(HERE, 'wiki_images.json'); out = json.load(open(P)) if os.path.exists(P) else {}
UA = {'User-Agent': 'city-guide-research/1.0'}
OKLIC = re.compile(r'^(cc0|public domain|pd|cc by(-sa)? [1-4]\.\d)', re.I)
def get(u):
    for i in range(5):
        time.sleep(0.9)
        try: return json.loads(urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=40).read())
        except urllib.error.HTTPError as e:
            if e.code == 404: return None
            time.sleep(6 + i * 8)
        except Exception: time.sleep(4 + i * 4)
    return None
def clean(s): return re.sub(r'\s+', ' ', re.sub('<[^>]+>', '', s or '')).strip()
for slug, w in sorted(W.items()):
    if slug in out or not w.get('title'): continue
    rec = None
    s = get('https://en.wikipedia.org/api/rest_v1/page/summary/' + urllib.parse.quote(w['title'].replace(' ', '_'), safe=''))
    img = ((s or {}).get('originalimage') or {}).get('source')
    if img:
        name = urllib.parse.unquote(img.split('?')[0].split('/')[-1])
        ii = get('https://commons.wikimedia.org/w/api.php?action=query&format=json&prop=imageinfo&iiprop=url|size|extmetadata|mime&iiurlwidth=1920&titles=' + urllib.parse.quote('File:' + name))
        try:
            pg = list(ii['query']['pages'].values())[0]; info = pg['imageinfo'][0]; m = info.get('extmetadata', {})
            lic = clean(m.get('LicenseShortName', {}).get('value', ''))
            if OKLIC.match(lic) and info.get('mime') == 'image/jpeg' and info['width'] >= 1200:
                rec = {'file': pg['title'], 'thumb': info.get('thumburl'), 'url': info.get('url'), 'w': info['width'], 'h': info['height'], 'license': lic,
                       'licurl': m.get('LicenseUrl', {}).get('value', ''), 'author': clean(m.get('Artist', {}).get('value', ''))[:80],
                       'desc': clean(m.get('ImageDescription', {}).get('value', ''))[:200], 'page': info.get('descriptionurl')}
            else: rec = {'skip': '%s %s %s' % (lic, info.get('mime'), info.get('width')), 'file': pg['title']}
        except Exception as e: rec = {'skip': 'no info'}
    out[slug] = rec or {'skip': 'no image'}
    json.dump(out, open(P, 'w'), indent=1, ensure_ascii=False)
    print(slug, out[slug].get('file', ''), out[slug].get('license') or out[slug].get('skip'), flush=True)
print('done', len(out), 'usable', sum(1 for v in out.values() if 'skip' not in v))
