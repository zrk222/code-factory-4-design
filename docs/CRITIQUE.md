# Seven-lens critique receipts

Prestige 0.8 adds a deterministic-first composite critique:

```bash
prestige critique page.html --css page.css --json
prestige critique page.html --design DESIGN.md --mood MOOD.md --voice VOICE.md \
  --challenge --strict --out .prestige/critique.json
```

The `prestige.critique.v1` receipt contains exactly seven dimension summaries:
visual hierarchy, composition, color, affordance, information density,
typography, and brand consistency.

Every finding contains dimension, code, P1/P2/P3 severity, deterministic or
heuristic mode, observation, problem, fix, and evidence. Confidence is stored
inside the evidence object so the public finding shape stays stable.

Deterministic checks include semantic heading count, CTA competition, layout
structure, opaque hex contrast arithmetic, accessible control names, focus
states, 44px target evidence, navigation count, font size, line height, and
DESIGN.md token drift. Static source cannot resolve every computed browser
style, image background, overlap, state transition, or user outcome, so those
limits remain explicit.

`--challenge` creates one isolated mutant per dimension. The receipt earns
`CRITIQUE_MUTATIONS_REJECTED` only when all seven targeted defects produce a
deterministic P1 or P2 finding.

The taxonomy and Observation / Problem / Fix shape are adapted from
[Owl-Listener/designer-skills](https://github.com/Owl-Listener/designer-skills)
at commit `acc3e574b36ef2895268a176dbae886e1b845ae0` under MIT. Prestige adds
executable checks, confidence boundaries, atomic receipts, and mutation proof.

