from __future__ import annotations

from copy import deepcopy
import json
import os
from pathlib import Path
import subprocess

import pytest

from prestige_design.adapters import install
from prestige_design.cli import main
from prestige_design.habit import digest, habit_audit
from prestige_design.habit_ast import habit_remediate
from prestige_design import habit_ast

EXAMPLE = Path(__file__).resolve().parent.parent / "examples/habit-contract.json"
COMPONENT = """function Panel({save, close, next}) {
  return <main>
    <header><h1>Expenses</h1><button type="button" data-prestige-primary onClick={save}>Save £</button></header>
    <div className="dock" data-prestige-action-dock></div>
    <section data-prestige-completion data-prestige-next-handler="next" data-prestige-next-label="Add &amp; review">
      <button type="button" data-prestige-done onClick={close}>Done</button>
    </section>
  </main>;
}
"""


def _write(path, value):
    path.write_text(json.dumps(value), encoding="utf-8")
    return path


@pytest.fixture
def proposal():
    return json.loads(EXAMPLE.read_text(encoding="utf-8"))


def _observed(root, proposal):
    proposal["mode"] = "observed"
    artifact = {
        "schema": "prestige.habit-observations.v1",
        **{
            key: proposal[key]
            for key in ("app_name", "lens", "baseline", "candidate", "controls")
        },
    }
    output = _write(root / "observation.json", artifact)
    proposal["evidence"] = [
        {"path": output.name, "sha256": digest(output.read_bytes())}
    ]


def test_audit_proposal_and_observed_cli(tmp_path, proposal, capsys):
    _write(tmp_path / "habit.json", proposal)
    argv = ["habit-audit", "habit.json", "--root", str(tmp_path)]
    with pytest.raises(SystemExit) as exit_info:
        main([*argv, "--strict"])
    assert exit_info.value.code == 1
    result = json.loads(capsys.readouterr().out)
    assert result["decision"] == "PROPOSED"
    assert result["baseline"]["tafi"] == 11
    assert result["candidate"] == {"tafi": 2, "tzer": 1, "ppdv": 1, "scer": 1}
    assert len(result["habit_steps"]) == 6
    _observed(tmp_path, proposal)
    _write(tmp_path / "habit.json", proposal)
    main([*argv, "--strict", "--format", "markdown"])
    report = capsys.readouterr().out
    assert "Verdict: PASS" in report
    assert "| TAFI | 11.00 | 2.00 |" in report
    assert "Variable Reward" in report
    assert "Contract SHA-256" in report and "Receipt SHA-256" in report
    assert "observation.json" in report


def test_tampered_or_unrelated_observations_are_refused(tmp_path, proposal):
    _observed(tmp_path, proposal)
    source = _write(tmp_path / "habit.json", proposal).name
    other = _write(tmp_path / "observation.json", {"unrelated": True})
    with pytest.raises(ValueError, match="changed"):
        habit_audit(tmp_path, source)
    proposal["evidence"][0]["sha256"] = digest(other.read_bytes())
    _write(tmp_path / source, proposal)
    with pytest.raises(ValueError, match="matching"):
        habit_audit(tmp_path, source)


@pytest.mark.parametrize(
    "field, value, code",
    [
        ("taps", 4, "FRICTION_BARRIER"),
        ("landing", "choice", "DEFAULT_PATH_FORK"),
        (
            "ctas",
            [
                {
                    "id": "save-expense",
                    "width": 360,
                    "center_y": 420,
                    "height": 640,
                    "visible": True,
                    "reachable": False,
                }
            ],
            "THUMB_ZONE_MISS",
        ),
        (
            "completions",
            [
                {
                    "id": "expense-saved",
                    "can_exit": True,
                    "has_next": True,
                    "auto_advances": True,
                    "user_enabled": False,
                }
            ],
            "DEAD_END_TERMINAL",
        ),
    ],
)
def test_habit_metric_mutations(tmp_path, proposal, field, value, code):
    proposal["candidate"][field] = value
    _observed(tmp_path, proposal)
    source = _write(tmp_path / "habit.json", proposal).name
    result = habit_audit(tmp_path, source)
    assert result["decision"] == "BLOCKED"
    assert code in result["findings"]


