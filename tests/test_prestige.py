import sys, subprocess
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from prestige_design.audit import audit_html

GOOD = (ROOT/"references"/"premium-template.html").read_text(encoding="utf-8")
BAD = """<html><head><title>x</title></head><body>
<nav><a>1</a><a>2</a><a>3</a><a>4</a><a>5</a><a>6</a><a>7</a><a>8</a><a>9</a></nav>
<div>hi</div><form><input><button></button></form><div>Buy $9</div>
<img src=a><img src=b><img src=c></body></html>"""

def test_premium_template_passes_all_laws():
    r = audit_html(GOOD)
    assert r.passed and r.overall >= 90
    assert all(v >= 80 for v in r.scores.values())
    assert not r.hard_failures

def test_bad_page_fails():
    r = audit_html(BAD)
    assert not r.passed and r.overall < 40

def test_law1_halo_needs_hero_and_h1():
    r = audit_html("<html><head><meta name=viewport content=x><style>@media(max-width:768px){}</style></head><body><p>no hero</p></body></html>")
    codes = [f.code for f in r.findings]
    assert "H_NO_H1" in codes

def test_law2_flags_nav_overload():
    r = audit_html(BAD)
    assert any(f.code == "F_NAV_OVERLOAD" for f in r.findings)

def test_law3_transactional_needs_security_cue():
    html = "<html><body><h1>Shop</h1><div>Buy now $50</div><button>Pay</button></body></html>"
    r = audit_html(html)
    assert any(f.code == "T_NO_SECURITY" for f in r.findings)

def test_law3_flags_hidden_cost():
    html = "<html><body><h1>x</h1><div>secure checkout — $99</div><span>verified</span><div>5 reviews ★</div><button>Buy</button></body></html>"
    r = audit_html(html)
    assert any(f.code == "T_HIDDEN_COST" for f in r.findings)

def test_law4_peak_needs_transitions_and_hover():
    html = "<html><head><style>.b{color:red}</style></head><body><h1>x</h1><button>Go</button></body></html>"
    r = audit_html(html)
    codes = [f.code for f in r.findings]
    assert "P_NO_TRANSITIONS" in codes and "P_NO_HOVER" in codes

def test_law5_horn_needs_responsive_and_viewport():
    html = "<html><head><style>.x{color:red}</style></head><body><h1>x</h1></body></html>"
    r = audit_html(html)
    codes = [f.code for f in r.findings]
    assert "C_NO_RESPONSIVE" in codes and "C_NO_VIEWPORT" in codes

def test_hard_fail_unlabeled_cta_blocks_ship():
    html = "<html><body><h1>Buy</h1><div>secure $10 total</div><button></button></body></html>"
    r = audit_html(html)
    assert r.hard_failures and not r.passed

def test_hard_fail_missing_alt_blocks_ship():
    html = "<html><body><h1>x</h1><img src=1><img src=2><img src=3></body></html>"
    r = audit_html(html)
    assert any("alt" in h for h in r.hard_failures)

def test_aesthetics_never_mask_major_flaw():
    # a visually perfect page with a broken (unlabeled) primary action must still fail
    perfect_but_broken = GOOD.replace('<button class="btn-primary" type="submit">Claim my launch price</button>',
                                      '<button class="btn-primary" type="submit"></button>')
    r = audit_html(perfect_but_broken)
    assert not r.passed  # the warning is enforced: function over aesthetics

def test_cli_strict_mode_exit_code(tmp_path):
    bad = tmp_path/"b.html"; bad.write_text(BAD)
    res = subprocess.run([sys.executable,"-m","prestige_design.cli","audit",str(bad),"--strict"],
                         capture_output=True, cwd=ROOT)
    assert res.returncode == 1

def test_install_into_agents(tmp_path):
    from prestige_design.adapters import install
    c = install(tmp_path, "claude")
    assert (tmp_path/".claude"/"skills"/"prestige-design"/"SKILL.md").exists()
    install(tmp_path, "codex")
    assert (tmp_path/"AGENTS.md").exists()


# ============ v0.2: bias engine, CTA/hooks, mobile, workflows, precision ============
from prestige_design.biases import run_bias_suite
from prestige_design.cta_hooks import verify_cta_and_hooks
from prestige_design.mobile_judge import judge_mobile
from prestige_design.score import score_design
from prestige_design.workflows import get_workflow, list_workflows
from prestige_design.purpose import audit_purpose, infer_purpose, list_purposes

