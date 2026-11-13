#!/usr/bin/env python3
"""Rebuild public/photo-credits.html from every photo the site uses:
  photo_credits_live67.json  the 67 city photos that went live 2026-11-13
  photo_credits.json         one Wikipedia lead photo per city (fetch_wiki_photos.py)
  place_photos.json          parks, museums and landmarks (fetch_place_photos.py)
Only photos whose file is actually in public/img are listed.  Run:  python3 servicemap/build_credits.py"""
import collections, html, json, os, re
HERE = os.path.dirname(os.path.abspath(__file__)); PUB = os.path.join(HERE, '..', 'public'); e = html.escape
def j(n, d): 
    p = os.path.join(HERE, n); return json.load(open(p)) if os.path.exists(p) else d
ALL = dict(j('master_v2_192.json', {})); ALL.update(j('master.json', {}))
def fix(s): return re.sub(r'\s+', ' ', (s or '').replace('–', '-').replace('—', '-')).strip()
by = collections.defaultdict(list)
for city, cap, title, author, lic, licurl, page in j('photo_credits_live67.json', []): by[city].append((cap, title, author, lic, licurl, page))
for slug, items in j('photo_credits.json', {}).items():
    for p in items:
        if os.path.exists(os.path.join(PUB, 'img', 'cities', p['file'])): by[ALL[slug]['name']].append((p['caption'], p['title'], p['author'], p['license'], p['licurl'], p['page']))
for slug, items in j('place_photos.json', {}).items():
    for p in items:
        if os.path.exists(os.path.join(PUB, 'img', 'places', p['file'])): by[ALL[slug]['name']].append((p['name'], p['title'], p['author'], p['license'], p['licurl'], p['page']))
t = open(os.path.join(PUB, 'photo-credits.html')).read()
a = t.index('<section class="legal-hero">'); b = t.index('<!-- ===================== FOOTER ===================== -->')
m = re.search(r'<article[^>]*>', t[a:b]).group(0)
body = ['<section class="legal-hero">\n  <div class="legal-hero-inner">\n    <h1>Photo Credits</h1>\n    <p>The photos on our city guides, and the people who took them.</p>\n  </div>\n</section>\n\n' + m]
n = 0
for city in sorted(by):
    body.append(f'  <h2>{e(city)}</h2>\n  <ul>')
    for cap, title, author, lic, licurl, page in by[city]:
        l = f'<a href="{e(licurl)}" rel="noopener license">{e(lic)}</a>' if licurl else e(lic)
        body.append(f'    <li>{e(fix(cap))}. <a href="{e(page)}" rel="noopener">{e(fix(os.path.splitext(title)[0]))}</a>, by {e(fix(author))}. {l}.</li>'); n += 1
    body.append('  </ul>')
body.append('</article>\n\n')
open(os.path.join(PUB, 'photo-credits.html'), 'w').write(t[:a] + '\n'.join(body) + t[b:])
print('credits page:', n, 'photos,', len(by), 'cities; dashes:', len(re.findall('[—–]|&mdash;|&ndash;', '\n'.join(body))))
