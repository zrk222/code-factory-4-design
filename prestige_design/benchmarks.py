"""Transparent fixture benchmark runner for token-contract detection."""
from __future__ import annotations

from pathlib import Path
import json

from .tokens import report_tokens, verify_tokens


def run_benchmarks(root: Path) -> dict:
    cases = []
    for manifest_path in sorted(root.glob("*.json")):
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        page = manifest_path.parent / manifest["page"]
        design = manifest_path.parent / manifest["design"]
        css_name = manifest.get("css")
        css = manifest_path.parent / css_name if css_name else None
        html = page.read_text(encoding="utf-8")
        css_text = css.read_text(encoding="utf-8") if css and css.exists() else ""
        lint = report_tokens(html, design, css_text)
        mutation = verify_tokens(html, design, css_text)
        actual_block = not lint["passed"] or not mutation["passed"]
        expected_block = bool(manifest["expected_block"])
        outcome = "true_positive" if expected_block and actual_block else "true_negative" if not expected_block and not actual_block else "false_negative" if expected_block else "false_positive"
        cases.append({"id": manifest["id"], "framework": manifest["framework"], "outcome": outcome,
                      "expected_block": expected_block, "actual_block": actual_block,
                      "lint": lint, "mutation": mutation})
    counts = {key: sum(case["outcome"] == key for case in cases) for key in ("true_positive", "true_negative", "false_positive", "false_negative")}
    positives = counts["true_positive"] + counts["false_negative"]
    negatives = counts["true_negative"] + counts["false_positive"]
    return {"schema": "prestige.benchmark.v1", "cases": cases, "counts": counts,
            "true_positive_rate": counts["true_positive"] / positives if positives else None,
            "false_positive_rate": counts["false_positive"] / negatives if negatives else None,
            "scope_limits": ["Fixture benchmark only; it is not a claim about production framework coverage.", "Runtime and flake metrics require repeated rendered runs and are not synthesized here."]}
