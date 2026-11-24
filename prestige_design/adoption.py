"""Local-first adoption surfaces: contract discovery, proof reports, and PR bundles."""
from __future__ import annotations

from collections import Counter
from html import escape
import json
from pathlib import Path
import re
import shutil

import yaml

from .tokens import PROPERTY_GROUPS, _values, report_tokens, verify_tokens


SOURCE_SUFFIXES = {".css", ".scss", ".sass", ".html", ".htm", ".jsx", ".tsx", ".vue", ".svelte"}
IGNORED_PARTS = {".git", "node_modules", "dist", "build", ".next", ".prestige", ".factory", "venv", ".venv"}


def _source_files(root: Path) -> list[Path]:
    return [path for path in root.rglob("*") if path.is_file() and path.suffix.lower() in SOURCE_SUFFIXES
            and not any(part in IGNORED_PARTS for part in path.parts)]


def _group_for_property(prop: str) -> str | None:
    for group, pattern in PROPERTY_GROUPS.items():
        if pattern.search(prop):
            return group
    return None


def _key(prefix: str, value: str, used: set[str]) -> str:
    base = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-") or "value"
    candidate = f"{prefix}-{base}"
    index = 2
    while candidate in used:
        candidate = f"{prefix}-{base}-{index}"
        index += 1
    used.add(candidate)
    return candidate


def scan_contract(root: Path) -> dict:
    """Discover literal design values from checked-in source without changing source files."""
    root = root.resolve()
    values = {"spacing": set(), "font_size": set(), "font_weight": set(), "radius": set(), "color": set()}
    variables: dict[str, str] = {}
    files = _source_files(root)
    for path in files:
        text = path.read_text(encoding="utf-8", errors="ignore")
        for name, value in re.findall(r"(--[\w-]+)\s*:\s*([^;}]+)", text):
            variables[name] = value.strip()
        for prop, raw in re.findall(r"([\w-]+)\s*:\s*([^;}]+)", text):
            group = _group_for_property(prop)
            if group:
                values[group].update(_values(group, raw))

    def named(group: str) -> dict[str, str]:
        used: set[str] = set()
        return {_key(group.replace("_", "-"), value, used): value for value in sorted(values[group])}

    typography: dict[str, dict[str, str]] = {}
    used: set[str] = set()
    for value in sorted(values["font_size"]):
        typography[_key("size", value, used)] = {"fontSize": value}
    for value in sorted(values["font_weight"]):
        typography[_key("weight", value, used)] = {"fontWeight": value}
    contract = {
        "version": "alpha",
        "name": f"{root.name} scanned design contract",
        "colors": named("color"),
        "typography": typography,
        "spacing": named("spacing"),
        "rounded": named("radius"),
    }
    return {
        "schema": "prestige.contract_scan.v1",
        "root": str(root),
        "files_scanned": [str(path.relative_to(root)) for path in files],
        "css_variables": variables,
        "contract": contract,
        "scope_limits": [
            "Discovers literal CSS values and CSS custom properties only.",
            "Does not infer semantic intent, Tailwind configuration, or runtime-generated styles.",
            "Review and commit the generated contract before using it as a gate.",
        ],
    }


def write_scanned_contract(root: Path, out: Path, *, force: bool = False) -> dict:
    if out.exists() and not force:
        raise FileExistsError(f"refusing to overwrite existing contract: {out}; pass --force after review")
    payload = scan_contract(root)
    front_matter = yaml.safe_dump(payload["contract"], sort_keys=False, allow_unicode=False).strip()
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        f"---\n{front_matter}\n---\n\n# DESIGN.md\n\n"
        "Generated from checked-in source. Review, edit, and commit this contract before enforcing it.\n",
        encoding="utf-8",
    )
    scan_path = out.parent / "contract-scan.json"
    scan_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    return payload | {"contract_path": str(out), "scan_path": str(scan_path)}


def _locations(root: Path, value: str, limit: int = 12) -> list[str]:
    locations = []
    for path in _source_files(root):
        for number, line in enumerate(path.read_text(encoding="utf-8", errors="ignore").splitlines(), 1):
            if value.lower() in line.lower():
                locations.append(f"{path.relative_to(root)}:{number}")
                if len(locations) >= limit:
                    return locations
    return locations


def _definition_location(design: Path, value: str) -> str | None:
    for number, line in enumerate(design.read_text(encoding="utf-8").splitlines(), 1):
        if value.lower() in line.lower():
            return f"{design}:{number}"
    return None


