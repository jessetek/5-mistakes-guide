#!/usr/bin/env python3
"""The data blocks every city guide shares ("the hub"): price history chart, what each bedroom count costs,
houses vs condos, rent vs own, where the city ranks among every city on the map, and its public schools.
Pure functions that return HTML. Numbers come from citydata.py, which reads public sources only.
A block is left out when its data does not exist for that city. Nothing is filled in."""
import collections, os, json, datetime, html, json
import citydata as CD

e = lambda s: html.escape(str(s), quote=True)
def money(n): return '${:,.0f}'.format(n)
def short(n): return ('$%.2fM' % (n / 1e6)).replace('0M', 'M') if n >= 1e6 else '$%.0fK' % (n / 1e3)
def pct(a, b): return (a - b) / b * 100.0
def signed(p, d=1): return ('+' if p >= 0 else '') + ('%.' + str(d) + 'f%%') % p
def month(d): return datetime.date.fromisoformat(d).strftime('%B %Y')
def ordinal(n): return '%d%s' % (n, 'th' if 10 <= n % 100 <= 20 else {1: 'st', 2: 'nd', 3: 'rd'}.get(n % 10, 'th'))
def join(xs): return xs[0] if len(xs) == 1 else ', '.join(xs[:-1]) + ' and ' + xs[-1]


# ---------------------------------------------------------------- 1. price history
def chart(r):
    h = r['history']
    if len(h) < 24: return ''
    vals = [v for _, v in h]; lo, hi = min(vals), max(vals); span = (hi - lo) or 1
    lo -= span * 0.08; hi += span * 0.08
    W, H = 1000.0, 300.0
    pts = [(i / (len(h) - 1) * W, H - (v - lo) / (hi - lo) * H) for i, v in enumerate(vals)]
    line = 'M' + ' L'.join('%.1f,%.1f' % p for p in pts)
    area = line + ' L%.1f,%.1f L0,%.1f Z' % (W, H, H)
    years = []
    for i, (d, _) in enumerate(h):
        if d[5:7] == '01' and int(d[:4]) % 2 == 0: years.append((i / (len(h) - 1) * 100, d[:4]))
    chips = []
    for label, key in (('1 year', 'y1'), ('5 years', 'y5'), ('10 years', 'y10')):
        if r[key]: chips.append('<span><b>%s</b> %s</span>' % (signed(pct(r['value'], r[key]), 1 if key == 'y1' else 0), label))
    peak = max(h, key=lambda x: x[1])
    note = ('The highest point in these ten years is %s, %s.' % (money(peak[1]), 'this month' if peak[0] == h[-1][0] else 'in ' + month(peak[0])))
    data = json.dumps({'start': h[0][0][:7], 'v': vals}, separators=(',', ':'))
    return f'''<!-- hub: price history -->
<section class="hub-section">
  <div class="hub-inner">
    <div class="sec-head reveal">
      <h2 class="sec-title">Ten Years of<br>{e(r['name'])} Home Values.</h2>
      <p class="sec-sub">The typical home value, month by month. Move across the chart to read any month.</p>
    </div>
    <div class="hub-card hub-chart reveal" data-hub-chart='{e(data)}'>
      <div class="hub-chart-top">
        <div><div class="hub-chart-val" data-hc="val">{money(r['value'])}</div><div class="hub-chart-date" data-hc="date">{month(r['value_date'])}</div></div>
        <div class="hub-chips">{''.join(chips)}</div>
      </div>
      <div class="hub-plot">
        <svg viewBox="0 0 1000 300" preserveAspectRatio="none" role="img" aria-label="Line chart of the typical home value in {e(r['name'])} over ten years">
          <path class="hub-area" d="{area}"/><path class="hub-line" d="{line}" vector-effect="non-scaling-stroke"/>
        </svg>
        <div class="hub-cursor" data-hc="cursor" hidden><i></i></div>
        <div class="hub-range"><span>{short(max(vals))}</span><span>{short(min(vals))}</span></div>
      </div>
      <div class="hub-years">{''.join('<span style="left:%.2f%%">%s</span>' % y for y in years)}</div>
      <p class="hub-note">{e(note)}</p>
    </div>
  </div>
</section>

'''