def test_saas_lens_and_user_enabled_continuation(tmp_path, proposal):
    proposal["lens"] = "habit_saas"
    proposal["candidate"]["taps"] = 4
    proposal["candidate"]["landing"] = "recommended"
    proposal["candidate"]["completions"][0].update(
        auto_advances=True, user_enabled=True
    )
    _observed(tmp_path, proposal)
    result = habit_audit(tmp_path, _write(tmp_path / "habit.json", proposal).name)
    assert result["candidate"]["tafi"] == 5
    assert result["candidate"]["ppdv"] == 0.5
    assert result["decision"] == "PASS"


@pytest.mark.parametrize(
    "flag",
    [
        "no_deceptive_controls",
        "no_predatory_rewards",
        "feasible_streak",
        "notification_controls",
        "portable_data",
    ],
)
def test_habit_controls_block(tmp_path, proposal, flag):
    proposal["controls"][flag] = False
    _observed(tmp_path, proposal)
    result = habit_audit(tmp_path, _write(tmp_path / "habit.json", proposal).name)
    assert result["decision"] == "BLOCKED"
    assert len(result["findings"]) == 1


def test_bad_metrics_or_incomplete_blueprint_fail(tmp_path, proposal):
    changed = deepcopy(proposal)
    changed["candidate"]["taps"] = True
    incomplete = deepcopy(proposal)
    del incomplete["habit_steps"]["stored_value"]
    for item in (changed, incomplete):
        with pytest.raises(ValueError):
            habit_audit(tmp_path, _write(tmp_path / "habit.json", item).name)


def test_skill_install_is_idempotent_preserves_local_variant(tmp_path, capsys):
    args = [
        "install",
        "codex",
        "--root",
        str(tmp_path),
        "--skill",
        "app-habit-engineer",
    ]
    main(args)
    [path] = install(tmp_path, "codex", skill="app-habit-engineer")
    assert path == tmp_path / ".agents/skills/app-habit-engineer/SKILL.md"
    recorder = path.with_name("record-journey.mjs")
    assert "export async function recordJourney" in recorder.read_text(encoding="utf-8")
    for term in (
        "The Itch",
        "The Lazy Thumb",
        "The Paved Path",
        "Variable Reward",
        "Continuation",
        "Stored Value",
    ):
        assert term in path.read_text(encoding="utf-8")
    path.write_text("local design contract", encoding="utf-8")
    with pytest.raises(SystemExit) as exit_info:
        main(args)
    assert exit_info.value.code == 2
    assert "local changes" in capsys.readouterr().err
    assert path.read_text(encoding="utf-8") == "local design contract"


@pytest.fixture
def parser_required():
    pytest.importorskip("tree_sitter")
    pytest.importorskip("tree_sitter_javascript")
    pytest.importorskip("tree_sitter_typescript")


@pytest.mark.parametrize("suffix", ["jsx", "tsx"])
def test_ast_preview_apply_and_idempotence(tmp_path, parser_required, suffix, capsys):
    src = COMPONENT
    if suffix == "tsx":
        src = src.replace(
            "{save, close, next})",
            "{save, close, next}: {save():void; close():void; next?:()=>void})",
        )
    path = tmp_path / f"fixture.{suffix}"
    path.write_bytes(src.encode("utf-8"))
    argv = ["habit-remediate", path.name, "--root", str(tmp_path)]
    main(argv)
    preview = json.loads(capsys.readouterr().out)
    assert preview["repairs"] == ["DEAD_END_TERMINAL", "FRICTION_BARRIER"]
    assert preview["verification"] == {
        "syntax": "PASS",
        "idempotent": True,
        "behavior": "NOT_RUN",
    }
    assert path.read_bytes() == src.encode("utf-8")
    main([*argv, "--apply", "--expect-sha256", preview["source_sha256"]])
    report = json.loads(capsys.readouterr().out)
    assert (
        report["applied"] and digest(path.read_bytes()) == preview["candidate_sha256"]
    )
    result = path.read_text(encoding="utf-8")
    assert "<header><h1>Expenses</h1></header>" in result
    assert (
        'data-prestige-action-dock><button type="button" data-prestige-primary onClick={save}>Save £'
        in result
    )
    assert "onClick={close}>Done</button>" in result
    assert (
        'typeof next === "function"' in result
        and "onClick={() => next()}>Add &amp; review" in result
    )
    assert habit_remediate(tmp_path, path.name)["repairs"] == []
    with pytest.raises(ValueError, match="differs"):
        habit_remediate(tmp_path, path.name, preview["source_sha256"])


