#!/usr/bin/env python3
"""Build seo-engine/data/cities.json from the live city guides (public/neighborhoods/*.html).

The city guides are the site's source of truth for median price, days on market,
population, ZIPs, schools and neighbors. Articles must reuse these numbers so the
site never contradicts itself. Re-run after any city guide changes:

    python3 seo-engine/tools/build_cities.py
"""
import json, pathlib, re

ROOT = pathlib.Path(__file__).resolve().parents[2]
PUB = ROOT / 'public'
OUT = ROOT / 'seo-engine' / 'data' / 'cities.json'

# Jesse's farm (CLAUDE.md). Farm cities get priority in topics and agent pages.
FARM = ['downey', 'whittier', 'pico-rivera', 'long-beach', 'cerritos', 'norwalk',
        'la-mirada', 'bellflower', 'la-habra', 'lakewood', 'montebello']


def clean(t):
    return re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', '', t)).strip()


def main():
    cities = {}
    for f in sorted((PUB / 'neighborhoods').glob('*.html')):
        s = f.read_text(encoding='utf-8')
        slug = f.stem
        title = clean(re.search(r'<title>(.*?)</title>', s, re.S).group(1))
        name = title.split(' Real Estate')[0].split(' |')[0].strip()
        badge = re.search(r'<div class="hero-badge">(.*?)</div>', s, re.S)
        badge = clean(badge.group(1)) if badge else ''
        county = 'Orange County' if 'Orange County' in badge or 'OC' in badge.split('·') else ('LA County' if 'LA County' in badge else '')
        zips = re.findall(r'\b9\d{4}\b', badge)
        stats = {clean(l): clean(n) for n, l in re.findall(r'<div class="nbhd-stat-num">(.*?)</div>\s*<div class="nbhd-stat-label">(.*?)</div>', s, re.S)}
        schools = [clean(x) for x in re.findall(r'class="nbhd-school-name">(.*?)<', s)]
        neighbors = [h.split('/')[-1] for h in re.findall(r'href="(/neighborhoods/[a-z-]+)" class="related-city-card"', s)]
        pages = {
            'guide': f'/neighborhoods/{slug}',
            'first_time_buyer': f'/first-time-buyer-{slug}' if (PUB / f'first-time-buyer-{slug}.html').exists() else None,
            'sell_over_asking': f'/sell-over-asking-{slug}' if (PUB / f'sell-over-asking-{slug}.html').exists() else None,
            'agent': f'/real-estate-agent-{slug}' if (PUB / f'real-estate-agent-{slug}.html').exists() else None,
        }
        cities[slug] = {
            'name': name, 'county': county, 'zips': zips, 'farm': slug in FARM,
            'median_price': stats.get('Median Home Price') or stats.get('Median Sale Price'), 'days_on_market': stats.get('Avg Days on Market') or stats.get('Median Days on Market'),
            'residents': stats.get('Residents'), 'schools': schools, 'neighbors': neighbors, 'pages': pages,
        }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({'_source': 'public/neighborhoods/*.html (site source of truth)', 'farm_order': FARM, 'cities': cities}, indent=1) + '\n')
    missing_agent = [c for c in FARM if c in cities and not cities[c]['pages']['agent']]
    print(f'{len(cities)} cities -> {OUT.relative_to(ROOT)}; farm cities with no agent page: {missing_agent}')


if __name__ == '__main__':
    main()