# ---------------------------------------------------------------- 2. what your money buys
def money_buys(r):
    beds = r['beds']
    if len(beds) < 3 and not (r['house'] and r['condo']): return ''
    top = max(beds.values()) if beds else 1
    rows = ''.join(
        f'<button type="button" class="hub-bed" data-hub-price="{v}" aria-label="{n} bedroom, {money(v)}. Use this price in the payment tool."><span class="hub-bed-n">{n}{"+" if n == 5 else ""} bed</span><span class="hub-bar"><i style="width:{round(v / top * 100)}%"></i></span><span class="hub-bed-v">{short(v)}</span></button>'
        for n, v in sorted(beds.items()))
    left = f'''<div class="hub-card reveal">
        <h3>By bedroom count</h3>
        <p class="hub-sub">Tap a row to load that price into the payment tool below.</p>
        <div class="hub-beds">{rows}</div>
      </div>''' if len(beds) >= 3 else ''
    bits = []
    if r['house'] and r['condo']:
        gap = r['house'] - r['condo']
        bits.append(f'''<div class="hub-duo"><div><span>Single-family house</span><b>{short(r['house'])}</b></div><div><span>Condo or townhome</span><b>{short(r['condo'])}</b></div></div>
        <p class="hub-sub">A house costs about {money(gap)} more than a condo here.</p>''')
    elif r['house']:
        bits.append(f'''<div class="hub-duo"><div><span>Single-family house</span><b>{short(r['house'])}</b></div></div>''')
    if r['low'] and r['high'] and r['value']:
        a, b = r['low'], r['high']; pos = max(4, min(96, (r['value'] - a) / (b - a) * 100))
        bits.append(f'''<h3 class="hub-h3b">The range</h3>
        <div class="hub-rangebar"><i style="left:{pos:.0f}%"></i></div>
        <div class="hub-rangelab"><span><b>{short(a)}</b>lower-priced third</span><span><b>{short(r['value'])}</b>typical</span><span><b>{short(b)}</b>upper third</span></div>''')
    right = f'<div class="hub-card reveal"><h3>Houses and condos</h3>{"".join(bits)}</div>' if bits else ''
    return f'''<!-- hub: what your money buys -->
<section class="hub-section">
  <div class="hub-inner">
    <div class="sec-head reveal">
      <h2 class="sec-title">What Your Money Buys<br>in {e(r['name'])}.</h2>
      <p class="sec-sub">Typical values by home size and type, so you can match the city to your budget before you tour anything.</p>
    </div>
    <div class="hub-grid2">{left}{right}</div>
  </div>
</section>

'''


# ---------------------------------------------------------------- 3. rent vs own (sits under the payment tool)
def rent(r):
    if not r['rent']: return ''
    ch = (' That is %s from a year ago.' % signed(pct(r['rent'], r['rent_y1']))) if r['rent_y1'] else ''
    return f'''<!-- hub: rent vs own -->
<section class="hub-section hub-tight">
  <div class="hub-inner">
    <div class="hub-card hub-rent reveal" data-hub-rent="{r['rent']}">
      <div class="hub-rent-l">
        <h3>Renting in {e(r['name'])}</h3>
        <div class="hub-rent-n">{money(r['rent'])}<small>/mo</small></div>
        <p class="hub-sub">Typical asking rent, {month(r['rent_date'])}.{ch} Over a year that is {money(r['rent'] * 12)} in rent.</p>
      </div>
      <div class="hub-rent-r">
        <h3>Owning, at your settings above</h3>
        <div class="hub-rent-n" data-hr="own">&nbsp;</div>
        <p class="hub-sub" data-hr="line">Set a price and down payment in the tool above and this compares it with the rent.</p>
      </div>
    </div>
  </div>
</section>

'''


