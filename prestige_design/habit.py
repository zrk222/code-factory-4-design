"""Measure a declared habit journey and seal the evidence used to review it."""

from __future__ import annotations

import hashlib
from html import escape
import json
from pathlib import Path

LENSES = {"habit_consumer": 3, "habit_fintech": 3, "habit_saas": 5}
STEPS = {
    "itch": (
        "target_emotion",
        "routine_trigger_schedule",
        "notification_copy_examples",
    ),
    "lazy_thumb": (
        "compressed_core_action",
        "ergonomic_layout_changes",
        "calibrated_micro_threshold",
    ),
    "paved_path": ("zero_choice_landing_behavior", "preselected_defaults"),
    "variable_reward": (
        "reward_of_hunt",
        "reward_of_tribe",
        "reward_of_self",
        "variability_schedule",
    ),
    "continuation": ("dead_end_replacements", "continuous_loop_implementations"),
    "stored_value": ("stored_value_types", "reentry_value", "data_controls"),
}
GUARDRAILS = {
    "no_deceptive_controls": "DARK_PATTERN_TRAP",
    "no_predatory_rewards": "PREDATORY_REWARD",
    "feasible_streak": "HOLLOW_STREAK",
    "notification_controls": "NOTIFICATION_CONTROL_GAP",
    "portable_data": "STORED_VALUE_CONTROL_GAP",
}
_LIST_FIELDS = {
    "notification_copy_examples",
    "preselected_defaults",
    "dead_end_replacements",
    "continuous_loop_implementations",
    "stored_value_types",
}
_MAX_BYTES = 4 * 1024 * 1024


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def seal(report: dict) -> dict:
    return {
        **report,
        "receipt_sha256": digest(json.dumps(report, sort_keys=True).encode()),
    }


def bounded(path: Path, limit: int = _MAX_BYTES) -> bytes:
    with path.open("rb") as stream:
        data = stream.read(limit + 1)
    if not data or len(data) > limit:
        raise ValueError("Expected a nonempty file within the input byte limit")
    return data


def local_path(root: Path, name: str) -> Path:
    path = Path(name)
    if path.is_absolute() or ":" in name or ".." in path.parts:
        raise ValueError("Use a workspace-relative path")
    resolved = (root / path).resolve()
    if not resolved.is_relative_to(root):
        raise ValueError("Path leaves the workspace")
    return resolved


def _dict(value, keys, label):
    if not isinstance(value, dict) or set(value) != set(keys):
        raise ValueError(f"{label} requires exactly {', '.join(keys)}")
    return value


def _text(value, label):
    if not isinstance(value, str) or not value.strip() or len(value) > 1500:
        raise ValueError(f"{label} requires bounded nonempty text")
    return value


def _items(value, label):
    if not isinstance(value, list) or not 1 <= len(value) <= 50:
        raise ValueError(f"{label} requires 1 to 50 entries")
    return value


def _integer(value, label, maximum=10000):
    if type(value) is not int or not 0 <= value <= maximum:
        raise ValueError(f"{label} requires an integer from 0 to {maximum}")
    return value


def _booleans(value, keys, label):
    result = _dict(value, keys, label)
    if any(type(flag) is not bool for flag in result.values()):
        raise ValueError(f"{label} requires boolean observations")
    return result


def _cta_reached(value):
    row = _dict(
        value, ("id", "width", "center_y", "height", "visible", "reachable"), "CTA"
    )
    _text(row["id"], "CTA id")
    center, height = (_integer(row[key], key) for key in ("center_y", "height"))
    if _integer(row["width"], "width") == 0 or height == 0 or center > height:
        raise ValueError("CTA center must be inside a nonzero viewport")
    flags = _booleans(
        {key: row[key] for key in ("visible", "reachable")},
        ("visible", "reachable"),
        "CTA",
    )
    return center * 100 >= 65 * height and all(flags.values())


def _continuation(value):
    flags = ("can_exit", "has_next", "auto_advances", "user_enabled")
    row = _dict(value, ("id", *flags), "completion")
    _text(row["id"], "completion id")
    result = _booleans({key: row[key] for key in flags}, flags, "completion")
    return (
        result["can_exit"]
        and result["has_next"]
        and (not result["auto_advances"] or result["user_enabled"])
    )


