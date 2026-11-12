#!/usr/bin/env python3
"""Jessetek weekly SEO engine: the mechanical half. The writer (Claude) does the thinking,
this script does every step that must be identical each week.

  python3 seo-engine/tools/engine.py build  seo-engine/drafts/<slug>.json   # spec -> public/insights/<slug>.html
  python3 seo-engine/tools/engine.py wire   <slug>                          # index card + sitemap + feed + published.json
  python3 seo-engine/tools/engine.py touch  public/<page>.html [...]        # sitemap lastmod = today for refreshed pages
  python3 seo-engine/tools/engine.py qc     public/<file>.html [...]        # all gates; exit 1 on any failure
  python3 seo-engine/tools/engine.py status                                 # what is published, queued, and missing
  python3 seo-engine/tools/engine.py repoint <city>                         # after an agent page: move its retired redirect there

Spec JSON (drafts/<slug>.json):
{
 "slug": "downey-vs-whittier-where-to-buy-2026",
 "title": "Downey vs Whittier: Where to Buy a Home in 2026",      <- <title> (site name is appended)
 "h1": "Downey vs Whittier: <i>where to buy</i> in 2026",          <- hero headline, may use <i>
 "description": "...",                                             <- 140 to 160 chars, meta + og
 "category": "Buyer Education",                                    <- meta line + feed category
 "keyword": "downey vs whittier",                                  <- primary keyword (QC checks title/h1/intro)
 "city": "downey",                                                 <- cities.json slug or null
 "lede": "One or two sentences under the headline.",
 "tldr": ["three to five short takeaways"],
 "body_html": "<h2>..</h2><p>..</p> ...",                          <- the article, plain semantic HTML
 "faq": [{"q": "...", "a": "..."}],                                <- 3 to 6, become FAQPage schema
 "cta": {"h": "...", "p": "...", "href": "/zoom", "label": "Book my 15-min call"},
 "sources": [{"label": "...", "url": "..."}],                      <- every outside fact, cited at the bottom
 "og_image": "https://jessetek.net/img/og-guide.jpg"               <- optional
}
"""
import datetime as dt, html, json, pathlib, re, sys, zlib

ROOT = pathlib.Path(__file__).resolve().parents[2]
PUB = ROOT / 'public'
ENG = ROOT / 'seo-engine'
TPL = ENG / 'templates' / 'post.html'
PUBLISHED = ENG / 'published.json'
HUES = ['#B8CAF5', '#D1EEF9', '#9BD8A9', '#9ED4EF', '#FDE99B']   # Jtek knowledge base palette
SITE = 'https://jessetek.net'
TODAY = dt.date.today()

DASH = re.compile(r'—|–|&mdash;|&ndash;|&#8212;|&#8211;|&#x2014;|&#x2013;', re.I)
BANNED = [
    (re.compile(r'bilingual|biling[üu]e|espa[ñn]ol|habla|se habla|spanish[- ]speaking', re.I), 'never promote bilingual / Spanish (Jesse, 2026-10-02)'),
    (re.compile(r'wilcox|830 N', re.I), 'old office address, never use'),
    (re.compile(r'AggregateRating', re.I), 'no self-serving review schema'),
    (re.compile(r'\bguarantee(d)?\b', re.I), 'no guarantees in real estate copy'),
    (re.compile(r'\b(as an AI|in today\'s fast-paced|delve|tapestry|navigating the complexities|it\'s important to note)\b', re.I), 'reads AI-written'),
]


def die(msg):
    print('ERROR:', msg)
    sys.exit(1)


def hue(slug, k=0):
    return HUES[(zlib.crc32(slug.encode()) + k) % len(HUES)]


def esc(t):
    return html.escape(t, quote=True)


def strip_tags(t):
    return re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', ' ', t)).strip()


def load_published():
    return json.loads(PUBLISHED.read_text()) if PUBLISHED.exists() else {'posts': []}