# ---------------------------------------------------------------- 4. where it ranks
def ranks(r):
    if not r['on_map'] or not r['value']: return ''
    rk = CD.ranking('value'); n = len(rk); pos = [s for s, _ in rk].index(r['slug']) + 1
    import math
    lo = math.log(rk[-1][1]); hi = math.log(rk[0][1])
    near = set(CD.near(r['slug'], 4))
    dots = []
    for s, v in rk:
        x = (math.log(v) - lo) / (hi - lo) * 100
        cls = 'me' if s == r['slug'] else 'nb' if s in near else ''
        tag = f'<a href="/neighborhoods/{s}" class="hub-dot {cls}" style="left:{x:.2f}%" title="{e(CD.get(s)["name"])} {short(v)}" aria-label="{e(CD.get(s)["name"])}, typical value {short(v)}"></a>'
        dots.append((2 if cls == 'me' else 1 if cls else 0, tag))
    dots = ''.join(t for _, t in sorted(dots, key=lambda d: d[0]))
    median = rk[n // 2][1]
    if pos > n / 2: lead = f'<b>{ordinal(n - pos + 1)} most affordable of {n}</b> cities on my map by typical home value.'
    else: lead = f'<b>{ordinal(pos)} highest-priced of {n}</b> cities on my map by typical home value.'
    facts = [f'<li>{lead} The middle city is at {short(median)}; {e(r["name"])} is at {short(r["value"])}.</li>']
    if r['y1']:
        ch = sorted(((pct(CD.get(s)['value'], CD.get(s)['y1']), s) for s, _ in rk if CD.get(s)['y1']), reverse=True)
        p2 = [s for _, s in ch].index(r['slug']) + 1
        facts.append(f'<li><b>{ordinal(p2)} of {len(ch)}</b> for price growth over the past year ({signed(pct(r["value"], r["y1"]))}), where 1st grew the most.</li>')
    if r['rent']:
        rr = CD.ranking('rent'); p3 = [s for s, _ in rr].index(r['slug']) + 1
        facts.append(f'<li><b>{ordinal(p3)} of {len(rr)}</b> for typical rent ({money(r["rent"])} a month), where 1st is the highest rent.</li>')
    nb = [(s, CD.get(s)) for s in CD.near(r['slug'], 4) if CD.get(s)['value']]
    rows = sorted([(r['slug'], r)] + nb, key=lambda x: -x[1]['value']); top = rows[0][1]['value']
    bars = ''.join(
        (f'<div class="hv-row hv-me"><span class="hv-name">{e(c["name"])}</span>' if s == r['slug'] else f'<a class="hv-row" href="/neighborhoods/{s}"><span class="hv-name">{e(c["name"])}</span>') +
        f'<span class="hv-bar"><i style="width:{round(c["value"] / top * 100)}%"></i></span><span class="hv-num">{short(c["value"])}</span>' + ('</div>' if s == r['slug'] else '</a>')
        for s, c in rows)
    return f'''<!-- hub: where it ranks -->
<section class="hub-section">
  <div class="hub-inner">
    <div class="sec-head reveal">
      <h2 class="sec-title">Where {e(r['name'])} Sits<br>Among {n} Cities.</h2>
      <p class="sec-sub">Every dot is a city on my map, lined up from least to most expensive. Tap any dot to open that city.</p>
    </div>
    <div class="hub-card reveal">
      <div class="hub-strip">{dots}<span class="hub-strip-me{' hub-strip-me-r' if (math.log(r['value']) - lo) / (hi - lo) > .8 else ' hub-strip-me-l' if (math.log(r['value']) - lo) / (hi - lo) < .2 else ''}" style="left:{(math.log(r['value']) - lo) / (hi - lo) * 100:.2f}%">{e(r['name'])}</span></div>
      <div class="hub-strip-ax"><span>{short(rk[-1][1])}</span><span>{short(rk[0][1])}</span></div>
      <ul class="hub-facts">{''.join(facts)}</ul>
    </div>
    <div class="hv-compare reveal" style="margin-top:16px">
      <h3>{e(r['name'])} and the cities closest to it</h3>
      {bars}
    </div>
  </div>
</section>

'''


# ---------------------------------------------------------------- 5. schools (summary card; the dots are drawn on the map)
LEVEL_NAME = {'elementary': 'Elementary', 'middle': 'Middle', 'high': 'High', 'k12': 'K to 12'}
def schools(r):
    sc = r['schools']
    if not sc: return ''
    by = {}
    for s in sc: by.setdefault(s['level'], []).append(s)
    tiles = ''.join(f'<div class="hub-sch-n" style="background:{TINTS[i % 6]}"><b>{len(by[k])}</b><span><i class="hub-lvl hub-lvl-{k}"></i>{LEVEL_NAME[k]}</span></div>' for i, k in enumerate(k for k in ('elementary', 'middle', 'high', 'k12') if k in by))
    cols = ''
    for i, k in enumerate(k for k in ('elementary', 'middle', 'high', 'k12') if k in by):
        nm = sorted({x['name'] + (' (charter)' if x['charter'] else '') for x in by[k]})
        cols += f'<div class="hub-list" style="--tint:{TINTS[i % 6]}"><h3>{LEVEL_NAME[k]}</h3><ul>' + ''.join(f'<li>{e(n)}</li>' for n in nm[:40]) + (f'<li class="hub-list-more">and {len(nm) - 40} more</li>' if len(nm) > 40 else '') + '</ul></div>'
    every = f'<details class="hub-sch-all"><summary>See every school by name</summary><div class="hub-lists">{cols}</div></details>' if len(sc) >= 3 else ''
    highs = sorted({s['name'] for s in by.get('high', [])})
    hs = f'<p class="hub-sub"><b>Public high schools inside {e(r["name"])}:</b> {e(join(highs))}.</p>' if highs and len(highs) <= 14 else (f'<p class="hub-sub"><b>{len(highs)} public high schools</b> sit inside {e(r["name"])}.</p>' if highs else '')
    d = r['districts']
    ds = f'<p class="hub-sub"><b>School {"district" if len(d) == 1 else "districts"}:</b> {e(join(d)) if len(d) <= 6 else e(join(d[:6])) + ", and " + str(len(d) - 6) + " more"}.</p>' if d else ''
    ch = sum(1 for s in sc if s['charter'])
    where = 'limits' if r['kind'] == 'city' else 'boundary'
    return f'''<div class="hub-card hub-schools reveal">
      <h3>{len(sc)} public schools inside the {e(r['name'])} {where}</h3>
      <div class="hub-sch">{tiles}</div>
      {hs}{ds}
      {every}
      <p class="hub-fine">Counted from the California Department of Education school directory by each campus location{", including %d charter %s" % (ch, "school" if ch == 1 else "schools") if ch else ""}. Which school a home is assigned to depends on the address, so confirm with the district before you buy.</p>
    </div>'''


def school_points(r):
    """Compact list for the map layer."""
    return [[s['lon'], s['lat'], s['name'], s['level']] for s in r['schools']]


# ---------------------------------------------------------------- sources line
def sources(r):
    out = []
    if r['value']: out.append('Home values: Zillow Home Value Index, typical value, %s.' % month(r['value_date']))
    if r['rent']: out.append('Rent: Zillow Observed Rent Index, %s.' % month(r['rent_date']))
    if r['pop']: out.append('Population: U.S. Census Bureau, %s.' % r['pop']['label'])
    if r['schools']: out.append('Schools: California Department of Education public school directory.')
    if r.get('places'): out.append('Parks, places and restaurants: OpenStreetMap contributors.')
    out.append('Boundary: U.S. Census Bureau.')
    return ' '.join(out)


# ================================================================ local life: story, parks, things to do, food
# Everything below comes from citydata (OpenStreetMap places inside the official boundary, Wikipedia and Wikidata
# facts, the Census, the state school directory). Sentences are assembled from those facts. Nothing is made up,
# and a sentence is simply left out when its fact is missing.
import hashlib
def _pick(slug, salt, options): return options[int(hashlib.md5((slug + salt).encode()).hexdigest(), 16) % len(options)]
def acres(a): return format(round(a), ',') if a >= 10 else ('%.1f' % a).rstrip('0').rstrip('.')
def names(ps, n): return [p['name'] for p in ps[:n]]


def story_sentences(r):
    s = r['slug']; name = r['name']; w = r['wiki']; pl = r['places']; out = []
    kind = {'city': 'city', 'cdp': 'unincorporated community', 'neighborhood': 'neighborhood'}[r['kind']]
    # where and how big
    if r['pop']:
        out.append(_pick(s, 'a', [f'{name} is a {kind} of about {r["pop"]["n"]:,} people in {CD.COUNTY_Z[r["county"]]}.',
                                 f'About {r["pop"]["n"]:,} people call {name} home. It sits in {CD.COUNTY_Z[r["county"]]}.',
                                 f'{name}, in {CD.COUNTY_Z[r["county"]]}, is a {kind} of roughly {r["pop"]["n"]:,} residents.']))
    else: out.append(f'{name} is a {kind} in {CD.COUNTY_Z[r["county"]]}.')
    # roots
    if w.get('founded') and r['kind'] == 'city':
        age = 2026 - w['founded']
        out.append(_pick(s, 'b', [f'Its official start date is {w["founded"]}, about {age} years ago.', f'It dates to {w["founded"]}.', f'It has been its own community since {w["founded"]}.']))
    if w.get('named_after'): out.append(f'The name comes from {w["named_after"]}.')
    if w.get('nickname'): out.append(f'It goes by the nickname "{w["nickname"]}".')
    elif w.get('motto'): out.append(f'The official motto is "{w["motto"]}".')
    # outdoors
    parks = [p for p in pl.get('parks', []) if p['acres'] >= 0.5]
    if parks:
        big = parks[0]
        if len(parks) >= 2 and big['acres'] >= 2:
            out.append(_pick(s, 'c', [f'There are {len(parks)} parks inside the boundary. The biggest is {big["name"]}, at about {acres(big["acres"])} acres.',
                                     f'For green space, {name} has {len(parks)} parks, led by {big["name"]} at roughly {acres(big["acres"])} acres.',
                                     f'{big["name"]}, about {acres(big["acres"])} acres, is the largest of {len(parks)} parks here.']))
        else: out.append(f'{big["name"]} is the main park here.')
    od = pl.get('outdoors', [])
    beach = [p for p in od if p['kind'] == 'Beach']; golf = [p for p in od if p['kind'] == 'Golf course']; nat = [p for p in od if p['kind'] == 'Nature area']
    if beach: out.append(f'It has ocean beach: {join(names(beach, 3))}.')
    if nat: out.append(f'Open space and trails include {join(names(nat, 2))}.')
    if golf: out.append(f'Golfers have {join(names(golf, 2))}.')
    # culture and hangouts
    fun = pl.get('fun', [])
    star = [p for p in fun if p['known']] or fun
    if star: out.append(_pick(s, 'd', [f'For a day out there is {join(names(star, 3))}.', f'Places people go: {join(names(star, 3))}.', f'Local draws include {join(names(star, 3))}.']))
    col = [p for p in pl.get('learn', []) if p['kind'] == 'College']
    if col: out.append(f'{col[0]["name"]} is here too.')
    # food
    eat = pl.get('eat', [])
    if len(eat) >= 8:
        top = [c for c, _ in r['cuisines'][:3]]
        out.append(f'The map shows {len(eat)} places to eat and drink' + (f', with {join(top)} the most common.' if len(top) >= 2 else '.'))
    # schools
    if r['schools']:
        d = r['districts']
        out.append(f'There {"are" if len(r["schools"]) != 1 else "is"} {len(r["schools"])} public school{"s" if len(r["schools"]) != 1 else ""} inside the boundary' + (f', run by {join(d[:3])}{" and others" if len(d) > 3 else ""}.' if d else '.'))
    # price
    if r['on_map'] and r['value']:
        rk = CD.ranking('value'); n = len(rk); pos = [x for x, _ in rk].index(s) + 1
        where = f'the {ordinal(n - pos + 1)} most affordable of {n} cities on my map' if pos > n / 2 else f'the {ordinal(pos)} highest-priced of {n} cities on my map'
        grow = f', and values are up {pct(r["value"], r["y10"]):.0f}% in ten years' if r['y10'] and r['value'] > r['y10'] else ''
        out.append(f'On price, {name} is {where} at about {short(r["value"])} for the typical home{grow}.')
    return out


def _place_photos(slug):
    f = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'place_photos.json')
    global _PP
    if _PP is None: _PP = json.load(open(f)) if os.path.exists(f) else {}
    pub = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'public', 'img', 'places')
    return [p for p in _PP.get(slug, []) if os.path.exists(os.path.join(pub, p['file']))]
