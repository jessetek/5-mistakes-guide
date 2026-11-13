#!/usr/bin/env python3
"""Pull jessetek.net Search Console data into seo-engine/data/gsc-latest.json for the weekly engine.

Runs on Jesse's Mac (the credentials live in Jessetek/tools/.env.local and never go to the cloud).
Read-only. Writes the last 28 days of query+page rows plus a short list of "near page 1" targets:
queries at average position 5 to 20 with impressions, which the weekly engine prioritizes.

    python3 seo-engine/tools/gsc_snapshot.py            # writes the file
    python3 seo-engine/tools/gsc_snapshot.py --push     # also commits and pushes just that file
"""
import datetime as dt, json, pathlib, subprocess, sys, urllib.parse, urllib.request

ROOT = pathlib.Path(__file__).resolve().parents[2]            # landing-page/
ENV = ROOT.parent / 'tools' / '.env.local'                    # Jessetek/tools/.env.local
OUT = ROOT / 'seo-engine' / 'data' / 'gsc-latest.json'


def env():
    vals = {}
    for line in ENV.read_text().splitlines():
        if '=' in line and not line.lstrip().startswith('#'):
            k, v = line.split('=', 1)
            vals[k.strip()] = v.strip().strip('"').strip("'")
    return vals


def post(url, data, headers=None):
    req = urllib.request.Request(url, data=data, headers=headers or {}, method='POST')
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read().decode())


def main():
    e = env()
    tok = post('https://oauth2.googleapis.com/token', urllib.parse.urlencode({
        'client_id': e['GSC_CLIENT_ID'], 'client_secret': e['GSC_CLIENT_SECRET'],
        'refresh_token': e['GSC_REFRESH_TOKEN'], 'grant_type': 'refresh_token'}).encode())['access_token']
    prop = e.get('GSC_PROPERTY') or 'https://jessetek.net/'
    end = dt.date.today() - dt.timedelta(days=3)               # GSC reports with a 2 to 3 day lag
    start = end - dt.timedelta(days=27)
    body = json.dumps({'startDate': start.isoformat(), 'endDate': end.isoformat(),
                       'dimensions': ['query', 'page'], 'rowLimit': 1000}).encode()
    url = f'https://www.googleapis.com/webmasters/v3/sites/{urllib.parse.quote(prop, safe="")}/searchAnalytics/query'
    data = post(url, body, {'Authorization': f'Bearer {tok}', 'Content-Type': 'application/json'})
    rows = [{'query': r['keys'][0], 'page': r['keys'][1], 'clicks': r['clicks'], 'impressions': r['impressions'],
             'ctr': round(r['ctr'], 4), 'position': round(r['position'], 1)} for r in data.get('rows', [])]
    near = sorted([r for r in rows if 5 <= r['position'] <= 20 and r['impressions'] >= 5],
                  key=lambda r: (-r['impressions'], r['position']))[:40]
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({'generated': dt.date.today().isoformat(), 'window': f'{start}..{end}', 'property': prop,
                               'totals': {'rows': len(rows), 'clicks': sum(r['clicks'] for r in rows),
                                          'impressions': sum(r['impressions'] for r in rows)},
                               'near_page_one': near, 'rows': rows[:400]}, indent=1) + '\n')
    print(f'wrote {OUT.relative_to(ROOT)}: {len(rows)} rows, {len(near)} near-page-1 targets, window {start}..{end}')
    if '--push' in sys.argv:
        run = lambda *a: subprocess.run(a, cwd=ROOT, check=True)
        run('git', 'pull', '--rebase', '--autostash', 'origin', 'main')
        run('git', 'add', str(OUT.relative_to(ROOT)))
        if subprocess.run(['git', 'diff', '--cached', '--quiet'], cwd=ROOT).returncode:
            run('git', 'commit', '-m', f'SEO engine: Search Console snapshot {dt.date.today()}')
            run('git', 'push', 'origin', 'main')
            print('pushed')


if __name__ == '__main__':
    main()
