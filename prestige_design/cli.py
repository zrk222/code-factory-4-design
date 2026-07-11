"""prestige CLI - audit a page or scaffold a premium starter template."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .audit import audit_html


def _safe(text: str) -> str:
    return text.encode("ascii", "replace").decode("ascii")


def _print(text: str) -> None:
    print(_safe(text))


def _fmt(report, path, as_json):
    if as_json:
        return json.dumps(
            {
                "file": str(path),
                "overall": report.overall,
                "passed": report.passed,
                "scores": report.scores,
                "attribution": report.attribution.to_dict(),
                "hard_failures": report.hard_failures,
                "findings": [f.__dict__ for f in report.findings],
            },
            indent=2,
        )
    C = {"g": "\033[92m", "y": "\033[93m", "r": "\033[91m", "c": "\033[96m", "d": "\033[2m", "x": "\033[0m"}
    icon = {
        "pass": f"{C['g']}OK{C['x']}",
        "warn": f"{C['y']}WARN{C['x']}",
        "fail": f"{C['r']}FAIL{C['x']}",
        "hard_fail": f"{C['r']}BLOCK{C['x']}",
    }
    out = [f"\n{C['c']}Prestige audit - {path}{C['x']}"]
    verdict = f"{C['g']}PASS{C['x']}" if report.passed else f"{C['r']}NEEDS WORK{C['x']}"
    out.append(f"Overall: {report.overall}/100   Verdict: {verdict}")
    out.append(f"{C['d']}" + "  ".join(f"{k}:{v}" for k, v in report.scores.items()) + C["x"])
    if report.hard_failures:
        out.append(f"\n{C['r']}HARD FAILURES (fix before shipping - function over aesthetics):{C['x']}")
        for failure in report.hard_failures:
            out.append(f"   {failure}")
    if report.findings:
        out.append("")
        for finding in report.findings:
            if finding.level == "pass":
                continue
            out.append(f"  {icon.get(finding.level, '-')} [{finding.law}] {finding.code}: {finding.message}")
    return _safe("\n".join(out))


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="prestige",
        description="Premium design audit and scaffold",
    )
    sub = parser.add_subparsers(required=True, dest="cmd")
    audit = sub.add_parser("audit", help="score an HTML file against the five laws")
    audit.add_argument("file")
    audit.add_argument("--css", default=None, help="optional separate CSS file")
    audit.add_argument("--json", action="store_true")
    audit.add_argument("--strict", action="store_true", help="exit nonzero if not passing")

    score = sub.add_parser("score", help="conversion-readiness score with ranked recommendations")
    score.add_argument("file")
    score.add_argument("--css", default=None)
    score.add_argument("--workflow", default="conversion", choices=["conversion", "luxury", "trust", "editorial", "product"])
    score.add_argument("--purpose", default=None, help="purpose-fit lens: auto, developer, healthcare, fintech, luxury, marketplace, saas, editorial")
    score.add_argument("--json", action="store_true")
    score.add_argument("--strict", action="store_true")

    workflows = sub.add_parser("workflows", help="list the five design-principle workflows")
    workflows.add_argument("--json", action="store_true")

    purposes = sub.add_parser("purposes", help="list purpose-fit design lenses")
    purposes.add_argument("--json", action="store_true")

    purpose_cmd = sub.add_parser("purpose", help="audit whether design choices fit the interface purpose")
    purpose_cmd.add_argument("file")
    purpose_cmd.add_argument("--css", default=None)
    purpose_cmd.add_argument("--purpose", default="auto", help="auto, developer, healthcare, fintech, luxury, marketplace, saas, editorial")
    purpose_cmd.add_argument("--json", action="store_true")
    purpose_cmd.add_argument("--strict", action="store_true")

    theme = sub.add_parser("theme", help="compile an opinionated purpose-driven Visual DNA contract")
    theme.add_argument("purpose", choices=["developer", "healthcare", "fintech", "luxury", "marketplace", "saas", "editorial"])
    theme.add_argument("--out", default=None)
    theme.add_argument("--json", action="store_true")

    render = sub.add_parser("render-audit", help="collect browser-rendered desktop and mobile evidence")
    render.add_argument("target")
    render.add_argument("--out-dir", default=".prestige/render")
    render.add_argument("--json", action="store_true")

    challenge = sub.add_parser("challenge", help="prove the design gate rejects sabotaged pages")
    challenge.add_argument("file")
    challenge.add_argument("--purpose", default="developer")
    challenge.add_argument("--workflow", default="product", choices=["conversion", "luxury", "trust", "editorial", "product"])
    challenge.add_argument("--feature", default=None)
    challenge.add_argument("--out", default=None)

    brief = sub.add_parser("brief", help="compile a purpose-driven design brief before UI work")
    brief.add_argument("source", nargs="?", default=None, help="optional PRD/spec/content file")
    brief.add_argument("--purpose", default="developer", help="developer, healthcare, fintech, luxury, marketplace, saas, editorial")
    brief.add_argument("--out", default=None, help="write markdown brief to this path")
    brief.add_argument("--json", action="store_true")

    scaffold = sub.add_parser("scaffold", help="write a premium starter template")
    scaffold.add_argument("out", nargs="?", default="premium-template.html")

    install_cmd = sub.add_parser("install", help="install the skill into an agent")
    install_cmd.add_argument("agent")
    install_cmd.add_argument("--root", default=".")

    args = parser.parse_args(argv)

    if args.cmd == "workflows":
        from .workflows import list_workflows

        wfs = list_workflows()
        if args.json:
            print(json.dumps(wfs, indent=2))
        else:
            C = {"c": "\033[96m", "b": "\033[1m", "d": "\033[2m", "x": "\033[0m"}
            _print(f"\n{C['b']}Five Design-Principle Workflows{C['x']}\n")
            for workflow in wfs:
                _print(f"{C['c']}{workflow['name']}{C['x']}  {C['d']}(--workflow {workflow['key']}){C['x']}")
                _print(f"  optimizes for: {workflow['optimizes_for']}")
                _print(f"  {workflow['philosophy']}")
                _print(f"  {C['d']}signature move: {workflow['signature_move']}{C['x']}\n")
        return

    if args.cmd == "purposes":
        from .purpose import list_purposes

        data = list_purposes()
        if args.json:
            print(json.dumps(data, indent=2))
        else:
            C = {"c": "\033[96m", "b": "\033[1m", "d": "\033[2m", "x": "\033[0m"}
            _print(f"\n{C['b']}Purpose-Fit Design Lenses{C['x']}\n")
            for item in data:
                _print(f"{C['c']}{item['name']}{C['x']}  {C['d']}(--purpose {item['key']}){C['x']}")
                _print(f"  {item['psychology']}")
                _print(f"  {C['d']}{item['directives'][0]}{C['x']}\n")
        return

    if args.cmd == "theme":
        from .theme import theme_for, write_theme
        payload = theme_for(args.purpose).to_dict()
        if args.out:
            write_theme(args.purpose, Path(args.out))
            payload["path"] = str(Path(args.out))
        print(json.dumps(payload, indent=2) if args.json or not args.out else f"theme written: {args.out}")
        return

    if args.cmd == "render-audit":
        from .render_audit import render_audit
        try:
            payload = render_audit(args.target, Path(args.out_dir))
        except RuntimeError as exc:
            _print(str(exc))
            raise SystemExit(2)
        print(json.dumps(payload, indent=2) if args.json else f"render audit: {'PASS' if payload['passed'] else 'BLOCK'}\nreceipt: {payload['receipt_path']}")
        if not payload["passed"]:
            raise SystemExit(1)
        return

    if args.cmd == "challenge":
        from .challenge import challenge_html
        payload = challenge_html(Path(args.file).read_text(encoding="utf-8"), purpose=args.purpose, workflow=args.workflow)
        payload["feature"] = args.feature
        out = Path(args.out) if args.out else Path(".prestige") / "challenge.json"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
        print(json.dumps(payload | {"receipt_path": str(out)}, indent=2))
        if not payload["passed"]:
            raise SystemExit(1)
        return

    if args.cmd == "purpose":
        from .purpose import audit_purpose

        html = Path(args.file).read_text(encoding="utf-8")
        css = Path(args.css).read_text(encoding="utf-8") if args.css else ""
        rep = audit_purpose(html, css, args.purpose)
        if args.json:
            print(
                json.dumps(
                    {
                        "purpose": rep.purpose,
                        "profile": rep.profile,
                        "score": rep.score,
                        "grade": rep.grade,
                        "passed": rep.passed,
                        "findings": [f.__dict__ for f in rep.findings],
                        "recommendations": rep.recommendations,
                        "attribution": rep.attribution.to_dict(),
                    },
                    indent=2,
                )
            )
        else:
            C = {"g": "\033[92m", "r": "\033[91m", "c": "\033[96m", "d": "\033[2m", "b": "\033[1m", "x": "\033[0m"}
            verdict = f"{C['g']}PASS{C['x']}" if rep.passed else f"{C['r']}NEEDS WORK{C['x']}"
            _print(f"\n{C['c']}Purpose fit - {args.file}{C['x']}")
            _print(f"{C['d']}profile: {rep.profile}{C['x']}")
            _print(f"{C['b']}Purpose score: {rep.score}/100  (grade {rep.grade})  {verdict}{C['x']}")
            for finding in rep.findings:
                _print(f"  {finding.criterion}: {finding.score}/100 - {finding.message}")
            if rep.recommendations:
                _print(f"\n{C['b']}Purpose recommendations:{C['x']}")
                for i, rec in enumerate(rep.recommendations[:8], 1):
                    _print(f"  {i}. {rec}")
        if args.strict and not rep.passed:
            sys.exit(1)
        return

    if args.cmd == "brief":
        from .brief import compile_brief, render_brief

        rep = compile_brief(Path(args.source) if args.source else None, purpose=args.purpose)
        if args.json:
            print(json.dumps(rep.to_dict(), indent=2))
        else:
            rendered = render_brief(rep)
            if args.out:
                Path(args.out).write_text(rendered, encoding="utf-8")
                _print(f"design brief written: {args.out}")
            else:
                _print(rendered)
        return

    if args.cmd == "score":
        from .score import score_design

        html = Path(args.file).read_text(encoding="utf-8")
        css = Path(args.css).read_text(encoding="utf-8") if args.css else ""
        rep = score_design(html, css, args.workflow, args.purpose)
        if args.json:
            print(
                json.dumps(
                    {
                        "workflow": rep.workflow,
                        "conversion_score": rep.conversion_score,
                        "grade": rep.grade,
                        "passed": rep.passed,
                        "law_scores": rep.law_scores,
                        "bias_scores": rep.bias_scores,
                        "cta_score": rep.cta_score,
                        "hook_score": rep.hook_score,
                        "mobile_score": rep.mobile_score,
                        "purpose_score": rep.purpose_score,
                        "purpose": rep.purpose,
                        "primary_cta": rep.primary_cta,
                        "hook": rep.hook,
                        "hard_failures": rep.hard_failures,
                        "recommendations": rep.recommendations,
                    },
                    indent=2,
                )
            )
        else:
            C = {"g": "\033[92m", "r": "\033[91m", "c": "\033[96m", "d": "\033[2m", "b": "\033[1m", "x": "\033[0m"}
            verdict = f"{C['g']}PASS{C['x']}" if rep.passed else f"{C['r']}NEEDS WORK{C['x']}"
            _print(f"\n{C['c']}Precision score - {args.file}{C['x']}")
            _print(f"{C['d']}workflow: {rep.workflow}{C['x']}")
            _print(f"{C['b']}Conversion readiness: {rep.conversion_score}/100  (grade {rep.grade})  {verdict}{C['x']}")
            _print(
                f"{C['d']}CTA:{rep.cta_score}  Hook:{rep.hook_score}  Mobile:{rep.mobile_score}  "
                + (f"Purpose:{rep.purpose_score}  " if rep.purpose_score is not None else "")
                + "  ".join(f"{k}:{v}" for k, v in rep.law_scores.items())
                + C["x"]
            )
            if rep.primary_cta:
                _print(f'  primary CTA: "{rep.primary_cta}"')
            if rep.hook:
                _print(f'  hook: "{rep.hook}"')
            if rep.hard_failures:
                _print(f"\n{C['r']}HARD FAILURES:{C['x']}")
                for failure in rep.hard_failures:
                    _print(f"   {failure}")
            if rep.recommendations:
                _print(f"\n{C['b']}Recommendations (ranked by conversion impact):{C['x']}")
                for i, rec in enumerate(rep.recommendations[:10], 1):
                    _print(f"  {i}. {rec}")
        if args.strict and not rep.passed:
            sys.exit(1)
        return

    if args.cmd == "audit":
        html = Path(args.file).read_text(encoding="utf-8")
        css = Path(args.css).read_text(encoding="utf-8") if args.css else ""
        rep = audit_html(html, css)
        print(_fmt(rep, args.file, args.json))
        if args.strict and not rep.passed:
            sys.exit(1)
    elif args.cmd == "install":
        from .adapters import install

        created = install(Path(args.root), args.agent)
        _print("installed skill:\n  " + "\n  ".join(str(c) for c in created))
    elif args.cmd == "scaffold":
        template = Path(__file__).resolve().parent.parent / "references" / "premium-template.html"
        dst = Path(args.out)
        dst.write_text(template.read_text(encoding="utf-8"), encoding="utf-8")
        _print(f"Wrote premium starter -> {dst}\nNext: edit, then `prestige audit {dst}`")


if __name__ == "__main__":
    main()