# --------------------------------------------------------------------------- build
def build(spec_path):
    spec = json.loads(pathlib.Path(spec_path).read_text())
    for k in ['slug', 'title', 'h1', 'description', 'category', 'keyword', 'lede', 'body_html', 'faq', 'cta']:
        if not spec.get(k):
            die(f'spec missing "{k}"')
    slug = spec['slug']
    if not re.fullmatch(r'[a-z0-9]+(-[a-z0-9]+)*', slug):
        die('slug must be lowercase words joined by single hyphens')
    out = PUB / 'insights' / f'{slug}.html'
    words = len(strip_tags(spec['body_html']).split())
    read_min = max(4, round(words / 230))
    pub_date = spec.get('published') or TODAY.isoformat()
    mod_date = TODAY.isoformat()
    month = dt.date.fromisoformat(pub_date).strftime('%B %Y')
    mod_human = dt.date.fromisoformat(mod_date).strftime('%B %-d, %Y')
    url = f'{SITE}/insights/{slug}'
    og = spec.get('og_image') or f'{SITE}/img/og-guide.jpg'

    tldr = ''
    if spec.get('tldr'):
        tldr = '  <div class="post-tldr"><b>The short version</b><ul>' + ''.join(f'<li>{t}</li>' for t in spec['tldr']) + '</ul></div>\n'
    sources = ''
    if spec.get('sources'):
        sources = ('\n  <div class="post-sources"><b>Sources</b><ul>' +
                   ''.join(f'<li><a href="{esc(s["url"])}" rel="nofollow noopener" target="_blank">{esc(s["label"])}</a></li>' for s in spec['sources']) + '</ul></div>')
    faq_html = '  <section class="post-faq">\n    <h2>Questions people ask me</h2>\n' + ''.join(
        f'    <details><summary>{esc(f["q"])}</summary><p>{f["a"]}</p></details>\n' for f in spec['faq']) + '  </section>'

    schema = [
        {'@context': 'https://schema.org', '@type': 'BlogPosting', 'headline': spec['title'], 'description': spec['description'],
         'image': og, 'datePublished': pub_date, 'dateModified': mod_date, 'wordCount': words, 'keywords': spec['keyword'],
         'author': {'@type': 'Person', '@id': f'{SITE}/about#jesse', 'name': 'Jesse Onate', 'jobTitle': 'Realtor',
                    'identifier': 'DRE #02133131', 'url': f'{SITE}/about'},
         'publisher': {'@type': 'Organization', 'name': 'Jesse Oñate Real Estate', 'logo': {'@type': 'ImageObject', 'url': f'{SITE}/img/jesse-headshot.jpeg'}},
         'mainEntityOfPage': {'@type': 'WebPage', '@id': url}},
        {'@context': 'https://schema.org', '@type': 'BreadcrumbList', 'itemListElement': [
            {'@type': 'ListItem', 'position': 1, 'name': 'Home', 'item': f'{SITE}/'},
            {'@type': 'ListItem', 'position': 2, 'name': 'Insights', 'item': f'{SITE}/insights/'},
            {'@type': 'ListItem', 'position': 3, 'name': spec['title'], 'item': url}]},
        {'@context': 'https://schema.org', '@type': 'FAQPage', 'mainEntity': [
            {'@type': 'Question', 'name': f['q'], 'acceptedAnswer': {'@type': 'Answer', 'text': strip_tags(f['a'])}} for f in spec['faq']]},
    ]
    city = spec.get('city')
    if city:
        cities = json.loads((ENG / 'data' / 'cities.json').read_text())['cities']
        if city in cities:
            schema[0]['about'] = {'@type': 'City', 'name': cities[city]['name'], 'containedInPlace': {'@type': 'State', 'name': 'California'}}
    schema_html = '\n'.join('<script type="application/ld+json">\n' + json.dumps(s, ensure_ascii=False, indent=1) + '\n</script>' for s in schema)

    rep = {
        'TITLE': esc(spec['title']), 'DESCRIPTION': esc(spec['description']), 'SLUG': slug,
        'OG_TITLE': esc(spec.get('og_title') or spec['title']), 'OG_IMAGE': og,
        'PUBLISHED_ISO': f'{pub_date}T09:00:00-08:00', 'MODIFIED_ISO': f'{mod_date}T09:00:00-08:00',
        'THEME': hue(slug), 'THEME2': hue(slug, 2),
        'META_LINE': f'{esc(spec["category"])} · {month} · {read_min} min read',
        'H1': spec['h1'], 'LEDE': spec['lede'], 'MODIFIED_HUMAN': mod_human,
        'BODY': tldr + spec['body_html'], 'FAQ_HTML': faq_html + sources,
        'CTA_H': esc(spec['cta']['h']), 'CTA_P': esc(spec['cta']['p']), 'CTA_HREF': spec['cta']['href'], 'CTA_LABEL': esc(spec['cta']['label']),
        'SCHEMA': schema_html,
    }
    page = TPL.read_text(encoding='utf-8')
    for k, v in rep.items():
        page = page.replace('{{' + k + '}}', v)
    if '{{' in page:
        die('unfilled placeholder: ' + re.search(r'\{\{\w+\}\}', page).group(0))
    out.write_text(page, encoding='utf-8')
    print(f'built {out.relative_to(ROOT)}  ({words} words, {read_min} min, theme {rep["THEME"]})')


