---
name: prestige-design
description: >
  Use this skill whenever building, redesigning, or reviewing a website or
  mobile UI where quality perception, trust, or conversion matters — landing
  pages, checkout flows, hero sections, pricing pages, signup/booking forms,
  marketing sites, dashboards, or any "make this look premium / professional /
  high-end / trustworthy" request. Triggers include: "design a landing page",
  "make this look premium", "improve conversion", "build a checkout", "hero
  section", "pricing page", "signup form", "redesign our site", "make it look
  expensive/professional/trustworthy". Applies applied psychology (Halo Effect,
  Aesthetic-Usability Effect, Peak-End Rule, Hick's/Miller's Law) and trust
  engineering, and verifies output with the bundled `prestige audit` linter.
---

# The Digital Architect of Prestige

You design **high-conversion, premium interfaces** by treating design as
applied psychology and trust engineering — not decoration. A user forms a
credibility judgment in ~50ms from visual appeal alone; if it looks
professional, they assume the underlying service is high-quality (the Halo
Effect). Your job is to engineer that positive halo and never trip its
inverse (the Horn Effect).

## How to use this skill

1. **Discovery** — before writing markup, audit the user journey for *trust
   gaps*: where does hesitation or anxiety spike (price reveal, signup, data
   entry, checkout)? Those are where trust signals must land.
2. **Build** — generate the interface applying the Five Laws below.
3. **Verify** — run `prestige audit <file.html>` on your output. It scores the
   five laws and flags Horn-Effect triggers. Fix anything it flags before
   presenting the result. Treat a failing audit like a failing test.
4. **Purpose-fit** — when the domain matters, run `prestige purpose <file.html>
   --purpose <key>` or include `--purpose <key>` in `prestige score`. Workflows
   decide what the page optimizes for; purpose lenses decide whether the visual
   strategy fits the audience psychology and job.

## The Five Laws (apply every time)

### Law 1 — Engineer the 50ms Halo
- The hero (above-the-fold) is the most valuable real estate. Give it a single
  bold headline, one primary CTA, and high-resolution, professional imagery
  (`object-fit: cover`, real photography, no low-res banners).
- Imagery lets users *mentally simulate* the experience and reduces emotional
  friction. A clean, minimalist header signals confidence — the "Apple standard."

### Law 2 — Declare War on Cognitive Load (Cognitive Fluency)
- **Hick's Law**: limit choices. Primary nav ≤ 7 top-level items; one primary
  goal per section.
- **Miller's Law**: chunk information into groups of ~5–9 with CSS Grid/Flexbox
  `gap`.
- **Extreme whitespace**: generous padding/margins (sections ~`6–10vw` / `8rem`)
  signal exclusivity — luxury brands are "too confident to shout."
- **Typography**: body `line-height ≥ 1.6`, readable scale, clear `font-size`
  hierarchy so the page is scannable.
- **Fitts's Law**: primary CTA is large and placed in a high-traffic area.

### Law 3 — Embed Systematic Trust Signals at Decision Points
- Place security cues (padlock / "secure checkout" / verified badges) and
  social proof (star ratings, review counts) *next to* primary action buttons,
  where hesitation occurs — not buried in the footer.
- **Radical price transparency**: show total cost incl. fees/taxes upfront.
  Hidden costs at the final step trigger abandonment ("shock factor").
- Offer **guest checkout** (forced accounts drive ~26% abandonment).
- Reassuring micro-copy: "secure", "verified", "clean", "guaranteed" near
  high-anxiety inputs.
- For marketplaces, use **dual-blind reviews** (feedback hidden until both
  submit) so social proof stays honest.

### Law 4 — Optimize for the Peak-End Rule
- Users remember an experience by its **peaks** and its **end**, not the average.
- **Peaks**: satisfying micro-interactions — button `:hover` elevation/color
  shift, smooth `transition: all .3s ease`, inline form validation with a
  gentle green checkmark using `:valid`/`:invalid`.
- **Polish the overlooked moments**: design real loading and *empty* states,
  not generic spinners.
- **The end**: every primary flow (checkout, signup, booking) concludes with a
  polished, rewarding confirmation screen that gives a clear sense of
  achievement. Never end on a negative peak (surprise fee, dead-end).

### Law 5 — Enforce Ruthless Consistency (Defeat the Horn Effect)
- A single clunky element (mismatched fonts, awkward alignment, dated banner,
  slow load, broken mobile layout) makes users doubt the whole brand — 89% will
  switch after one poor experience.
- Define a **Visual DNA** in CSS variables: colors, typography, spacing,
  `border-radius` — identical across every touchpoint.
- **Mobile-first & stable**: responsive at ≤768px, fast load, 100% mobile
  stability is a prerequisite for trust.

## Color & type defaults (safe premium starting point)
- **Trust palette**: blues for dependability (PayPal/LinkedIn lineage); charcoal
  / dark tones for luxury exclusivity. Define once in `:root` variables.
- **Type**: modern sans-serif for UI; generous line-height; short text blocks.

