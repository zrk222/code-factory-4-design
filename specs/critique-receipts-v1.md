# Spec: critique-receipts-v1
Status: approved
SpecFactor-target: 0.75-2.5

## MUST - Functional core

### Description

Prestige shall provide a deterministic-first composite critique that evaluates
visual hierarchy, composition, color, affordance, information density,
typography, and brand consistency. Each finding shall distinguish observed
evidence from interpretation, label deterministic versus heuristic checks, and
remain publication-safe. The feature adapts the critique taxonomy from the
MIT-licensed Owl-Listener/designer-skills repository at commit
`acc3e574b36ef2895268a176dbae886e1b845ae0` without presenting advisory rules
as measured conversion claims.

### User roles

- Designer or developer auditing an HTML/CSS interface.
- Coding agent consuming machine-readable findings.
- Reviewer verifying that the critique rejects deliberate defects.

### Requirements (EARS)

- When the CLI receives `prestige critique page.html --json`, the system shall return marker `CRITIQUE_SEVEN_LENSES` with exactly 7 named dimensions: `visual_hierarchy`, `composition`, `color`, `affordance`, `information_density`, `typography`, and `brand_consistency`. [R1]
- The system shall return marker `CRITIQUE_SCHEMA_V1` with schema `prestige.critique.v1`, a SHA-256 source digest, exactly 7 dimension summaries, findings, severity counts, pass state, and scope statements. [R2]
- When a finding is emitted, the system shall return marker `CRITIQUE_FINDING_SHAPE_EXACT` with exactly 8 required finding fields: dimension, code, severity, mode, observation, problem, fix, and evidence. [R3]
- When a finding is based on parsed HTML, CSS, contrast arithmetic, accessible-name presence, interaction states, target dimensions, text sizing, line height, line measure, or supplied contract hashes, the system shall label mode `deterministic`. [R4]
- When a finding concerns eye flow, balance, visual rhythm, or inferred cognitive load, the system shall label mode `heuristic` and include confidence between 0.0 and 1.0. [R5]
- If a deterministic P1 finding exists, the system shall return marker `CRITIQUE_BLOCKED_P1` and passed false. [R6]
- When the strict verdict is `blocked`, the system shall return marker `CRITIQUE_STRICT_EXIT_EXACT` with a nonzero CLI exit status. [R7]
- When discovery reports a `missing` DESIGN.md, MOOD.md, or VOICE.md contract, the system shall return marker `CRITIQUE_CONTRACT_ABSENT` with contract status `missing`. [R8]
- When a supplied brand contract exists, the system shall return marker `CRITIQUE_CONTRACT_HASHED` with its SHA-256 and shall never include the contract body in the receipt. [R9]
- When challenge status is `all_mutants_rejected`, the system shall return marker `CRITIQUE_MUTATIONS_REJECTED` with 7 targeted mutation results. [R10]
- When receipt output mode is `requested`, the system shall return marker `CRITIQUE_RECEIPT_ATOMIC` after an atomic receipt write and shall return its resolved path. [R11]
- The system shall return marker `CRITIQUE_ATTRIBUTED_MIT` and include the upstream repository URL, pinned commit, and MIT attribution in packaged documentation or notice metadata. [R12]
- The system shall return marker `RELEASE_080_SYNCHRONIZED` after identifying version 0.8.0 in package, runtime, documentation, and release metadata. [R13]

### Acceptance criteria (Gherkin)

```gherkin
Scenario: Emit a seven-lens critique receipt
  Given an HTML page and optional CSS
  When the operator runs `prestige critique page.html --json`
  Then the schema is `prestige.critique.v1`
  And exactly 7 dimension summaries are present
  And every finding contains the 8 required fields

Scenario: Block a deterministic major defect
  Given the strict verdict is `blocked`
  And an interactive control without an accessible name
  When the operator runs the critique in strict mode
  Then an affordance finding has severity P1 and mode deterministic
  And the command exits with code 1
  And marker `CRITIQUE_STRICT_EXIT_EXACT` is present

Scenario: Preserve absent brand context
  Given discovery reports a `missing` DESIGN.md contract
  And discovery reports a `missing` MOOD.md contract
  And discovery reports a `missing` VOICE.md contract
  When the page is critiqued
  Then all 3 optional brand contracts are reported absent
  And no contract content is inferred
  And each missing contract has marker `CRITIQUE_CONTRACT_ABSENT`

Scenario: Prove the critique is non-hollow
  Given challenge status is `all_mutants_rejected`
  And 7 deliberate dimension-specific mutants
  When critique challenge runs
  Then all 7 mutants are rejected by deterministic P1 or P2 findings
  And marker `CRITIQUE_MUTATIONS_REJECTED` is present

Scenario: Write the requested receipt atomically
  Given receipt output mode is `requested`
  When the page is critiqued
  Then an atomic receipt is written at the resolved output path
  And marker `CRITIQUE_RECEIPT_ATOMIC` is present

Scenario: Every requirement has an observable validator marker
  Given the Critique Receipts contract
  When strict validator mutation runs
  Then contract markers include `CRITIQUE_SEVEN_LENSES`, `CRITIQUE_SCHEMA_V1`, `CRITIQUE_FINDING_SHAPE_EXACT`, `deterministic`, `heuristic`, `CRITIQUE_BLOCKED_P1`, `CRITIQUE_STRICT_EXIT_EXACT`, `CRITIQUE_CONTRACT_ABSENT`, `CRITIQUE_CONTRACT_HASHED`, `CRITIQUE_MUTATIONS_REJECTED`, `CRITIQUE_RECEIPT_ATOMIC`, `CRITIQUE_ATTRIBUTED_MIT`, and `RELEASE_080_SYNCHRONIZED`
```

## SHOULD - Technical/structural

- ADR references: `docs/CRITIQUE.md` and packaged `NOTICE` attribution.
- Data model: `prestige.critique.v1` JSON receipt.
- API contract: `prestige critique page.html --css page.css --design DESIGN.md --mood MOOD.md --voice VOICE.md --challenge --strict --json --out critique.json`; every option except `page.html` is optional.
- Contrast arithmetic shall normalize 8-bit RGB channels by 255.
- Deterministic receipt ordering shall map P1, P2, and P3 to sort priorities 0,
  1, and 2 respectively, and emitted JSON shall use an indentation width of 2.

## SHOULD NOT - Implementation details

- Do not claim measured conversion, usability, accessibility conformance, or brand fidelity.
- Do not hard-fail on subjective eye-flow, composition, rhythm, or density heuristics.
- Do not include HTML, CSS, brand-contract bodies, absolute paths, or prompts in receipts.
- Do not add a third-party runtime dependency.

## Decision logic (factory candidates)

The deterministic verdict rules are fully declared by R6 through R10 and are
mutation-tested. Heuristic findings never participate in the blocking verdict.
