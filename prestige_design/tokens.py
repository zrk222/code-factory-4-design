"""Frozen DESIGN.md token contracts and deterministic CSS enforcement."""
from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path

from .attribution import FailureClass

TEMPLATE = '''# DESIGN.md

This committed file is the frozen visual token contract for this project.
Do not query a live design system during a gate run.

```design-tokens
{
  "spacing": ["4px", "8px", "12px", "16px", "24px", "32px", "48px"],
  "font_size": ["14px", "16px", "20px", "24px", "32px", "48px"],
  "font_weight": ["400", "600", "700"],
  "radius": ["0px", "4px", "8px"],
  "color": ["#101828", "#ffffff", "#2563eb", "#16a34a", "#dc2626"]
}
```
'''

PROPERTY_GROUPS = {
    "spacing": re.compile(r"^(?:padding|margin|gap|top|right|bottom|left|inset)", re.I),
    "font_size": re.compile(r"^font-size$", re.I),
    "font_weight": re.compile(r"^font-weight$", re.I),
    "radius": re.compile(r"^border(?:-[a-z-]+)?-radius$", re.I),
    "color": re.compile(r"(?:color|background|border|outline|fill|stroke)$", re.I),
}


@dataclass(frozen=True)
class TokenFinding:
    property: str
    value: str
    group: str
    passed: bool
    failure_class: str | None = None
    nearest: str | None = None

    def to_dict(self):
        return self.__dict__


def write_template(path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(TEMPLATE, encoding="utf-8")
    return path


def load_contract(path: Path) -> dict[str, list[str]]:
    text = path.read_text(encoding="utf-8")
    match = re.search(r"```design-tokens\s*(\{.*?\})\s*```", text, re.S)
    if not match:
        raise ValueError("DESIGN.md must contain one ```design-tokens JSON block```")
    payload = json.loads(match.group(1))
    required = {"spacing", "font_size", "font_weight", "radius", "color"}
    if set(payload) != required or any(not isinstance(payload[key], list) for key in required):
        raise ValueError("design token contract must define spacing, font_size, font_weight, radius, and color lists")
    return {key: [str(value).lower() for value in values] for key, values in payload.items()}


def _css(html: str, css: str) -> str:
    embedded = "\n".join(re.findall(r"<style[^>]*>(.*?)</style>", html, re.I | re.S))
    inline = "\n".join(re.findall(r"style=[\"'](.*?)[\"']", html, re.I | re.S))
    return "\n".join([embedded, inline, css])


def _nearest(value: str, allowed: list[str]) -> str | None:
    number = re.fullmatch(r"(-?\d+(?:\.\d+)?)(px)?", value)
    if not number:
        return allowed[0] if allowed else None
    unit = number.group(2) or ""
    candidates = []
    for item in allowed:
        candidate = re.fullmatch(r"(-?\d+(?:\.\d+)?)(px)?", item)
        if candidate and (candidate.group(2) or "") == unit:
            candidates.append((abs(float(number.group(1)) - float(candidate.group(1))), item))
    return min(candidates)[1] if candidates else (allowed[0] if allowed else None)


def _values(group: str, raw: str) -> list[str]:
    raw = raw.strip().lower()
    if "var(" in raw or raw in {"inherit", "initial", "unset", "auto", "none", "transparent"}:
        return []
    if group == "color":
        return re.findall(r"#[0-9a-f]{3,8}\b", raw)
    if group == "font_weight":
        return re.findall(r"\b(?:[1-9]00)\b", raw)
    return re.findall(r"-?\d+(?:\.\d+)?px", raw)


def lint_tokens(html: str, contract: dict[str, list[str]], css: str = "") -> list[TokenFinding]:
    findings: list[TokenFinding] = []
    for prop, raw in re.findall(r"([\w-]+)\s*:\s*([^;}]+)", _css(html, css)):
        for group, pattern in PROPERTY_GROUPS.items():
            if not pattern.search(prop):
                continue
            for value in _values(group, raw):
                allowed = contract[group]
                passed = value in allowed
                findings.append(TokenFinding(
                    property=prop, value=value, group=group, passed=passed,
                    failure_class=None if passed else FailureClass.OFF_TOKEN.value,
                    nearest=None if passed else _nearest(value, allowed),
                ))
            break
    return findings


def report_tokens(html: str, design: Path | None, css: str = "") -> dict:
    if design is None or not design.exists():
        return {
            "stage": "design_tokens", "passed": False, "n_checked": 0, "n_passed": 0,
            "rate": 0.0, "dominant_failure_class": FailureClass.CONTRACT_MISSING.value,
            "findings": [{"failure_class": FailureClass.CONTRACT_MISSING.value,
                          "evidence": "DESIGN.md is required for strict token linting"}],
        }
    contract = load_contract(design)
    findings = lint_tokens(html, contract, css)
    passed = sum(item.passed for item in findings)
    failures = [item for item in findings if not item.passed]
    return {
        "stage": "design_tokens", "passed": not failures, "n_checked": len(findings),
        "n_passed": passed, "rate": passed / len(findings) if findings else 1.0,
        "dominant_failure_class": FailureClass.OFF_TOKEN.value if failures else None,
        "findings": [item.to_dict() for item in findings], "contract": str(design),
    }


def verify_tokens(html: str, design: Path, css: str = "") -> dict:
    contract = load_contract(design)
    baseline = lint_tokens(html, contract, css)
    exercised = [item for item in baseline if item.passed]
    mutations = []
    for item in exercised:
        mutated = {key: list(values) for key, values in contract.items()}
        mutated[item.group].remove(item.value)
        caught = any(
            not result.passed and result.value == item.value and result.group == item.group
            for result in lint_tokens(html, mutated, css)
        )
        mutations.append({"token": item.value, "group": item.group, "killed": caught,
                          "failure_class": None if caught else FailureClass.HOLLOW_TOKEN.value})
    unique = {(item["token"], item["group"]): item for item in mutations}
    mutations = list(unique.values())
    return {
        "schema": "factory.challenge.v1", "brick": "prestige", "stage": "design_tokens",
        "passed": not any(not item.passed for item in baseline) and bool(mutations) and all(item["killed"] for item in mutations),
        "baseline_passed": not any(not item.passed for item in baseline),
        "mutants_total": len(mutations), "mutants_killed": sum(item["killed"] for item in mutations),
        "mutations": mutations, "scope": "mutates every token exercised by the supplied page",
    }