@pytest.mark.parametrize(
    "source, reason",
    [
        ("function Broken() { return <button>", "syntax"),
        (COMPONENT.replace("className=", "{...props} className="), "spread"),
        (COMPONENT.replace("className=", "hidden className="), "visible"),
        (COMPONENT.replace("<header>", "<header onClick={save}>"), "delegated"),
        (COMPONENT.replace("className=", "onClick={save} className="), "delegated"),
        (COMPONENT.replace(" onClick={save}", ""), "own callable"),
        (
            COMPONENT.replace("data-prestige-done", "data-prestige-done disabled"),
            "enabled",
        ),
        (COMPONENT.replace("<section", "<section hidden"), "visible"),
        (
            COMPONENT.replace("<section", "<section onClick={close}"),
            "delegated completion",
        ),
        (
            COMPONENT.replace("<main", "<main onClickCapture={close}"),
            "delegated completion",
        ),
        (
            COMPONENT.replace(
                "</section>",
                "<button data-prestige-next onClick={next}>Next</button></section>",
            ),
            "existing next action must be a non-submit",
        ),
        (COMPONENT.replace("onClick={close}", "onClick={null}"), "click handler"),
        (
            COMPONENT.replace(
                "  return <main>",
                "  switch (0) { case 0: let next = wrong; return <main>",
            ).replace("</main>;", "</main>; }"),
            "shadow",
        ),
        (
            COMPONENT.replace('next-handler="next"', 'next-handler="unknown"'),
            "existing",
        ),
        (COMPONENT.replace("<main>", "<form>").replace("</main>", "</form>"), "form"),
        (
            COMPONENT.replace(
                "<h1>Expenses</h1>", "<h1 data-prestige-primary>Duplicate</h1>"
            ),
            "duplicate",
        ),
        (
            COMPONENT.replace(
                'type="button" data-prestige-primary',
                'type="submit" data-prestige-primary',
            ),
            "non-submit",
        ),
    ],
)
def test_ast_rejects_unsafe_or_ambiguous_inputs(
    tmp_path, parser_required, source, reason
):
    path = tmp_path / "fixture.jsx"
    path.write_bytes(source.encode("utf-8"))
    with pytest.raises(ValueError, match=reason):
        habit_remediate(tmp_path, path.name, digest(path.read_bytes()))
    assert path.read_bytes() == source.encode("utf-8")


def test_ast_workspace_and_cli_apply_guard(tmp_path, parser_required):
    with pytest.raises(ValueError, match="workspace-relative"):
        habit_remediate(tmp_path, "../outside.jsx")
    args = ["habit-remediate", "fixture.jsx", "--root", str(tmp_path), "--apply"]
    with pytest.raises(SystemExit) as exit_info:
        main(args)
    assert exit_info.value.code == 2


def test_independent_component_functions_share_one_file(tmp_path, parser_required):
    path = tmp_path / "panels.jsx"
    source = COMPONENT + COMPONENT.replace("function Panel", "function SecondPanel")
    path.write_bytes(source.encode("utf-8"))
    result = habit_remediate(tmp_path, path.name, digest(path.read_bytes()))
    assert result["applied"]
    assert path.read_text(encoding="utf-8").count("data-prestige-next onClick") == 2
    assert habit_remediate(tmp_path, path.name)["patch"] == ""


