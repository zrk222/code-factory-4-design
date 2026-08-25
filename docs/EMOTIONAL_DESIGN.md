# Ethical Emotional Design

Prestige treats emotion as a journey requirement, not a conversion claim.
The `emotion` gate reviews observable HTML/CSS signals across six dimensions:

1. **Visceral** — one declared emotional intent and a coherent visual language.
2. **Behavioral** — named active state, truthful progress, and responsive feedback.
3. **Reflective** — meaningful completion, evidence, continuity, and a next step.
4. **Safe failure** — non-punitive explanation with retry, edit, revert, back, or support.
5. **Agency** — review and reversal controls, especially for AI-generated work.
6. **Inclusion** — reduced-motion adaptation, redundant state cues, and explicit opt-in.

```bash
prestige brief PRD.md --purpose fintech --out DESIGN_BRIEF.md
prestige emotion app.html --intent confidence --challenge --strict \
  --out .prestige/emotional-design.json
```

The receipt contains a source hash, dimension scores, deterministic findings,
attribution units, and an explicit claim boundary. It never copies the source
page into the receipt. The challenge injects three isolated regressions—shaming
copy, a preselected opt-in, and motion without adaptation—and must reject all
three before emitting `EMOTIONAL_MUTATIONS_REJECTED`.

## Ethical boundary

The research supplied for this feature included useful models alongside
coercive patterns. Prestige adopts the tripartite model, safe failure,
low-friction action, honest continuity, multisensory redundancy, and
meaningful completion. It rejects:

- guilt or anthropomorphic pressure;
- confirm-shaming or preselected consent;
- fake scarcity and anxiety monetization;
- variable-reward mechanics intended to create compulsion;
- punitive streak loss or sunk-cost lock-in;
- hidden AI authorship or automation without user controls.

These patterns are not required for engagement. They are trust risks and are
reported as deterministic P1 blockers when observable in source.

## Evidence boundary

Static analysis can establish that a page includes declared intent, status,
recovery, control, and preference-adaptation signals. It cannot establish that
a person felt calm, delighted, motivated, or included. Product impact requires
consented user research and the product's own analytics or experiment receipt.
Rendered motion, audio, and haptic quality require native-device review.

