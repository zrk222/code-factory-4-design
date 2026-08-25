"""Ethical emotional-design audit and counterfactual challenge.

The source audit is deliberately conservative: it verifies explicit interface
signals and rejects observable coercive patterns. It does not infer a user's
feelings or claim that an interface causes retention, delight, or conversion.
"""
from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field
from pathlib import Path

from .attribution import Attribution, FailureClass, UnitResult


DIMENSIONS = (
    "visceral",
    "behavioral",
    "reflective",
    "safe_failure",
    "agency",
    "inclusion",
)

INTENTS = {
    "calm": "Reduce anxiety with restrained hierarchy, predictable feedback, and reversible actions.",
    "confidence": "Make state, evidence, and the next safe action unmistakable.",
    "momentum": "Show honest progress without punishing pauses or manufacturing urgency.",
    "delight": "Use brief, optional sensory polish after meaningful success.",
    "belonging": "Use respectful, inclusive language without social pressure or shame.",
}


@dataclass(frozen=True)
class EmotionalFinding:
    dimension: str
    code: str
    severity: str
    mode: str
    observation: str
    problem: str
    fix: str
    evidence: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "dimension": self.dimension,
            "code": self.code,
            "severity": self.severity,
            "mode": self.mode,
            "observation": self.observation,
            "problem": self.problem,
            "fix": self.fix,
            "evidence": self.evidence,
        }


@dataclass
class EmotionalReport:
    intent: str
    scores: dict[str, int]
    findings: list[EmotionalFinding]
    recommendations: list[str]
    source_sha256: str

    @property
    def blocking_findings(self) -> list[EmotionalFinding]:
        return [item for item in self.findings if item.severity in {"P1", "P2"}]

    @property
    def overall(self) -> int:
        return round(sum(self.scores.values()) / len(self.scores))

    @property
    def passed(self) -> bool:
        return not self.blocking_findings and self.overall >= 70 and min(self.scores.values()) >= 45

    @property
    def attribution(self) -> Attribution:
        units = [
            UnitResult(
                unit=f"emotion:{dimension}",
                stage="emotional_design",
                passed=score >= 70,
                evidence=f"score={score}; threshold=70",
                failure_class=None if score >= 70 else FailureClass.WRONG_OUTPUT,
            )
            for dimension, score in self.scores.items()
        ]
        return Attribution("emotional_design", len(units), sum(unit.passed for unit in units), units)

    def to_dict(self) -> dict:
        return {
            "schema": "prestige.emotional-design.v1",
            "intent": self.intent,
            "intent_directive": INTENTS[self.intent],
            "overall": self.overall,
            "passed": self.passed,
            "scores": self.scores,
            "blocking": len(self.blocking_findings),
            "findings": [item.to_dict() for item in self.findings],
            "recommendations": self.recommendations,
            "source_sha256": self.source_sha256,
            "attribution": self.attribution.to_dict(),
            "claim_boundary": (
                "Static source evidence only. This receipt does not measure emotion, retention, "
                "conversion, accessibility conformance, or rendered haptic quality."
            ),
            "markers": [
                "EMOTIONAL_SCHEMA_V1",
                "EMOTIONAL_TRIPARTITE_REVIEW",
                "SAFE_FAILURE_REVIEW",
                "AGENCY_REVIEW",
                "ANTI_MANIPULATION_REVIEW",
            ],
        }


def _has(pattern: str, text: str, flags: int = re.I | re.S) -> bool:
    return re.search(pattern, text, flags) is not None


