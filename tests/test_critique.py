from __future__ import annotations

import json

import pytest

from prestige_design.critique import (
    CritiqueFinding,
    DIMENSIONS,
    challenge_critique,
    contrast_ratio,
    critique_html,
    write_critique_receipt,
)
from prestige_design.cli import main


GOOD_HTML = """<!doctype html><html><head><style>
:root{--ink:#111;--surface:#fff}main{display:grid;gap:24px;color:#111;background:#fff;max-width:65ch;font-size:16px;line-height:1.6}
button{min-height:44px}button:focus-visible{outline:3px solid #000}
</style></head><body><main><h1>Build verified software</h1><button class="primary">Start now</button></main></body></html>"""


def test_finding_to_dict_has_exact_public_shape():
    finding = CritiqueFinding(
        "composition", "TEST", "P3", "heuristic", "observed", "problem", "fix",
        {"confidence": 0.5},
    )
    assert set(finding.to_dict()) == {
        "dimension", "code", "severity", "mode", "observation", "problem", "fix", "evidence",
    }


def test_critique_emits_exact_seven_lens_public_safe_receipt():
    result = critique_html(GOOD_HTML)
    assert result["schema"] == "prestige.critique.v1"
    assert [item["name"] for item in result["dimensions"]] == list(DIMENSIONS)
    assert len(result["dimensions"]) == 7
    assert "CRITIQUE_SEVEN_LENSES" in result["markers"]
    encoded = json.dumps(result)
    assert GOOD_HTML not in encoded
    assert "absolute_path" not in encoded
    for finding in result["findings"]:
        assert set(finding) == {"dimension", "code", "severity", "mode", "observation", "problem", "fix", "evidence"}


def test_contrast_arithmetic_blocks_low_contrast():
    assert round(contrast_ratio("#000", "#fff"), 2) == 21.0
    result = critique_html("<main><h1>Title</h1></main>", "main{display:grid;color:#777;background:#777}")
    finding = next(item for item in result["findings"] if item["code"] == "COLOR_TEXT_CONTRAST")
    assert finding["severity"] == "P1"
    assert finding["mode"] == "deterministic"
    assert result["passed"] is False
    assert "CRITIQUE_BLOCKED_P1" in result["markers"]


def test_unnamed_control_is_deterministic_p1():
    result = critique_html("<main><h1>Title</h1><button></button></main>", "main{display:flex}button{min-height:44px}button:focus{outline:2px solid}")
    finding = next(item for item in result["findings"] if item["code"] == "AFFORDANCE_NAME_MISSING")
    assert finding["dimension"] == "affordance"
    assert finding["severity"] == "P1"
    assert result["strict_passed"] is False


def test_heuristics_carry_bounded_confidence_and_never_block_alone():
    result = critique_html(GOOD_HTML.replace("gap:24px;", ""))
    heuristics = [item for item in result["findings"] if item["mode"] == "heuristic"]
    assert heuristics
    assert all(0.0 <= item["evidence"]["confidence"] <= 1.0 for item in heuristics)
    assert result["passed"] is True


def test_missing_contracts_are_explicit_and_not_invented():
    result = critique_html(GOOD_HTML)
    assert [item["status"] for item in result["contracts"]] == ["missing", "missing", "missing"]
    assert all(item["marker"] == "CRITIQUE_CONTRACT_ABSENT" for item in result["contracts"])


def test_design_contract_is_hashed_and_off_token_value_is_found(tmp_path):
    design = tmp_path / "DESIGN.md"
    design.write_text(
        "```design-tokens\n" + json.dumps({
            "spacing": ["24px"], "font_size": ["16px"], "font_weight": [],
            "radius": [], "color": ["#111111", "#ffffff"],
        }) + "\n```\n",
        encoding="utf-8",
    )
    result = critique_html(GOOD_HTML, ".off{color:#ff00ff}", design=design)
    assert result["contracts"][0]["status"] == "hashed"
    assert len(result["contracts"][0]["sha256"]) == 64
    finding = next(item for item in result["findings"] if item["code"] == "BRAND_TOKEN_DRIFT")
    assert finding["mode"] == "deterministic"
    assert "#ff00ff" not in json.dumps(finding)


def test_atomic_receipt_output(tmp_path):
    destination = tmp_path / "nested" / "critique.json"
    result = critique_html(GOOD_HTML)
    assert write_critique_receipt(result, destination) == destination.resolve()
    assert json.loads(destination.read_text(encoding="utf-8"))["schema"] == "prestige.critique.v1"


def test_challenge_kills_one_mutant_per_dimension():
    result = challenge_critique(GOOD_HTML)
    assert result["passed"] is True
    assert result["mutants_total"] == 7
    assert result["mutants_killed"] == 7
    assert {item["dimension"] for item in result["mutations"]} == set(DIMENSIONS)
    assert result["marker"] == "CRITIQUE_MUTATIONS_REJECTED"


def test_cli_writes_receipt_and_reports_challenge(tmp_path, capsys):
    page = tmp_path / "page.html"
    page.write_text(GOOD_HTML, encoding="utf-8")
    output = tmp_path / "critique.json"
    assert main(["critique", str(page), "--challenge", "--out", str(output), "--json"]) is None
    payload = json.loads(capsys.readouterr().out)
    assert payload["challenge"]["passed"] is True
    assert "CRITIQUE_MUTATIONS_REJECTED" in payload["markers"]
    assert "CRITIQUE_RECEIPT_ATOMIC" in payload["markers"]
    assert output.is_file()


def test_cli_strict_blocks_deterministic_p2(tmp_path):
    page = tmp_path / "page.html"
    page.write_text("<main><h1>Title</h1><button>Go</button></main><style>main{display:grid}</style>", encoding="utf-8")
    with pytest.raises(SystemExit) as error:
        main(["critique", str(page), "--strict", "--json"])
    assert error.value.code == 1
