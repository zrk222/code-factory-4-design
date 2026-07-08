"""prestige CLI — audit a page against the five laws, or scaffold a premium
starting template. Designed to be called by an agent as a verification step."""
from __future__ import annotations
import argparse, json, sys
from pathlib import Path
from .audit import audit_html

def _fmt(report, path, as_json):
    if as_json:
        return json.dumps({"file": str(path), "overall": report.overall,
                           "passed": report.passed, "scores": report.scores,
                           "hard_failures": report.hard_failures,
                           "findings": [f.__dict__ for f in report.findings]}, indent=2)
    C = {"g":"\033[92m","y":"\033[93m","r":"\033[91m","c":"\033[96m","d":"\033[2m","x":"\033[0m"}
    icon = {"pass":f"{C['g']}✓{C['x']}","warn":f"{C['y']}▲{C['x']}","fail":f"{C['r']}✗{C['x']}","hard_fail":f"{C['r']}⛔{C['x']}"}
    out = [f"\n{C['c']}Prestige audit — {path}{C['x']}"]
    verdict = f"{C['g']}PASS{C['x']}" if report.passed else f"{C['r']}NEEDS WORK{C['x']}"
    out.append(f"Overall: {report.overall}/100   Verdict: {verdict}")
    out.append(f"{C['d']}" + "  ".join(f"{k}:{v}" for k,v in report.scores.items()) + C['x'])
    if report.hard_failures:
        out.append(f"\n{C['r']}⛔ HARD FAILURES (fix before shipping — function over aesthetics):{C['x']}")
        for h in report.hard_failures: out.append(f"   {h}")
    if report.findings:
        out.append("")
        for fi in report.findings:
            if fi.level == "pass": continue
            out.append(f"  {icon.get(fi.level,'·')} [{fi.law}] {fi.code}: {fi.message}")
    return "\n".join(out)

def main(argv=None):
    p = argparse.ArgumentParser(prog="prestige", description="The Digital Architect of Prestige — premium design audit + scaffold")
    sub = p.add_subparsers(required=True, dest="cmd")
    a = sub.add_parser("audit", help="score an HTML file against the five laws")
    a.add_argument("file"); a.add_argument("--css", default=None, help="optional separate CSS file")
    a.add_argument("--json", action="store_true"); a.add_argument("--strict", action="store_true",
        help="exit nonzero if not passing (for CI / agent gate)")

    sc = sub.add_parser("score", help="PRECISE conversion-readiness score (laws+biases+CTA+hooks+mobile) with ranked recommendations")
    sc.add_argument("file"); sc.add_argument("--css", default=None)
    sc.add_argument("--workflow", default="conversion",
                    choices=["conversion","luxury","trust","editorial","product"])
    sc.add_argument("--json", action="store_true"); sc.add_argument("--strict", action="store_true")

    wf = sub.add_parser("workflows", help="list the five design-principle workflows")
    wf.add_argument("--json", action="store_true")
    s = sub.add_parser("scaffold", help="write a premium starter template")
    s.add_argument("out", nargs="?", default="premium-template.html")
    ia = sub.add_parser("install", help="install the skill into an agent (claude|codex|opencode|cursor|generic)")
    ia.add_argument("agent"); ia.add_argument("--root", default=".")
    args = p.parse_args(argv)

    if args.cmd == "workflows":
        from .workflows import list_workflows
        wfs = list_workflows()
        if args.json:
            print(json.dumps(wfs, indent=2))
        else:
            C = {"c":"\033[96m","b":"\033[1m","d":"\033[2m","x":"\033[0m"}
            print(f"\n{C['b']}Five Design-Principle Workflows{C['x']}\n")
            for w in wfs:
                print(f"{C['c']}{w['name']}{C['x']}  {C['d']}(--workflow {w['key']}){C['x']}")
                print(f"  optimizes for: {w['optimizes_for']}")
                print(f"  {w['philosophy']}")
                print(f"  {C['d']}signature move: {w['signature_move']}{C['x']}\n")
        return
    if args.cmd == "score":
        from .score import score_design
        html = Path(args.file).read_text()
        css = Path(args.css).read_text() if args.css else ""
        rep = score_design(html, css, args.workflow)
        if args.json:
            print(json.dumps({"workflow": rep.workflow, "conversion_score": rep.conversion_score,
                              "grade": rep.grade, "passed": rep.passed, "law_scores": rep.law_scores,
                              "bias_scores": rep.bias_scores, "cta_score": rep.cta_score,
                              "hook_score": rep.hook_score, "mobile_score": rep.mobile_score,
                              "primary_cta": rep.primary_cta, "hook": rep.hook,
                              "hard_failures": rep.hard_failures,
                              "recommendations": rep.recommendations}, indent=2))
        else:
            C = {"g":"\033[92m","y":"\033[93m","r":"\033[91m","c":"\033[96m","d":"\033[2m","b":"\033[1m","x":"\033[0m"}
            verdict = f"{C['g']}PASS{C['x']}" if rep.passed else f"{C['r']}NEEDS WORK{C['x']}"
            print(f"\n{C['c']}Precision score — {args.file}{C['x']}")
            print(f"{C['d']}workflow: {rep.workflow}{C['x']}")
            print(f"{C['b']}Conversion readiness: {rep.conversion_score}/100  (grade {rep.grade})  {verdict}{C['x']}")
            print(f"{C['d']}CTA:{rep.cta_score}  Hook:{rep.hook_score}  Mobile:{rep.mobile_score}  "
                  + "  ".join(f"{k}:{v}" for k,v in rep.law_scores.items()) + C['x'])
            if rep.primary_cta: print(f'  primary CTA: "{rep.primary_cta}"')
            if rep.hook: print(f'  hook: "{rep.hook}"')
            if rep.hard_failures:
                print(f"\n{C['r']}⛔ HARD FAILURES:{C['x']}")
                for h in rep.hard_failures: print(f"   {h}")
            if rep.recommendations:
                print(f"\n{C['b']}Recommendations (ranked by conversion impact):{C['x']}")
                for i, rec in enumerate(rep.recommendations[:10], 1):
                    print(f"  {i}. {rec}")
        if args.strict and not rep.passed:
            sys.exit(1)
        return
    if args.cmd == "audit":
        html = Path(args.file).read_text()
        css = Path(args.css).read_text() if args.css else ""
        rep = audit_html(html, css)
        print(_fmt(rep, args.file, args.json))
        if args.strict and not rep.passed:
            sys.exit(1)
    elif args.cmd == "install":
        from .adapters import install
        created = install(Path(args.root), args.agent)
        print("installed skill:\n  " + "\n  ".join(str(c) for c in created))
    elif args.cmd == "scaffold":
        tpl = (Path(__file__).resolve().parent.parent/"references"/"premium-template.html")
        dst = Path(args.out); dst.write_text(tpl.read_text())
        print(f"Wrote premium starter → {dst}\nNext: edit, then `prestige audit {dst}`")

if __name__ == "__main__":
    main()
