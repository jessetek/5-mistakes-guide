"""SEO touch-ups for the 47 hand-written city guides. Safe to re-run.

Run after build_guides.py:  python3 servicemap/seo_pass.py
  - breadcrumb "Service Areas" now points to /service-areas (it pointed to /about)
  - share image: the city's own photo where the page used the generic site image
  - pages with no breadcrumb schema get the same WebPage + BreadcrumbList graph as the generated guides
  - pages without the city data hub (Sherman Oaks) still get the same next-step card
"""
import os, re, html, sys
sys.path.insert(0, os.path.dirname(__file__))
import build_guides as B

NB = os.path.join(B.PUB, 'neighborhoods')
GEN = 'content="servicemap/build_guides.py"'


def run():
    done = []
    for f in sorted(os.listdir(NB)):
        if not f.endswith('.html'): continue
        slug = f[:-5]; p = os.path.join(NB, f); h0 = h = open(p).read()
        if GEN in h: continue
        h = re.sub(r'("name": "Service Areas",\s*"item": ")https://jessetek\.net/about(")', r'\1https://jessetek.net/service-areas\2', h)
        pic = B.photo(slug)
        if not pic and os.path.exists(os.path.join(B.PUB, 'img', 'cities', slug + '-1.webp')) and f'/img/cities/{slug}-1.webp' in h:
            pic = {'src': f'/img/cities/{slug}-1.webp'}   # the page's own photo, already credited on /photo-credits
        if pic and 'og-home.jpg' in h:
            for pat in (r'(<meta property="og:image" content=")https://jessetek\.net/img/og-home\.jpg(">)',
                        r'(<meta name="twitter:image" content=")https://jessetek\.net/img/og-home\.jpg(">)'):
                h = re.sub(pat, r'\g<1>https://jessetek.net' + pic['src'] + r'\g<2>', h, count=1)
        m = re.search(r'<meta property="og:image" content="https://jessetek\.net(/img/cities/[^"]+)">', h)
        if m:   # width and height must match the real file
            w, ht = B.img_size(m.group(1))
            h = re.sub(r'(<meta property="og:image" content="https://jessetek\.net/img/cities/[^"]+">\s*<meta property="og:image:width" content=")\d+(">\s*<meta property="og:image:height" content=")\d+(">)',
                       rf'\g<1>{w}\g<2>{ht}\g<3>', h, count=1)
        if 'BreadcrumbList' not in h and slug in B.CD.ALL and slug in B.CD.T:
            r = B.CD.get(slug)
            m = re.search(r'<meta name="description" content="([^"]*)"', h)
            desc = html.unescape(m.group(1)) if m else f"{r['name']} real estate guide."
            g = B.schema_graph(r, slug, desc, pic)
            h = h.replace('</body>', g + '</body>', 1)
        if '<!-- citycta:start -->' not in h:
            m = re.search(r'<h1[^>]*>(.*?)</h1>', h, re.S)
            name = {'sherman-oaks': 'Sherman Oaks'}.get(slug) or (B.CD.get(slug)['name'] if slug in B.CD.ALL else None)
            if name:
                for anchor in ('<section class="cta-section cta-section-cal">', '<!-- RELATED CITIES -->', '<section class="related-cities">'):
                    if anchor in h:
                        h = h.replace(anchor, B.city_cta(slug, name) + anchor, 1); break
        if h != h0:
            open(p, 'w').write(h); done.append(slug)
    print('seo pass updated', len(done), 'pages:', ' '.join(done))


if __name__ == '__main__':
    run()
