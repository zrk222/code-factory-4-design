"""The Cognitive Bias Engine — maps psychological triggers to concrete,
detectable interface elements. This is the depth upgrade: instead of five
vague 'laws', the audit checks whether specific, research-backed biases are
actually engaged in the markup, and scores how well each is executed.

Early credibility judgments can form in fractions of a second. Treat every
conversion hypothesis as project-specific until an experiment receipts it. Each bias below has:
a detector (is it present?), a quality check (is it done right?), and a
precise recommendation (how to fix it).
"""
from __future__ import annotations
import re
from dataclasses import dataclass, field

@dataclass
class BiasCheck:
    name: str
    present: bool
    quality: float          # 0..1 — how well executed when present
    weight: int             # conversion impact weight
    recommendation: str = ""
    evidence: str = ""

def _has(p, t): return re.search(p, t, re.I) is not None
def _count(p, t): return len(re.findall(p, t, re.I))

def check_von_restorff(html: str, css: str) -> BiasCheck:
    """Isolation effect: the CTA must visually stand out. Single, contrasting
    primary button. Competing equal-weight CTAs KILL this (a documented mistake)."""
    buttons = re.findall(r'<(?:button|a)[^>]*class=["\'][^"\']*(?:btn|button|cta)[^"\']*["\'][^>]*>', html, re.I)
    primary_markers = _count(r'(btn-primary|cta-primary|primary|hero-cta)', html)
    has_contrast = _has(r'(background|bg-)[^;]*(var\(--|#[0-9a-f]{3,6}|rgb)', css)
    present = len(buttons) > 0 or _count(r'<button', html) > 0
    # too many equal CTAs = failure of isolation
    total_ctas = _count(r'<button|class=["\'][^"\']*(btn|cta)', html)
    quality = 1.0
    rec = ""
    if total_ctas > 4:
        quality = 0.4; rec = f"{total_ctas} button-like elements compete — isolate ONE primary CTA with unique color/size (Von Restorff)."
    elif primary_markers == 0 and total_ctas > 1:
        quality = 0.6; rec = "No distinct 'primary' CTA class — mark the single most important action so it stands out."
    elif not has_contrast:
        quality = 0.7; rec = "Primary CTA needs a contrasting color vs background to trigger the isolation effect."
    return BiasCheck("Von Restorff (CTA isolation)", present, quality, 20, rec,
                     f"{total_ctas} CTA-like elements, {primary_markers} marked primary")

def check_anchoring(html: str, css: str) -> BiasCheck:
    """Anchoring: show a higher reference price next to the actual price so the
    real price reads as a deal. Present only relevant on pricing UIs."""
    has_price = _has(r'[\$£€]\s?\d', html)
    if not has_price:
        return BiasCheck("Anchoring (price)", False, 1.0, 12, "", "no pricing shown (N/A)")
    # look for a struck-through / original / 'was' price near the active one
    has_anchor = (_has(r'(was|originally|reg\.|<s>|<del>|line-through|strikethrough|compare)', html) or
                  _has(r'text-decoration\s*:\s*line-through', css))
    quality = 1.0 if has_anchor else 0.3
    rec = "" if has_anchor else "Pricing shown with no anchor — display an original/higher reference price (e.g. 'Was $199, now $99') so the real price reads as a deal."
    return BiasCheck("Anchoring (price)", True, quality, 12, rec,
                     "anchor present" if has_anchor else "no reference anchor")

