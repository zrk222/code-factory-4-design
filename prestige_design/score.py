"""The Precision Scoring Engine — fuses the five laws, the cognitive-bias
suite, CTA/hook verification, and the mobile judge into one workflow-weighted
conversion-readiness score with prioritized, precise recommendations ranked by
conversion impact. This is the 'score precisely with recommendation' upgrade."""
from __future__ import annotations
from dataclasses import dataclass, field
from .audit import audit_html
from .biases import run_bias_suite
from .cta_hooks import verify_cta_and_hooks
from .mobile_judge import judge_mobile
from .workflows import get_workflow

@dataclass
class PrecisionReport:
    workflow: str
    conversion_score: int = 0        # 0..100, workflow-weighted composite
    grade: str = "F"
    law_scores: dict = field(default_factory=dict)
    bias_scores: dict = field(default_factory=dict)
    cta_score: int = 0
    hook_score: int = 0
    mobile_score: int = 0
    primary_cta: str = ""
    hook: str = ""
    hard_failures: list = field(default_factory=list)
    recommendations: list = field(default_factory=list)   # prioritized, impact-ranked

    @property
    def passed(self) -> bool:
        return not self.hard_failures and self.conversion_score >= 70

def _extract_css(html: str, css_extra: str) -> str:
    import re
    inline = " ".join(re.findall(r"<style[^>]*>(.*?)</style>", html, re.S | re.I))
    return css_extra + "\n" + inline

def score_design(html: str, css_extra: str = "", workflow_key: str = "conversion") -> PrecisionReport:
    css = _extract_css(html, css_extra)
    wf = get_workflow(workflow_key)
    r = PrecisionReport(workflow=wf.name)

    # 1. five laws
    law = audit_html(html, css_extra)
    r.law_scores = law.scores
    r.hard_failures = list(law.hard_failures)

    # 2. cognitive biases
    biases = run_bias_suite(html, css)
    r.bias_scores = {b.name: round(b.quality * 100) for b in biases if b.present or b.weight}

    # 3. CTA + hooks
    ch = verify_cta_and_hooks(html)
    r.cta_score, r.hook_score = ch.cta_score, ch.hook_score
    r.primary_cta, r.hook = ch.primary_cta_text, ch.hook_text

    # 4. mobile
    mob = judge_mobile(html, css)
    r.mobile_score = mob.score

    # ---- workflow-weighted composite ----
    # base channels with default weights
    channels = {
        "halo": law.scores.get("halo", 0), "fluency": law.scores.get("fluency", 0),
        "trust": law.scores.get("trust", 0), "peak": law.scores.get("peak", 0),
        "horn": law.scores.get("horn", 0), "cta": ch.cta_score, "hook": ch.hook_score,
        "mobile": mob.score,
    }
    # fold bias quality into their related channels
    bias_map = {"Von Restorff (CTA isolation)": "cta", "Social Proof": "social_proof",
                "Cognitive Fluency": "fluency", "Anchoring (price)": "anchoring",
                "Loss Aversion (scarcity/urgency)": "loss_aversion", "Reciprocity": "reciprocity"}
    for b in biases:
        ch_key = bias_map.get(b.name)
        if ch_key and ch_key not in channels:
            channels[ch_key] = round(b.quality * 100)

    weights = {k: 1.0 for k in channels}
    for k, mult in wf.weights.items():
        if k in weights:
            weights[k] = mult
    total_w = sum(weights.values())
    composite = sum(channels[k] * weights[k] for k in channels) / total_w
    r.conversion_score = round(composite)
    r.grade = ("A" if composite >= 88 else "B" if composite >= 75 else
               "C" if composite >= 60 else "D" if composite >= 45 else "F")

    # ---- prioritized recommendations (ranked by conversion impact) ----
    recs = []
    for b in biases:
        if b.recommendation:
            recs.append((b.weight, f"[{b.name}] {b.recommendation}"))
    for rec in ch.recommendations:
        recs.append((18, f"[CTA/Hook] {rec}"))
    for rec in mob.recommendations:
        recs.append((14, f"[Mobile] {rec}"))
    # law-level gaps
    law_recs = {"halo":"Strengthen the hero — bold single headline + high-res cover image (50ms halo).",
                "trust":"Add security + social-proof cues at decision points.",
                "peak":"Add micro-interactions (hover, transitions, inline validation) for peaks of delight.",
                "horn":"Fix consistency/mobile stability to avoid the Horn Effect."}
    for law_key, sc in law.scores.items():
        if sc < 70 and law_key in law_recs:
            recs.append((12, f"[{law_key.title()}] {law_recs[law_key]}"))
    # dedupe + rank by impact desc
    seen = set(); ranked = []
    for w, msg in sorted(recs, key=lambda x: -x[0]):
        if msg not in seen:
            seen.add(msg); ranked.append(msg)
    r.recommendations = ranked
    return r