OPT = (ROOT/"references"/"premium-template.html").read_text(encoding="utf-8")

def test_bias_engine_detects_social_proof_and_cta():
    biases = run_bias_suite(OPT, "")
    names = {b.name for b in biases}
    assert "Von Restorff (CTA isolation)" in names and "Social Proof" in names
    social = next(b for b in biases if b.name == "Social Proof")
    assert social.present and social.quality >= 0.6

def test_bias_engine_flags_missing_anchor_on_bad_pricing():
    html = "<html><body><h1>Buy</h1><div>Price: $99</div><button>Buy</button></body></html>"
    biases = run_bias_suite(html, "")
    anchor = next(b for b in biases if b.name == "Anchoring (price)")
    assert anchor.present and anchor.quality < 0.5 and anchor.recommendation

def test_optimized_template_has_anchor_and_scarcity():
    biases = run_bias_suite(OPT, "")
    anchor = next(b for b in biases if b.name == "Anchoring (price)")
    loss = next(b for b in biases if b.name.startswith("Loss Aversion"))
    assert anchor.quality >= 0.9        # 'Was $199' anchor present
    assert loss.present                 # 'only 40 seats left'

def test_cta_verifier_rewards_strong_cta():
    r = verify_cta_and_hooks(OPT)
    assert r.cta_score >= 70
    assert "free" in r.primary_cta_text.lower() or "my" in r.primary_cta_text.lower()

def test_cta_verifier_penalizes_weak_verb():
    html = '<html><body><h1>Welcome to our product</h1><button>Submit</button></body></html>'
    r = verify_cta_and_hooks(html)
    assert r.cta_score < 70 and any("WEAK" in f for f in r.findings)
    assert r.recommendations

def test_hook_verifier_scores_reader_focused_headline():
    r = verify_cta_and_hooks(OPT)
    assert r.hook_score >= 80  # addresses 'you', has power words, specific

def test_hook_verifier_penalizes_flat_headline():
    html = '<html><body><h1>Our Company Provides Solutions</h1><button>Get started</button></body></html>'
    r = verify_cta_and_hooks(html)
    assert r.hook_score < 80 and r.recommendations

def test_mobile_judge_strict_on_missing_responsive():
    html = '<html><head><style>.x{color:red}</style></head><body><h1>x</h1></body></html>'
    r = judge_mobile(html, ".x{color:red}")
    assert r.score < 70
    assert any("VIEWPORT" in f or "BREAKPOINT" in f for f in r.findings)

def test_mobile_judge_rewards_responsive_template():
    import re
    css = " ".join(re.findall(r"<style[^>]*>(.*?)</style>", OPT, re.S))
    r = judge_mobile(OPT, css)
    assert r.score >= 80

def test_five_workflows_exist_with_distinct_weights():
    wfs = list_workflows()
    assert len(wfs) == 5
    keys = {w["key"] for w in wfs}
    assert keys == {"conversion","luxury","trust","editorial","product"}
    # weights differ across workflows
    assert get_workflow("conversion").weights != get_workflow("luxury").weights

def test_precision_score_is_workflow_weighted():
    conv = score_design(OPT, workflow_key="conversion")
    lux = score_design(OPT, workflow_key="luxury")
    assert conv.workflow != lux.workflow
    assert conv.grade in ("A","B") and lux.grade in ("A","B")

def test_precision_score_gives_ranked_recommendations():
    html = '<html><head><meta name=viewport content="width=device-width"><style>@media(max-width:768px){}.x{color:red}</style></head><body><h1>Our Company Provides Enterprise Solutions For Businesses Today</h1><button>Submit</button><div>Price $99</div></body></html>'
    r = score_design(html)
    assert r.conversion_score < 70 and not r.passed
    assert len(r.recommendations) >= 3   # multiple prioritized fixes

def test_optimized_template_scores_A():
    r = score_design(OPT, workflow_key="conversion")
    assert r.grade == "A" and r.passed and r.conversion_score >= 88

def test_precision_hard_fails_on_broken_function():
    # visually rich but broken primary action must still fail
    broken = OPT.replace('<button class="btn-primary" type="submit">Claim my launch price</button>',
                         '<button class="btn-primary" type="submit"></button>')
    r = score_design(broken, workflow_key="conversion")
    assert not r.passed  # aesthetics never mask a major functional flaw


