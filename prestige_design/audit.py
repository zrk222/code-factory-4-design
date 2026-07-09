"""The Prestige design linter — encodes the five laws as executable checks so
an agent can VERIFY its output, not just intend it. Pure-stdlib HTML/CSS
heuristics; no browser needed. Returns per-law scores + Horn-Effect triggers +
hard failures for major functional flaws (the non-negotiable warning)."""
from __future__ import annotations
import re
from dataclasses import dataclass, field

@dataclass
class Finding:
    law: str
    level: str          # "pass" | "warn" | "fail" | "hard_fail"
    code: str
    message: str

@dataclass
class AuditReport:
    findings: list = field(default_factory=list)
    scores: dict = field(default_factory=dict)      # law -> 0..100
    hard_failures: list = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return not self.hard_failures and all(v >= 60 for v in self.scores.values())

    @property
    def overall(self) -> int:
        return round(sum(self.scores.values()) / len(self.scores)) if self.scores else 0

    @property
    def attribution(self):
        from .attribution import Attribution, FailureClass, UnitResult
        units = [
            UnitResult(
                unit=f"criterion:{law}",
                stage="design_audit",
                passed=score >= 60,
                evidence=f"score={score}; threshold=60",
                failure_class=None if score >= 60 else FailureClass.WRONG_OUTPUT,
            )
            for law, score in sorted(self.scores.items())
        ]
        return Attribution("design_audit", len(units), sum(unit.passed for unit in units), units)

def _has(pattern, text, flags=re.I):
    return re.search(pattern, text, flags) is not None

def _count(pattern, text, flags=re.I):
    return len(re.findall(pattern, text, flags))

