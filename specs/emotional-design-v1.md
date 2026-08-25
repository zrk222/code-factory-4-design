# Spec: emotional-design-v1

Status: approved

## MUST — Functional core

Prestige shall convert emotional intent into an ethical, deterministic-first
review across visceral, behavioral, reflective, safe-failure, agency, and
inclusion dimensions without inferring user feelings or claiming product impact.

### Requirements (EARS)

- When emotional schema output is requested, the system shall return marker `EMOTIONAL_SCHEMA_V1`, schema `prestige.emotional-design.v1`, exactly six dimension scores, a SHA-256 source binding, findings, recommendations, attribution, and an explicit claim boundary. [R1]
- When a visible error region lacks a recovery action, the system shall return `E_FAILURE_DEAD_END` as deterministic P1 and reject strict mode. [R2]
- When punitive copy, confirm-shaming, preselected opt-in, fake scarcity, or a declared compulsion mechanic is present, the system shall return `E_PUNITIVE_COPY` or `E_MANIPULATIVE_PATTERN` and reject strict mode. [R3]
- When motion exists without a user preference alternative, the system shall return `E_REDUCED_MOTION_MISSING` as deterministic P2 and reject strict mode unless `prefers-reduced-motion` is present. [R4]
- When AI or agent behavior is present without visible authorship disclosure, the system shall return `E_AI_AUTHORSHIP_HIDDEN` as deterministic P2 and reject strict mode. [R5]
- When challenge mode runs against a passing baseline, the system shall reject all three isolated safety mutants and emit marker `EMOTIONAL_MUTATIONS_REJECTED`. [R6]
- When atomic receipt output is requested, the system shall store marker `EMOTIONAL_RECEIPT_ATOMIC` with the receipt atomically and without input HTML, CSS, prompts, credentials, or network data. [R7]

## Acceptance criteria (Gherkin)

```gherkin
Scenario: Verify an emotionally resilient journey
  Given a page declares confidence as its emotional intent
  And the page provides active state, recovery, completion, and user controls
  When the operator runs the emotional-design gate in strict challenge mode
  Then the system returns six passing dimension scores
  And all three safety mutants are rejected
  And the receipt includes the static-analysis claim boundary

Scenario: Reject coercive engagement
  Given a page contains a preselected opt-in or punitive failure copy
  When the operator runs the emotional-design gate in strict mode
  Then the system returns a deterministic P1 finding
  And the command exits with code 1

Scenario: Every requirement has an observable validator marker
  Given the emotional design contract defines `EMOTIONAL_SCHEMA_V1`
  When strict validator mutation runs
  Then the validators reference `E_FAILURE_DEAD_END`
  And the validators reference `E_PUNITIVE_COPY`
  And the validators reference `E_REDUCED_MOTION_MISSING`
  And the validators reference `E_AI_AUTHORSHIP_HIDDEN`
  And the validators reference `EMOTIONAL_MUTATIONS_REJECTED`
  And the validators reference `EMOTIONAL_RECEIPT_ATOMIC`
```

## SHOULD — Integration

- `prestige brief` should add a purpose-matched emotional intent, a six-stage
  journey, ethical guardrails, and the exact emotional verification command.
- The feature should add no runtime dependency and should make no network or
  process call.

## Data model and exact bounds

- The report contains exactly `6` dimension scores, each clamped to the closed
  integer range `0` through `100`; the passing threshold is `70`.
- The challenge contains exactly `3` isolated mutants.
- Portable JSON uses UTF-8 and indentation width `2`.
- Finding penalties are deterministic constants: `15`, `20`, `25`, `30`,
  `35`, `45`, `50`, `60`, and `70` points depending on the declared check.

## SHOULD NOT — Claim boundary

- Do not claim measured emotion, retention, conversion, accessibility
  conformance, haptic fidelity, or cultural universality from static source.
- Do not recommend shame, guilt, variable-reward compulsion, punitive streaks,
  fake scarcity, or hidden automation.
