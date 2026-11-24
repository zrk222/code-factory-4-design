import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

import pytest

from prestige_design.brief import compile_brief, render_brief
from prestige_design.habit import digest, habit_audit
from prestige_design.tokens import write_template

ROOT = Path(__file__).resolve().parents[1]
EXAMPLES = ROOT / "examples"


def _json(path, value):
    path.write_text(json.dumps(value), encoding="utf-8")


def _read(path):
    return json.loads(path.read_bytes())


@pytest.fixture(scope="module")
def browser_captures(tmp_path_factory):
    if not os.environ.get("PRESTIGE_RUN_BROWSER_TESTS"):
        pytest.skip("Run the browser proof job to replay the Node Playwright fixture")
    playwright = pytest.importorskip("playwright")
    driver = Path(playwright.__file__).parent / "driver" / "package"
    directory = tmp_path_factory.mktemp("browser-captures")
    subprocess.run(
        ["node", ROOT / "tests/fixtures/saas-onboarding.mjs", driver, directory],
        check=True,
        timeout=40,
    )
    shutil.copyfile(EXAMPLES / "saas-habit-contract.json", directory / "habit.json")
    return directory


def _bundle(root, destination, *options, expected):
    page = root / "page.html"
    page.write_text(
        '<main style="color:#101828;padding:16px">Project</main>', encoding="utf-8"
    )
    argv = [
        sys.executable,
        "-m",
        "prestige_design.cli",
        "pr",
        str(page),
        "--design",
        str(write_template(root / "DESIGN.md")),
        "--root",
        str(root),
        "--out-dir",
        str(destination),
        "--journey",
        "habit.json",
        "baseline.json",
        "candidate.json",
        *options,
    ]
    result = subprocess.run(
        argv, cwd=ROOT, capture_output=True, text=True, encoding="utf-8", timeout=20
    )
    assert result.returncode == expected, result.stdout + result.stderr
    return result


def test_replayed_journey_reuses_habit_metrics_and_reports_recovery(
    browser_captures, tmp_path
):
    root = browser_captures
    report = habit_audit(
        root, "habit.json", captures=("baseline.json", "candidate.json")
    )
    assert report["decision"] == "PASS"
    assert (report["baseline"]["tafi"], report["candidate"]["tafi"]) == (5, 4)
    assert (report["baseline"]["tzer"], report["candidate"]["tzer"]) == (0, 1)
    assert [binding["sha256"] for binding in report["evidence"]] == [
        digest((root / name).read_bytes())
        for name in ("baseline.json", "candidate.json")
    ]
    error = report["journey"]["checkpoints"][1]
    assert error["id"] == "save-error"
    assert error["baseline"]["checks"]["draft-preserved"] is False
    assert error["candidate"]["checks"]["draft-preserved"] is True
    assert (
        error["baseline"]["screenshot"]["sha256"]
        != error["candidate"]["screenshot"]["sha256"]
    )
    assert all(
        step["screenshot"] is None
        for step in _read(root / "private.json")["checkpoints"]
    )
    assert not list(root.glob("private.json-*.png"))
    without = tmp_path / "plain"
    _bundle(root, without, expected=0)
    assert not (without / "journey-screenshots").exists()
    output = tmp_path / "visual"
    _bundle(root, output, "--include-journey-screenshots", expected=0)
    proof = _read(output / "proof-report.json")
    for phase in ("baseline", "candidate"):
        image = proof["journey"]["checkpoints"][1][phase]["screenshot"]
        assert digest((output / image["file"]).read_bytes()) == image["sha256"]
    page = (output / "proof-report.html").read_text(encoding="utf-8")
    assert 'id="journey-save-error"' in page and "baseline view of save-error" in page
    assert "Private project name" not in page
    _check_viewer(output / "proof-report.html")
    _bundle(root, output, expected=2)


def _check_viewer(file):
    playwright = pytest.importorskip("playwright.sync_api")
    with playwright.sync_playwright() as pw, pw.chromium.launch() as browser:
        page = browser.new_page(viewport={"width": 1200, "height": 800})
        page.goto(file.as_uri())
        images = page.locator("#journey-save-error img")
        left, right = (images.nth(i).bounding_box() for i in range(2))
        assert left["x"] < right["x"] and left["y"] == right["y"]
        assert images.evaluate_all(
            "images => images.every(image => image.naturalWidth > 0)"
        )
        page.set_viewport_size({"width": 390, "height": 844})
        assert images.nth(0).bounding_box()["y"] < images.nth(1).bounding_box()["y"]
        assert page.evaluate("document.documentElement.scrollWidth") == 390


