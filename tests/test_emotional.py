from __future__ import annotations

import json

import pytest

from prestige_design.cli import main
from prestige_design.emotional import (
    DIMENSIONS,
    audit_emotional_design,
    challenge_emotional_design,
    write_emotional_receipt,
)


GOOD = """<!doctype html><html><head><meta name="viewport" content="width=device-width"><style>
:root{--ink:#172033;--calm:#28666e;--surface:#f7fbfa}
body{color:var(--ink);background:var(--surface);font-size:16px;line-height:1.7}
h1{font-size:2.4rem;font-weight:700}.action{transition:transform .2s ease}
@media (prefers-reduced-motion: reduce){.action{transition:none}}
</style></head><body><main data-emotion-intent="confidence" data-journey-stage="task">
<h1>Review the change with confidence</h1>
<p>Review before applying this automated suggestion. Edit or cancel at any time.</p>
<button class="action">Approve</button><button>Edit</button><button>Cancel</button>
<div role="status" aria-live="polite">Checking evidence...</div>
<progress value="2" max="3">2 of 3 checks</progress>
<section class="error" role="alert"><p>One check needs attention. Your progress is saved.</p><button>Review details</button><button>Try again</button></section>
<section class="success"><h2>Review complete</h2><p>Receipt saved. Continue from recent activity when ready.</p></section>
</main></body></html>"""


def test_tripartite_emotional_gate_passes_complete_safe_journey():
    report = audit_emotional_design(GOOD, intent="confidence")
    assert report.passed
    assert report.overall == 100
    assert tuple(report.scores) == DIMENSIONS
    assert report.to_dict()["schema"] == "prestige.emotional-design.v1"
    assert report.attribution.n_checked == 6


def test_failure_dead_end_is_a_deterministic_blocker():
    page = GOOD.replace("<button>Review details</button><button>Try again</button>", "")
    report = audit_emotional_design(page)
    assert not report.passed
    assert "E_FAILURE_DEAD_END" in {item.code for item in report.blocking_findings}


@pytest.mark.parametrize("control", ['<input type="checkbox" checked>', '<input checked type="checkbox">'])
def test_coercive_patterns_fail_closed_regardless_of_attribute_order(control):
    page = GOOD.replace("</main>", f'<label>{control} Keep me enrolled</label><p>No thanks, I hate progress</p></main>')
    report = audit_emotional_design(page)
    assert not report.passed
    finding = next(item for item in report.findings if item.code == "E_MANIPULATIVE_PATTERN")
    assert finding.severity == "P1"


def test_motion_requires_user_preference_adaptation():
    page = GOOD.replace("prefers-reduced-motion", "motion-preference-disabled")
    report = audit_emotional_design(page)
    assert not report.passed
    assert "E_REDUCED_MOTION_MISSING" in {item.code for item in report.blocking_findings}


def test_ai_surface_requires_disclosure_and_controls():
    page = GOOD.replace('data-journey-stage="task"', 'data-journey-stage="task" data-ai-generated="true"')
    page = page.replace("Review before applying this automated suggestion. Edit or cancel at any time.", "A result is ready.")
    report = audit_emotional_design(page)
    assert not report.passed
    assert "E_AI_AUTHORSHIP_HIDDEN" in {item.code for item in report.blocking_findings}


def test_challenge_rejects_all_isolated_safety_mutants():
    result = challenge_emotional_design(GOOD)
    assert result["passed"]
    assert result["mutants_killed"] == result["mutants_total"] == 3
    assert result["marker"] == "EMOTIONAL_MUTATIONS_REJECTED"


def test_cli_writes_portable_atomic_receipt(tmp_path, capsys):
    page = tmp_path / "journey.html"
    receipt = tmp_path / "proof" / "emotion.json"
    page.write_text(GOOD, encoding="utf-8")
    assert main(["emotion", str(page), "--intent", "confidence", "--challenge", "--strict", "--out", str(receipt), "--json"]) is None
    payload = json.loads(capsys.readouterr().out)
    saved = json.loads(receipt.read_text(encoding="utf-8"))
    assert payload["passed"] and saved["challenge"]["passed"]
    assert "EMOTIONAL_RECEIPT_ATOMIC" in saved["markers"]
    assert "EMOTIONAL_MUTATIONS_REJECTED" in saved["markers"]
    assert GOOD not in json.dumps(saved)
    assert len(saved["source_sha256"]) == 64


def test_write_emotional_receipt_is_atomic_and_exact(tmp_path):
    destination = tmp_path / "nested" / "receipt.json"
    payload = {"schema": "prestige.emotional-design.v1", "passed": True}
    assert write_emotional_receipt(payload, destination) == destination.resolve()
    assert json.loads(destination.read_text(encoding="utf-8")) == payload
    assert not destination.with_suffix(".json.tmp").exists()


def test_cli_strict_blocks_manipulative_page(tmp_path):
    page = tmp_path / "bad.html"
    page.write_text('<main data-emotion-intent="momentum"><h1>Keep going</h1><input type="checkbox" checked></main>', encoding="utf-8")
    with pytest.raises(SystemExit) as error:
        main(["emotion", str(page), "--strict", "--json"])
    assert error.value.code == 1