def check_loss_aversion(html: str) -> BiasCheck:
    """Scarcity / urgency / FOMO: limited stock, countdowns, 'only N left'.
    Powerful but must be genuine — flag but reward when present."""
    is_transactional = _has(r'(buy|checkout|purchase|book|subscribe|order|add to cart)', html)
    if not is_transactional:
        return BiasCheck("Loss Aversion (scarcity/urgency)", False, 1.0, 10, "", "not transactional (N/A)")
    has_scarcity = _has(r'(only \d+[\w\s]{0,15}left|limited|selling fast|\d+ (seats?|left|spots?|in stock)|ends? (in|soon)|today only|last chance|launch pricing|hurry|\d+ people (are )?viewing)', html)
    has_urgency = _has(r'(countdown|timer|expires?|deadline|\d+:\d+:\d+)', html)
    present = has_scarcity or has_urgency
    quality = 1.0 if present else 0.5
    rec = "" if present else "Transactional page with no scarcity/urgency cue — a genuine 'only N left' or time-limited signal engages loss aversion (use only if TRUE)."
    return BiasCheck("Loss Aversion (scarcity/urgency)", present, quality, 10, rec,
                     "scarcity/urgency present" if present else "none")

def check_social_proof(html: str) -> BiasCheck:
    """Social proof near the decision point. Best: specific numbers + near CTA."""
    has_proof = _has(r'(review|rating|testimonial|★|⭐|\d+[\d,]*\+? (customers|users|happy|reviews)|trusted by|as seen (in|on)|join \d)', html)
    has_specific = _has(r'\d[\d,]*\+?\s*(customers|users|reviews|companies|teams|happy)', html)
    has_logos = _has(r'(logo|featured|as-seen|press|forbes|techcrunch|trusted-by)', html)
    present = has_proof
    quality = 1.0 if (has_specific and (has_proof or has_logos)) else 0.6 if present else 0.0
    rec = ("" if quality >= 1.0 else
           "Add specific social proof numbers ('Join 5,000+ customers') and trust logos near the CTA." if not has_specific else
           "Social proof present — move it adjacent to the primary CTA for maximum effect.")
    return BiasCheck("Social Proof", present, quality, 18, rec,
                     "specific + logos" if (has_specific and has_logos) else "present" if present else "absent")

def check_cognitive_fluency(html: str, css: str) -> BiasCheck:
    """Easy-to-process = trustworthy. Whitespace, hierarchy, short blocks."""
    has_whitespace = bool(re.search(r'padding[^;:]*:\s*([3-9]|\d{2,})(rem|vw|vh|em)', css, re.I))
    has_hierarchy = _count(r'<h[12]', html) >= 1 and _has(r'font-size', css)
    has_generous_leading = _has(r'line-height\s*:\s*(1\.[6-9]|[2-9])', css)
    score = sum([has_whitespace, has_hierarchy, has_generous_leading]) / 3
    rec = ""
    if not has_whitespace: rec = "Increase section padding (≥6vw) — whitespace reads as premium and reduces cognitive load."
    elif not has_generous_leading: rec = "Set body line-height ≥1.6 — easier processing reads as more trustworthy (fluency effect)."
    return BiasCheck("Cognitive Fluency", True, score, 15, rec,
                     f"whitespace={has_whitespace}, hierarchy={has_hierarchy}, leading={has_generous_leading}")

def check_reciprocity(html: str) -> BiasCheck:
    """Give before you ask: free trial, free guide, value upfront."""
    has_give = _has(r'(free|trial|no (credit card|cost)|complimentary|gift|download.{0,20}free|get started free)', html)
    is_transactional = _has(r'(buy|subscribe|sign\s*up|checkout|book)', html)
    if not is_transactional:
        return BiasCheck("Reciprocity", has_give, 1.0 if has_give else 0.7, 8, "", "N/A")
    quality = 1.0 if has_give else 0.5
    rec = "" if has_give else "Offer value before asking — a free trial/guide/'no credit card' cue triggers reciprocity and lowers signup friction."
    return BiasCheck("Reciprocity", has_give, quality, 8, rec,
                     "value-first present" if has_give else "asks without giving")

def run_bias_suite(html: str, css: str) -> list[BiasCheck]:
    return [
        check_von_restorff(html, css),
        check_social_proof(html),
        check_cognitive_fluency(html, css),
        check_anchoring(html, css),
        check_loss_aversion(html),
        check_reciprocity(html),
    ]