def test_checkpoint_failure_blocks_pr_and_links_report(browser_captures, tmp_path):
    root = tmp_path / "captures"
    shutil.copytree(browser_captures, root)
    candidate = _read(root / "private.json")
    candidate["checkpoints"][1]["checks"]["draft-preserved"] = False
    _json(root / "candidate.json", candidate)
    out = tmp_path / "proof"
    _bundle(root, out, expected=1)
    proof = _read(out / "proof-report.json")
    assert proof["summary"]["blocking"] == 1
    assert not proof["passed"]
    assert 'href="#journey-save-error"' in (out / "proof-report.html").read_text(
        encoding="utf-8"
    )
    assert "proof-report.html#journey-save-error" in (out / "pr-summary.md").read_text(
        encoding="utf-8"
    )


@pytest.mark.parametrize(
    "change, message",
    [
        ("checkpoint", "matching checkpoints"),
        ("profile", "same app and execution profile"),
        ("tampered", "PNG is invalid or has changed"),
        ("malformed", "PNG is invalid or has changed"),
        ("path", "workspace-relative path"),
        ("missing-field", "requires exactly"),
        ("oversize", "input byte limit"),
        ("duplicate", "unique checkpoint IDs"),
        ("alias", "distinct baseline and candidate"),
    ],
)
def test_capture_pair_rejects_unbound_or_incompatible_evidence(
    browser_captures, tmp_path, change, message
):
    shutil.copytree(browser_captures, tmp_path, dirs_exist_ok=True)
    name = tmp_path / "candidate.json"
    capture = _read(name)
    if change == "checkpoint":
        capture["checkpoints"][1]["checks"]["other"] = True
    elif change == "profile":
        capture["profile"] = "other"
    elif change == "path":
        capture["checkpoints"][1]["screenshot"]["path"] = "../outside.png"
    elif change == "malformed":
        attachment = capture["checkpoints"][1]["screenshot"]
        image = tmp_path / attachment["path"]
        raw = image.read_bytes()
        malformed = raw[:33] + raw[-12:]
        image.write_bytes(malformed)
        attachment["sha256"] = digest(malformed)
    elif change in {"tampered", "oversize"}:
        image = tmp_path / capture["checkpoints"][1]["screenshot"]["path"]
        image.write_bytes(
            image.read_bytes()
            + (b"X" if change == "tampered" else bytes(2 * 1024 * 1024))
        )
    elif change == "missing-field":
        del capture["controls"]
    elif change == "duplicate":
        capture["checkpoints"].append(capture["checkpoints"][0])
    if change == "alias":
        name.unlink()
        os.link(tmp_path / "baseline.json", name)
    else:
        _json(name, capture)
    with pytest.raises(ValueError, match=message):
        habit_audit(
            tmp_path, "habit.json", captures=("baseline.json", "candidate.json")
        )


def test_component_brief_has_state_contract_and_anchored_components():
    brief = compile_brief(
        purpose="saas", root=ROOT, components="examples/saas-components.json"
    )
    assert set(brief.journey_states) == {
        "loading",
        "empty",
        "error",
        "retry",
        "expired",
        "success",
    }
    component = brief.component_inventory["components"]["form_error"]
    assert component["name"] == "FormError"
    assert component["source"]["sha256"] == digest(
        (EXAMPLES / "saas-onboarding.html").read_bytes()
    )
    markdown = render_brief(brief)
    assert "preserve input" in markdown and "FormError" in markdown
    assert "journey_states" not in compile_brief().to_dict()


@pytest.mark.parametrize(
    "source, name, error",
    [
        ("../outside.jsx", "PrimaryAction", "workspace-relative"),
        ("component.jsx", "MissingButton", "absent"),
    ],
)
def test_inventory_rejects_unsubstantiated_components(tmp_path, source, name, error):
    (tmp_path / "component.jsx").write_text(
        "export const PrimaryAction = () => <button />;", encoding="utf-8"
    )
    _json(
        tmp_path / "inventory.json",
        {
            "schema": "prestige.component-inventory.v1",
            "tokens": None,
            "components": {
                "primary_action": {
                    "name": name,
                    "source": source,
                    "usage": "Primary save",
                }
            },
        },
    )
    with pytest.raises(ValueError, match=error):
        compile_brief(purpose="saas", root=tmp_path, components="inventory.json")