_PP = None


def facts(r):
    """Short, sourced figures for the colored tiles under the story."""
    pl = r['places']; w = r['wiki']; out = []
    if w.get('founded') and r['kind'] == 'city': out.append((str(w['founded']), 'Established'))
    if r['pop']: out.append((f'{r["pop"]["n"]:,}', 'People, ' + r['pop']['label']))
    ps = [p for p in pl.get('parks', []) if p['acres'] >= 0.5]
    if ps: out.append((str(len(ps)), 'Parks' if len(ps) != 1 else 'Park'))
    if len(ps) > 1: out.append((acres(sum(p['acres'] for p in ps)), 'Acres of parks'))
    if r['schools']: out.append((str(len(r['schools'])), 'Public schools'))
    if len(pl.get('eat', [])) >= 5: out.append((str(len(pl['eat'])), 'Places to eat'))
    if r['value']: out.append((short(r['value']), 'Typical home value'))
    return out[:6]


def story(r, photo=None):
    sents = story_sentences(r)
    if len(sents) < 3: return ''
    half = (len(sents) + 1) // 2
    text = f'<p class="hub-lede">{e(sents[0])}</p><p>{e(" ".join(sents[1:half]))}</p><p>{e(" ".join(sents[half:]))}</p>'
    fig = ''; pp = _place_photos(r['slug'])
    if not photo and pp:
        photo = {'src': '/img/places/' + pp[0]['file'], 'sm': None, 'alt': pp[0]['name'] + ' in ' + r['name'] + '.', 'caption': pp[0]['name']}
    if photo:
        ss = f' srcset="{photo["sm"]} 800w, {photo["src"]} 1600w" sizes="(max-width:760px) 100vw, 520px"' if photo.get('sm') else ''
        fig = f'''<figure class="hub-story-photo" style="background:{avg_color(photo['src'])}"><img src="{photo['src']}"{ss} alt="{e(photo['alt'])}" loading="lazy" width="1600" height="1000"><figcaption>{e(photo['caption'])}</figcaption></figure>'''
    fx = facts(r)
    tiles = '<div class="hub-factrow reveal">' + ''.join(f'<div class="hub-fact" style="--tint:{TINTS[i % 6]}"><b{"" if k == "Established" else " data-count"}>{e(v)}</b><span>{e(k)}</span></div>' for i, (v, k) in enumerate(fx)) + '</div>' if len(fx) >= 3 else ''
    return f'''<!-- hub: story -->
<section class="hub-section hub-band">
  <div class="hub-inner hub-story{" hub-story-solo" if not photo and not tiles else ""}">
    <div class="hub-story-text reveal">
      {eye('The place', '#B8CAF5')}
      <h2 class="sec-title">The Story of<br>{e(r['name'])}.</h2>
      {text}
      <p class="hub-fine">Assembled from the U.S. Census Bureau, Wikidata, OpenStreetMap and the California Department of Education.{' <a href="/photo-credits">Photo credits</a>.' if photo else ''}</p>
    </div>
    {fig or tiles.replace('hub-factrow', 'hub-factrow hub-factside')}
  </div>
  {'<div class="hub-inner">' + tiles + '</div>' if fig else ''}
</section>

'''


