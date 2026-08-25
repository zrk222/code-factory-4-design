# AKU: Ethical Emotional Design Gate

## Intent

Turn a product's intended feeling into a bounded, reviewable journey contract
and prevent emotional polish from masking coercion, inaccessible motion, silent
automation, or dead-end failure states.

## Procedure

1. Select one intent: `calm`, `confidence`, `momentum`, `delight`, or `belonging`.
2. Compile a purpose brief and review its six-stage emotional journey.
3. Implement explicit state, progress, recovery, completion, and user controls.
4. Run `prestige emotion <file> --intent <intent> --challenge --strict --out <receipt>`.
5. Treat P1/P2 findings and surviving mutations as blocking.
6. Pair static proof with render/native-device and human research evidence before making experiential claims.

## Tools

- `prestige brief` for the pre-build journey and ethical guardrails.
- `prestige emotion` for deterministic source review and a portable receipt.
- `prestige critique`, `render-audit`, `challenge`, and token verification for the existing visual proof lanes.

## Metadata

- Schema: `prestige.emotional-design.v1`
- Challenge schema: `prestige.emotional-challenge.v1`
- Source binding: SHA-256 of supplied HTML plus CSS
- Runtime authority: local file read and optional atomic receipt write only
- External authority: none

## Governance

- Autonomy class: **supervised**. The tool may diagnose and write a requested local receipt; a human owns design intent, research consent, and release.
- No network, publication, deployment, notification, biometric collection, or source mutation authority.
- Psychology mechanisms are hypotheses until supported by product-specific evidence.
- Coercion, fabricated urgency, hidden AI authorship, and accessibility bypasses fail closed when deterministically observable.

## Continuations

- If static checks pass, continue to rendered desktop/mobile review.
- If motion, audio, or haptics are in scope, continue to real-device testing with accessibility settings enabled.
- If experiential or conversion claims are desired, continue to consented qualitative research and a separately bound analytics receipt.
- If any required evidence is unavailable, preserve an explicit unverified state.

## Validators

- Focused tests: `python -m pytest tests/test_emotional.py -q`
- Full tests: `python -m pytest -q`
- CLI mutation gate: `prestige emotion <file> --challenge --strict`
- Architecture contract: `specs/emotional-design-v1.ssat.yaml`

