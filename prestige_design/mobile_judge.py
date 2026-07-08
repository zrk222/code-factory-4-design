"""Mobile-first strict judge. Mobile is where trust breaks first: a broken
mobile layout is an instant unreliability signal. Judges thumb-reach, tap
targets, viewport discipline, responsive breakpoints, and text legibility
with stricter thresholds than desktop."""
from __future__ import annotations
import re
from dataclasses import dataclass, field

@dataclass
class MobileReport:
    score: int = 0
    findings: list = field(default_factory=list)
    recommendations: list = field(default_factory=list)

def judge_mobile(html: str, css: str) -> MobileReport:
    r = MobileReport(); score = 100

    if not re.search(r'<meta[^>]*viewport[^>]*width=device-width', html, re.I):
        score -= 30
        r.findings.append("M_NO_VIEWPORT: missing responsive viewport meta.")
        r.recommendations.append('Add <meta name="viewport" content="width=device-width, initial-scale=1">.')

    media_queries = re.findall(r'@media[^{]*\(([^)]*)\)', css, re.I)
    if not media_queries:
        score -= 30
        r.findings.append("M_NO_BREAKPOINTS: no @media queries — layout won't adapt.")
        r.recommendations.append("Add a mobile breakpoint (@media (max-width:768px)) that stacks columns and resizes the hero.")
    elif not any('max-width' in q or 'min-width' in q for q in media_queries):
        score -= 15
        r.recommendations.append("Use explicit min/max-width breakpoints for predictable mobile behavior.")

    # tap target size — buttons need adequate padding for thumbs (≥44px effective)
    btn_padding = re.findall(r'(?:\.btn|button)[^{]*\{[^}]*padding[^;:]*:\s*([^;]+)', css, re.I)
    tiny_targets = any(re.search(r'0?\.\d|[0-4]px', p) and 'rem' not in p and 'em' not in p for p in btn_padding)
    if btn_padding and tiny_targets:
        score -= 15
        r.findings.append("M_SMALL_TAP_TARGETS: button padding may be < 44px thumb-friendly minimum.")
        r.recommendations.append("Give tap targets ≥0.9rem vertical padding so thumbs hit reliably (Fitts's Law on mobile).")

    # fixed widths break mobile
    fixed_px = re.findall(r'width\s*:\s*(\d{3,})px', css, re.I)
    if any(int(w) > 480 for w in fixed_px):
        score -= 15
        r.findings.append(f"M_FIXED_WIDTH: fixed widths >480px ({max(int(w) for w in fixed_px)}px) overflow small screens.")
        r.recommendations.append("Replace fixed pixel widths with max-width + % / vw so content fits any screen.")

    # legible mobile text (≥16px base avoids iOS zoom-on-focus)
    if re.search(r'font-size\s*:\s*(1[0-3]px|0?\.[0-8]rem)', css, re.I):
        score -= 10
        r.recommendations.append("Base font ≥16px on mobile — smaller triggers zoom-on-focus and hurts legibility.")

    # thumb-zone: primary CTA should not be top-only on mobile
    if not re.search(r'position\s*:\s*(sticky|fixed)', css, re.I) and re.search(r'(buy|checkout|cta)', html, re.I):
        r.recommendations.append("Consider a sticky bottom CTA on mobile — keeps the primary action in the thumb zone.")

    r.score = max(score, 0)
    return r
