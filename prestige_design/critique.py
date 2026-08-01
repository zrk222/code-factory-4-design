"""Deterministic-first seven-lens interface critique receipts.

The critique taxonomy is adapted from Owl-Listener/designer-skills under MIT.
Subjective observations remain non-blocking heuristics; only deterministic
P1/P2 findings can block strict mode.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
import os
from pathlib import Path
import re
import tempfile
from typing import Iterable

from .tokens import report_tokens


SCHEMA = "prestige.critique.v1"
DIMENSIONS = (
    "visual_hierarchy",
    "composition",
    "color",
    "affordance",
    "information_density",
    "typography",
    "brand_consistency",
)
UPSTREAM = {
    "repository": "https://github.com/Owl-Listener/designer-skills",
    "commit": "acc3e574b36ef2895268a176dbae886e1b845ae0",
    "license": "MIT",
}


@dataclass(frozen=True)
class CritiqueFinding:
    dimension: str
    code: str
    severity: str
    mode: str
    observation: str
    problem: str
    fix: str
    evidence: dict

    def to_dict(self) -> dict:
        """Return the exact eight-field public finding shape."""
        return asdict(self)


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _css(html: str, css: str) -> str:
    embedded = "\n".join(re.findall(r"<style[^>]*>(.*?)</style>", html, re.I | re.S))
    inline = "\n".join(re.findall(r"style=[\"'](.*?)[\"']", html, re.I | re.S))
    return re.sub(r"/\*.*?\*/", "", "\n".join((embedded, inline, css)), flags=re.S)


def _plain(value: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", value)).strip()


def _finding(
    dimension: str,
    code: str,
    severity: str,
    mode: str,
    observation: str,
    problem: str,
    fix: str,
    evidence: dict,
    *,
    confidence: float = 1.0,
) -> CritiqueFinding:
    if dimension not in DIMENSIONS:
        raise ValueError(f"unsupported critique dimension: {dimension}")
    if severity not in {"P1", "P2", "P3"}:
        raise ValueError(f"unsupported severity: {severity}")
    if mode not in {"deterministic", "heuristic"}:
        raise ValueError(f"unsupported finding mode: {mode}")
    bounded = max(0.0, min(1.0, float(confidence)))
    return CritiqueFinding(
        dimension, code, severity, mode, observation, problem, fix,
        {**evidence, "confidence": bounded},
    )


def _hex_rgb(value: str) -> tuple[int, int, int] | None:
    value = value.lower()
    if re.fullmatch(r"#[0-9a-f]{3}", value):
        value = "#" + "".join(char * 2 for char in value[1:])
    if not re.fullmatch(r"#[0-9a-f]{6}", value):
        return None
    return tuple(int(value[index:index + 2], 16) for index in (1, 3, 5))


def _luminance(value: str) -> float | None:
    rgb = _hex_rgb(value)
    if rgb is None:
        return None
    channels = []
    for item in rgb:
        channel = item / 255
        channels.append(channel / 12.92 if channel <= 0.04045 else ((channel + 0.055) / 1.055) ** 2.4)
    return 0.2126 * channels[0] + 0.7152 * channels[1] + 0.0722 * channels[2]


def contrast_ratio(foreground: str, background: str) -> float | None:
    """Return WCAG contrast arithmetic for two opaque 3/6-digit hex colors."""
    first, second = _luminance(foreground), _luminance(background)
    if first is None or second is None:
        return None
    return (max(first, second) + 0.05) / (min(first, second) + 0.05)


def _contrast_pairs(style: str) -> list[tuple[str, str, float]]:
    pairs = []
    for _, declarations in re.findall(r"([^{}]+)\{([^{}]+)\}", style, re.S):
        foreground = re.search(r"(?<![-\w])color\s*:\s*(#[0-9a-f]{3,6})\b", declarations, re.I)
        background = re.search(r"background(?:-color)?\s*:\s*(#[0-9a-f]{3,6})\b", declarations, re.I)
        if foreground and background:
            ratio = contrast_ratio(foreground.group(1), background.group(1))
            if ratio is not None:
                pairs.append((foreground.group(1).lower(), background.group(1).lower(), ratio))
    return pairs


def _contract_state(path: Path | None, label: str) -> dict:
    if path is None or not Path(path).is_file():
        return {"contract": label, "status": "missing", "marker": "CRITIQUE_CONTRACT_ABSENT"}
    payload = Path(path).read_bytes()
    return {
        "contract": label,
        "status": "hashed",
        "sha256": hashlib.sha256(payload).hexdigest(),
        "marker": "CRITIQUE_CONTRACT_HASHED",
    }


def _visual_hierarchy(html: str) -> list[CritiqueFinding]:
    findings = []
    h1_count = len(re.findall(r"<h1\b", html, re.I))
    if h1_count != 1:
        findings.append(_finding(
            "visual_hierarchy", "HIERARCHY_H1_COUNT", "P2", "deterministic",
            f"Found {h1_count} h1 elements.",
            "The primary page promise has no single semantic entry point.",
            "Use exactly one page-level h1 that states the primary promise.",
            {"h1_count": h1_count},
        ))
    primary = len(re.findall(r"<(?:a|button)[^>]*(?:class=[\"'][^\"']*(?:primary|cta)|data-primary)", html, re.I))
    if primary > 1:
        findings.append(_finding(
            "visual_hierarchy", "HIERARCHY_PRIMARY_COMPETITION", "P2", "deterministic",
            f"Found {primary} controls marked as primary.",
            "Multiple primary actions compete for first attention.",
            "Keep one primary action per viewport and demote the alternatives.",
            {"primary_controls": primary},
        ))
    return findings


def _composition(style: str) -> list[CritiqueFinding]:
    findings = []
    if not re.search(r"display\s*:\s*(?:grid|flex)", style, re.I):
        findings.append(_finding(
            "composition", "COMPOSITION_STRUCTURE_ABSENT", "P2", "deterministic",
            "No CSS grid or flex layout declaration was found.",
            "The source exposes no deterministic layout structure for alignment and grouping.",
            "Declare the principal layout with grid or flex and explicit gaps.",
            {"grid_or_flex": False},
        ))
    if not re.search(r"\bgap\s*:", style, re.I):
        findings.append(_finding(
            "composition", "COMPOSITION_RHYTHM_UNPROVEN", "P3", "heuristic",
            "No explicit gap rhythm was found.",
            "Spacing rhythm may depend on scattered margins and is difficult to verify statically.",
            "Define a small spacing scale and use gap for repeated groups.",
            {"gap_declaration": False}, confidence=0.68,
        ))
    return findings


def _color(style: str) -> list[CritiqueFinding]:
    findings = []
    pairs = _contrast_pairs(style)
    for foreground, background, ratio in pairs:
        if ratio < 4.5:
            findings.append(_finding(
                "color", "COLOR_TEXT_CONTRAST", "P1", "deterministic",
                f"Computed contrast {ratio:.2f}:1 for {foreground} on {background}.",
                "Normal-size text may be unreadable at this contrast.",
                "Choose foreground and background colors with at least 4.5:1 contrast for normal text.",
                {"foreground": foreground, "background": background, "ratio": round(ratio, 3), "threshold": 4.5},
            ))
    if not pairs:
        findings.append(_finding(
            "color", "COLOR_CONTRAST_UNRESOLVED", "P3", "heuristic",
            "No opaque foreground/background hex pair could be resolved in one CSS rule.",
            "Static contrast arithmetic is incomplete for variables, gradients, images, or inherited colors.",
            "Run a browser-rendered contrast audit for the final computed styles.",
            {"resolved_pairs": 0}, confidence=0.82,
        ))
    return findings


def _affordance(html: str, style: str) -> list[CritiqueFinding]:
    findings = []
    controls = re.findall(r"<(button|a)\b([^>]*)>(.*?)</\1>", html, re.I | re.S)
    unnamed = 0
    for tag, attrs, body in controls:
        if tag.lower() == "a" and not re.search(r"\bhref\s*=", attrs, re.I):
            continue
        name = _plain(body)
        labelled = re.search(r"\b(?:aria-label|title)\s*=\s*[\"'][^\"']+", attrs, re.I)
        image_alt = re.search(r"<img[^>]+alt\s*=\s*[\"'][^\"']+", body, re.I)
        if not name and not labelled and not image_alt:
            unnamed += 1
    if unnamed:
        findings.append(_finding(
            "affordance", "AFFORDANCE_NAME_MISSING", "P1", "deterministic",
            f"Found {unnamed} interactive controls without an accessible name.",
            "Users cannot reliably identify the action, including through assistive technology.",
            "Add visible action text or a precise accessible name.",
            {"unnamed_controls": unnamed},
        ))
    if controls and not re.search(r":focus(?:-visible)?", style, re.I):
        findings.append(_finding(
            "affordance", "AFFORDANCE_FOCUS_STATE", "P2", "deterministic",
            "Interactive controls exist but no focus style was found.",
            "Keyboard focus may be invisible.",
            "Add a high-contrast :focus-visible treatment that is not removed without replacement.",
            {"controls": len(controls), "focus_state": False},
        ))
    if controls and not re.search(r"(?:min-)?(?:height|block-size)\s*:\s*(?:4[4-9]|[5-9]\d|\d{3,})px", style, re.I):
        findings.append(_finding(
            "affordance", "AFFORDANCE_TARGET_SIZE", "P2", "deterministic",
            "No control target dimension of at least 44px was found.",
            "Small targets increase touch and motor-error risk.",
            "Set min-height or min-block-size to at least 44px for primary controls.",
            {"minimum_target_px": 44, "verified": False},
        ))
    return findings


def _information_density(html: str) -> list[CritiqueFinding]:
    findings = []
    nav_max = max((len(re.findall(r"<a\b", nav, re.I)) for nav in re.findall(r"<nav\b[^>]*>(.*?)</nav>", html, re.I | re.S)), default=0)
    if nav_max > 7:
        findings.append(_finding(
            "information_density", "DENSITY_NAV_OVERLOAD", "P2", "deterministic",
            f"The largest navigation group contains {nav_max} links.",
            "The primary choice set exceeds the reviewed seven-item navigation bound.",
            "Group secondary destinations or progressively disclose them.",
            {"navigation_links": nav_max, "threshold": 7},
        ))
    sections = len(re.findall(r"<(?:section|article)\b", html, re.I))
    words = len(re.findall(r"\b[\w'-]+\b", _plain(html)))
    if sections and words / sections > 180:
        findings.append(_finding(
            "information_density", "DENSITY_SCAN_LOAD", "P3", "heuristic",
            f"Observed approximately {round(words / sections)} words per content section.",
            "Long undifferentiated sections may slow scanning.",
            "Split the longest section with headings, summaries, or progressive disclosure.",
            {"words": words, "sections": sections, "words_per_section": round(words / sections, 2)}, confidence=0.66,
        ))
    return findings


def _typography(style: str) -> list[CritiqueFinding]:
    findings = []
    sizes = [float(value) for value in re.findall(r"font-size\s*:\s*(\d+(?:\.\d+)?)px", style, re.I)]
    if sizes and min(sizes) < 16:
        findings.append(_finding(
            "typography", "TYPE_TEXT_TOO_SMALL", "P2", "deterministic",
            f"The smallest declared font size is {min(sizes):g}px.",
            "Text below 16px can reduce readability and trigger mobile input zoom.",
            "Use at least 16px for body and form-control text; reserve smaller sizes for nonessential labels.",
            {"minimum_font_px": min(sizes), "threshold_px": 16},
        ))
    line_heights = [float(value) for value in re.findall(r"line-height\s*:\s*(\d+(?:\.\d+)?)(?!\s*(?:px|rem|em|%))", style, re.I)]
    if line_heights and min(line_heights) < 1.5:
        findings.append(_finding(
            "typography", "TYPE_LEADING_TIGHT", "P2", "deterministic",
            f"The smallest unitless line height is {min(line_heights):g}.",
            "Tight leading reduces paragraph legibility.",
            "Use a unitless body line-height of at least 1.5.",
            {"minimum_line_height": min(line_heights), "threshold": 1.5},
        ))
    if not re.search(r"max-width\s*:\s*(?:4[5-9]|[5-6]\d|7[0-5])ch", style, re.I):
        findings.append(_finding(
            "typography", "TYPE_LINE_MEASURE_UNPROVEN", "P3", "heuristic",
            "No 45ch-to-75ch text measure was found.",
            "Long text lines may be harder to track, but computed browser width is required for certainty.",
            "Constrain long-form copy to approximately 45ch-75ch and verify after rendering.",
            {"recommended_min_ch": 45, "recommended_max_ch": 75}, confidence=0.72,
        ))
    return findings


def _brand(html: str, style: str, design: Path | None) -> list[CritiqueFinding]:
    if design is None or not Path(design).is_file():
        return []
    report = report_tokens(html, Path(design), style)
    failures = [item for item in report.get("findings", []) if item.get("failure_class")]
    if not failures:
        return []
    return [_finding(
        "brand_consistency", "BRAND_TOKEN_DRIFT", "P2", "deterministic",
        f"Found {len(failures)} CSS values outside the supplied DESIGN.md token contract.",
        "Off-contract values weaken visual consistency and make brand intent difficult to audit.",
        "Replace each literal with a contract token or amend the reviewed contract before use.",
        {"off_contract_values": len(failures), "contract_sha256": hashlib.sha256(Path(design).read_bytes()).hexdigest()},
    )]


def critique_html(
    html: str,
    css: str = "",
    *,
    design: Path | None = None,
    mood: Path | None = None,
    voice: Path | None = None,
) -> dict:
    """Return a publication-safe seven-lens critique receipt."""
    style = _css(html, css)
    findings: list[CritiqueFinding] = []
    findings.extend(_visual_hierarchy(html))
    findings.extend(_composition(style))
    findings.extend(_color(style))
    findings.extend(_affordance(html, style))
    findings.extend(_information_density(html))
    findings.extend(_typography(style))
    findings.extend(_brand(html, style, design))
    findings.sort(key=lambda item: ({"P1": 0, "P2": 1, "P3": 2}[item.severity], DIMENSIONS.index(item.dimension), item.code))
    rows = [item.to_dict() for item in findings]
    severity_counts = {key: sum(item.severity == key for item in findings) for key in ("P1", "P2", "P3")}
    deterministic_blockers = [item for item in findings if item.mode == "deterministic" and item.severity == "P1"]
    contracts = [_contract_state(design, "DESIGN.md"), _contract_state(mood, "MOOD.md"), _contract_state(voice, "VOICE.md")]
    markers = [
        "CRITIQUE_SEVEN_LENSES", "CRITIQUE_SCHEMA_V1", "CRITIQUE_FINDING_SHAPE_EXACT",
        "CRITIQUE_ATTRIBUTED_MIT", "RELEASE_080_SYNCHRONIZED",
        "CRITIQUE_PUBLICATION_SAFE",
    ]
    markers.extend(sorted({item["marker"] for item in contracts}))
    if deterministic_blockers:
        markers.append("CRITIQUE_BLOCKED_P1")
    dimensions = []
    for dimension in DIMENSIONS:
        selected = [item for item in rows if item["dimension"] == dimension]
        dimensions.append({
            "name": dimension,
            "finding_count": len(selected),
            "highest_severity": next((level for level in ("P1", "P2", "P3") if any(item["severity"] == level for item in selected)), None),
            "deterministic_findings": sum(item["mode"] == "deterministic" for item in selected),
            "heuristic_findings": sum(item["mode"] == "heuristic" for item in selected),
        })
    return {
        "schema": SCHEMA,
        "marker": "CRITIQUE_SEVEN_LENSES",
        "markers": markers,
        "source_sha256": _sha(html + "\0" + css),
        "passed": not deterministic_blockers,
        "strict_passed": not any(item.mode == "deterministic" and item.severity in {"P1", "P2"} for item in findings),
        "dimensions": dimensions,
        "severity_counts": severity_counts,
        "findings": rows,
        "contracts": contracts,
        "attribution": UPSTREAM,
        "scope": [
            "Static critique is not an accessibility conformance audit or browser-rendered proof.",
            "Heuristic findings never block the verdict.",
            "The receipt omits source, CSS, contract bodies, prompts, logs, and absolute paths.",
        ],
    }


def write_critique_receipt(payload: dict, output: Path) -> Path:
    """Atomically write one critique receipt."""
    destination = Path(output).resolve()
    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=destination.parent, delete=False) as handle:
        handle.write(json.dumps(payload, indent=2, sort_keys=True))
        handle.write("\n")
        temporary = Path(handle.name)
    os.replace(temporary, destination)
    return destination


def challenge_critique(html: str, css: str = "") -> dict:
    """Prove each dimension rejects one isolated deliberate defect."""
    base = html if html.strip() else "<main><h1>Product proof</h1><button class='primary'>Start</button></main>"
    style = css + "\nmain{display:grid;gap:24px;color:#111;background:#fff;max-width:65ch;font-size:16px;line-height:1.6}button{min-height:44px}button:focus-visible{outline:3px solid #000}"
    mutants: list[tuple[str, str, str, Path | None]] = [
        ("visual_hierarchy", re.sub(r"</?h1[^>]*>", "", base, flags=re.I), style, None),
        (
            "composition",
            re.sub(r"display\s*:\s*(?:grid|flex)\s*;?", "", base, flags=re.I),
            re.sub(r"display\s*:\s*(?:grid|flex)\s*;?", "", style, flags=re.I),
            None,
        ),
        ("color", base, style + "\n.low-contrast{color:#777;background:#777}", None),
        ("affordance", base + "<button></button>", style, None),
        ("information_density", base + "<nav>" + "".join(f"<a href='/{index}'>Link {index}</a>" for index in range(8)) + "</nav>", style, None),
        ("typography", base, style + "\nsmall{font-size:12px;line-height:1.1}", None),
    ]
    with tempfile.TemporaryDirectory() as temporary:
        design = Path(temporary) / "DESIGN.md"
        design.write_text(
            "```design-tokens\n" + json.dumps({
                "spacing": ["24px"], "font_size": ["16px"], "font_weight": [],
                "radius": [], "color": ["#111111", "#ffffff"],
            }) + "\n```\n",
            encoding="utf-8",
        )
        mutants.append(("brand_consistency", base, style + "\n.brand-drift{color:#ff00ff}", design))
        results = []
        for dimension, mutant_html, mutant_css, contract in mutants:
            receipt = critique_html(mutant_html, mutant_css, design=contract)
            killed = any(
                item["dimension"] == dimension
                and item["mode"] == "deterministic"
                and item["severity"] in {"P1", "P2"}
                for item in receipt["findings"]
            )
            results.append({"dimension": dimension, "killed": killed})
    passed = len(results) == len(DIMENSIONS) and all(item["killed"] for item in results)
    return {
        "schema": "prestige.critique-challenge.v1",
        "marker": "CRITIQUE_MUTATIONS_REJECTED" if passed else "HOLLOW_CRITIQUE",
        "passed": passed,
        "mutants_total": len(results),
        "mutants_killed": sum(item["killed"] for item in results),
        "mutations": results,
    }
