# skills.py
"""
Autonomous skill system.

Skills live in ./skills/ as .py files.
The AI reads skill descriptions automatically and decides when to apply them —
the user never has to say "use skill X".

Every skill file must define:
    def run(args: str) -> str

Header comments (parsed for metadata):
    # skill: <name>
    # description: <when and why the AI should use this automatically>
    # args: <what args contains>
"""
from __future__ import annotations
import importlib.util
import traceback
from pathlib import Path

SKILLS_DIR = Path("./skills").resolve()
SKILLS_DIR.mkdir(exist_ok=True)

_SKILL_REGISTRY: dict[str, callable] = {}
_SKILL_META:     dict[str, dict]     = {}


# ---------------------------------------------------------------------------
# Header parsing
# ---------------------------------------------------------------------------

def _parse_header(source: str) -> dict:
    meta = {"name": "", "description": "No description.", "args": "No args info."}
    for line in source.splitlines():
        line = line.strip()
        if not line.startswith("#"):
            break
        for key in ("name", "description", "args"):
            prefix = f"# {key}:"
            if line.lower().startswith(prefix):
                meta[key] = line[len(prefix):].strip()
    return meta


# ---------------------------------------------------------------------------
# Load / reload
# ---------------------------------------------------------------------------

def load_skill(path: Path) -> bool:
    try:
        source = path.read_text(encoding="utf-8")
        meta   = _parse_header(source)
        name   = meta["name"] or path.stem

        spec   = importlib.util.spec_from_file_location(f"skill_{name}", path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        if not hasattr(module, "run"):
            print(f"⚠️  Skill '{name}' has no run() — skipped.")
            return False

        _SKILL_REGISTRY[name] = module.run
        _SKILL_META[name]     = {
            "description": meta["description"],
            "args":        meta["args"],
            "path":        str(path),
        }
        print(f"✅ Skill loaded: '{name}'")
        return True
    except Exception as e:
        print(f"❌ Failed to load skill '{path.name}': {e}")
        return False


def load_all_skills() -> None:
    _SKILL_REGISTRY.clear()
    _SKILL_META.clear()
    for path in sorted(SKILLS_DIR.glob("*.py")):
        load_skill(path)


# ---------------------------------------------------------------------------
# Save (AI writes a new skill)
# ---------------------------------------------------------------------------

def save_skill(name: str, code: str) -> str:
    name = name.strip().lower().replace(" ", "_").replace("-", "_")
    if not name:
        return "Error: skill name cannot be empty."

    # Ensure header is present
    if "# skill:" not in code:
        code = f"# skill: {name}\n# description: A learned skill.\n# args: varies\n\n{code}"

    path = SKILLS_DIR / f"{name}.py"
    try:
        path.write_text(code, encoding="utf-8")
        ok = load_skill(path)
        if ok:
            return f"Skill '{name}' saved and active."
        return f"Skill '{name}' saved but failed to load — check the run() function."
    except Exception as e:
        return f"Error saving skill: {e}"


# ---------------------------------------------------------------------------
# Run
# ---------------------------------------------------------------------------

def run_skill(args: str) -> str:
    args = args.strip()
    if not args:
        return "Error: provide '<skill_name> <arguments>'."
    parts      = args.split(" ", 1)
    skill_name = parts[0].strip().lower()
    skill_args = parts[1].strip() if len(parts) > 1 else ""

    if skill_name not in _SKILL_REGISTRY:
        return f"Skill '{skill_name}' not found. Available: {list(_SKILL_REGISTRY.keys())}"
    try:
        return str(_SKILL_REGISTRY[skill_name](skill_args))
    except Exception as e:
        return f"Skill '{skill_name}' error: {e}\n{traceback.format_exc()}"


# ---------------------------------------------------------------------------
# List / delete
# ---------------------------------------------------------------------------

def list_skills(_args: str = "") -> str:
    if not _SKILL_REGISTRY:
        return "No skills loaded yet."
    lines = [f"{len(_SKILL_REGISTRY)} skill(s) available:\n"]
    for name, meta in _SKILL_META.items():
        lines.append(f"• {name}: {meta['description']}")
        lines.append(f"  Args: {meta['args']}\n")
    return "\n".join(lines)


def delete_skill(name: str) -> str:
    name = name.strip().lower()
    if name not in _SKILL_REGISTRY:
        return f"Skill '{name}' not found."
    path = Path(_SKILL_META[name]["path"])
    try:
        path.unlink()
        del _SKILL_REGISTRY[name]
        del _SKILL_META[name]
        return f"Skill '{name}' deleted."
    except Exception as e:
        return f"Error: {e}"


# ---------------------------------------------------------------------------
# Context helpers used by brain.py
# ---------------------------------------------------------------------------

def get_skill_context() -> str:
    """
    Returns a rich context block injected into every brain prompt.
    The AI reads this and autonomously decides when skills are relevant.
    """
    if not _SKILL_REGISTRY:
        return "No skills loaded yet."
    lines = ["LEARNED SKILLS (use these autonomously when relevant):\n"]
    for name, meta in _SKILL_META.items():
        lines.append(f"SKILL:{name}")
        lines.append(f"  When to use: {meta['description']}")
        lines.append(f"  Args format: {meta['args']}")
        lines.append(f"  Invoke with: TOOL:use_skill {name} <args>\n")
    return "\n".join(lines)


def get_skill_descriptions() -> dict[str, str]:
    return {n: m["description"] for n, m in _SKILL_META.items()}


# Auto-load on import
load_all_skills()
