# Prestige 0.9.0 — Ethical Emotional Design

Prestige 0.9.0 adds a deterministic-first emotional journey gate for teams
that want interfaces to feel calm, confident, motivating, delightful, or
welcoming without relying on coercive engagement mechanics.

## What changes

- `prestige brief` now defines a purpose-matched emotional intent, the six
  journey phases, and explicit anti-manipulation guardrails before UI work.
- `prestige emotion` reviews visceral coherence, behavioral feedback,
  reflective completion, safe failure, user agency, and inclusion.
- `--challenge` proves the gate rejects shaming copy, preselected consent, and
  motion that ignores user preferences.
- `--out` writes a portable, SHA-256-bound local receipt.

## What it will not claim

Static source cannot prove that users felt an emotion or that retention or
conversion improved. Accessibility conformance, cultural interpretation,
rendered motion, audio, and haptics remain separate review surfaces.

## Upgrade verification

```bash
python -m pytest -q
python -m build
python -m twine check dist/*
prestige emotion references/emotional-journey.html --intent confidence --challenge --strict
```