def _plain(html: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", html)).strip().lower()


def _finding(
    findings: list[EmotionalFinding],
    dimension: str,
    code: str,
    severity: str,
    observation: str,
    problem: str,
    fix: str,
    **evidence,
) -> None:
    findings.append(EmotionalFinding(dimension, code, severity, "deterministic", observation, problem, fix, evidence))


def _review_visceral(html: str, style: str, intent: str) -> tuple[int, list[EmotionalFinding], list[str]]:
    score, findings, recommendations = 100, [], []
    if not _has(r'data-emotion-intent\s*=\s*["\'](?:calm|confidence|momentum|delight|belonging)["\']', html):
        score -= 20
        recommendations.append(f'Declare the intended feeling with data-emotion-intent="{intent}" on the primary journey region.')
    if not _has(r":root\s*\{|var\(--", style):
        score -= 25
        recommendations.append("Use named visual tokens so color, rhythm, type, and motion express one coherent emotional intent.")
    if not (_has(r"<h1\b", html) and _has(r"font-(?:size|weight)\s*:", style)):
        score -= 20
        recommendations.append("Create an immediately legible heading and typographic hierarchy; do not rely on mood alone.")
    return score, findings, recommendations


def _review_behavioral(html: str, plain: str) -> tuple[int, list[EmotionalFinding], list[str]]:
    score, findings, recommendations = 100, [], []
    has_live_state = _has(r'aria-live\s*=|role\s*=\s*["\'](?:status|progressbar)["\']|data-state\s*=', html)
    has_loading_copy = _has(r"(?:loading|saving|checking|processing|working|preparing)(?:\.{3}|&hellip;|…)?", plain)
    has_progress = _has(r"<progress\b|aria-valuenow\s*=|data-progress\s*=", html)
    if not (has_live_state and (has_loading_copy or has_progress)):
        score -= 35
        recommendations.append("Pair non-instant actions with a named live status and truthful progress or active-state copy.")
    if _has(r"<button[^>]*(?:disabled|aria-disabled)", html) and not has_live_state:
        score -= 20
        _finding(findings, "behavioral", "E_STATE_SILENT", "P2", "A disabled action is present without a live status region.", "The interface can remove control without explaining whether work is progressing.", "Expose an aria-live status and update the action label while work is active.")
    return score, findings, recommendations


def _review_reflective(plain: str) -> tuple[int, list[EmotionalFinding], list[str]]:
    score, findings, recommendations = 100, [], []
    if not _has(r"(?:complete|completed|success|receipt|summary|what happens next|next step|saved)", plain):
        score -= 30
        recommendations.append("End the primary journey with a concrete confirmation, receipt, or next step.")
    if not _has(r"(?:history|progress|resume|continue|recent|previous|activity)", plain):
        score -= 15
        recommendations.append("Show honest continuity such as saved progress or resumable work without imposing streak loss.")
    return score, findings, recommendations


def _review_safe_failure(html: str, plain: str) -> tuple[int, list[EmotionalFinding], list[str]]:
    score, findings, recommendations = 100, [], []
    failure_pattern = r'<(?P<tag>[a-z][\w-]*)\b(?P<attrs>[^>]*(?:role\s*=\s*["\']alert["\']|class\s*=\s*["\'][^"\']*(?:error|failure|warning)[^"\']*["\'])[^>]*)>(?P<body>.*?)</(?P=tag)>'
    failure_regions = [match.group("body") for match in re.finditer(failure_pattern, html, re.I | re.S)]
    recovery_pattern = r"(?:retry|try again|edit|undo|revert|restore|back|cancel|contact support|review details)"
    has_recovery = any(_has(recovery_pattern, _plain(region)) for region in failure_regions)
    if failure_regions and not has_recovery:
        score -= 50
        _finding(findings, "safe_failure", "E_FAILURE_DEAD_END", "P1", "A visible failure surface has no recovery action.", "A dead end converts an error into helplessness and can strand the user.", "Add a specific retry, edit, revert, back, or support action beside the explanation.")
    elif not failure_regions:
        score -= 20
        recommendations.append("Design and label a recoverable error state before claiming the journey is emotionally resilient.")
    if _has(r"(?:you failed|your fault|you disappointed|do not let us down|don.t lose everything|shame on you)", plain):
        score -= 60
        _finding(findings, "safe_failure", "E_PUNITIVE_COPY", "P1", "Punitive or shaming failure copy was found.", "Shame and guilt trade short-term pressure for damaged trust and reduced psychological safety.", "State what happened without blame, preserve progress, and offer a recovery action.")
    return score, findings, recommendations


def _review_agency(html: str, plain: str) -> tuple[int, list[EmotionalFinding], list[str]]:
    score, findings, recommendations = 100, [], []
    agency_terms = ("retry", "edit", "undo", "revert", "cancel", "pause", "review", "approve", "reject")
    if sum(term in plain for term in agency_terms) < 2:
        score -= 30
        recommendations.append("Provide at least two clear control paths such as edit/retry and cancel/revert.")
    has_ai = _has(r'data-(?:ai-generated|automation|agent-output)\s*=', html) or _has(
        r"(?:ai-generated|generated by ai|automated suggestion|agent suggestion|agent result|ai result)", plain
    )
    has_disclosure = _has(r"(?:ai-generated|generated by ai|automated suggestion|agent suggestion|review before applying)", plain)
    if has_ai and not has_disclosure:
        score -= 35
        _finding(findings, "agency", "E_AI_AUTHORSHIP_HIDDEN", "P2", "AI or agent behavior is named without an authorship or automation disclosure.", "Hidden automation weakens informed control and reflective trust.", "Label generated output and keep review, edit, reject, and revert actions available.")
    return score, findings, recommendations


def _review_inclusion(blob: str, plain: str, style: str) -> tuple[int, list[EmotionalFinding], list[str]]:
    score, findings, recommendations = 100, [], []
    if _has(r"animation\s*:|transition\s*:", style) and not _has(r"prefers-reduced-motion", style):
        score -= 45
        _finding(findings, "inclusion", "E_REDUCED_MOTION_MISSING", "P2", "Motion is defined without a prefers-reduced-motion alternative.", "Sensory delight can become discomfort when motion preferences are ignored.", "Disable non-essential animation or substitute a cross-fade under prefers-reduced-motion.")
    color_only = _has(r"(?:green means|red means|shown in red|shown in green|color indicates)", plain) and not _has(r"(?:icon|label|text|pattern|symbol)", plain)
    if color_only:
        score -= 50
        _finding(findings, "inclusion", "E_COLOR_ONLY_STATE", "P1", "Critical state is described by color without a redundant cue.", "Color-only meaning excludes users who cannot reliably perceive the color difference.", "Add explicit text, iconography, and shape or border differences.")
    manipulative_patterns = (r'<input\b(?=[^>]*type\s*=\s*["\']checkbox["\'])(?=[^>]*\bchecked\b)[^>]*>', r'data-(?:fake-scarcity|variable-reward|confirmshaming)\s*=', r"(?:no thanks,? i (?:hate|don.t want)|keep my bad|lose (?:all|your) progress|streak dies)")
    if any(_has(pattern, blob) for pattern in manipulative_patterns):
        score -= 70
        _finding(findings, "inclusion", "E_MANIPULATIVE_PATTERN", "P1", "A preselected, confirm-shaming, fake-scarcity, or compulsion marker was found.", "The pattern reduces informed choice or exploits loss anxiety.", "Use explicit opt-in, truthful timing, predictable rewards, and neutral decline language.")
    return score, findings, recommendations


def audit_emotional_design(html: str, css: str = "", *, intent: str = "confidence") -> EmotionalReport:
    """Audit explicit emotional-design signals without inferring user affect."""
    resolved_intent = intent if intent in INTENTS else "confidence"
    style = css + "\n" + " ".join(re.findall(r"<style[^>]*>(.*?)</style>", html, re.I | re.S))
    plain = _plain(html)
    reviews = {
        "visceral": _review_visceral(html, style, resolved_intent),
        "behavioral": _review_behavioral(html, plain),
        "reflective": _review_reflective(plain),
        "safe_failure": _review_safe_failure(html, plain),
        "agency": _review_agency(html, plain),
        "inclusion": _review_inclusion(html + "\n" + style, plain, style),
    }
    scores = {key: max(0, result[0]) for key, result in reviews.items()}
    findings = [finding for result in reviews.values() for finding in result[1]]
    recommendations = list(dict.fromkeys(item for result in reviews.values() for item in result[2]))
    return EmotionalReport(resolved_intent, scores, findings, recommendations, hashlib.sha256((html + "\n" + css).encode("utf-8")).hexdigest())


def challenge_emotional_design(html: str, css: str = "", *, intent: str = "confidence") -> dict:
    """Prove that the gate rejects isolated emotional-safety regressions."""
    baseline = audit_emotional_design(html, css, intent=intent)
    mutants = (
        ("coercive_copy", html.replace("</body>", "<p>You failed. Do not let us down.</p></body>", 1)),
        ("prechecked_opt_in", html.replace("</body>", '<input type="checkbox" checked> Keep nudging me</body>', 1)),
        (
            "motion_without_adaptation",
            html.replace("prefers-reduced-motion", "motion-preference-disabled"),
            css.replace("prefers-reduced-motion", "motion-preference-disabled") + "\n.pulse{animation:pulse 1s infinite}",
        ),
    )
    results = []
    for item in mutants:
        name, mutant_html, *mutant_css = item
        report = audit_emotional_design(mutant_html, mutant_css[0] if mutant_css else css, intent=intent)
        results.append({
            "unit": name,
            "killed": not report.passed and bool(report.blocking_findings),
            "blocking_codes": [finding.code for finding in report.blocking_findings],
        })
    killed = sum(item["killed"] for item in results)
    return {
        "schema": "prestige.emotional-challenge.v1",
        "passed": baseline.passed and killed == len(results),
        "baseline_passed": baseline.passed,
        "mutants_total": len(results),
        "mutants_killed": killed,
        "mutations": results,
        "marker": "EMOTIONAL_MUTATIONS_REJECTED" if killed == len(results) else "EMOTIONAL_MUTATION_SURVIVED",
    }


def write_emotional_receipt(payload: dict, destination: Path) -> Path:
    destination = Path(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_suffix(destination.suffix + ".tmp")
    temporary.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    temporary.replace(destination)
    return destination.resolve()
