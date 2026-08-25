"""Purpose-driven design brief compiler."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .purpose import PROFILES


EMOTIONAL_INTENTS = {
    "developer": "confidence",
    "healthcare": "calm",
    "fintech": "confidence",
    "luxury": "delight",
    "marketplace": "confidence",
    "saas": "momentum",
    "editorial": "belonging",
}


PSYCHOLOGY = {
    "developer": ["proof before persuasion", "low-friction scanning", "copy must survive technical skepticism"],
    "healthcare": ["calm reduces anxiety", "privacy and consent must be visible", "avoid urgency that feels coercive"],
    "fintech": ["control builds trust", "cost transparency prevents abandonment", "security cues belong near actions"],
    "luxury": ["restraint signals confidence", "fewer choices increase perceived value", "craft details become proof"],
    "marketplace": ["bilateral trust is the product", "comparison lowers uncertainty", "review integrity matters"],
    "saas": ["product visibility beats vague claims", "ROI must be concrete", "activation should feel reversible"],
    "editorial": ["rhythm creates comprehension", "source clarity creates authority", "end beats determine memory"],
}


@dataclass(frozen=True)
class DesignBrief:
    purpose: str
    profile: str
    psychology: list[str]
    directives: list[str]
    anti_patterns: list[str]
    sections: list[str]
    verification: list[str]
    emotional_intent: str
    emotional_journey: list[str]
    ethical_guardrails: list[str]

    def to_dict(self) -> dict:
        return {
            "purpose": self.purpose,
            "profile": self.profile,
            "psychology": self.psychology,
            "directives": self.directives,
            "anti_patterns": self.anti_patterns,
            "sections": self.sections,
            "verification": self.verification,
            "emotional_intent": self.emotional_intent,
            "emotional_journey": self.emotional_journey,
            "ethical_guardrails": self.ethical_guardrails,
        }


def compile_brief(source: Path | None = None, *, purpose: str = "developer") -> DesignBrief:
    profile = PROFILES.get(purpose, PROFILES["saas"])
    source_hint = ""
    if source:
        text = Path(source).read_text(encoding="utf-8").lower()
        if "api" in text or "cli" in text:
            source_hint = "Lead with install, command, receipt, and GitHub proof."
        elif "checkout" in text or "payment" in text:
            source_hint = "Place total cost, security, and reassurance next to the payment action."
        elif "clinical" in text or "patient" in text:
            source_hint = "Prioritize consent, privacy, clinician review, and calm state language."
    directives = list(profile.directives)
    if source_hint:
        directives.insert(0, source_hint)
    emotional_intent = EMOTIONAL_INTENTS.get(profile.key, "confidence")
    return DesignBrief(
        purpose=profile.key,
        profile=profile.name,
        psychology=PSYCHOLOGY.get(profile.key, []),
        directives=directives,
        anti_patterns=list(profile.anti_terms),
        sections=[
            "first viewport: literal product/workflow signal, not abstract marketing",
            "proof band: docs, receipts, screenshots, metrics, or trust cues matched to purpose",
            "primary workflow: one action path with visible state and failure handling",
            "ending state: confirmation, receipt, next step, or handoff",
        ],
        verification=[
            f"prestige score <file> --workflow product --purpose {profile.key}",
            f"prestige purpose <file> --purpose {profile.key}",
            f"prestige emotion <file> --intent {emotional_intent} --challenge --strict",
            "capture desktop and mobile screenshots before claiming polish",
        ],
        emotional_intent=emotional_intent,
        emotional_journey=[
            "entry: establish the intended feeling and one legible next action",
            "action: minimize friction while preserving informed choice",
            "feedback: name active state and truthful progress immediately",
            "recovery: explain failure without blame and preserve a way forward",
            "completion: provide confirmation, evidence, and a useful next step",
            "return: preserve continuity without guilt, artificial loss, or compulsion",
        ],
        ethical_guardrails=[
            "no shame, guilt, confirm-shaming, fake scarcity, or punitive streak loss",
            "predictable rewards and explicit opt-in; never manufacture variable-reward compulsion",
            "disclose AI authorship and keep review, edit, reject, cancel, and revert controls",
            "respect reduced-motion preferences and never encode critical state with color alone",
        ],
    )


def render_brief(brief: DesignBrief) -> str:
    lines = [
        f"# Design Brief: {brief.profile}",
        "",
        "## Psychology",
        *[f"- {item}" for item in brief.psychology],
        "",
        "## Directives",
        *[f"- {item}" for item in brief.directives],
        "",
        f"## Emotional Intent: {brief.emotional_intent}",
        *[f"- {item}" for item in brief.emotional_journey],
        "",
        "## Ethical Guardrails",
        *[f"- {item}" for item in brief.ethical_guardrails],
        "",
        "## Anti-Patterns",
        *[f"- {item}" for item in brief.anti_patterns],
        "",
        "## Required Sections",
        *[f"- {item}" for item in brief.sections],
        "",
        "## Verification",
        *[f"- `{item}`" for item in brief.verification],
    ]
    return "\n".join(lines)