def test_ast_apply_uses_latest_source_bytes(tmp_path, parser_required, monkeypatch):
    path = tmp_path / "fixture.jsx"
    initial = COMPONENT.encode("utf-8")
    concurrent = initial + b"// editor saved\n"
    path.write_bytes(initial)
    plan = habit_ast._plan

    def edit_then_plan(parser, raw):
        if raw != initial:
            path.write_bytes(concurrent)
        return plan(parser, raw)

    monkeypatch.setattr(habit_ast, "_plan", edit_then_plan)
    with pytest.raises(ValueError, match="changed since preview"):
        habit_remediate(tmp_path, path.name, digest(initial))
    assert path.read_bytes() == concurrent
    assert not (tmp_path / ".fixture.jsx.prestige-lock").exists()


def test_audit_refuses_unpaired_or_duplicate_viewports(tmp_path, proposal):
    mismatched = deepcopy(proposal)
    mismatched["candidate"]["ctas"][0]["width"] = 390
    proposal["candidate"]["ctas"] *= 2
    for item, error in ((mismatched, "same controls"), (proposal, "Duplicate")):
        _observed(tmp_path, item)
        with pytest.raises(ValueError, match=error):
            habit_audit(tmp_path, _write(tmp_path / "habit.json", item).name)


_RUNTIME = r"""
const h = (tag, props, ...children) => {
  const node = document.createElement(tag);
  for (const [key, value] of Object.entries(props || {})) {
    if (key === "onClick") node.addEventListener("click", value);
    else node.setAttribute(key === "className" ? "class" : key, String(value));
  }
  for (const child of children.flat()) {
    if (typeof child === "string" || child instanceof Node) node.append(child);
  }
  return node;
};
window.mount = (available) => {
  window.actions = {save: 0, close: 0, next: 0};
  document.body.replaceChildren(Panel({
    save: () => window.actions.save++,
    close: () => {
      window.actions.close++;
      document.querySelector("section").hidden = true;
      document.querySelector("[data-prestige-primary]").focus();
    },
    next: available ? () => window.actions.next++ : undefined,
  }));
};
"""


def _typecheck(source, module):
    ambient = source.with_name("intrinsic.d.ts")
    ambient.write_text(
        "declare namespace JSX { interface IntrinsicElements { "
        "[tag: string]: { [attribute: string]: unknown; onClick?: (event: MouseEvent) => void }; "
        "} }\n",
        encoding="utf-8",
    )
    tsc = Path(module).parent / "typescript/bin/tsc"
    subprocess.run(
        [
            "node",
            str(tsc),
            "--noEmit",
            "--strict",
            "--jsx",
            "preserve",
            str(ambient),
            str(source),
        ],
        check=True,
        capture_output=True,
        timeout=20,
    )


def _compile(source, module):
    transpiler = (
        "const f=require('fs');const es=require(process.argv[1]);"
        "const p=process.argv[2];"
        "process.stdout.write(es.transformSync(f.readFileSync(p,'utf8'),"
        "{loader:p.endsWith('.tsx')?'tsx':'jsx',jsxFactory:'h'}).code)"
    )
    return subprocess.check_output(
        ["node", "-e", transpiler, module, str(source)],
        text=True,
        encoding="utf-8",
        timeout=20,
    )