# --------------------------------------------------------------------------- wire
def wire(slug):
    page = PUB / 'insights' / f'{slug}.html'
    if not page.exists():
        die(f'{page} not found, run build first')
    s = page.read_text(encoding='utf-8')
    title = html.unescape(re.search(r'<title>(.*?) \| Jesse', s).group(1))
    desc = html.unescape(re.search(r'<meta name="description" content="([^"]*)"', s).group(1))
    meta = html.unescape(strip_tags(re.search(r'<div class="post-meta">(.*?)</div>', s, re.S).group(1)))
    category = meta.split('·')[0].strip()
    url = f'{SITE}/insights/{slug}'

    # 1) insights index: newest card first
    idx = PUB / 'insights' / 'index.html'
    t = idx.read_text(encoding='utf-8')
    if f'href="/insights/{slug}"' not in t:
        card = (f'\n  <a href="/insights/{slug}" class="insights-card">\n    <div class="insights-card-meta">{esc(meta)}</div>\n'
                f'    <h3>{esc(title)}</h3>\n    <p>{esc(desc)}</p>\n  </a>\n')
        t = t.replace('<section class="insights-list">\n', '<section class="insights-list">\n' + card, 1)
        idx.write_text(t, encoding='utf-8')
        print('index: card added')

    # 2) sitemap
    sm = PUB / 'sitemap.xml'
    t = sm.read_text(encoding='utf-8')
    entry = f'  <url><loc>{url}</loc><lastmod>{TODAY.isoformat()}</lastmod><changefreq>monthly</changefreq><priority>0.8</priority></url>\n'
    if f'<loc>{url}</loc>' in t:
        t = re.sub(rf'(<loc>{re.escape(url)}</loc>)(<lastmod>[^<]*</lastmod>)?', rf'\1<lastmod>{TODAY.isoformat()}</lastmod>', t)
    else:
        t = t.replace('</urlset>', entry + '</urlset>')
    # the insights hub changed too
    t = re.sub(rf'(<loc>{re.escape(SITE)}/insights/</loc>)(<lastmod>[^<]*</lastmod>)?', rf'\1<lastmod>{TODAY.isoformat()}</lastmod>', t)
    sm.write_text(t, encoding='utf-8')
    print('sitemap: updated')

    # 3) RSS feed: newest item first
    feed = PUB / 'insights' / 'feed.xml'
    t = feed.read_text(encoding='utf-8')
    if f'<link>{url}</link>' not in t:
        pub = dt.datetime.combine(TODAY, dt.time(17, 0)).strftime('%a, %d %b %Y %H:%M:%S GMT')
        item = (f'\n    <item>\n      <title>{esc(title)}</title>\n      <link>{url}</link>\n      <guid isPermaLink="true">{url}</guid>\n'
                f'      <pubDate>{pub}</pubDate>\n      <dc:creator>Jesse Oñate</dc:creator>\n      <category>{esc(category)}</category>\n'
                f'      <description>{esc(desc)}</description>\n    </item>\n')
        t = t.replace('    </image>\n', '    </image>\n' + item, 1)
        t = re.sub(r'<lastBuildDate>[^<]*</lastBuildDate>', f'<lastBuildDate>{pub}</lastBuildDate>', t)
        feed.write_text(t, encoding='utf-8')
        print('feed: item added')

    # 4) ledger
    led = load_published()
    if not any(p['slug'] == slug for p in led['posts']):
        kw = re.search(r'"keywords": "([^"]*)"', s)
        led['posts'].append({'slug': slug, 'date': TODAY.isoformat(), 'title': title, 'category': category, 'keyword': kw.group(1) if kw else ''})
        PUBLISHED.write_text(json.dumps(led, indent=1, ensure_ascii=False) + '\n')
        print('published.json: logged')


