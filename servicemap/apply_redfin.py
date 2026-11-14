#!/usr/bin/env python3
"""Put Redfin median sale price + median days on market (three months ending October 2026)
on the hand-written city guides, from seo-engine/data/redfin-city-stats.json. Idempotent."""
import json, os, re, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PUB = os.path.join(ROOT, 'public')
D = json.load(open(os.path.join(ROOT, 'seo-engine/data/redfin-city-stats.json')))['cities']

def short(v):
    if v >= 1_000_000:
        return '$' + f'{v/1e6:.2f}'.rstrip('0').rstrip('.') + 'M'
    return f'${round(v/1000)}K'

SRC = '<p class="nbhd-stats-src">Median sale price and median days on market: Redfin, three months ending October 2026.</p>'
SRC_SO = '<p class="nbhd-stats-src">Median sale price and median days on market: Redfin (Sherman Oaks neighborhood of Los Angeles), three months ending October 2026.</p>'

def guide(slug):
    p = os.path.join(PUB, 'neighborhoods', slug + '.html'); h = open(p).read(); o = h
    r = D[slug]; price = short(r['median_sale_price']); dom = str(r['median_days_on_market'])
    h = re.sub(r'(<div class="nbhd-stat-num">)[^<]*(</div>\s*<div class="nbhd-stat-label">)(?:Median Home Price|Median Sale Price)(</div>)',
               lambda m: m.group(1) + price + m.group(2) + 'Median Sale Price' + m.group(3), h, count=1)
    h = re.sub(r'(<div class="nbhd-stat-num">)[^<]*(</div>\s*<div class="nbhd-stat-label">)(?:Avg Days on Market|Median Days on Market)(</div>)',
               lambda m: m.group(1) + dom + m.group(2) + 'Median Days on Market' + m.group(3), h, count=1)
    src = SRC_SO if slug == 'sherman-oaks' else SRC
    i = h.index('<section class="nbhd-stats">'); j = h.index('</section>', i)
    block = h[i:j]
    block = re.sub(r'\s*<p class="nbhd-stats-src">.*?</p>', '', block)
    block = block.rstrip() + '\n  ' + src + '\n'
    h = h[:i] + block + h[j:]
    # payment calculator starts at the median (its hint reads "<City> median is $X")
    h = re.sub(r'(<div class="cp-card" data-citypay[^>]*? data-median=")\d+(")', lambda m: m.group(1) + str(round(r['median_sale_price'] / 1000) * 1000) + m.group(2), h, count=1)
    # FAQ answers (JSON-LD)
    h = re.sub(r'As of 2026, the median home price in ([^"]+?) is \$[\d.,]+[MK]?\.',
               lambda m: f'In the three months ending October 2026, the median sale price in {m.group(1)} was ${r["median_sale_price"]:,} (Redfin).', h)
    h = re.sub(r'Homes in ([^"]+?) typically spend 30-45 days on market on average, though well-priced homes in top school zones often sell in under 14 days\. Days-on-market also varies by season and price tier\.',
               lambda m: f'In the three months ending October 2026, the median home in {m.group(1)} sold in {dom} days (Redfin). Days on market also varies by season, price tier, and condition.', h)
    if h != o: open(p, 'w').write(h)
    return h != o

if __name__ == '__main__':
    slugs = sys.argv[1:] or sorted(D)
    print(sum(guide(s) for s in slugs), 'guides changed')
