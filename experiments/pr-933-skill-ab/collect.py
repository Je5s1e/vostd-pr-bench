#!/usr/bin/env python3
"""Archive completed blind passes and check the evidence schema / frozen inputs."""
import hashlib
import json
import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent
MANIFEST = json.loads((ROOT / "manifest.json").read_text())
WORK = Path(MANIFEST["workspace"])
ROLES = ("maintainability", "proof-engineering", "specification")
FIELDS = {
    "id", "severity", "guideline", "location", "quoted_evidence", "problem",
    "key_premise", "experiment", "suggestion",
}


def main():
    errors = []
    records = []
    for item in json.loads((ROOT / "input-hashes.json").read_text()):
        path = WORK / item["path"]
        if not path.exists() or hashlib.sha256(path.read_bytes()).hexdigest() != item["sha256"]:
            errors.append(f"Input missing or changed: {item['path']}")
    for variant in ("baseline", "candidate"):
        for role in ROLES:
            source = WORK / variant / role
            dest = ROOT / "raw" / variant / role
            dest.mkdir(parents=True, exist_ok=True)
            expected_rules = (
                {"api-preconditions", "api-postconditions"}
                if role == "specification" else
                set(re.findall(r"<!-- guideline: ([\w-]+) -->",
                               (ROOT / "guidelines" / f"{role}.md").read_text()))
            )
            for case in MANIFEST["cases"]:
                name = case["sample_id"] + ".json"
                path = source / name
                if not path.exists():
                    errors.append(f"Missing output: {variant}/{role}/{name}")
                    continue
                data = json.loads(path.read_text())
                if set(data) != {"Findings", "Compliance"}:
                    errors.append(f"Wrong top-level keys: {path}")
                seen = set()
                for finding in data["Findings"]:
                    missing = FIELDS - set(finding)
                    if missing:
                        errors.append(f"Missing fields {missing}: {path}/{finding.get('id')}")
                    seen.update(re.findall(r"[a-z]+(?:-[a-z]+)+", finding["guideline"]))
                for item in data["Compliance"]:
                    seen.update(re.findall(r"[a-z]+(?:-[a-z]+)+", item["guideline"]))
                if expected_rules - seen:
                    errors.append(f"Rules uncovered {sorted(expected_rules - seen)}: {path}")
                if (dest / name).exists() and (dest / name).read_bytes() != path.read_bytes():
                    raise RuntimeError(f"Refusing to replace previously archived raw output: {dest / name}")
                shutil.copy2(path, dest / name)
                records.append({"variant": variant, "persona": role,
                                "sample_id": case["sample_id"],
                                "findings": len(data["Findings"]),
                                "compliance": len(data["Compliance"]),
                                "sha256": hashlib.sha256(path.read_bytes()).hexdigest()})
            notes = source / "execution-notes.txt"
            if notes.exists():
                shutil.copy2(notes, dest / notes.name)
    result = {"outputs": records, "errors": errors}
    (ROOT / "validation.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({"outputs": len(records), "errors": errors}, indent=2))
    raise SystemExit(bool(errors))


if __name__ == "__main__":
    main()
