#!/usr/bin/env python3
"""Validate one existing or incremental bench case using only the standard library."""
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import sys


def validate(case):
    errors = []

    def check(condition, message):
        if not condition:
            errors.append(message)

    def local_path(root, value):
        if not isinstance(value, str) or not value:
            raise ValueError('empty or non-string relative path')
        rel = PurePosixPath(value)
        if rel.is_absolute() or '..' in rel.parts:
            raise ValueError(f'unsafe path: {value}')
        target = root / value
        if not target.resolve().is_relative_to(root.resolve()):
            raise ValueError(f'path escapes snapshot: {value}')
        return target

    metadata = json.loads((case / 'metadata.json').read_text())
    labels = json.loads((case / 'labels.json').read_text())
    sample = case.name
    check(metadata['sample_id'] == labels['sample_id'] == sample, 'sample_id mismatch')
    check(metadata['schema_version'] == labels['schema_version'] == 1, 'unsupported schema')
    check(metadata['repository'] == 'https://github.com/asterinas/vostd', 'wrong upstream')
    for key in ('base_sha', 'head_sha'):
        check(bool(re.fullmatch(r'[0-9a-f]{40}', metadata[key])), f'invalid {key}')
    check(sample == f"pr-{metadata['pr_number']}-{metadata['head_sha'][:12]}", 'directory name mismatch')
    check(hashlib.sha256((case / 'diff.patch').read_bytes()).hexdigest() == metadata['diff_sha256'], 'diff hash mismatch')
    issues = labels['issues']
    check(isinstance(issues, list) and len(issues) > 0, 'issues must be a nonempty array')
    check(metadata['known_issue_count'] == len(issues), 'issue count mismatch')
    for version, sha_key in (('before', 'base_sha'), ('after', 'head_sha')):
        root = case / version
        check((root / 'ostd').is_dir(), f'{version}: missing ostd')
        info = metadata['versions'][version]
        check(info['commit'] == metadata[sha_key], f'{version}: commit mismatch')
        count = sum(p.is_file() or p.is_symlink() for p in root.rglob('*'))
        check(info['file_count'] == count, f'{version}: file_count expected {count}')
        for name in info['license_files']:
            check(local_path(root, name).is_file(), f'{version}: missing license {name}')
        for submodule in info['submodules']:
            check(bool(re.fullmatch(r'[0-9a-f]{40}', submodule['sha'])), 'invalid submodule SHA')
            if submodule['included']:
                check(local_path(root, submodule['path']).is_dir(), 'missing included submodule')
    for name in metadata['changed_paths']:
        check(any(local_path(case / version, name).exists() or (case / version / name).is_symlink()
                  for version in ('before', 'after')), f'changed path absent: {name}')
    seen = set()
    for issue in issues:
        ident = issue['id']
        check(ident.startswith(sample + ':') and ident not in seen, f'invalid/duplicate issue id: {ident}')
        seen.add(ident)
        check(issue['category'] in ('guideline', 'semantic'), f'{ident}: invalid category')
        for key in ('description', 'rationale', 'source_evidence', 'review_url', 'verification'):
            check(isinstance(issue[key], str) and bool(issue[key].strip()), f'{ident}: empty {key}')
        check(bool(issue['locations']), f'{ident}: missing locations')
        for location in issue['locations']:
            version = location['version']
            if version not in ('before', 'after'):
                errors.append(f'{ident}: invalid version')
                continue
            source = local_path(case / version, location['path'])
            lines = len(source.read_text().splitlines())
            start, end = location['start_line'], location['end_line']
            check(type(start) is int and type(end) is int and 1 <= start <= end <= lines,
                  f'{ident}: invalid location in {source}')
        if metadata['original_split'] == 'incremental':
            check(issue['original_label_id'] is None, f'{ident}: new issue has frozen label id')
            check(bool(issue['sources']), f'{ident}: missing provenance')
    if metadata['original_split'] == 'incremental':
        check(labels['status'] == 'incremental_source_adjudicated', 'invalid incremental status')
        for key in ('collected_at', 'reviewed_at', 'upstream_updated_at', 'source_urls', 'guideline_sources'):
            check(key in metadata['collection'], f'missing collection.{key}')
    return errors


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('case_dir', type=Path)
    args = parser.parse_args()
    try:
        errors = validate(args.case_dir)
    except (KeyError, TypeError, ValueError, OSError) as exc:
        errors = [f'malformed or unreadable case: {exc}']
    for error in errors:
        print(f'ERROR: {error}', file=sys.stderr)
    if errors:
        return 1
    print(f'OK: {args.case_dir.name}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