def gallery(r, skip_first=False):
    """Real photos of named places in this city (freely licensed, credited on /photo-credits)."""
    pp = _place_photos(r['slug'])
    if skip_first: pp = pp[1:]
    if len(pp) < 2: return ''
    cards = ''.join(f'''<figure class="hub-shot" style="background:{avg_color('/img/places/' + p['file'])}"><img src="/img/places/{p['file']}" alt="{e(p['name'])} in {e(r['name'])}." loading="lazy" width="720" height="480"><figcaption><b>{e(p['name'])}</b><span>{e(p['kind'])}</span></figcaption></figure>''' for p in pp[:6])
    return f'''<!-- hub: gallery -->
<section class="hub-section">
  <div class="hub-inner">
    <div class="sec-head reveal">
      {eye('In photos', '#F7C9B6')}
      <h2 class="sec-title">A Look Around<br>{e(r['name'])}.</h2>
      <p class="sec-sub">Real places inside the {"city limit" if r['kind'] == 'city' else "community"}. <a href="/photo-credits">Photo credits</a>.</p>
    </div>
    <div class="hub-shots hub-shots-{min(len(pp), 6)} reveal">{cards}</div>
  </div>
</section>

'''


TINTS = ['#FDE99B', '#D1EEF9', '#9BD8A9', '#B8CAF5', '#9ED4EF', '#F7C9B6']
def eye(label, color): return f'<span class="hub-eye"><i style="background:{color}"></i>{e(label)}</span>'
def spot(p): return f' data-spot="{p["lon"]},{p["lat"]}" role="button" tabindex="0" title="Show {e(p["name"])} on the map"'
_IC = lambda d: f'<svg class="hub-ic" viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">{d}</svg>'
ICONS = {
    'Museum': _IC('<path d="M3 9.5 12 4l9 5.5"/><path d="M5 10v8M9.5 10v8M14.5 10v8M19 10v8M3.5 20h17"/>'),
    'Attraction': _IC('<path d="m12 3 2.6 5.6 6 .7-4.5 4.1 1.2 6L12 16.5 6.7 19.4l1.2-6L3.4 9.3l6-.7z"/>'),
    'Theme park': _IC('<circle cx="12" cy="11" r="7"/><path d="M12 4v14M5 11h14M7 6l10 10M17 6 7 16M9 21l3-3 3 3"/>'),
    'Zoo': _IC('<circle cx="7" cy="9" r="1.8"/><circle cx="17" cy="9" r="1.8"/><circle cx="10" cy="5.5" r="1.6"/><circle cx="14" cy="5.5" r="1.6"/><path d="M12 11c-3 0-5 2.4-5 5 0 2 1.7 3 5 3s5-1 5-3c0-2.6-2-5-5-5z"/>'),
    'Aquarium': _IC('<path d="M3 12c3-5 9-6 14-1l4-3v8l-4-3c-5 5-11 4-14-1z"/><circle cx="8" cy="11" r=".6"/>'),
    'Theater': _IC('<path d="M4 5h16v6a8 8 0 0 1-16 0z"/><path d="M8.5 9h.01M15.5 9h.01M9 13c1.8 1.5 4.200 1.5 6 0"/>'),
    'Arts center': _IC('<path d="M12 3a9 9 0 1 0 0 18c1.5 0 2-1 1.5-2.2-.6-1.5.3-2.800 2-2.800H18a3 3 0 0 0 3-3c0-5.5-4-10-9-10z"/><circle cx="7.5" cy="11" r="1"/><circle cx="10.5" cy="7" r="1"/><circle cx="15" cy="7.5" r="1"/>'),
    'Gallery': _IC('<rect x="3.5" y="5" width="17" height="14" rx="2"/><path d="m4 16 4.5-4.5 3.5 3.5 2.5-2.5L20 17"/><circle cx="9" cy="9" r="1.3"/>'),
    'Movie theater': _IC('<rect x="3.5" y="5" width="17" height="14" rx="2"/><path d="M3.5 9.5h17M8 5l-1.5 4.5M13 5l-1.5 4.5M18 5l-1.5 4.5"/>'),
    'Shopping center': _IC('<path d="M5 8h14l-1 12H6z"/><path d="M9 8V7a3 3 0 0 1 6 0v1"/>'),
    'Market': _IC('<path d="M4 9 5.5 4h13L20 9"/><path d="M4 9a2.7 2.7 0 0 0 5.300 0 2.7 2.7 0 0 0 5.400 0A2.7 2.7 0 0 0 20 9M5.5 12v8h13v-8"/>'),
    'Stadium': _IC('<ellipse cx="12" cy="9" rx="8.5" ry="4"/><path d="M3.5 9v6c0 2.2 3.800 4 8.5 4s8.5-1.8 8.5-4V9"/>'),
    'Water park': _IC('<path d="M3 16c1.5-1.5 3-1.5 4.5 0s3 1.5 4.5 0 3-1.5 4.5 0 3 1.5 4.5 0M3 20c1.5-1.5 3-1.5 4.5 0s3 1.5 4.5 0 3-1.5 4.5 0 3 1.5 4.5 0"/><path d="M8 12V6a3 3 0 0 1 6 0v6"/>'),
    'Viewpoint': _IC('<path d="m3 19 6-10 4 6 2.5-3.5L21 19z"/><circle cx="17" cy="6" r="1.8"/>'),
    'Landmark': _IC('<path d="M6 20V9l6-5 6 5v11"/><path d="M4 20h16M10 20v-5h4v5"/>'),
    'Library': _IC('<path d="M4 5.5c2.7-1 5.300-1 8 .5v13c-2.7-1.5-5.300-1.5-8-.5zM20 5.5c-2.7-1-5.300-1-8 .5v13c2.7-1.5 5.300-1.5 8-.5z"/>'),
    'College': _IC('<path d="m2.5 9.5 9.5-4.5 9.5 4.5L12 14z"/><path d="M6.5 11.5V16c1.5 1.5 3.5 2 5.5 2s4-.5 5.5-2v-4.5"/>'),
}
_AVG = {}
def avg_color(path):
    """The photo's average color, shown in its frame while the photo loads."""
    if path not in _AVG:
        try:
            from PIL import Image
            f = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'public', path.lstrip('/'))
            r_, g_, b_ = Image.open(f).convert('RGB').resize((1, 1)).getpixel((0, 0)); _AVG[path] = '#%02X%02X%02X' % (r_, g_, b_)
        except Exception: _AVG[path] = '#E9E6DF'
    return _AVG[path]
