#!/usr/bin/env python3
"""Local preview server that behaves like the live site: /about opens about.html (clean URLs),
/ opens the home page, and the redirects in vercel.json work. Preview only, never deployed.
Run:  python3 preview_server.py [port]      (default 8125)"""
import http.server, json, os, re, sys
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'public')
V = json.load(open(os.path.join(ROOT, '..', 'vercel.json')))
REDIR = {r['source']: r['destination'] for r in V.get('redirects', []) if ':' not in r['source'] and '(' not in r['source']}
REWR = {r['source']: r['destination'] for r in V.get('rewrites', []) if ':' not in r['source'] and '(' not in r['source']}

class H(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *a, **k): super().__init__(*a, directory=ROOT, **k)
    def do_GET(self):
        path, _, q = self.path.partition('?')
        clean = path.rstrip('/') or '/'
        if clean in REDIR:
            self.send_response(308); self.send_header('Location', REDIR[clean] + ('?' + q if q else '')); self.end_headers(); return
        if clean in REWR: path = REWR[clean]
        elif clean == '/' and not os.path.exists(os.path.join(ROOT, 'index.html')) and os.path.exists(os.path.join(ROOT, 'home.html')): path = '/home.html'
        fs = os.path.join(ROOT, path.lstrip('/'))
        if not os.path.exists(fs) and os.path.exists(fs.rstrip('/') + '.html'): path = path.rstrip('/') + '.html'
        elif os.path.isdir(fs) and not os.path.exists(os.path.join(fs, 'index.html')) and os.path.exists(fs.rstrip('/') + '.html'): path = path.rstrip('/') + '.html'
        self.path = path + ('?' + q if q else '')
        return super().do_GET()
    def end_headers(self):
        self.send_header('Cache-Control', 'no-store')   # previews always show the newest files
        super().end_headers()
    def log_message(self, *a): pass

if __name__ == '__main__':
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8125
    http.server.ThreadingHTTPServer(('127.0.0.1', port), H).serve_forever()
