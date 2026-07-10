"""Purpose-driven design brief compiler."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .purpose import PROFILES


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

    def to_dict(self) -> dict:
        return {
            "purpose": self.purpose,
            "profile": self.profile,
            "psychology": self.psychology,
            "directives": self.directives,
            "anti_patterns": self.anti_patterns,
            "sections": self.sections,
            "verification": self.verification,
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
            "capture desktop and mobile screenshots before claiming polish",
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