def parkland(r, ps):
    """Share of the city's land that is park, and park space per resident. Land area: U.S. Census Gazetteer."""
    a = CD.land_m2(r['slug']); total = sum(p['acres'] for p in ps) * 4046.86
    if not a or not ps: return ''
    share = total / a * 100
    if not 2 <= share <= 30: return ''            # under 2% the map is likely missing parks; over 30% an outline spills past the city
    per = total * 10.7639 / r['pop']['n'] if r['pop'] else None
    right = f'<div class="hub-pl-n"><b data-count>{round(per):,}</b><span>square feet of park for each resident</span></div>' if per and per >= 20 else ''
    return f'''<div class="hub-pl reveal"><div class="hub-pl-n"><b>{share:.1f}%</b><span>of {e(r['name'])}'s land is park</span></div>
      <div class="hub-pl-bar" aria-hidden="true"><i style="width:{min(100, share * 100 / 30):.1f}%"></i></div>{right}</div>'''


def parks(r):
    pl = r['places']; ps = [p for p in pl.get('parks', []) if p['acres'] >= 0.5]
    od = pl.get('outdoors', [])
    if not ps and not od: return ''
    top = max([p['acres'] for p in ps[:6]] + [1])
    def card(p, i, bar=True):
        size = f'<span class="hub-place-m">{acres(p["acres"])} acres</span>' if p['acres'] >= 1 or bar else ''
        meter = f'<span class="hub-place-bar" aria-hidden="true"><i style="width:{max(6, round(p["acres"] / top * 100))}%"></i></span>' if bar else ''
        return f'<div class="hub-place" style="--tint:{TINTS[i % 6]}"{spot(p)}><span class="hub-place-k">{e(p["kind"])}</span><b>{e(p["name"])}</b>{size}{meter}</div>'
    cards = ''.join(card(p, i) for i, p in enumerate(ps[:6])) + ''.join(card(p, i + 3, False) for i, p in enumerate(od[:4]))
    total = sum(p['acres'] for p in ps)
    more = ps[6:18]
    line = f'{len(ps)} parks, about {acres(total)} acres of them in all.' if len(ps) > 1 else ''
    rest = '<p class="hub-sub hub-more"><b>More parks:</b> ' + ', '.join(f'<span class="hub-morelink"{spot(p)}>{e(p["name"])}</span>' for p in more) + (' and others' if len(ps) > 18 else '') + '.</p>' if more else ''
    return f'''<!-- hub: parks -->
<section class="hub-section hub-band hub-band-g">
  <div class="hub-inner">
    <div class="sec-head reveal">
      {eye('Outdoors', '#2F9E63')}
      <h2 class="sec-title">Parks and Open Space<br>in {e(r['name'])}.</h2>
      <p class="sec-sub">{e(line)} Sizes are measured from each park's mapped outline. Tap any park to see it on the map.</p>
    </div>
    {parkland(r, ps)}
    <div class="hub-places reveal">{cards}</div>
    {rest}
  </div>
</section>

'''


