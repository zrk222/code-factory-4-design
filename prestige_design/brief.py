"""Purpose-driven design brief compiler."""
from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import re

from .habit import _dict, _plain, _text, _unique_pairs, bounded, digest, local_path
from .journey import STATES
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

COMPONENT_ROLES = {
    "primary_action", "dialog", "form_error", "text_input", "empty_state",
    "progress", "status_message", "session_prompt",
}


def _reference(root, name):
    path = local_path(root, _text(name, "source path"))
    if not path.is_file():
        raise ValueError("Component and token references must be regular workspace files")
    raw = bounded(path, 512 * 1024)
    return raw, {"path": path.relative_to(root).as_posix(), "sha256": digest(raw)}


def _inventory(root, source):
    raw, reference = _reference(root, source)
    inventory = _dict(
        json.loads(raw, object_pairs_hook=_unique_pairs),
        ("schema", "components", "tokens"),
        "component inventory",
    )
    if inventory["schema"] != "prestige.component-inventory.v1":
        raise ValueError("Unsupported component inventory")
    components = inventory["components"]
    if not isinstance(components, dict) or not 1 <= len(components) <= len(COMPONENT_ROLES):
        raise ValueError("Declare at least one supported component role")
    bound = {}
    for role, value in components.items():
        if role not in COMPONENT_ROLES:
            raise ValueError(f"Unknown component role: {role}")
        row = _dict(value, ("name", "source", "usage"), "component")
        name = _text(row["name"], "component name")
        _text(row["usage"], "component usage")
        if not re.fullmatch(r"[$A-Za-z_][$\w]{0,79}", name, re.ASCII):
            raise ValueError("Component name must be a source identifier")
        code, location = _reference(root, row["source"])
        if not re.search(rf"(?<![\w$]){re.escape(name)}(?![\w$])", code.decode("utf-8")):
            raise ValueError(f"{name} is absent from its declared source")
        bound[role] = {"name": name, "source": location, "usage": row["usage"]}
    return {
        "inventory": reference,
        "components": bound,
        "tokens": _reference(root, inventory["tokens"])[1] if inventory["tokens"] is not None else None,
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
    journey_states: dict | None = None
    component_inventory: dict | None = None

    def to_dict(self) -> dict:
        report = {
            "purpose": self.purpose,
            "profile": self.profile,
            "psychology": self.psychology,
            "directives": self.directives,
            "anti_patterns": self.anti_patterns,
            "sections": self.sections,
            "verification": self.verification,
        }
        if self.journey_states:
            report["journey_states"] = self.journey_states
        if self.component_inventory:
            report["component_inventory"] = self.component_inventory
        return report


def compile_brief(source: Path | None = None, *, purpose: str = "developer",
                  root: Path = Path("."), components: str | None = None) -> DesignBrief:
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
        journey_states=dict(STATES) if profile.key == "saas" or components else None,
        component_inventory=_inventory(root.resolve(), components) if components else None,
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
    if brief.journey_states:
        lines += ["", "## App states", ""]
        lines.extend(f"- **{state.title()}** – {guidance}" for state, guidance in brief.journey_states.items())
    if brief.component_inventory:
        lines += ["", "## Existing components", ""]
        for role, item in brief.component_inventory["components"].items():
            lines.append(f"- **{role.replace('_', ' ').capitalize()}** – "
                         f"`{item['name']}` in {_plain(item['source']['path'])}. {_plain(item['usage'])}")
        if tokens := brief.component_inventory["tokens"]:
            lines.append(f"- Reuse the tokens in {_plain(tokens['path'])}.")
    return "\n".join(lines)
