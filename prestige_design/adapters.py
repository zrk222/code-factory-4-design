"""Install this skill into any coding agent. The SKILL.md is the contract;
each agent reads it from a different location."""
from __future__ import annotations
from pathlib import Path

def skill_text() -> str:
    return (Path(__file__).resolve().parent/"SKILL.md").read_text()

TARGETS = {
    "claude":   [".claude/skills/prestige-design/SKILL.md"],
    "codex":    ["AGENTS.md"],           # appended, not overwritten
    "opencode": [".opencode/skills/prestige-design.md"],
    "cursor":   [".cursor/rules/prestige-design.md"],
    "generic":  ["SKILL-prestige-design.md"],
}

def install(root: Path, agent: str) -> list[Path]:
    root = Path(root); created = []
    key = {"claude-code":"claude"}.get(agent, agent)
    text = skill_text()
    for rel in TARGETS.get(key, ["AGENTS.md"]):
        dst = root/rel; dst.parent.mkdir(parents=True, exist_ok=True)
        if dst.name == "AGENTS.md" and dst.exists():
            dst.write_text(dst.read_text().rstrip()+"\n\n"+text)
        else:
            dst.write_text(text)
        created.append(dst)
    return created
