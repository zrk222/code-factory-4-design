---
name: app-habit-engineer
description: Audit and build six-step habit loops for mobile apps, SaaS, consumer products, fintech, health and productivity. Use for repeat-use design, friction reduction, rewards, completion flows, or habit audits.
---

# App Habit Engineer

Build a repeatable path from the moment a user needs the product to a valuable result and an easier return. Apply all six mechanisms to the same primary journey. Return a JSON blueprint and a Markdown audit with source evidence, the smallest shippable changes, and how to measure each change.

## 1. Map and measure the current journey

Identify the app, audience, normal usage cadence, core value, and the action that delivers it. Capture the shortest realistic route and the routes for first use, returning use, error recovery, and completion. Observe touch and keyboard where they apply. Count taps, required inputs, and decisions. Record viewport height and the IDs, center positions, visibility, and reachability of primary controls. Observe the default landing experience and each completion path. Include the source or browser observations in the audit evidence.

Measure the Studio metrics on matching before and after routes.

| Metric | Definition and passing threshold |
| --- | --- |
| TAFI | Taps + inputs + twice the number of decisions. At most 3 for consumer and fintech, or 5 for SaaS. |
| TZER | Visible and reachable primary actions centered in the lower 35% of tested viewports. At least 90%. |
| PPDV | Direct landing is 1, a recommended default is 0.5, and a required choice fork is 0. Require at least 0.5. |
| SCER | Fraction of completion states with a clear exit and a meaningful available next action. Require 1. |

Keep mandatory confirmations for purchases, destructive actions, and sensitive data. Review pinch zoom, the mobile keyboard, safe areas, focus order, distraction, and sticky controls that obscure content. A class name or a proposed layout does not constitute a viewport observation.

## 2. Build all six mechanics

1. **The Itch.** Map the felt need, the situation that prompts it, and the fastest value the product can deliver. Write timely, specific notification copy and a routine schedule. Use triggers the user can control. For B2B, start with unfinished work, handoff delays, cognitive load, or a recurring deadline.
2. **The Lazy Thumb.** Remove repeat entry and compress the critical action to one gesture where feasible. Put the primary control within reach. Make a meaningful minimum action small enough to repeat. Where appropriate, make streaks reflect that minimum and provide a recovery path.
3. **The Paved Path.** Land on the relevant work or the next meaningful action. Pre-fill reversible choices from known intent. Keep an accessible way to change a default. Offer an immediate action and keep advanced decisions progressively disclosed.
4. **Variable Reward.** Design discovery, social acknowledgement, and mastery feedback independently. Vary relevant insights, useful suggestions, and the timing of genuine feedback while making primary outcomes predictable. For SaaS, favor found time, automation, and decision support over unrelated activity.
5. **Continuation.** Replace dead-end errors and empty states with recovery or a useful next task. Pair successful completion with an explicit, low-friction next action such as Add another, Open the next lesson, or Review the next item. Preserve Done and return focus. Verify that selecting one control causes exactly its intended action.
6. **Stored Value.** Let personalization, history, progress, and collaboration compound at each useful return. Ask for small investments after value is delivered. Give the user ways to inspect, correct, export, delete, and pause data use. For low-frequency products, prioritize continuity and fast re-entry over daily streaks.

## 3. Challenge the design

Replay the same task before and after. Deliberately break the primary action, keyboard focus, recovery, the recommended default, and the continuation path. Check for hidden billing, deceptive opt-outs, forced sharing, predatory reward structures, unrealistic streaks, and missing notification or data controls. A claimed pass needs an observation. A design estimate is a proposal.

Use `prestige habit-remediate` for structural React JSX or TSX changes. Mark a reviewed non-submit primary button and an authored action dock. Mark the completion container, its exit button, and an existing next-action parameter. Preview the edits, review source identity, and replay the transformed component. Test one activation, one effect, the original exit, and an independently chosen follow-on.

## 4. Deliver and measure

Write an input conforming to `prestige.habit-contract.v1`. Show before and after metrics, all six concrete mechanics, any gate findings, and the implementation roadmap. Each roadmap row needs a feature, effort, a success metric, and a falsifiable hypothesis. Use measured task completion, return-to-value, repeat qualified actions, or time to value. Include guardrail outcomes for abandonment, opt-outs, regret, or unintended effects. State retention lift only when a product experiment measures it.

Run:

```sh
prestige habit-audit habit.json --format json
prestige habit-audit habit.json --format markdown
prestige habit-audit habit.json --strict
```

The strict gate requires a recorded observation mode and passing metrics on the supplied contract. Review what the observation artifacts actually establish before promoting a build.
