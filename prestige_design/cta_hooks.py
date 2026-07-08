"""CTA & Hook Verification — the conversion-critical layer. Judges whether the
call-to-action and the headline hook are actually engineered to convert, not
just present. Strict scoring with precise rewrites."""
from __future__ import annotations
import re
from dataclasses import dataclass, field

@dataclass
class CTAReport:
    cta_count: int = 0
    primary_cta_text: str = ""
    hook_text: str = ""
    cta_score: int = 0
    hook_score: int = 0
    findings: list = field(default_factory=list)
    recommendations: list = field(default_factory=list)

# weak CTA verbs that underperform
WEAK_CTA = ["submit", "click here", "enter", "go", "ok", "continue", "next", "send"]
# strong action/value CTA patterns
STRONG_CTA = ["get started", "start free", "get my", "claim", "unlock", "try", "join",
              "book", "reserve", "grab", "download", "start my", "see", "show me"]
# hook power words (emotional / value / specificity)
POWER_WORDS = ["you", "your", "free", "now", "instantly", "proven", "guaranteed",
               "without", "stop", "finally", "secret", "how", "why", "new"]

def _extract_ctas(html: str) -> list[str]:
    ctas = []
    for m in re.findall(r'<(?:button|a)[^>]*>(.*?)</(?:button|a)>', html, re.S | re.I):
        text = re.sub(r'<[^>]+>', '', m).strip()
        if text and len(text) < 40:
            ctas.append(text)
    return ctas

def _extract_hook(html: str) -> str:
    m = re.search(r'<h1[^>]*>(.*?)</h1>', html, re.S | re.I)
    return re.sub(r'<[^>]+>', '', m.group(1)).strip() if m else ""

def verify_cta_and_hooks(html: str) -> CTAReport:
    r = CTAReport()
    ctas = _extract_ctas(html)
    r.cta_count = len(ctas)
    # identify the primary CTA (first prominent action-like button)
    action_ctas = [c for c in ctas if any(s in c.lower() for s in STRONG_CTA + WEAK_CTA)]
    r.primary_cta_text = action_ctas[0] if action_ctas else (ctas[0] if ctas else "")
    r.hook_text = _extract_hook(html)

    # ---- CTA scoring ----
    cta_score = 100
    if not r.primary_cta_text:
        cta_score = 0; r.findings.append("CTA_MISSING: no identifiable call-to-action.")
        r.recommendations.append("Add a single prominent primary CTA button with a value-driven label.")
    else:
        low = r.primary_cta_text.lower()
        if any(w in low for w in WEAK_CTA) and not any(s in low for s in STRONG_CTA):
            cta_score -= 35
            r.findings.append(f"CTA_WEAK_VERB: '{r.primary_cta_text}' uses a low-energy verb.")
            r.recommendations.append(f"Rewrite '{r.primary_cta_text}' → a value+action label like 'Start my free trial' or 'Get instant access'.")
        if not any(s in low for s in STRONG_CTA):
            cta_score -= 15
            r.recommendations.append("Lead the CTA with a strong action verb (Get / Start / Claim / Unlock).")
        if "free" not in low and "my" not in low and len(low.split()) < 2:
            cta_score -= 10
            r.recommendations.append("Make the CTA first-person or benefit-led ('Get my free quote' beats 'Submit').")
        # too many competing CTAs
        if r.cta_count > 4:
            cta_score -= 20
            r.findings.append(f"CTA_COMPETITION: {r.cta_count} CTAs compete for attention.")
            r.recommendations.append("Reduce to one primary CTA per section; demote the rest to secondary styling.")
    r.cta_score = max(cta_score, 0)

    # ---- Hook scoring ----
    hook_score = 100
    if not r.hook_text:
        hook_score = 0; r.findings.append("HOOK_MISSING: no <h1> headline hook.")
        r.recommendations.append("Add one bold headline that names the outcome the user wants.")
    else:
        h = r.hook_text.lower()
        words = h.split()
        power_hits = [w for w in POWER_WORDS if re.search(rf"\b{w}\b", h)]
        if len(power_hits) == 0:
            hook_score -= 30
            r.findings.append(f"HOOK_FLAT: headline lacks emotional/value words.")
            r.recommendations.append("Inject a power word — address the reader ('you/your'), promise ('proven/guaranteed'), or outcome.")
        if len(words) > 14:
            hook_score -= 20
            r.findings.append(f"HOOK_LONG: {len(words)}-word headline dilutes impact.")
            r.recommendations.append("Tighten the headline to ≤12 words — one clear promise.")
        if not re.search(r'\byou(r)?\b', h):
            hook_score -= 15
            r.recommendations.append("Make the headline about the reader ('you/your'), not the product.")
        # benefit vs feature: numbers/outcomes are strong
        if not re.search(r'\d', h) and len(power_hits) < 2:
            hook_score -= 10
            r.recommendations.append("Add specificity — a number or concrete outcome makes the promise believable.")
    r.hook_score = max(hook_score, 0)
    return r
