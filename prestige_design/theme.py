"""Opinionated purpose-driven Visual DNA contracts."""
from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from pathlib import Path


@dataclass(frozen=True)
class ThemeDNA:
    purpose: str
    archetype: str
    palette: dict[str, str]
    typography: dict[str, str]
    spacing: str
    radius_px: int
    density: str
    imagery: str
    motion: str
    trust_placement: str
    anti_patterns: tuple[str, ...]

    def to_dict(self) -> dict:
        return {"schema": "prestige.theme.v1", **asdict(self)}


THEMES = {
    "developer": ThemeDNA(
        "developer", "Proof-forward product",
        {"ink": "#172033", "paper": "#ffffff", "accent": "#2563eb", "signal": "#0f766e", "warning": "#b45309"},
        {"display": "Inter, ui-sans-serif, system-ui", "body": "Inter, ui-sans-serif, system-ui", "code": "ui-monospace, SFMono-Regular, Consolas"},
        "compact 8px grid", 6, "information-dense",
        "real terminal, product UI, or receipt evidence above the fold",
        "fast 120-180ms state changes; no decorative motion",
        "install command, CI result, and GitHub link beside the primary action",
        ("abstract AI imagery", "unsupported benchmark numbers", "marketing-only hero"),
    ),
    "healthcare": ThemeDNA(
        "healthcare", "Calm clinical assurance",
        {"ink": "#18323a", "paper": "#ffffff", "accent": "#087f8c", "signal": "#397367", "warning": "#a16207"},
        {"display": "Source Sans 3, ui-sans-serif, system-ui", "body": "Source Sans 3, ui-sans-serif, system-ui", "code": "ui-monospace, monospace"},
        "open 8px grid", 6, "calm-medium",
        "clear care context with identifiable workflow, never generic wellness stock",
        "gentle 180-240ms feedback with reduced-motion support",
        "privacy, clinician review, and next-step reassurance beside forms",
        ("scarcity", "miracle claims", "aggressive red", "celebratory denial states"),
    ),
    "fintech": ThemeDNA(
        "fintech", "Controlled financial clarity",
        {"ink": "#17212b", "paper": "#ffffff", "accent": "#005ea8", "signal": "#16794b", "warning": "#9a6700"},
        {"display": "IBM Plex Sans, ui-sans-serif, system-ui", "body": "IBM Plex Sans, ui-sans-serif, system-ui", "code": "IBM Plex Mono, ui-monospace"},
        "compact 8px grid", 4, "precise-medium",
        "real account, risk, fee, or control state with legible figures",
        "short 120-180ms transitions; confirmations favor clarity over delight",
        "fees, control, security, and audit evidence at the decision point",
        ("hidden fees", "fake urgency", "crypto-neon decoration", "unqualified guarantees"),
    ),
    "luxury": ThemeDNA(
        "luxury", "Quiet craft",
        {"ink": "#181818", "paper": "#ffffff", "accent": "#7c2d3e", "signal": "#2f6b57", "warning": "#8a5a00"},
        {"display": "Cormorant Garamond, Georgia, serif", "body": "Inter, ui-sans-serif, system-ui", "code": "ui-monospace, monospace"},
        "expansive 8px grid", 2, "sparse",
        "high-detail material, object, place, or craft photography",
        "slow restrained 220-320ms reveals; reduced-motion equivalent required",
        "provenance and craft details near inquiry or purchase actions",
        ("discount bursts", "badge clutter", "multiple competing CTAs", "generic stock"),
    ),
    "marketplace": ThemeDNA(
        "marketplace", "Bilateral trust",
        {"ink": "#1f2933", "paper": "#ffffff", "accent": "#0b6e75", "signal": "#2d7d46", "warning": "#b15c00"},
        {"display": "Inter, ui-sans-serif, system-ui", "body": "Inter, ui-sans-serif, system-ui", "code": "ui-monospace, monospace"},
        "compact 8px grid", 6, "comparison-dense",
        "inspectable listing, provider, location, or product imagery",
        "fast filtering and selection feedback; no layout-shifting hover",
        "identity, reviews, protection, and dispute path beside listing actions",
        ("anonymous proof", "inconsistent cards", "buried protection", "fake reviews"),
    ),
    "saas": ThemeDNA(
        "saas", "Product-led operations",
        {"ink": "#172033", "paper": "#ffffff", "accent": "#1d4ed8", "signal": "#0f766e", "warning": "#a15c00"},
        {"display": "Inter, ui-sans-serif, system-ui", "body": "Inter, ui-sans-serif, system-ui", "code": "ui-monospace, SFMono-Regular"},
        "compact 8px grid", 6, "work-focused",
        "actual workflow UI with legible data and real product state",
        "fast 120-180ms feedback; motion explains state change",
        "integration, security, and activation proof beside trial or demo",
        ("oversized empty hero", "decorative card grids", "vague all-in-one claims"),
    ),
    "editorial": ThemeDNA(
        "editorial", "Evidence-led narrative",
        {"ink": "#202124", "paper": "#ffffff", "accent": "#9f1239", "signal": "#126e5a", "warning": "#995c00"},
        {"display": "Newsreader, Georgia, serif", "body": "Source Sans 3, ui-sans-serif, system-ui", "code": "ui-monospace, monospace"},
        "rhythmic 8px grid", 2, "reading-medium",
        "figures, documents, data, or people directly supporting the story",
        "subtle 180-240ms reveals that preserve reading position",
        "source, date, method, and author adjacent to consequential claims",
        ("ecommerce pressure", "unsourced charts", "wall of text", "ambient stock"),
    ),
}


def theme_for(purpose: str) -> ThemeDNA:
    if purpose not in THEMES:
        raise ValueError(f"unknown purpose: {purpose}")
    return THEMES[purpose]


def write_theme(purpose: str, path: Path) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(theme_for(purpose).to_dict(), indent=2), encoding="utf-8")
    return path