# --------------------------------------------------------------------------- touch
def touch(paths):
    sm = PUB / 'sitemap.xml'
    t = sm.read_text(encoding='utf-8')
    for p in paths:
        rel = pathlib.Path(p).resolve().relative_to(PUB).as_posix()
        loc = SITE + '/' + re.sub(r'(index)?\.html$', '', rel)
        if rel == 'home.html':
            loc = SITE + '/'
        if f'<loc>{loc}</loc>' not in t:
            print(f'touch: {loc} not in sitemap (skipped)')
            continue
        t = re.sub(rf'(<loc>{re.escape(loc)}</loc>)(<lastmod>[^<]*</lastmod>)?', rf'\1<lastmod>{TODAY.isoformat()}</lastmod>', t)
        print(f'touch: {loc} lastmod {TODAY}')
    sm.write_text(t, encoding='utf-8')


# --------------------------------------------------------------------------- repoint
def repoint(city):
    """After building public/real-estate-agent-<city>.html, move the retired /best-bilingual-realtor-<city>
    redirect from the city guide to the new agent page. This is the ONLY vercel.json edit the engine may make."""
    page = PUB / f'real-estate-agent-{city}.html'
    if not page.exists():
        die(f'{page.name} does not exist yet; build the agent page first')
    vf = ROOT / 'vercel.json'
    t = vf.read_text()
    old = f'{{ "source": "/best-bilingual-realtor-{city}", "destination": "/neighborhoods/{city}", "permanent": true }}'
    new = f'{{ "source": "/best-bilingual-realtor-{city}", "destination": "/real-estate-agent-{city}", "permanent": true }}'
    if new in t:
        print(f'repoint: already points at /real-estate-agent-{city}')
        return
    if old not in t:
        print(f'repoint: no retired bilingual redirect for {city} (nothing to do)')
        return
    t = t.replace(old, new, 1)
    json.loads(t)   # never write invalid JSON
    vf.write_text(t)
    print(f'repoint: /best-bilingual-realtor-{city} now 301s to /real-estate-agent-{city}')


# --------------------------------------------------------------------------- qc
def visible_text(s):
    s = re.sub(r'<(script|style)[^>]*>.*?</\1>', ' ', s, flags=re.S)
    s = re.sub(r'<head>.*?</head>', ' ', s, flags=re.S)
    s = re.sub(r'<!--.*?-->', ' ', s, flags=re.S)
    return html.unescape(re.sub(r'<[^>]+>', ' ', s))


