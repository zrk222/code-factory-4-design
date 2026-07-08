"""Five Design-Principle Workflows — selectable 'lenses' the agent designs
through. Each is a complete philosophy with a weighting profile that biases
the audit toward what that style optimizes. This is the '5 variations of great
design principle workflows' — not themes, but distinct optimization strategies."""
from __future__ import annotations
from dataclasses import dataclass, field

@dataclass
class Workflow:
    key: str
    name: str
    philosophy: str
    optimizes_for: str
    weights: dict          # law/bias -> multiplier (biases the composite score)
    directives: list       # concrete build directives the agent follows
    signature_move: str

WORKFLOWS = {
    "conversion": Workflow(
        key="conversion",
        name="The Conversion Architect",
        philosophy="Every pixel earns its place by moving the visitor one step closer to action. Beauty serves the click.",
        optimizes_for="Sign-ups, purchases, lead capture",
        weights={"cta": 2.0, "social_proof": 1.8, "loss_aversion": 1.6, "anchoring": 1.5, "halo": 1.0},
        directives=[
            "One dominant CTA per screen, isolated by color and size (Von Restorff).",
            "Social proof with specific numbers placed adjacent to every primary CTA.",
            "Anchor pricing: show the higher reference price beside the real one.",
            "Genuine scarcity/urgency where true (loss aversion).",
            "Value-led CTA copy — first person, benefit-driven ('Get my free audit').",
        ],
        signature_move="Reduce every page to a single, unmissable next action surrounded by proof."),
    "luxury": Workflow(
        key="luxury",
        name="The Luxury Minimalist",
        philosophy="Confidence is quiet. Extreme whitespace, restraint, and craft signal a brand too premium to shout.",
        optimizes_for="Premium positioning, high-ticket, brand prestige",
        weights={"fluency": 2.0, "halo": 1.8, "horn": 1.6, "peak": 1.4, "cta": 0.8},
        directives=[
            "Extreme whitespace (sections ≥8vw padding) — let everything breathe.",
            "One hero image, museum-grade. Minimal, confident type. No clutter.",
            "Restrained palette (charcoal/dark tones or a single accent).",
            "Micro-interactions subtle and slow — craftsmanship, not flash.",
            "Fewer words, larger type, more silence between elements.",
        ],
        signature_move="Remove until it hurts, then remove one more thing."),
    "trust": Workflow(
        key="trust",
        name="The Trust Engineer",
        philosophy="Dismantle skepticism systematically. Every hesitation point gets a reassurance placed exactly there.",
        optimizes_for="Fintech, healthcare, marketplaces, high-anxiety transactions",
        weights={"trust": 2.2, "social_proof": 1.8, "horn": 1.6, "halo": 1.2, "peak": 1.2},
        directives=[
            "Security cues (padlock, verified, encrypted) beside every data-entry point.",
            "Radical price transparency — total incl. fees/taxes upfront, always.",
            "Guarantees and clear policies visible at the decision point.",
            "Guest checkout; never force account creation.",
            "Dual-blind reviews for marketplaces; specific verified social proof.",
        ],
        signature_move="For every moment of doubt, place the answer within one glance of it."),
    "editorial": Workflow(
        key="editorial",
        name="The Editorial Storyteller",
        philosophy="Guide the eye through a narrative. Rhythm, hierarchy, and pacing turn a page into a story that sells.",
        optimizes_for="Content, brand campaigns, product launches, long-form",
        weights={"fluency": 1.8, "peak": 1.8, "halo": 1.5, "cta": 1.0},
        directives=[
            "Strong typographic hierarchy — a clear reading rhythm top to bottom.",
            "Alternating layout cadence (image-left / image-right) to pace the scroll.",
            "Scroll-triggered reveals as peaks of delight along the narrative.",
            "One idea per section, each building toward the CTA as the story's climax.",
            "Generous line-height and short paragraphs for effortless reading.",
        ],
        signature_move="Structure the page like a story with a beginning, tension, and a resolving CTA."),
    "product": Workflow(
        key="product",
        name="The Product-Led Pragmatist",
        philosophy="Show the product working. Clarity and demonstrated value beat persuasion — let the thing sell itself.",
        optimizes_for="SaaS, apps, tools, developer products",
        weights={"fluency": 1.8, "cta": 1.5, "peak": 1.5, "trust": 1.3, "halo": 1.2},
        directives=[
            "Show the actual UI/product in the hero — a real screenshot or live demo.",
            "Benefit-led headline naming the outcome, not the feature.",
            "Interactive micro-demos or hover states that prove the product works.",
            "Frictionless primary CTA ('Start free — no credit card').",
            "Concrete social proof: usage numbers, logos, specific outcomes.",
        ],
        signature_move="Replace claims with a working demonstration the visitor can see or touch."),
}

def get_workflow(key: str) -> Workflow:
    return WORKFLOWS.get(key, WORKFLOWS["conversion"])

def list_workflows() -> list[dict]:
    return [{"key": w.key, "name": w.name, "optimizes_for": w.optimizes_for,
             "philosophy": w.philosophy, "signature_move": w.signature_move}
            for w in WORKFLOWS.values()]
