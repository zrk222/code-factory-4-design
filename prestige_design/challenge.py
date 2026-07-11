"""Counterfactual visual-instrument challenge for Prestige."""
from __future__ import annotations

import re

from .audit import audit_html
from .score import score_design


def _remove_viewport_and_media(html: str) -> str:
    value = re.sub(r"<meta[^>]*viewport[^>]*>", "", html, flags=re.I)
    return re.sub(r"@media[^\{]*\{(?:[^{}]|\{[^{}]*\})*\}", "", value, flags=re.I | re.S)


def _empty_actions(html: str) -> str:
    return re.sub(
        r"(<(?:button|a)\b[^>]*>).*?(</(?:button|a)>)",
        r"\1\2",
        html,
        flags=re.I | re.S,
    )


def challenge_html(html: str, *, purpose: str = "developer", workflow: str = "product") -> dict:
    baseline = score_design(html, workflow_key=workflow, purpose_key=purpose)
    mutations = [
        ("hidden_surface", html.replace("</style>", "body{display:none}</style>", 1)),
        ("broken_mobile", _remove_viewport_and_media(html)),
        ("empty_primary_action", _empty_actions(html)),
    ]
    results = []
    for name, mutant in mutations:
        audit = audit_html(mutant)
        score = score_design(mutant, workflow_key=workflow, purpose_key=purpose)
        targeted_failure = (
            bool(audit.hard_failures) if name == "hidden_surface" else
            score.mobile_score < 70 if name == "broken_mobile" else
            score.cta_score < 70
        )
        killed = targeted_failure or not audit.passed or not score.passed
        results.append({
            "unit": name,
            "killed": killed,
            "evidence": (f"audit_passed={audit.passed}; score_passed={score.passed}; "
                         f"score={score.conversion_score}; mobile={score.mobile_score}; cta={score.cta_score}"),
        })
    killed = sum(bool(item["killed"]) for item in results)
    return {
        "schema": "factory.challenge.v1",
        "brick": "prestige",
        "feature": None,
        "stage": "design_counterfactual",
        "passed": baseline.passed and killed == len(results),
        "baseline": {"passed": baseline.passed, "score": baseline.conversion_score, "grade": baseline.grade},
        "mutants_total": len(results),
        "mutants_killed": killed,
        "mutations": results,
        "scope": "source challenge; pair with render-audit for browser evidence",
    }