def things(r):
    pl = r['places']; fun = pl.get('fun', []); learn = pl.get('learn', []); hist = pl.get('historic', [])
    groups = collections.OrderedDict()
    for p in fun: groups.setdefault(p['kind'], []).append(p)
    for p in learn: groups.setdefault(p['kind'], []).append(p)
    if hist: groups['Landmark'] = hist
    if not groups: return ''
    order = ['Museum', 'Attraction', 'Theme park', 'Zoo', 'Aquarium', 'Theater', 'Arts center', 'Gallery', 'Movie theater', 'Shopping center', 'Market', 'Stadium', 'Water park', 'Viewpoint', 'Landmark', 'Library', 'College']
    plural = {'Museum': 'Museums', 'Attraction': 'Attractions', 'Theme park': 'Theme parks', 'Zoo': 'Zoos', 'Aquarium': 'Aquariums', 'Theater': 'Theaters', 'Arts center': 'Arts centers', 'Gallery': 'Galleries',
              'Movie theater': 'Movie theaters', 'Shopping center': 'Shopping centers', 'Market': 'Markets', 'Stadium': 'Stadiums', 'Water park': 'Water parks', 'Viewpoint': 'Viewpoints',
              'Landmark': 'Historic landmarks', 'Library': 'Libraries', 'College': 'Colleges'}
    rows = ''
    for i, k in enumerate(k for k in order if k in groups):
        items = groups[k]
        rows += f'<div class="hub-list" style="--tint:{TINTS[i % 6]}"><h3>{ICONS.get(k, "")}{plural[k] if len(items) > 1 else k}</h3><ul>' + ''.join(f'<li{spot(p)}>{e(p["name"])}</li>' for p in items[:7]) + (f'<li class="hub-list-more">and {len(items) - 7} more</li>' if len(items) > 7 else '') + '</ul></div>'
    return f'''<!-- hub: things to do -->
<section class="hub-section">
  <div class="hub-inner">
    <div class="sec-head reveal">
      {eye('Weekends', '#6A5BD6')}
      <h2 class="sec-title">Things to Do and<br>Places to Hang Out.</h2>
      <p class="sec-sub">Real places inside {e(r['name'])}. Tap any one to see it on the map.</p>
    </div>
    <div class="hub-lists reveal">{rows}</div>
  </div>
</section>

'''