def _metrics(value):
    run = _dict(
        value,
        ("taps", "inputs", "choices", "ctas", "landing", "completions"),
        "journey",
    )
    ctas, completions = (_items(run[key], key) for key in ("ctas", "completions"))
    landing = {"direct": 1.0, "recommended": 0.5, "choice": 0.0}
    if not isinstance(run["landing"], str) or run["landing"] not in landing:
        raise ValueError("landing requires direct, recommended, or choice")
    return {
        "tafi": _integer(run["taps"], "taps")
        + _integer(run["inputs"], "inputs")
        + 2 * _integer(run["choices"], "choices"),
        "tzer": sum(map(_cta_reached, ctas)) / len(ctas),
        "ppdv": landing[run["landing"]],
        "scer": sum(map(_continuation, completions)) / len(completions),
    }


def _blueprint(value):
    steps = _dict(value, STEPS, "habit_steps")
    for name, keys in STEPS.items():
        for field, item in _dict(steps[name], keys, name).items():
            for entry in _items(item, field) if field in _LIST_FIELDS else [item]:
                _text(entry, field)
    return steps


def _identities(rows, keys):
    identities = {tuple(row[key] for key in keys) for row in rows}
    if len(identities) != len(rows):
        raise ValueError("Duplicate control observation")
    return identities


def _matching_observations(baseline, candidate):
    for kind, keys in (("ctas", ("id", "width", "height")), ("completions", ("id",))):
        comparable = [_identities(run[kind], keys) for run in (baseline, candidate)]
        if comparable[0] != comparable[1]:
            raise ValueError(
                "Baseline and candidate must observe the same controls and viewports"
            )


def _evidence(root, value):
    if value["mode"] == "proposal" and value["evidence"] == []:
        return []
    entries = _items(value["evidence"], "evidence")
    paths = set()
    for index, item in enumerate(entries):
        row = _dict(item, ("path", "sha256"), "evidence")
        path = local_path(root, _text(row["path"], "evidence path"))
        raw = bounded(path)
        if path in paths or digest(raw) != row["sha256"]:
            raise ValueError("Evidence is duplicated or has changed")
        paths.add(path)
        if index == 0 and value["mode"] == "observed":
            _bound_observations(raw, value)
    return entries


def _bound_observations(raw, value):
    expected = {
        "schema": "prestige.habit-observations.v1",
        **{
            key: value[key]
            for key in ("app_name", "lens", "baseline", "candidate", "controls")
        },
    }
    observed = json.loads(raw, object_pairs_hook=_unique_pairs)
    if json.dumps(observed, sort_keys=True) != json.dumps(expected, sort_keys=True):
        raise ValueError(
            "The first evidence artifact must contain the matching journey observations"
        )


def _unique_pairs(items):
    result = dict(items)
    if len(result) != len(items):
        raise ValueError("Duplicate JSON key")
    return result


def _roadmap(value):
    for item in _items(value, "implementation_roadmap"):
        row = _dict(
            item, ("feature", "effort", "success_metric", "hypothesis"), "roadmap item"
        )
        for key in ("feature", "success_metric", "hypothesis"):
            _text(row[key], key)
        if row["effort"] not in ("LOW", "MEDIUM", "HIGH"):
            raise ValueError("effort requires LOW, MEDIUM, or HIGH")
    return value


def _findings(lens, scores, guards):
    rules = {
        "FRICTION_BARRIER": scores["tafi"] > LENSES[lens],
        "THUMB_ZONE_MISS": scores["tzer"] < 0.9,
        "DEFAULT_PATH_FORK": scores["ppdv"] == 0,
        "DEAD_END_TERMINAL": scores["scer"] < 1,
        **{code: not guards[name] for name, code in GUARDRAILS.items()},
    }
    return [code for code, failed in rules.items() if failed]