# ============ v0.3: purpose-fit psychology and theme judgment ============
DEV_GOOD = """<!doctype html><html><head><meta name="viewport" content="width=device-width"><style>
:root{--ink:#111827;--accent:#2563eb} body{font-family:Inter,sans-serif;line-height:1.7;color:var(--ink)}
.hero{padding:6rem 8vw;background:#f8fafc}.terminal{font-family:ui-monospace,monospace;background:#111827;color:white}
.btn-primary{background:var(--accent);padding:1rem 1.2rem}@media(max-width:768px){.hero{padding:4rem 6vw}}
</style></head><body><section class="hero"><h1>Ship your API workflow with deterministic CI receipts</h1>
<p>Open source CLI with GitHub Actions, docs, quickstart, and no secrets.</p>
<pre class="terminal"><code>pip install code-factory-2-forge\nforge demo</code></pre>
<a class="btn-primary">Install from GitHub</a><a>View docs</a></section></body></html>"""

DEV_BAD = """<!doctype html><html><head><style>.hero{color:purple}</style></head>
<body><h1>Revolutionary effortless AI magic for everyone</h1><button>Contact sales</button></body></html>"""

LUXURY_BAD = """<!doctype html><html><head><style>:root{--x:red}.sale{color:red}</style></head>
<body><h1>Cheap flash sale hurry buy now</h1><button>Buy now</button><button>Submit</button>
<button>Free discount</button><p>Last chance discount cheap offer.</p></body></html>"""


def test_purpose_lenses_are_listed():
    keys = {item["key"] for item in list_purposes()}
    assert {"developer", "healthcare", "fintech", "luxury", "marketplace", "saas", "editorial"} <= keys


def test_purpose_inference_detects_developer_tool():
    assert infer_purpose(DEV_GOOD, "") == "developer"


def test_developer_purpose_fit_passes_concrete_product_proof():
    r = audit_purpose(DEV_GOOD, purpose="developer")
    assert r.passed
    assert r.score >= 80
    assert r.attribution.n_checked == 5


def test_developer_purpose_fit_flags_vague_marketing():
    r = audit_purpose(DEV_BAD, purpose="developer")
    assert not r.passed
    assert r.score < 70
    assert any("code" in rec.lower() or "docs" in rec.lower() for rec in r.recommendations)


def test_luxury_purpose_fit_rejects_loud_discount_language():
    r = audit_purpose(LUXURY_BAD, purpose="luxury")
    assert not r.passed
    anti = next(f for f in r.findings if f.criterion == "anti_patterns")
    assert anti.score < 70


def test_precision_score_can_include_purpose_channel():
    r = score_design(DEV_GOOD, workflow_key="product", purpose_key="developer")
    assert r.purpose_score is not None
    assert r.purpose == "Developer Tool Clarity"
    assert "purpose" in r.__dict__


def test_cli_purpose_json_exposes_attribution(tmp_path, capsys):
    from prestige_design.cli import main
    page = tmp_path / "dev.html"
    page.write_text(DEV_GOOD)
    main(["purpose", str(page), "--purpose", "developer", "--json"])
    import json
    payload = json.loads(capsys.readouterr().out)
    assert payload["profile"] == "Developer Tool Clarity"
    assert payload["attribution"]["stage"] == "purpose_fit"


def test_cli_score_json_includes_purpose_when_requested(tmp_path, capsys):
    from prestige_design.cli import main
    page = tmp_path / "dev.html"
    page.write_text(DEV_GOOD)
    main(["score", str(page), "--workflow", "product", "--purpose", "developer", "--json"])
    import json
    payload = json.loads(capsys.readouterr().out)
    assert payload["purpose"] == "Developer Tool Clarity"
    assert payload["purpose_score"] >= 70


def test_design_audit_emits_per_criterion_attribution():
    from prestige_design.audit import audit_html
    report = audit_html("<html><head></head><body><h1>Test</h1></body></html>")
    attr = report.attribution
    assert attr.n_checked == len(report.scores) == 5
    assert {unit.unit for unit in attr.units} == {
        "criterion:fluency", "criterion:halo", "criterion:horn",
        "criterion:peak", "criterion:trust",
    }
    assert attr.rate == attr.n_passed / attr.n_checked


def test_cli_json_exposes_attribution(tmp_path, capsys):
    from prestige_design.cli import main
    page = tmp_path / "page.html"
    page.write_text("<html><head></head><body><h1>Test</h1></body></html>")
    main(["audit", str(page), "--json"])
    import json
    payload = json.loads(capsys.readouterr().out)
    assert payload["attribution"]["n_checked"] == 5