def _finding(issue_id: str, category: str, severity: str, failure_class: str, evidence: str,
             *, value: str | None = None, nearest: str | None = None, design: Path | None = None,
             root: Path | None = None, page: Path | None = None) -> dict:
    references = _locations(root, value) if root and value else []
    suggestion = None
    if failure_class == "off_token" and value and nearest:
        suggestion = f"Replace literal {value} with approved token value {nearest}."
    elif failure_class == "hollow_token":
        suggestion = "Add or repair the enforcement rule so removal of this exercised token causes a failing finding."
    elif failure_class in {"contract_missing", "contract_invalid"}:
        suggestion = "Add or repair the committed DESIGN.md contract, then rerun strict token lint."
    return {
        "id": issue_id,
        "category": category,
        "severity": severity,
        "failure_class": failure_class,
        "evidence": evidence,
        "defined": _definition_location(design, value) if design and value else None,
        "referenced": references,
        "page": str(page) if page else None,
        "suggested_repair": suggestion,
    }


def proof_report(page: Path, design: Path, *, css: Path | None = None, root: Path | None = None,
                 changed: list[str] | None = None, render_receipt: Path | None = None,
                 habit: dict | None = None) -> dict:
    page = page.resolve()
    design = design.resolve()
    root = (root or page.parent).resolve()
    html = page.read_text(encoding="utf-8")
    css_text = css.read_text(encoding="utf-8") if css else ""
    lint = report_tokens(html, design, css_text)
    mutation = verify_tokens(html, design, css_text)
    issues = []
    for index, item in enumerate(lint["findings"], 1):
        failure = item.get("failure_class")
        if failure:
            issues.append(_finding(
                f"P-DESIGN-{failure.upper()}-{index:03d}", "contract", "blocking", failure,
                item.get("evidence") or f"{item.get('property')} uses {item.get('value')}",
                value=item.get("value"), nearest=item.get("nearest"), design=design, root=root, page=page,
            ))
    for index, item in enumerate(mutation.get("mutations", []), 1):
        if not item.get("killed"):
            issues.append(_finding(
                f"P-DESIGN-HOLLOW-TOKEN-{index:03d}", "proof", "blocking", "hollow_token",
                f"Removing exercised {item['group']} token {item['token']} did not create a failing finding.",
                value=item["token"], design=design, root=root, page=page,
            ))
    render = None
    if render_receipt:
        try:
            render = json.loads(render_receipt.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            issues.append(_finding("P-DESIGN-RENDER-RECEIPT-001", "proof", "blocking", "invalid_render_receipt",
                                   str(error), design=design, root=root, page=page))
    journey = None
    if habit:
        journey = habit["journey"] | {
            key: habit[key] for key in ("decision", "baseline", "candidate", "receipt_sha256")
        }
        for index, step in enumerate(journey["checkpoints"], 1):
            if step["failed"]:
                issues.append(_finding(
                    f"P-JOURNEY-{index:03d}", "proof", "blocking", "journey_checkpoint",
                    f"{step['id']}: {', '.join(step['failed'])}",
                ) | {"anchor": f"journey-{step['id']}", "suggested_repair": "Replay this step and restore the expected behavior."})
        for code in habit["findings"]:
            if code != "JOURNEY_CHECKPOINT_FAILED":
                issues.append(_finding(f"P-JOURNEY-{code}", "proof", "blocking",
                                       code, "The candidate journey failed a habit threshold or user-control check."))
    summary = Counter(item["category"] for item in issues)
    report = {
        "schema": "prestige.proof_report.v1",
        "page": str(page), "contract": str(design), "css": str(css) if css else None,
        "changed_files": changed or [], "passed": lint["passed"] and mutation["passed"] and (
            habit is None or habit["decision"] == "PASS"
        ),
        "verified_tokens": lint["n_passed"], "checked_tokens": lint["n_checked"],
        "lint": lint, "mutation": mutation, "render": render, "issues": issues,
        "summary": {"blocking": sum(item["severity"] == "blocking" for item in issues),
                    "contract_failures": summary["contract"], "proof_failures": summary["proof"],
                    "design_advisories": 0},
        "scope_limits": [
            "Source references are literal-value matches within scanned text files.",
            "No visual-change claim is made unless a separate render-audit receipt is attached.",
            "Suggested repairs are reviewable recommendations, not applied patches.",
        ],
    }
    if journey:
        report["journey"] = journey
    return report


def _journey_html(journey: dict) -> str:
    metrics = "".join(
        f"<li>{key.upper()} {before:g} → {journey['candidate'][key]:g}</li>"
        for key, before in journey["baseline"].items()
    )
    blocks = []
    for step in journey["checkpoints"]:
        identifier = escape(step["id"])
        sides = []
        for phase in ("baseline", "candidate"):
            side = step[phase]
            image = (side["screenshot"] or {}).get("file")
            picture = f'<img src="{escape(image)}" alt="{phase} view of {identifier}">' if image else ""
            checks = "".join(
                f"<li>{escape(key)} · {'Pass' if passed else 'Fail'}</li>"
                for key, passed in side["checks"].items()
            )
            sides.append(f"<div><h4>{phase.title()}</h4>{picture}<ul>{checks}</ul></div>")
        blocks.append(f'<section id="journey-{identifier}"><h3>{identifier}</h3><p>{escape(step["state"])}</p>'
                      f'<div class="compare">{"".join(sides)}</div></section>')
    return f'<h2>App journey · {escape(journey["profile"])}</h2><ul>{metrics}</ul>{"".join(blocks)}'


def _html_report(report: dict) -> str:
    rows = "".join(
        "<tr><td>" + (
            f'<a href="#{escape(item["anchor"])}">{escape(item["id"])}</a>'
            if item.get("anchor") else escape(item["id"])
        ) + "</td>" + "".join(f"<td>{escape(str(item.get(key) or '-'))}</td>" for key in
                              ("category", "severity", "failure_class", "evidence", "suggested_repair")) + "</tr>"
        for item in report["issues"]
    ) or "<tr><td colspan='6'>No blocking findings.</td></tr>"
    mutation = "".join(
        f"<li><code>{escape(item['group'])}:{escape(item['token'])}</code> - {'killed' if item['killed'] else 'SURVIVED'}</li>"
        for item in report["mutation"].get("mutations", [])
    ) or "<li>No exercised literal tokens.</li>"
    screenshots = ""
    if report.get("render"):
        screenshots = "<h2>Rendered evidence</h2>" + "".join(
            f"<figure><figcaption>{escape(item['viewport'])}</figcaption><img src='{escape(item['screenshot'])}' alt='{escape(item['viewport'])} capture'></figure>"
            for item in report["render"].get("viewports", [])
        )
    payload = escape(json.dumps(report, indent=2, sort_keys=True))
    journey = _journey_html(report["journey"]) if report.get("journey") else ""
    return f"""<!doctype html><html lang='en'><meta charset='utf-8'><meta name='viewport' content='width=device-width, initial-scale=1'><title>Prestige proof report</title>
<style>body{{font:16px/1.5 system-ui,sans-serif;margin:clamp(12px,4vw,32px);color:#101828;background:#f8fafc}}main{{max-width:1180px;margin:auto}}h1{{margin-bottom:0}}.status{{font-weight:700;color:{'#15803d' if report['passed'] else '#b91c1c'}}}.table-scroll{{overflow:auto}}table{{border-collapse:collapse;width:100%;background:white}}td,th{{border:1px solid #cbd5e1;padding:9px;text-align:left;vertical-align:top}}th{{background:#e2e8f0}}code{{background:#e2e8f0;padding:2px 4px}}details{{margin-top:24px}}pre{{overflow:auto;background:#0f172a;color:#e2e8f0;padding:16px}}.compare{{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,240px),1fr));gap:16px;overflow-wrap:anywhere}}img{{max-width:100%;height:auto}}section:target{{outline:2px solid #175cd3;outline-offset:6px}}</style>
<main><h1>Prestige Design Proof</h1><p class='status'>{'PASS' if report['passed'] else 'BLOCK'} - {report['verified_tokens']}/{report['checked_tokens']} verified tokens</p>
<h2>Decision</h2><p>Blocking: {report['summary']['blocking']} | Contract failures: {report['summary']['contract_failures']} | Proof failures: {report['summary']['proof_failures']} | Advisories: 0</p>
<h2 id='findings'>Actionable findings</h2><div class='table-scroll' role='region' aria-labelledby='findings' tabindex='0'><table><thead><tr><th>ID</th><th>Category</th><th>Severity</th><th>Class</th><th>Evidence</th><th>Suggested repair</th></tr></thead><tbody>{rows}</tbody></table></div>
<h2>Mutation proof</h2><ul>{mutation}</ul>{screenshots}{journey}<details><summary>Receipt JSON</summary><pre>{payload}</pre></details></main>"""


def _bundle_journey(report, out_dir, assets):
    directory = out_dir / "journey-screenshots"
    allowed = {f"{sha}.png" for sha in assets}
    if directory.is_symlink() or (directory.exists() and (
        not directory.is_dir()
        or any(item.is_symlink() or item.name not in allowed for item in directory.iterdir())
    )):
        raise ValueError("Choose a fresh output directory for journey proof")
    if not assets:
        return
    directory.mkdir(exist_ok=True)
    for step in report["journey"]["checkpoints"]:
        for phase in ("baseline", "candidate"):
            image = step[phase]["screenshot"]
            if image:
                sha = image["sha256"]
                target = directory / f"{sha}.png"
                target.write_bytes(assets[sha])
                image["file"] = target.relative_to(out_dir).as_posix()


def write_proof_report(report: dict, out_dir: Path, *, journey_assets=None) -> dict:
    out_dir.mkdir(parents=True, exist_ok=True)
    # Keep linked screenshots inside the exported proof bundle, not on a CI runner.
    portable_report = json.loads(json.dumps(report))
    if portable_report.get("journey"):
        _bundle_journey(portable_report, out_dir, journey_assets or {})
    for item in (portable_report.get("render") or {}).get("viewports", []):
        screenshot = Path(item.get("screenshot", ""))
        if screenshot.is_file():
            screenshot_dir = out_dir / "screenshots"
            screenshot_dir.mkdir(exist_ok=True)
            target = screenshot_dir / screenshot.name
            shutil.copy2(screenshot, target)
            item["screenshot"] = target.relative_to(out_dir).as_posix()
    json_path = out_dir / "proof-report.json"
    html_path = out_dir / "proof-report.html"
    json_path.write_text(json.dumps(portable_report, indent=2, sort_keys=True), encoding="utf-8")
    html_path.write_text(_html_report(portable_report), encoding="utf-8")
    return {"json": str(json_path), "html": str(html_path)}


def write_pr_bundle(report: dict, out_dir: Path, *, journey_assets=None) -> dict:
    paths = write_proof_report(report, out_dir, journey_assets=journey_assets)
    lines = ["## Prestige Design Check", "", f"**{'PASS' if report['passed'] else 'BLOCK'}**: {report['summary']['blocking']} blocking findings; {report['verified_tokens']} verified tokens.", ""]
    for item in report["issues"]:
        label = f"**{item['id']}**"
        if item.get("anchor"):
            label = f"[{label}](proof-report.html#{item['anchor']})"
        lines.append(f"- {label} ({item['category']}): {item['evidence']}  ")
        lines.append(f"  Repair: {item['suggested_repair']}")
    if not report["issues"]:
        lines.append("- No blocking contract or proof failures.")
    markdown = out_dir / "pr-summary.md"
    annotations = out_dir / "annotations.json"
    markdown.write_text("\n".join(lines) + "\n", encoding="utf-8")
    annotations.write_text(json.dumps(report["issues"], indent=2, sort_keys=True), encoding="utf-8")
    return paths | {"markdown": str(markdown), "annotations": str(annotations)}


def github_annotations(report: dict) -> list[str]:
    """Return GitHub Actions workflow commands only for known changed-file references."""
    changed = {Path(path).as_posix() for path in report.get("changed_files", [])}
    commands = []
    for item in report["issues"]:
        for reference in item.get("referenced", []):
            path, _, line = reference.rpartition(":")
            if changed and Path(path).as_posix() not in changed:
                continue
            message = item["evidence"].replace("\n", " ")
            commands.append(f"::error file={path},line={line},title={item['id']}::{message}")
    return commands


def ci_template(platform: str, page: str, design: str) -> str:
    if platform == "github":
        return f"""name: prestige\non: [pull_request]\npermissions:\n  contents: read\njobs:\n  proof:\n    runs-on: ubuntu-latest\n    steps:\n      - uses: actions/checkout@v5\n      - uses: actions/setup-python@v6\n        with: {{ python-version: '3.12' }}\n      - run: python -m pip install 'code-factory-4-design[render]'\n      - run: prestige render-audit {page} --out-dir .prestige/render\n      - run: prestige pr {page} --design {design} --out-dir .prestige/pr --render-receipt .prestige/render/render-receipt.json --github-annotations\n      - uses: actions/upload-artifact@v4\n        if: always()\n        with: {{ name: prestige-proof, path: .prestige }}\n"""
    return f"""prestige:\n  image: python:3.12\n  script:\n    - pip install 'code-factory-4-design[render]'\n    - prestige render-audit {page} --out-dir .prestige/render\n    - prestige pr {page} --design {design} --out-dir .prestige/pr --render-receipt .prestige/render/render-receipt.json\n  artifacts:\n    when: always\n    paths:\n      - .prestige/\n"""
