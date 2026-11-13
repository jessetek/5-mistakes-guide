#!/usr/bin/env python3
"""Background facts and one representative photo per city, from Wikipedia, Wikidata and Wikimedia Commons.
Facts kept: founding or incorporation year, nickname, motto, what the place is named after, elevation.
Photo kept only when Commons says it is freely licensed (public domain or Creative Commons), with author and license.
Writes wiki.json (resumable).  Run:  python3 servicemap/fetch_wiki.py"""
import json, os, re, time, urllib.parse, urllib.request
HERE = os.path.dirname(os.path.abspath(__file__))
ALL = dict(json.load(open(os.path.join(HERE, 'master_v2_192.json')))); ALL.update(json.load(open(os.path.join(HERE, 'master.json'))))
GUIDES = {f[:-5] for f in os.listdir(os.path.join(HERE, '..', 'public', 'neighborhoods')) if f.endswith('.html')}
P = os.path.join(HERE, 'wiki.json'); out = json.load(open(P)) if os.path.exists(P) else {}
UA = {'User-Agent': 'city-guide-research/1.0'}
LAST = [0.0]
def get(u):
    for i in range(5):
        w = 0.8 - (time.time() - LAST[0])
        if w > 0: time.sleep(w)
        LAST[0] = time.time()
        try: return json.loads(urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=40).read())
        except urllib.error.HTTPError as e:
            if e.code == 404: return None
            time.sleep(5 + i * 8)
        except Exception: time.sleep(4 + i * 4)
    return None
OKLIC = re.compile(r'^(cc0|public domain|pd|cc by(-sa)? [1-4]\.0)', re.I)
def label(q):
    d = get('https://www.wikidata.org/w/api.php?action=wbgetentities&props=labels&languages=en&format=json&ids=' + q)
    try: return d['entities'][q]['labels']['en']['value']
    except Exception: return None
for slug in sorted(GUIDES):
    if slug in out or slug not in ALL: continue
    c = ALL[slug]; rec = {}
    title = 'Sherman Oaks, Los Angeles' if slug == 'sherman-oaks' else c['name'] + ', California'
    s = get('https://en.wikipedia.org/api/rest_v1/page/summary/' + urllib.parse.quote(title.replace(' ', '_'), safe=''))
    if s and s.get('type') == 'standard':
        rec['title'] = s.get('title'); rec['wiki_url'] = s.get('content_urls', {}).get('desktop', {}).get('page'); rec['short'] = s.get('description')
        q = s.get('wikibase_item')
        img = (s.get('originalimage') or {}).get('source')
        if img:
            name = urllib.parse.unquote(img.split('/')[-1])
            ii = get('https://commons.wikimedia.org/w/api.php?action=query&format=json&prop=imageinfo&iiprop=url|size|extmetadata|mime&iiurlwidth=1920&titles=' + urllib.parse.quote('File:' + name))
            try:
                pg = list(ii['query']['pages'].values())[0]; info = pg['imageinfo'][0]; m = info.get('extmetadata', {})
                lic = m.get('LicenseShortName', {}).get('value', '')
                if OKLIC.match(lic) and info.get('mime') == 'image/jpeg' and info['width'] >= 1200:
                    rec['image'] = {'file': pg['title'], 'thumb': info.get('thumburl'), 'url': info.get('url'), 'w': info['width'], 'h': info['height'], 'license': lic,
                                    'licurl': m.get('LicenseUrl', {}).get('value', ''), 'author': re.sub('<[^>]+>', '', m.get('Artist', {}).get('value', '')).strip()[:80],
                                    'desc': re.sub('<[^>]+>', '', m.get('ImageDescription', {}).get('value', '')).strip()[:200], 'page': info.get('descriptionurl')}
            except Exception: pass
        if q:
            d = get('https://www.wikidata.org/w/api.php?action=wbgetentities&props=claims&format=json&ids=' + q)
            try:
                cl = d['entities'][q]['claims']
                def val(p):
                    v = cl.get(p, [{}])[0].get('mainsnak', {}).get('datavalue', {}).get('value'); return v
                t = val('P571')
                if t: rec['founded'] = int(t['time'][1:5])
                for p, k in (('P1449', 'nickname'), ('P1451', 'motto')):
                    v = val(p)
                    if isinstance(v, dict) and v.get('language', 'en') == 'en': rec[k] = v.get('text')
                v = val('P138')
                if isinstance(v, dict) and v.get('id'): rec['named_after'] = label(v['id'])
                v = val('P2044')
                if isinstance(v, dict) and v.get('amount'): rec['elevation_m'] = round(float(v['amount']))
            except Exception: pass
    out[slug] = rec; json.dump(out, open(P, 'w'), indent=1, ensure_ascii=False)
    print(slug, {k: (v if k != 'image' else v['license']) for k, v in rec.items() if k in ('founded', 'nickname', 'motto', 'named_after', 'image')}, flush=True)
print('done', len(out))
