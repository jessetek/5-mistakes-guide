#!/usr/bin/env python3
"""
strip-fake-aggregate-rating.py  — SEO Brain repair tool (SKILL 4 / ACT)

Removes the fabricated `aggregateRating` node (e.g. 5.0 / 100 reviews) from every
JSON-LD block under public/. Self-serving aggregateRating on a RealEstateAgent /
LocalBusiness / Organization entity earns NO Google star treatment (since 2019) and,
when unbacked by real reviews, is an FTC fake-review + Google manual-action liability.

Surgical: only the `aggregateRating` object is removed (individual Review/reviewRating
nodes are left untouched). Every modified JSON-LD block is re-validated as parseable
JSON before the file is written; a file that would become invalid is skipped + reported.

Usage:
    python3 seo-brain/tools/strip-fake-aggregate-rating.py            # apply
    python3 seo-brain/tools/strip-fake-aggregate-rating.py --dry-run  # report only
Run from the landing-page/ directory (the parent of public/).
"""
import os, re, glob, json, sys

DRY = "--dry-run" in sys.argv
PUB = "public"

block_re = re.compile(r'(<script type="application/ld\+json">)(.*?)(</script>)', re.DOTALL)
# AggregateRating has no nested objects, so [^{}]* safely captures its body.
agg_re = re.compile(r',?\s*"aggregateRating"\s*:\s*\{[^{}]*\}')

changed, failed = [], []
nodes_removed = 0

def clean(body: str) -> str:
    b = agg_re.sub('', body)
    b = b.replace('{,', '{').replace(',}', '}')
    b = re.sub(r',\s*,', ',', b)
    b = re.sub(r'\{\s*,', '{', b)
    b = re.sub(r',\s*\}', '}', b)
    return b

def fix_block(m):
    global nodes_removed
    head, body, tail = m.group(1), m.group(2), m.group(3)
    if 'aggregateRating' not in body:
        return m.group(0)
    new_body = clean(body)
    json.loads(new_body)  # raises if we broke it -> file skipped
    nodes_removed += body.count('"aggregateRating"')
    return head + new_body + tail

files = sorted(glob.glob(f"{PUB}/**/*.html", recursive=True))
for f in files:
    t = open(f, encoding='utf-8').read()
    if 'aggregateRating' not in t:
        continue
    try:
        new_t = block_re.sub(fix_block, t)
        for bm in block_re.finditer(new_t):
            json.loads(bm.group(2))  # full revalidation pass
    except Exception as e:
        failed.append((f, str(e)[:80]))
        continue
    if new_t != t:
        changed.append(f)
        if not DRY:
            open(f, 'w', encoding='utf-8').write(new_t)

remaining = [f for f in files if 'aggregateRating' in open(f, encoding='utf-8').read()]
print(("DRY-RUN " if DRY else "") + f"changed={len(changed)} nodes_removed={nodes_removed} "
      f"failed={len(failed)} remaining_with_aggregateRating={len(remaining) - (len(changed) if DRY else 0)}")
for f, e in failed[:15]:
    print("  FAIL:", f, "->", e)
if not DRY:
    still = [f for f in files if 'aggregateRating' in open(f, encoding='utf-8').read()]
    print("post-run files still containing aggregateRating:", len(still))
    for f in still[:15]:
        print("  REMAINS:", f)
