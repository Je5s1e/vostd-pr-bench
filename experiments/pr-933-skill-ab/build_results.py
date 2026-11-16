#!/usr/bin/env python3
"""Render results from frozen raw outputs and explicit human-readable adjudication.

This script does not run a model or infer correctness by keyword matching.
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
VARIANTS = ("baseline", "candidate")
ROLES = ("maintainability", "proof-engineering", "specification")


def main():
    manifest = json.loads((ROOT / "manifest.json").read_text())
    judgments = json.loads((ROOT / "adjudication.json").read_text())
    indexed = {(x["variant"], x["persona"], x["finding_id"]): x for x in judgments}
    metrics = {v: {"target_hits": 0, "target_total": 6,
                   "all_label_hits": 0, "all_label_total": 7} for v in VARIANTS}
    matches = json.loads((ROOT / "matches.json").read_text())
    for row in matches:
        for v in VARIANTS:
            if row[v]["status"] == "hit":
                metrics[v]["all_label_hits"] += 1
                metrics[v]["target_hits"] += int(row["target"])
                for finding_id in row[v]["finding_ids"]:
                    assert any(x["variant"] == v and x["finding_id"] == finding_id
                               and x["verdict"] == "confirmed" for x in judgments)
    for v in VARIANTS:
        for case in manifest["cases"]:
            sample = case["sample_id"]
            findings = []
            for role in ROLES:
                path = ROOT / "raw" / v / role / f"{sample}.json"
                for item in json.loads(path.read_text())["Findings"]:
                    verdict = indexed[(v, role, item["id"])]
                    findings.append((role, item, verdict))
            report = [f"# Review: {sample} ({v})", "",
                      "> Mode: files, full target file. Frozen source and guideline hashes are in manifest.json / input-hashes.json.",
                      "> Static source review only. Historical CI status was not established and Verus was not run.", "",
                      f"Target: `{case['target']}`. The raw persona outputs remain unchanged; the annotations below record static adjudication.", ""]
            for severity in ("high", "medium", "low"):
                subset = [(r, f, j) for r, f, j in findings if f["severity"] == severity]
                if not subset:
                    continue
                report.extend([f"## {severity.title()}", ""])
                for role, f, j in subset:
                    prefix = "(unverified) " if j["verdict"] == "uncertain" else ""
                    report.extend([f"### {f['id']} — {f['guideline']}", "",
                                   f"Location: `{j.get('corrected_location', f['location'])}`. Persona: {role}. Verdict: **{j['verdict']}**.", "",
                                   prefix + f["problem"], "", "```text", f["quoted_evidence"], "```", "",
                                   "Suggested correction: " + j.get("corrected_suggestion", f["suggestion"]), "",
                                   "Evidence check: " + j["reason"], ""])
            report.extend(["## Evidence check record", "",
                           "Full Findings and Compliance records, including unexecuted experiments, are in the three raw persona JSON files. No verifier-certified fix is claimed. Missing dependency evidence is not evidence of compliance. Unmatched findings are not automatically false positives.", "",
                           "## Addendum: cross-persona resolution", "",
                           "Keep public abstract contracts usable while hiding private representation. Correct misleading verification documentation with an explicit limitation note rather than silently replacing inherited runtime prose. Findings with distinct root causes remain separate; no exact duplicate root cause across the three personas was found in this batch.", ""])
            path = ROOT / "reviews" / v / f"{sample}.md"
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("\n".join(report))
    (ROOT / "metrics.json").write_text(json.dumps(metrics, indent=2) + "\n")
    print(json.dumps(metrics, indent=2))


if __name__ == "__main__":
    main()
