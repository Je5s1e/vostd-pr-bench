"""Recompute published tables from saved judgments without modifying this package."""
import hashlib
import subprocess
import sys
import tempfile
from pathlib import Path

PACKAGE = Path(__file__).resolve().parent.parent
ARTIFACTS = {
    **{name: 'data/' + name for name in [
        'metrics.json', 'cases.json', 'cases.csv', 'findings.json', 'findings.csv',
        'label_matches.json', 'label_matches.csv', 'rule_metrics.csv']},
    '逐条匹配.md': 'reports/label-matches.md',
}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    with tempfile.TemporaryDirectory(prefix='revolve-eval-') as tmp:
        output = Path(tmp) / 'results'
        result = subprocess.run(
            [sys.executable, str(PACKAGE / 'scripts/evaluate.py'),
             '--inputs', str(PACKAGE / 'evidence'), '--output', str(output)],
            capture_output=True, text=True,
        )
        if result.returncode:
            print(result.stderr, file=sys.stderr)
            return result.returncode
        failed = [target for name, target in ARTIFACTS.items()
                  if not (output/name).is_file()
                  or digest(output/name) != digest(PACKAGE/target)]
        if failed:
            print('FAIL: recomputed artifacts differ: ' + ', '.join(failed), file=sys.stderr)
            return 1
    print(f'PASS: {len(ARTIFACTS)} artifacts reproduce byte-for-byte; published files unchanged.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