@pytest.mark.parametrize("suffix", ["jsx", "tsx"])
def test_transformed_component_runs_in_chromium(
    tmp_path, parser_required, proposal, suffix
):
    module = os.environ.get("PRESTIGE_HABIT_ESBUILD")
    if not module:
        pytest.skip("Set PRESTIGE_HABIT_ESBUILD to the installed esbuild module path")
    sync_api = pytest.importorskip("playwright.sync_api")
    path = tmp_path / f"fixture.{suffix}"
    component = COMPONENT
    if suffix == "tsx":
        component = component.replace(
            "{save, close, next})",
            "{save, close, next}: {save():void; close():void; next?:()=>void})",
        )
    path.write_text(component + _RUNTIME, encoding="utf-8")
    before = _compile(path, module)
    habit_remediate(tmp_path, path.name, digest(path.read_bytes()))
    if suffix == "tsx":
        typed_source = path.with_name("component-only.tsx")
        typed_source.write_text(
            path.read_text(encoding="utf-8").split(_RUNTIME)[0], encoding="utf-8"
        )
        _typecheck(typed_source, module)
    after = _compile(path, module)
    with sync_api.sync_playwright() as tools:
        browser = tools.chromium.launch()
        page = browser.new_page(viewport={"width": 360, "height": 640})
        page.set_content("<style>.dock { position:fixed; bottom:8px }</style>")
        proposal["baseline"], proposal["candidate"] = _verify_runtime(
            page, before, after
        )
        browser.close()
    observed = _write(
        tmp_path / "browser-capture.json",
        {
            "schema": "prestige.habit-observations.v1",
            **{
                key: proposal[key]
                for key in ("app_name", "lens", "baseline", "candidate", "controls")
            },
        },
    )
    proposal["mode"] = "observed"
    proposal["evidence"] = [
        {"path": observed.name, "sha256": digest(observed.read_bytes())}
    ]
    result = habit_audit(tmp_path, _write(tmp_path / "habit.json", proposal).name)
    assert result["decision"] == "PASS"
    assert result["baseline"]["tzer"] == 0 and result["candidate"]["tzer"] == 1
    assert result["baseline"]["scer"] == 0 and result["candidate"]["scer"] == 1


def _observe(page):
    button = page.get_by_role("button", name="Save £")
    box = button.bounding_box()
    assert box is not None
    viewport = page.viewport_size
    x, y = box["x"] + box["width"] / 2, box["y"] + box["height"] / 2
    reachable = button.evaluate(
        "(el, [x,y]) => el.contains(document.elementFromPoint(x,y))", [x, y]
    )
    return {
        "taps": 1,
        "inputs": 0,
        "choices": 0,
        "landing": "direct",
        "ctas": [
            {
                "id": "save-expense",
                "width": viewport["width"],
                "height": viewport["height"],
                "center_y": round(y),
                "visible": button.is_visible(),
                "reachable": reachable,
            }
        ],
        "completions": [
            {
                "id": "expense-saved",
                "can_exit": page.get_by_role("button", name="Done").is_enabled(),
                "has_next": page.get_by_role("button", name="Add & review").count()
                == 1,
                "auto_advances": page.evaluate("actions.next > 0"),
                "user_enabled": False,
            }
        ],
    }


def _verify_runtime(page, before, after):
    page.add_script_tag(content=before)
    page.evaluate("mount(true)")
    button = page.get_by_role("button", name="Save £")
    assert button.bounding_box()["y"] < 640 * 0.65
    assert page.get_by_role("button", name="Add & review").count() == 0
    baseline = _observe(page)
    page.reload()
    page.set_content("<style>.dock { position:fixed; bottom:8px }</style>")
    page.add_script_tag(content=after)
    page.evaluate("mount(true)")
    assert button.bounding_box()["y"] >= 640 * 0.65
    candidate = _observe(page)
    button.click()
    done = page.get_by_role("button", name="Done")
    done.focus()
    page.keyboard.press("Enter")
    assert page.evaluate("actions") == {"save": 1, "close": 1, "next": 0}
    assert button.evaluate("e => e === document.activeElement")
    page.evaluate("mount(true)")
    page.get_by_role("button", name="Add & review").click()
    assert page.evaluate("actions") == {"save": 0, "close": 0, "next": 1}
    page.evaluate("mount(false)")
    assert page.get_by_role("button", name="Add & review").count() == 0
    return baseline, candidate