def audit_html(html: str, css: str = "") -> AuditReport:
    """css may be inline in html; we scan both together for style checks."""
    blob = html + "\n" + css
    style = css + "\n" + " ".join(re.findall(r"<style[^>]*>(.*?)</style>", html, re.S | re.I))
    r = AuditReport()
    f = r.findings

    # ---------- LAW 1: 50ms Halo (hero) ----------
    s = 100
    has_hero = _has(r'class=["\'][^"\']*hero', html) or _has(r'<header', html) or _has(r'<section[^>]*hero', html)
    if not has_hero:
        s -= 40; f.append(Finding("halo","warn","H_NO_HERO","No identifiable hero/header section for the 50ms credibility window."))
    if not _has(r'object-fit\s*:\s*cover', style) and not _has(r'background-size\s*:\s*cover', style):
        s -= 20; f.append(Finding("halo","warn","H_NO_COVER_IMG","No object-fit/background cover image — hero imagery drives the halo."))
    h1 = _count(r'<h1', html)
    if h1 == 0:
        s -= 25; f.append(Finding("halo","fail","H_NO_H1","No <h1> — the hero needs one bold headline."))
    elif h1 > 1:
        s -= 15; f.append(Finding("halo","warn","H_MULTI_H1",f"{h1} <h1> tags — a single bold headline signals confidence."))
    r.scores["halo"] = max(s, 0)

    # ---------- LAW 2: Cognitive Fluency ----------
    s = 100
    navlinks = _count(r'<nav[^>]*>.*?</nav>', html, re.S)
    nav_items = 0
    for nav in re.findall(r'<nav[^>]*>(.*?)</nav>', html, re.S | re.I):
        nav_items = max(nav_items, _count(r'<a\b', nav))
    if nav_items > 7:
        s -= 25; f.append(Finding("fluency","warn","F_NAV_OVERLOAD",f"Primary nav has {nav_items} items (Hick's Law: keep ≤7)."))
    if not _has(r'line-height\s*:\s*(1\.[6-9]|[2-9])', style):
        s -= 20; f.append(Finding("fluency","warn","F_TIGHT_LEADING","Body line-height < 1.6 hurts readability/fluency."))
    # whitespace: look for generous section padding
    pads = re.findall(r'padding[^;:]*:\s*([0-9.]+)(rem|vw|vh|em|px)', style, re.I)
    generous = any((u in ("rem","vw","em") and float(v) >= 3) or (u=="px" and float(v)>=48) for v,u in pads)
    if not generous:
        s -= 20; f.append(Finding("fluency","warn","F_NO_WHITESPACE","No generous section padding — extreme whitespace signals premium."))
    if not _has(r'display\s*:\s*(grid|flex)', style):
        s -= 15; f.append(Finding("fluency","warn","F_NO_CHUNKING","No grid/flex layout — use it to chunk info (Miller's Law)."))
    r.scores["fluency"] = max(s, 0)

    # ---------- LAW 3: Trust Engineering ----------
    s = 100
    trust_cues = _count(r'(secure|verified|guarantee|padlock|lock-icon|badge|ssl|encrypt|trusted)', blob)
    social = _has(r'(review|rating|stars?|testimonial|★|⭐|\bfrom\s+\d+\s+reviews?)', blob)
    is_transactional = _has(r'(checkout|buy|purchase|book now|subscribe|sign\s*up|pay\b|add to cart|price|\$\d)', blob)
    if is_transactional:
        if trust_cues == 0:
            s -= 35; f.append(Finding("trust","fail","T_NO_SECURITY","Transactional UI with no security/verification cue near actions."))
        if not social:
            s -= 25; f.append(Finding("trust","warn","T_NO_SOCIAL_PROOF","No social proof (reviews/ratings) near decision points."))
        # price transparency: look for fee/tax mention if a price is shown
        if _has(r'\$\d', blob) and not _has(r'(total|incl\.|including|fees?|tax|all-in)', blob):
            s -= 20; f.append(Finding("trust","warn","T_HIDDEN_COST","Price shown without total/fees/tax transparency (shock-factor risk)."))
        if _has(r'(create account|register).{0,40}(required|to continue)', blob) and not _has(r'guest', blob):
            s -= 15; f.append(Finding("trust","warn","T_FORCED_ACCOUNT","Forced account with no guest option (~26% abandonment)."))
    else:
        # non-transactional: trust cues optional but rewarded
        if trust_cues == 0 and not social:
            s -= 10; f.append(Finding("trust","warn","T_LIGHT_TRUST","Consider adding credibility cues (logos, testimonials)."))
    r.scores["trust"] = max(s, 0)

    # ---------- LAW 4: Peak-End Rule ----------
    s = 100
    if not _has(r'transition\s*:', style):
        s -= 30; f.append(Finding("peak","warn","P_NO_TRANSITIONS","No CSS transitions — micro-interactions create peaks of delight."))
    if not _has(r':hover', style):
        s -= 25; f.append(Finding("peak","warn","P_NO_HOVER","No :hover states — buttons should feel satisfying to interact with."))
    has_form = _has(r'<form|<input', html)
    if has_form and not (_has(r':valid|:invalid', style) or _has(r'(checkmark|✓|valid)', blob)):
        s -= 25; f.append(Finding("peak","warn","P_NO_INLINE_VALID","Form without inline validation feedback (gentle confirmation)."))
    r.scores["peak"] = max(s, 0)

    # ---------- LAW 5: Horn-Effect Defense (consistency + mobile) ----------
    s = 100
    if not _has(r'@media', style):
        s -= 40; f.append(Finding("horn","fail","C_NO_RESPONSIVE","No @media query — broken mobile is an instant unreliability signal."))
    if not _has(r'var\(--|:root', style):
        s -= 25; f.append(Finding("horn","warn","C_NO_CSS_VARS","No CSS variables — hard to keep Visual DNA consistent."))
    if not _has(r'<meta[^>]*viewport', html):
        s -= 20; f.append(Finding("horn","fail","C_NO_VIEWPORT","Missing viewport meta — mobile layout will break."))
    font_families = set(re.findall(r'font-family\s*:\s*([^;]+)', style, re.I))
    if len(font_families) > 3:
        s -= 15; f.append(Finding("horn","warn","C_FONT_SOUP",f"{len(font_families)} distinct font-family declarations — inconsistency risks the Horn Effect."))
    r.scores["horn"] = max(s, 0)

    # ---------- HARD FAILS: major functional flaws (the non-negotiable warning) ----------
    # a pretty page must never ship over a broken PRIMARY action / accessibility
    buttons = re.findall(r'<(button|a)\b[^>]*>(.*?)</\1>', html, re.S | re.I)
    unlabeled = [b for tag,b in buttons if not re.sub(r'<[^>]+>','',b).strip() and 'aria-label' not in b]
    if is_transactional and unlabeled:
        r.hard_failures.append("MAJOR_FLAW: primary action button has no accessible label/text.")
        f.append(Finding("warning","hard_fail","X_UNLABELED_CTA","A primary action is unlabeled — major usability flaw; fix before aesthetics."))
    imgs = re.findall(r'<img\b[^>]*>', html, re.I)
    missing_alt = [i for i in imgs if 'alt=' not in i]
    if len(missing_alt) >= max(3, len(imgs)//2) and imgs:
        r.hard_failures.append(f"MAJOR_FLAW: {len(missing_alt)}/{len(imgs)} images missing alt text (accessibility).")
        f.append(Finding("warning","hard_fail","X_NO_ALT","Widespread missing alt text — accessibility failure blocks ship."))
    return r