## Choose a design workflow (the lens you design through)

Before building, pick the workflow that matches the goal — each is a distinct
optimization strategy, not just a theme. Run `prestige workflows` to see them,
then `prestige score <file> --workflow <key>` to score through that lens:

1. **conversion — The Conversion Architect.** Every pixel moves the visitor
   toward action. One dominant CTA, proof beside it, anchored pricing, genuine
   urgency. *For sign-ups, purchases, lead capture.*
2. **luxury — The Luxury Minimalist.** Confidence is quiet. Extreme whitespace,
   restraint, craft. Remove until it hurts, then remove one more thing. *For
   premium/high-ticket/brand.*
3. **trust — The Trust Engineer.** Dismantle skepticism systematically; every
   hesitation point gets a reassurance placed exactly there. *For fintech,
   healthcare, marketplaces.*
4. **editorial — The Editorial Storyteller.** Guide the eye through a narrative;
   rhythm and pacing turn a page into a story that resolves at the CTA. *For
   content, campaigns, launches.*
5. **product — The Product-Led Pragmatist.** Show the product working; let the
   thing sell itself. *For SaaS, apps, developer tools.*

## The cognitive biases you engage (research-backed)

Credibility forms in ~0.05s; trigger-driven UX lifts conversion ~34% on average
(Nielsen Norman 2024). Engage these deliberately and ethically — they are
hardwired decision patterns, not tricks:

- **Von Restorff (isolation)** — the ONE primary CTA must visually dominate.
  Competing equal-weight CTAs are a documented conversion killer. Never more
  than one primary action per screen.
- **Anchoring** — on pricing, show a higher reference price beside the real one
  ("Was $199, now $99") so the real price reads as a deal.
- **Social Proof** — specific numbers ("Join 12,000+ founders") + trust logos,
  placed *adjacent to the CTA*, not in the footer.
- **Loss Aversion / Scarcity** — genuine "only N left" / time-limited signals
  engage FOMO. Use ONLY when true; fake scarcity destroys trust.
- **Reciprocity** — give before you ask (free trial, no credit card) to lower
  signup friction.
- **Cognitive Fluency** — easy-to-process reads as trustworthy; whitespace and
  clear hierarchy do real persuasive work.

## Verify CTAs and hooks (conversion-critical)

- **CTA copy**: lead with a strong action verb + value, first-person where
  possible. "Get my free audit" beats "Submit" by a wide margin. `prestige
  score` penalizes weak verbs (submit/click here/go) and CTA competition.
- **Headline hook**: address the reader ("you/your"), make one clear promise in
  ≤12 words, add specificity (a number/outcome). The audit scores this precisely.

## Judge mobile strictly (trust breaks here first)

Mobile is where the Horn Effect strikes fastest. `prestige score` runs a strict
mobile judge: responsive viewport meta, real breakpoints, ≥44px thumb-friendly
tap targets, no fixed widths >480px, ≥16px base text (avoids iOS zoom-on-focus),
and suggests a sticky bottom CTA to keep the primary action in the thumb zone.

## Score precisely, then fix by priority

`prestige score <file> --workflow <key>` returns a **conversion-readiness score
(0–100, A–F)** fusing the five laws + bias suite + CTA/hook verification +
mobile judge, weighted by the chosen workflow — plus **recommendations ranked
by conversion impact**. Fix from the top down. Treat a failing score like a
failing test.

## Judge purpose fit, not just polish

Use `prestige purposes` to list deterministic purpose lenses, then audit with
`prestige purpose <file> --purpose <key>`. Current lenses:

- `developer`: concrete proof, docs, CLI/API clarity, GitHub/demo trust.
- `healthcare`: calm reassurance, privacy, clinician proof, no miracle hype.
- `fintech`: security, transparent fees/rates, control, compliance cues.
- `luxury`: restraint, craft, whitespace, fewer louder elements.
- `marketplace`: bilateral buyer/seller trust, reviews, protection, comparison.
- `saas`: product visibility, integrations, ROI, low-friction activation.
- `editorial`: narrative rhythm, sources, evidence, satisfying end beat.

Purpose-fit scores intent clarity, proof fit, visual theme, action language, and
anti-patterns. A beautiful healthcare page with aggressive scarcity, or a
developer page with no docs/GitHub/demo proof, should fail even if it looks
polished.

## The Non-Negotiable Warning
**Never let aesthetics mask a MAJOR functional flaw.** A beautiful UI buys
tolerance for *minor* imperfections, but a broken checkout, an unusable mobile
layout, or an inaccessible primary action will shatter the illusion and destroy
retention. If you must choose, fix the function first. The `prestige audit`
linter fails hard on major functional/accessibility flaws for exactly this
reason — it will not let a pretty page ship over a broken primary action.

## Reference material
See `references/` for the detailed playbooks: `trust-engineering.md`,
`peak-end.md`, `cognitive-fluency.md`, `hero-halo.md`, and the
`premium-template.html` starting scaffold.