def eat(r):
    ps = r['places'].get('eat', [])
    if len(ps) < 4: return ''
    local = [p for p in ps if not p['chain']]
    cz = r['cuisines'][:7]; top = cz[0][1] if cz else 1
    bars = ''.join(f'<div class="hub-cz" style="--i:{i}"><span>{e(c)}</span><span class="hub-bar"><i style="width:{round(n / top * 100)}%"></i></span><b>{n}</b></div>' for i, (c, n) in enumerate(cz))
    CZT = {c: TINTS[i % 6] for i, (c, n) in enumerate(r['cuisines'])}
    lp = round(len(local) / len(ps) * 100)
    split = f'''<div class="hub-split reveal"><div class="hub-split-bar" aria-hidden="true"><i style="width:{lp}%"></i></div>
      <div class="hub-split-k"><span><b>{len(local)}</b> local spots</span><span><b>{len(ps) - len(local)}</b> chain locations</span></div></div>''' if len(ps) - len(local) >= 1 and len(local) >= 1 else ''
    kinds = collections.Counter(p['kind'] for p in ps)
    kline = ', '.join(f'{n} {k.lower()}{"s" if n != 1 and not k.endswith("y") else ""}'.replace('ice creams', 'ice cream shops').replace('ice cream,', 'ice cream shop,') for k, n in kinds.most_common(4))
    kline = __import__('re').sub(r'\b(\d+) (\w+)y\b', lambda m: m.group(0) if m.group(1) == '1' else f'{m.group(1)} {m.group(2)}ies', kline)
    if kline.endswith('1 ice cream'): kline += ' shop'
    # ten local spots, spread across the kinds of food here instead of the first ten in the alphabet
    def _h(p): return hashlib.md5((r['slug'] + p['name']).encode()).hexdigest()
    pool = collections.OrderedDict()
    for p in sorted(local, key=lambda p: (-p['known'], -p['detail'], _h(p))): pool.setdefault((p['cuisine'] or [p['kind']])[0], []).append(p)
    picks = []
    while len(picks) < 10 and any(pool.values()):
        for k in list(pool):
            if pool[k] and len(picks) < 10: picks.append(pool[k].pop(0))
    spots = ''.join(f'<li{spot(p)}><b>{e(p["name"])}</b><span style="background:{CZT.get((p["cuisine"] or [""])[0], "#EFEDE7")}">{e((p["cuisine"] or [p["kind"]])[0])}</span></li>' for p in picks)
    return f'''<!-- hub: food -->
<section class="hub-section hub-band hub-band-p">
  <div class="hub-inner">
    <div class="sec-head reveal">
      {eye('Food and drink', '#E0722F')}
      <h2 class="sec-title">Where {e(r['name'])}<br>Eats and Drinks.</h2>
      <p class="sec-sub">{len(ps)} places are on the map inside {e(r['name'])}: {e(kline)}. {len(local)} of them are local, not chains.</p>
    </div>
    {split}
    <div class="hub-grid2">
      {f'<div class="hub-card reveal"><h3>What is on the menu</h3><p class="hub-sub">The kitchens you find most often here.</p><div class="hub-czs">{bars}</div></div>' if cz else ''}
      <div class="hub-card reveal"><h3>Local spots on the map</h3><ul class="hub-spots">{spots}</ul>
      <p class="hub-fine">Listed from OpenStreetMap, not a ranking or a recommendation. Restaurants open and close, so check hours before you go.</p></div>
    </div>
  </div>
</section>

'''


def place_points(r):
    """Compact dots for the map: [lon, lat, name, layer, label]."""
    pl = r['places']; out = []
    for p in [x for x in pl.get('parks', []) if x['acres'] >= 0.5][:40] + pl.get('outdoors', [])[:12]: out.append([p['lon'], p['lat'], p['name'], 'park', p['kind']])
    for p in pl.get('fun', [])[:30] + pl.get('learn', [])[:12] + pl.get('historic', [])[:10]: out.append([p['lon'], p['lat'], p['name'], 'fun', p['kind']])
    for p in sorted([x for x in pl.get('eat', []) if not x['chain']], key=lambda p: (-p['known'], -p['detail']))[:50]: out.append([p['lon'], p['lat'], p['name'], 'eat', ', '.join(p['cuisine']) or p['kind']])
    return out
