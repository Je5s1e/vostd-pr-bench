"""Read-only integrity checks for the portable evaluation package."""
import argparse
import csv
import hashlib
import json
import re
import sys
from collections import Counter
from pathlib import Path
from urllib.parse import unquote, urlsplit

PACKAGE = Path(__file__).resolve().parent.parent


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(rel):
    return json.loads((PACKAGE/rel).read_text(encoding='utf-8'))


def ignored(path):
    return any(p in {'build', '__pycache__', '.git', '.DS_Store'} for p in path.parts)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--review-root', type=Path)
    parser.add_argument('--benchmark-root', type=Path)
    args = parser.parse_args()
    require(bool(args.review_root) == bool(args.benchmark_root),
            'Provide --review-root and --benchmark-root together')

    manifest = read('provenance/package_manifest.json')
    entries = manifest['files']
    for rel, expected in entries.items():
        path = (PACKAGE/rel).resolve()
        require(PACKAGE in path.parents, f'Manifest path outside package: {rel}')
        require(path.is_file(), f'Missing packaged file: {rel}')
        require(digest(path) == expected, f'Changed packaged file: {rel}')
    actual = {str(p.relative_to(PACKAGE)) for p in PACKAGE.rglob('*')
              if p.is_file() and not ignored(p.relative_to(PACKAGE))
              and p != PACKAGE/'provenance/package_manifest.json'}
    require(actual == set(entries), f'Untracked/missing package files: {actual ^ set(entries)}')

    snapshot = read('evidence/snapshot.json')
    cases = read('data/cases.json')
    labels = read('data/label_matches.json')
    findings = read('data/findings.json')
    metrics = read('data/metrics.json')
    frozen = {d['sample']: d for d in snapshot['cases']}
    require(len(frozen) == len(snapshot['cases']) == len(cases) == 179, 'Sample count mismatch')
    require(set(snapshot['all_samples']) == set(frozen), 'Frozen sample inventory mismatch')
    require({c['sample'] for c in cases} == set(frozen), 'Case coverage mismatch')
    require(len({c['pr_number'] for c in cases}) == metrics['distinct_pr_count'] == 164,
            'PR count mismatch')
    expected_labels = {(d['sample'], i['id']) for d in snapshot['cases'] for i in d['labels']['issues']}
    require(len(expected_labels) == len(labels) == 244, 'Label count mismatch')
    require({(r['sample'], r['label_id']) for r in labels} == expected_labels, 'Label coverage mismatch')
    require(len(findings) == 300, 'Finding count mismatch')
    for sample, d in frozen.items():
        require(hashlib.sha256(d['review'].encode('utf-8')).hexdigest() == d['review_sha256'],
                f'Public review text hash mismatch: {sample}')
    keys = {(f['sample'], f['finding']) for f in findings}
    require(len(keys) == len(findings), 'Duplicate finding keys')
    for r in labels:
        require(all((r['sample'], n) in keys for n in r['finding_ids']),
                f'Invalid finding reference: {r["label_id"]}')
    counts = Counter(r['status'] for r in labels)
    require(counts == {'F':58, 'P':7, 'M':176, 'X':3}, 'Judgment totals mismatch')
    for key, status in [('full','F'),('partial','P'),('miss','M'),('fixed_in_after','X')]:
        require(metrics['issue_stats'][key] == counts[status], f'Metric mismatch: {key}')
    require(metrics['issue_stats']['n'] == len(labels), 'Metric label denominator mismatch')
    require(metrics['issue_stats']['strict_recall'] == counts['F']/len(labels), 'Recall mismatch')
    require(metrics['findings'] == sum(c['findings'] for c in cases) == len(findings), 'Finding totals mismatch')
    require(Counter(f['severity'] for f in findings) == metrics['severity'], 'Severity counts mismatch')
    require(Counter(f['benchmark_status'] for f in findings) == metrics['finding_status'], 'Finding statuses mismatch')
    for name, expected in [('cases',cases),('label_matches',labels),('findings',findings)]:
        with (PACKAGE/f'data/{name}.csv').open(encoding='utf-8-sig', newline='') as f:
            require(len(list(csv.DictReader(f))) == len(expected), f'CSV row count mismatch: {name}')

    links = 0
    for path in PACKAGE.rglob('*.md'):
        for target in re.findall(r'\]\(([^)]+)\)', path.read_text(encoding='utf-8')):
            parsed = urlsplit(target)
            if parsed.scheme or target.startswith('#'):
                continue
            local = (path.parent / unquote(parsed.path)).resolve()
            require(local == PACKAGE or PACKAGE in local.parents, f'Nonportable link: {path.name}: {target}')
            require(local.exists(), f'Broken link: {path.name}: {target}')
            links += 1

    if args.review_root:
        for row in read('provenance/input_manifest.json'):
            sid = row['sample']
            review, bench = args.review_root/sid, args.benchmark_root/sid
            require(digest(review/'review.md') in {row['review_sha256'], frozen[sid]['review_sha256']},
                    f'External review hash mismatch: {sid}')
            require(digest(review/'diff.patch') == digest(bench/'diff.patch') == row['diff_sha256'],
                    f'External diff mismatch: {sid}')
            for name in ['labels', 'metadata']:
                require(digest(bench/(name+'.json')) == row[name+'_sha256'],
                        f'External {name} hash mismatch: {sid}')
        for row in read('provenance/context_integrity.json'):
            rel = Path(row['sample'])/row['version']/row['path']
            require(digest(args.review_root/rel) == digest(args.benchmark_root/rel) == row['sha256'],
                    f'External source context mismatch: {rel}')
        print('PASS: external review/benchmark inputs and 231 source contexts match frozen hashes.')
    print(f'PASS: {len(entries)} package files, {links} local links, 179 snapshots / 164 PRs / 244 labels / 300 findings.')
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except (ValueError, KeyError, OSError, json.JSONDecodeError) as exc:
        print(f'FAIL: {exc}', file=sys.stderr)
        sys.exit(1)
