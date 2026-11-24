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

def install(root: Path, agent: str, *, skill: str = "prestige-design") -> list[Path]:
    root = Path(root)
    created = []
    key = {"claude-code":"claude"}.get(agent, agent)
    if skill == "app-habit-engineer":
        return _install_habit(root, key)
    if skill != "prestige-design":
        raise ValueError("Unknown Prestige skill")
    text = skill_text()
    for rel in TARGETS.get(key, ["AGENTS.md"]):
        dst = root / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        if dst.name == "AGENTS.md" and dst.exists():
            dst.write_text(dst.read_text().rstrip()+"\n\n"+text)
        else:
            dst.write_text(text)
        created.append(dst)
    return created


def _install_habit(root: Path, agent: str) -> list[Path]:
    relative = {
        "codex": ".agents/skills/app-habit-engineer/SKILL.md",
        "claude": ".claude/skills/app-habit-engineer/SKILL.md",
        "opencode": ".opencode/skills/app-habit-engineer/SKILL.md",
        "cursor": ".cursor/rules/app-habit-engineer.md",
    }.get(agent, "SKILL-app-habit-engineer.md")
    source = Path(__file__).parent / "skills/app-habit-engineer/SKILL.md"
    destination = root / relative
    if not destination.resolve().is_relative_to(root.resolve()):
        raise ValueError("Skill destination leaves the workspace")
    data = source.read_bytes()
    destination.parent.mkdir(parents=True, exist_ok=True)
    try:
        with destination.open("xb") as output:
            output.write(data)
    except FileExistsError:
        if destination.read_bytes() != data:
            raise ValueError("Habit skill already exists with local changes") from None
    return [destination]