def habit_audit(root: Path, source: str, *, captures=None, assets=None) -> dict:
    root = root.resolve()
    raw = bounded(local_path(root, source))
    value = _dict(
        json.loads(raw, object_pairs_hook=_unique_pairs),
        (
            "schema",
            "app_name",
            "core_value_prop",
            "lens",
            "mode",
            "baseline",
            "candidate",
            "habit_steps",
            "controls",
            "evidence",
            "implementation_roadmap",
        ),
        "habit contract",
    )
    if value["schema"] != "prestige.habit-contract.v1":
        raise ValueError("Unsupported habit contract")
    lens, mode = value["lens"], value["mode"]
    if lens not in tuple(LENSES) or mode not in ("proposal", "observed"):
        raise ValueError("Unsupported habit lens or evidence mode")
    app = _text(value["app_name"], "app_name")
    goal = _text(value["core_value_prop"], "core_value_prop")
    evidence = _evidence(root, value)
    journey = None
    if captures:
        from .journey import load_pair

        if mode != "proposal":
            raise ValueError("Use a proposal contract with separate browser captures")
        baseline, candidate, journey = load_pair(root, *captures, assets=assets)
        if baseline["app_name"] != app:
            raise ValueError("The app name in the captures must match the contract")
        _booleans(baseline["controls"], GUARDRAILS, "baseline controls")
        value.update(
            baseline=baseline["metrics"],
            candidate=candidate["metrics"],
            controls=candidate["controls"],
        )
        evidence = evidence + list(journey["captures"].values())
        mode = "observed"
    before, after = map(_metrics, (value["baseline"], value["candidate"]))
    _matching_observations(value["baseline"], value["candidate"])
    controls = _booleans(value["controls"], GUARDRAILS, "controls")
    findings = _findings(lens, after, controls)
    if journey and any(step["failed"] for step in journey["checkpoints"]):
        findings.append("JOURNEY_CHECKPOINT_FAILED")
    report = {
        "schema": "prestige.habit-audit.v1",
        "app_name": app,
        "core_value_prop": goal,
        "lens": lens,
        "mode": mode,
        "contract_sha256": digest(raw),
        "evidence": evidence,
        "baseline": before,
        "candidate": after,
        "thresholds": {
            "tafi_max": LENSES[lens],
            "tzer_min": 0.9,
            "ppdv_min": 0.5,
            "scer_min": 1,
        },
        "habit_steps": _blueprint(value["habit_steps"]),
        "implementation_roadmap": _roadmap(value["implementation_roadmap"]),
        "findings": findings,
        "decision": "BLOCKED"
        if findings
        else ("PROPOSED" if mode == "proposal" else "PASS"),
        "evidence_boundary": "Submitted journey observations and artifact hashes. Retention requires a product experiment.",
    }
    if journey:
        report["journey"] = journey
    return seal(report)


def _plain(value):
    return escape(" ".join(value.split())).replace("[", r"\[").replace("`", r"\`")


def habit_markdown(report: dict) -> str:
    lines = [
        "# App Habit Engineer audit",
        "",
        f"- App: {_plain(report['app_name'])}",
        f"- Core value: {_plain(report['core_value_prop'])}",
        f"- Verdict: {report['decision']}",
        f"- Evidence mode: {report['mode']}",
        "",
        "| Metric | Before | Candidate |",
        "| --- | ---: | ---: |",
    ]
    for key, before in report["baseline"].items():
        after = report["candidate"][key]
        lines.append(f"| {key.upper()} | {before:.2f} | {after:.2f} |")
    if journey := report.get("journey"):
        lines += ["", "## Browser journey", "", journey["scope"], ""]
        for step in journey["checkpoints"]:
            status = ", ".join(step["failed"]) if step["failed"] else "Pass"
            lines.append(f"- {step['id']} ({step['state']}) — {status}")
    lines += ["", "## Six mechanics", ""]
    for name, step in report["habit_steps"].items():
        lines.append(f"### {name.replace('_', ' ').title()}")
        for key, value in step.items():
            lines.append(
                f"- {key.replace('_', ' ').capitalize()}: "
                + _plain(", ".join(value) if isinstance(value, list) else value)
            )
    lines += ["", "## Delivery and measurement", ""]
    for item in report["implementation_roadmap"]:
        lines.append(
            f"- {_plain(item['feature'])} ({item['effort']}). {_plain(item['hypothesis'])} "
            f"Measure {_plain(item['success_metric'])}."
        )
    lines += [
        "",
        "## Findings",
        "",
        *(report["findings"] or ["No gate findings."]),
        "",
        report["evidence_boundary"],
    ]
    lines += [
        "",
        "## Evidence bindings",
        "",
        f"- Contract SHA-256: {report['contract_sha256']}",
        f"- Receipt SHA-256: {report['receipt_sha256']}",
    ]
    lines.extend(
        f"- {_plain(row['path'])} · SHA-256 {row['sha256']}"
        for row in report["evidence"]
    )
    return "\n".join(lines) + "\n"
