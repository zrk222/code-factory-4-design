"""Purpose-fit design judgment.

The five laws answer "is this polished?" Purpose-fit answers the sharper
question: "is this polished for the job this interface has to do?"
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

from .attribution import Attribution, FailureClass, UnitResult


@dataclass(frozen=True)
class PurposeProfile:
    key: str
    name: str
    psychology: str
    intent_terms: tuple[str, ...]
    trust_terms: tuple[str, ...]
    proof_terms: tuple[str, ...]
    visual_terms: tuple[str, ...]
    cta_terms: tuple[str, ...]
    anti_terms: tuple[str, ...]
    directives: tuple[str, ...]


@dataclass(frozen=True)
class PurposeFinding:
    criterion: str
    score: int
    code: str
    message: str


@dataclass
class PurposeReport:
    purpose: str
    profile: str
    score: int
    grade: str
    passed: bool
    findings: list[PurposeFinding] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)

    @property
    def attribution(self) -> Attribution:
        units = [
            UnitResult(
                unit=f"purpose:{finding.criterion}",
                stage="purpose_fit",
                passed=finding.score >= 70,
                evidence=f"score={finding.score}; {finding.message}",
                failure_class=None if finding.score >= 70 else FailureClass.WRONG_OUTPUT,
            )
            for finding in self.findings
        ]
        return Attribution("purpose_fit", len(units), sum(unit.passed for unit in units), units)


PROFILES: dict[str, PurposeProfile] = {
    "developer": PurposeProfile(
        key="developer",
        name="Developer Tool Clarity",
        psychology="Engineers trust concrete proof: code, docs, API shape, CI, and a demo.",
        intent_terms=("api", "cli", "sdk", "docs", "github", "deploy", "workflow", "developer", "code"),
        trust_terms=("open source", "github", "ci", "tests", "docs", "api", "no secrets", "deterministic"),
        proof_terms=("demo", "quickstart", "code", "install", "pip", "npm", "curl", "terminal", "copy"),
        visual_terms=("mono", "code", "terminal", "screenshot", "product", "demo"),
        cta_terms=("install", "start", "try", "view docs", "github", "quickstart", "run"),
        anti_terms=("revolutionary", "magical", "effortless ai", "black box", "contact sales"),
        directives=(
            "Show the product working above the fold.",
            "Put install/docs/GitHub within one glance of the primary CTA.",
            "Prefer concrete terminal or code proof over abstract claims.",
        ),
    ),
    "healthcare": PurposeProfile(
        key="healthcare",
        name="Clinical Trust",
        psychology="Patients and clinicians need calm reassurance, privacy, accuracy, and low anxiety.",
        intent_terms=("care", "patient", "clinical", "health", "doctor", "medical", "therapy", "wellness"),
        trust_terms=("privacy", "secure", "hipaa", "clinician", "licensed", "verified", "evidence", "safe"),
        proof_terms=("clinical", "outcomes", "reviewed", "certified", "research", "board", "care team"),
        visual_terms=("calm", "soft", "blue", "green", "clear", "accessible"),
        cta_terms=("book", "schedule", "check", "talk", "start care", "find care"),
        anti_terms=("hurry", "last chance", "miracle", "guaranteed cure", "shocking", "only"),
        directives=(
            "Lead with reassurance before persuasion.",
            "Place privacy and clinician proof near forms and appointment CTAs.",
            "Avoid aggressive urgency, miracle language, and visual noise.",
        ),
    ),
    "fintech": PurposeProfile(
        key="fintech",
        name="Financial Confidence",
        psychology="Money interfaces must signal security, transparency, control, and regulatory seriousness.",
        intent_terms=("money", "finance", "bank", "card", "payment", "invoice", "tax", "invest", "loan"),
        trust_terms=("secure", "encrypted", "fdic", "soc 2", "audit", "compliance", "privacy", "verified"),
        proof_terms=("fees", "total", "rate", "apr", "risk", "report", "statement", "transparent"),
        visual_terms=("blue", "navy", "green", "ledger", "dashboard", "chart"),
        cta_terms=("open", "compare", "calculate", "start", "view", "transfer", "pay"),
        anti_terms=("guaranteed returns", "risk free profit", "get rich", "hidden fees", "limited time"),
        directives=(
            "Show the true cost, fee, rate, or risk before asking for action.",
            "Use security and compliance cues near data-entry and payment points.",
            "Avoid speculative or get-rich language.",
        ),
    ),
    "luxury": PurposeProfile(
        key="luxury",
        name="Luxury Restraint",
        psychology="Premium design persuades through confidence, scarcity of elements, craft, and silence.",
        intent_terms=("private", "atelier", "bespoke", "collection", "premium", "exclusive", "concierge"),
        trust_terms=("crafted", "heritage", "limited", "private", "curated", "appointment"),
        proof_terms=("materials", "craft", "edition", "atelier", "client", "concierge"),
        visual_terms=("serif", "charcoal", "ivory", "minimal", "gallery", "editorial", "spacious"),
        cta_terms=("request", "reserve", "book", "inquire", "view collection"),
        anti_terms=("cheap", "discount", "flash sale", "hurry", "free", "submit", "buy now"),
        directives=(
            "Reduce CTA pressure and let craft proof carry the page.",
            "Use whitespace, slower motion, fewer words, and fewer elements.",
            "Avoid loud discount language and commodity ecommerce cues.",
        ),
    ),
    "marketplace": PurposeProfile(
        key="marketplace",
        name="Marketplace Bilateral Trust",
        psychology="Both sides need proof that the other side is real, reviewed, protected, and accountable.",
        intent_terms=("marketplace", "seller", "buyer", "vendor", "booking", "listing", "host", "provider"),
        trust_terms=("verified", "protected", "secure", "escrow", "refund", "screened", "insured"),
        proof_terms=("reviews", "ratings", "verified sellers", "buyer protection", "returns", "dispute"),
        visual_terms=("cards", "ratings", "badges", "profiles", "map", "listing"),
        cta_terms=("browse", "list", "book", "compare", "request", "message"),
        anti_terms=("anonymous", "no refunds", "trust us", "instant approval"),
        directives=(
            "Show trust for both buyer and seller, not just aggregate popularity.",
            "Put ratings, identity, protection, and dispute policy near listing CTAs.",
            "Make comparison easy with consistent listing cards.",
        ),
    ),
    "saas": PurposeProfile(
        key="saas",
        name="SaaS Activation",
        psychology="Teams need fast comprehension, proof of fit, low signup friction, and visible product value.",
        intent_terms=("platform", "dashboard", "team", "automation", "workflow", "analytics", "saas", "crm"),
        trust_terms=("soc 2", "sso", "security", "uptime", "integrations", "roles", "admin"),
        proof_terms=("logos", "case study", "roi", "saved", "integrates", "template", "demo"),
        visual_terms=("screenshot", "dashboard", "product", "chart", "workflow", "clean"),
        cta_terms=("start", "try", "book demo", "see demo", "get started", "no credit card"),
        anti_terms=("contact us only", "vague", "all in one", "best-in-class"),
        directives=(
            "Show the product UI and the exact workflow it improves.",
            "Name integrations, admin/security posture, and measurable ROI.",
            "Keep the primary path low-friction: free trial or demo, not vague contact.",
        ),
    ),
    "editorial": PurposeProfile(
        key="editorial",
        name="Editorial Narrative",
        psychology="Narrative pages need rhythm, pacing, curiosity, and a satisfying end beat.",
        intent_terms=("story", "report", "research", "guide", "essay", "launch", "campaign", "magazine"),
        trust_terms=("source", "research", "editorial", "byline", "citation", "method", "date"),
        proof_terms=("data", "chart", "quote", "source", "evidence", "chapter", "section"),
        visual_terms=("serif", "article", "chapter", "pull quote", "figure", "caption"),
        cta_terms=("read", "download", "subscribe", "explore", "continue"),
        anti_terms=("buy now", "limited time", "submit", "wall of text"),
        directives=(
            "Use rhythm: clear sections, pull quotes, figures, and a resolving CTA.",
            "Make sources, date, and method visible to earn reader trust.",
            "Avoid ecommerce pressure that breaks narrative immersion.",
        ),
    ),
}


def _plain(html: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", html)).strip().lower()


def _count_terms(text: str, terms: tuple[str, ...]) -> int:
    return sum(1 for term in terms if re.search(rf"\b{re.escape(term.lower())}\b", text))


def _extract_ctas(html: str) -> list[str]:
    ctas = []
    for match in re.findall(r"<(?:button|a)\b[^>]*>(.*?)</(?:button|a)>", html, re.S | re.I):
        text = re.sub(r"<[^>]+>", " ", match).strip().lower()
        if text:
            ctas.append(text)
    return ctas


def infer_purpose(html: str, css: str = "") -> str:
    text = _plain(html) + " " + css.lower()
    scores = {
        key: _count_terms(text, profile.intent_terms + profile.trust_terms + profile.proof_terms)
        for key, profile in PROFILES.items()
    }
    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else "saas"


def _grade(score: int) -> str:
    return "A" if score >= 88 else "B" if score >= 75 else "C" if score >= 60 else "D" if score >= 45 else "F"


def audit_purpose(html: str, css: str = "", purpose: str = "auto") -> PurposeReport:
    key = infer_purpose(html, css) if purpose == "auto" else purpose
    profile = PROFILES.get(key, PROFILES["saas"])
    text = _plain(html)
    blob = text + " " + css.lower()
    ctas = _extract_ctas(html)
    findings: list[PurposeFinding] = []
    recommendations: list[str] = []

    def add(criterion: str, score: int, code: str, message: str, recommendation: str = "") -> None:
        findings.append(PurposeFinding(criterion, max(0, min(100, score)), code, message))
        if recommendation:
            recommendations.append(recommendation)

    intent_hits = _count_terms(text, profile.intent_terms)
    intent_score = min(100, 45 + intent_hits * 18)
    add(
        "intent_clarity",
        intent_score,
        "P_INTENT",
        f"{intent_hits} purpose terms found for {profile.name}",
        profile.directives[0] if intent_score < 70 else "",
    )

    trust_hits = _count_terms(text, profile.trust_terms)
    proof_hits = _count_terms(text, profile.proof_terms)
    proof_score = min(100, 35 + trust_hits * 12 + proof_hits * 12)
    add(
        "proof_fit",
        proof_score,
        "P_PROOF",
        f"{trust_hits} trust terms and {proof_hits} proof terms match the purpose",
        profile.directives[1] if proof_score < 70 else "",
    )

    visual_hits = _count_terms(blob, profile.visual_terms)
    has_visual_system = bool(re.search(r":root|var\(--|font-family|background|color\s*:", css, re.I))
    visual_score = min(100, 35 + visual_hits * 14 + (20 if has_visual_system else 0))
    add(
        "visual_theme",
        visual_score,
        "P_THEME",
        f"{visual_hits} visual-theme cues found; visual system={has_visual_system}",
        f"Align palette, type, and imagery with {profile.name}: {profile.directives[2]}" if visual_score < 70 else "",
    )

    cta_hits = sum(1 for cta in ctas if any(term in cta for term in profile.cta_terms))
    cta_pressure = len(ctas)
    cta_score = min(100, 45 + cta_hits * 25)
    if profile.key == "luxury" and cta_pressure > 3:
        cta_score -= 20
    if cta_pressure == 0:
        cta_score = 20
    add(
        "action_fit",
        cta_score,
        "P_ACTION",
        f"{cta_hits}/{cta_pressure} CTAs match the purpose vocabulary",
        f"Use purpose-fit CTA language such as: {', '.join(profile.cta_terms[:4])}" if cta_score < 70 else "",
    )

    anti_hits = _count_terms(text, profile.anti_terms)
    anti_score = max(0, 100 - anti_hits * 30)
    add(
        "anti_patterns",
        anti_score,
        "P_ANTI",
        f"{anti_hits} purpose-specific anti-pattern terms found",
        f"Remove language that fights {profile.name}: {', '.join(profile.anti_terms[:4])}" if anti_score < 85 else "",
    )

    score = round(sum(finding.score for finding in findings) / len(findings))
    return PurposeReport(
        purpose=profile.key,
        profile=profile.name,
        score=score,
        grade=_grade(score),
        passed=score >= 70 and all(f.score >= 55 for f in findings),
        findings=findings,
        recommendations=list(dict.fromkeys(recommendations)),
    )


def list_purposes() -> list[dict]:
    return [
        {
            "key": profile.key,
            "name": profile.name,
            "psychology": profile.psychology,
            "directives": list(profile.directives),
        }
        for profile in PROFILES.values()
    ]

