# Plan: critique-receipts-v1
Spec: specs/critique-receipts-v1.md
Architect verdict: PASS

## Logical decomposition (phases)

1. Implement the receipt model and seven deterministic-first critique lenses.
2. Expose the CLI and non-hollow mutation challenge.
3. Document attribution, scope limits, and release behavior.
4. Synchronize and publish version 0.8.0.

## Tasks (atomic - each independently shippable)

- [ ] T1 | slice=prestige_design | files=prestige_design/critique.py,tests/test_critique.py | verify=`python -m pytest -q tests/test_critique.py` | Implement seven-lens findings, receipt hashing, strict verdicts, brand-contract absence/hashing, and atomic output.
- [ ] T2 | slice=prestige_design | files=prestige_design/critique.py,prestige_design/cli.py,tests/test_critique.py | verify=`python -m pytest -q tests/test_critique.py` | Add the critique CLI and 7-mutant non-hollow challenge.
- [ ] T3 | slice=docs | files=docs/CRITIQUE.md,docs/RELEASE_NOTES_0.8.0.md | verify=`python -m pytest -q tests/test_critique.py` | Document usage, deterministic/heuristic boundaries, attribution, and release behavior.
- [ ] T3a | slice=prestige_design | files=prestige_design/SKILL.md | verify=`python -m pytest -q tests/test_critique.py tests/test_prestige.py` | Teach the installed skill to use critique receipts.
- [ ] T3b | slice=README.md | files=README.md | verify=`python -m pytest -q tests/test_critique.py` | Add the public quick-start.
- [ ] T3c | slice=NOTICE | files=NOTICE | verify=`python -m pytest -q tests/test_critique.py` | Add pinned MIT attribution.
- [ ] T4 | slice=pyproject.toml | files=pyproject.toml | verify=`python -m build` | Synchronize package version 0.8.0.
- [ ] T4a | slice=prestige_design | files=prestige_design/__init__.py | verify=`python -m pytest -q tests/test_prestige.py` | Synchronize runtime version 0.8.0.
