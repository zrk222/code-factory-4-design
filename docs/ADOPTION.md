# Prestige 0.7 Adoption Loop

Prestige is a local, deterministic design-constraint verifier. It does not
replace visual regression, accessibility testing, or human design review.
It proves whether selected design constraints are present and whether the
token verifier can reject a meaningful contract mutation.

## Five-minute setup

```bash
prestige init --root . --out DESIGN.md
# Review and commit DESIGN.md. The command will not overwrite it without --force.
prestige pr path/to/page.html --design DESIGN.md --root . --out-dir .prestige/pr
prestige ci init --platform github --page path/to/page.html --design DESIGN.md
```

`prestige init` produces `contract-scan.json` beside the proposed contract. It
records every scanned source file and CSS custom property. It does not infer
semantic naming, runtime styles, or a Tailwind configuration; those remain a
human review decision before the contract becomes a gate.

## PR bundle

`prestige pr` writes four local artifacts:

- `proof-report.json`: machine-readable receipt with categories and limits.
- `proof-report.html`: static visual viewer; no account or service is needed.
- `pr-summary.md`: concise comment-ready review summary.
- `annotations.json`: blocking, file-oriented findings for CI adapters.

Findings have one of three categories:

- `contract`, blocking: a literal implementation value contradicts the
  committed contract.
- `proof`, blocking: the verifier cannot prove an exercised token mutation is
  detected (`HOLLOW_TOKEN`).
- `advisory`, non-blocking: reserved for judgment-based design review. The 0.7
  token proof report does not manufacture advisory findings.

The report only gives a deterministic repair when it has one: for an
`OFF_TOKEN` value it names the approved nearest value. Literal-value references
are evidence, not a claim that every listed line is the root cause.

## CI templates

`prestige ci init --platform github` writes a pull-request workflow that runs
the PR bundle and uploads it as an artifact. `--platform gitlab` writes an
equivalent GitLab job. The templates do not post comments or call a hosted
service; teams can consume `pr-summary.md` and `annotations.json` using their
existing forge permissions and review policy.

## Benchmark fixture suite

```bash
prestige benchmark --json
```

The installed fixture suite contains static HTML, compiled React CSS Modules,
and compiled Tailwind CSS cases. It reports true/false-positive and
true/false-negative counts from labels committed with those fixtures. It does
not claim React runtime, Next.js, Vue, Nuxt, Svelte, Material UI, Shadcn,
mobile-rendering, setup-time, or flake coverage yet. Those require adapter and
repeated-render evidence rather than a made-up aggregate percentage.

## Evidence boundary

`verify-tokens` mutates the contract and proves the token lint rule notices
the removed value. It does not claim a visual screenshot changed. A visual
change claim requires a separate `prestige render-audit` receipt, which captures
browser screenshots and computed layout evidence.