def qc(paths):
    fails, warns = [], []
    for p in paths:
        f = pathlib.Path(p)
        s = f.read_text(encoding='utf-8')
        name = f.relative_to(ROOT).as_posix() if f.is_absolute() else p
        vis = visible_text(s)
        # copy rules: scan what readers and Google see (visible text, title, description, schema)
        title_t = (re.search(r'<title>(.*?)</title>', s, re.S) or [None, ''])[1] if re.search(r'<title>', s) else ''
        desc_t = (re.search(r'<meta name="description" content="([^"]*)"', s) or [None, ''])[1] if 'name="description"' in s else ''
        ld = ' '.join(re.findall(r'<script type="application/ld\+json">(.*?)</script>', s, re.S))
        scan = ' '.join([vis, html.unescape(title_t), html.unescape(desc_t), ld])
        m = DASH.search(scan)
        if m:
            fails.append(f'{name}: dash in copy "{scan[max(0, m.start() - 40):m.end() + 40].strip()}"')
        for rx, why in BANNED:
            hit = rx.search(s if 'Rating' in rx.pattern else scan)
            if hit:
                (warns if 'guarantee' in rx.pattern else fails).append(f'{name}: {why} ("{hit.group(0)}")')
        if re.search(r'\$97\b', vis):
            fails.append(f'{name}: $97 appears')
        # page structure
        if s.count('<h1') != 1:
            fails.append(f'{name}: needs exactly one <h1> (found {s.count("<h1")})')
        if '/css/kb.css' not in s:
            fails.append(f'{name}: missing kb.css')
        if not re.search(r'<body[^>]*--th:#', s):
            fails.append(f'{name}: body has no --th page color')
        if 'noindex' in s and '/insights/' in name:
            fails.append(f'{name}: noindex on an article')
        t = re.search(r'<title>(.*?)</title>', s, re.S)
        if not t or not (30 <= len(html.unescape(t.group(1))) <= 75):
            warns.append(f'{name}: title length {len(t.group(1)) if t else 0} (aim 30 to 70)')
        d = re.search(r'<meta name="description" content="([^"]*)"', s)
        if not d or not (110 <= len(html.unescape(d.group(1))) <= 165):
            fails.append(f'{name}: meta description length {len(d.group(1)) if d else 0} (need 110 to 165)')
        if 'rel="canonical"' not in s:
            fails.append(f'{name}: no canonical')
        # schema parses
        for block in re.findall(r'<script type="application/ld\+json">(.*?)</script>', s, re.S):
            try:
                json.loads(block)
            except Exception as e:
                fails.append(f'{name}: bad JSON-LD ({e})')
        # internal links resolve
        for href in set(re.findall(r'href="(/[^"#?]*)', s)):
            if href.startswith(('/api/', '/css/', '/js/', '/img/', '/icons/', '/favicon', '/manifest')):
                continue
            path = href.rstrip('/')
            cands = [PUB / (path.lstrip('/') + '.html'), PUB / path.lstrip('/') / 'index.html', PUB / path.lstrip('/')]
            if path == '':
                continue
            if not any(c.exists() for c in cands) and path not in ('/zoom', '/move', '/quiz', '/ig', '/buyer-quiz', '/valuation', '/seller'):
                fails.append(f'{name}: broken internal link {href}')
        # article-only gates
        if 'class="post-updated"' in s:   # article gates only for engine-built articles
            body = re.search(r'<article class="post-body">(.*?)</article>', s, re.S)
            words = len(visible_text(body.group(1)).split()) if body else 0
            if words < 1000:
                fails.append(f'{name}: only {words} words in the article (need 1000+)')
            inlinks = set(re.findall(r'href="(/(?!insights/)[a-z][^"#?]*)"', body.group(1) if body else ''))
            inlinks -= {'/zoom'}
            if len(inlinks) < 3:
                fails.append(f'{name}: only {len(inlinks)} links to other site pages inside the article (need 3+)')
            if not re.search(r'href="/neighborhoods/', body.group(1) if body else ''):
                warns.append(f'{name}: no link to a city guide')
            if '"FAQPage"' not in s:
                fails.append(f'{name}: no FAQPage schema')
            kw = re.search(r'"keywords": "([^"]*)"', s)
            if kw:
                k = kw.group(1).lower()
                head = (re.search(r'<title>(.*?)</title>', s).group(1) + ' ' + strip_tags(re.search(r'<h1>(.*?)</h1>', s, re.S).group(1))).lower()
                first = visible_text(body.group(1))[:900].lower() if body else ''
                core = [w for w in re.findall(r'[a-z0-9]+', k) if w not in ('a', 'the', 'in', 'to', 'for', 'of', 'vs', 'and')]
                if not all(w in head for w in core):
                    warns.append(f'{name}: keyword "{k}" not fully in title/h1')
                if not all(w in first for w in core):
                    warns.append(f'{name}: keyword "{k}" not in the first 150 words')
    for w in warns:
        print('WARN ', w)
    for f_ in fails:
        print('FAIL ', f_)
    print(f'QC: {len(paths)} file(s), {len(fails)} fail, {len(warns)} warn')
    sys.exit(1 if fails else 0)


# --------------------------------------------------------------------------- status
def status():
    led = load_published()
    q = json.loads((ENG / 'topic-queue.json').read_text())
    tasks = json.loads((ENG / 'site-tasks.json').read_text())
    print('published by the engine:', len(led['posts']))
    for p in led['posts'][-5:]:
        print('  ', p['date'], p['slug'])
    open_topics = [t for t in q['topics'] if t.get('status', 'queued') == 'queued']
    print('topics queued:', len(open_topics), '| next:', ', '.join(t['slug'] for t in open_topics[:3]))
    open_tasks = [t for t in tasks['tasks'] if t.get('status', 'open') == 'open']
    print('site tasks open:', len(open_tasks), '| next:', ', '.join(t['id'] for t in open_tasks[:3]))


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(0)
    cmd, args = sys.argv[1], sys.argv[2:]
    {'build': lambda: build(args[0]), 'wire': lambda: wire(args[0]), 'touch': lambda: touch(args),
     'qc': lambda: qc(args), 'status': status, 'repoint': lambda: repoint(args[0])}.get(cmd, lambda: die('unknown command ' + cmd))()
