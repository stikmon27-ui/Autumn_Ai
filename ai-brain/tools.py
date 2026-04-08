# tools.py
from __future__ import annotations
import ast
import operator
import subprocess
import sys
import textwrap
from pathlib import Path

try:
    from duckduckgo_search import DDGS
    DDG_AVAILABLE = True
except ImportError:
    DDG_AVAILABLE = False

from skills import save_skill, run_skill, list_skills, delete_skill, load_all_skills

SAFE_DIR = Path("./workspace").resolve()
SAFE_DIR.mkdir(exist_ok=True)
MAX_OUTPUT_CHARS = 3_000

def _safe_path(filename):
    resolved = (SAFE_DIR / filename).resolve()
    if not resolved.is_relative_to(SAFE_DIR):
        raise ValueError(f"Path '{filename}' is outside the workspace.")
    return resolved

def _truncate(text, label="Output"):
    if len(text) > MAX_OUTPUT_CHARS:
        return f"{text[:MAX_OUTPUT_CHARS]}\n[{label} truncated]"
    return text

_OPS = {
    ast.Add: operator.add, ast.Sub: operator.sub,
    ast.Mult: operator.mul, ast.Div: operator.truediv,
    ast.Pow: operator.pow, ast.Mod: operator.mod,
    ast.FloorDiv: operator.floordiv,
    ast.USub: operator.neg, ast.UAdd: operator.pos,
}

def _safe_eval(node):
    if isinstance(node, ast.Expression): return _safe_eval(node.body)
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)): return node.value
    if isinstance(node, ast.BinOp):
        fn = _OPS.get(type(node.op))
        if not fn: raise TypeError("Operator not allowed.")
        return fn(_safe_eval(node.left), _safe_eval(node.right))
    if isinstance(node, ast.UnaryOp):
        fn = _OPS.get(type(node.op))
        if not fn: raise TypeError("Operator not allowed.")
        return fn(_safe_eval(node.operand))
    raise TypeError(f"Unsupported: '{type(node).__name__}'.")

def run_python(code):
    code = textwrap.dedent(code).strip()
    if not code: return "No code provided."
    try:
        proc = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, timeout=10)
        out = proc.stdout + (f"\n[stderr]\n{proc.stderr}" if proc.stderr else "")
        return _truncate(out.strip() or "(no output)")
    except subprocess.TimeoutExpired: return "Error: timed out."
    except Exception as e: return f"Error: {e}"

def calculator(expression):
    expression = expression.strip()
    if not expression: return "No expression."
    try:
        result = _safe_eval(ast.parse(expression, mode="eval"))
        if isinstance(result, float) and result.is_integer(): result = int(result)
        return str(result)
    except ZeroDivisionError: return "Division by zero."
    except (TypeError, ValueError) as e: return f"Error: {e}"
    except SyntaxError: return "Invalid expression."

def write_file(args):
    if "|" not in args: return "Error: use '<filename>|<content>'."
    filename, content = args.split("|", 1)
    filename = filename.strip()
    if not filename: return "Error: empty filename."
    try:
        path = _safe_path(filename)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)
        return f"Written '{filename}' ({len(content)} chars)."
    except Exception as e: return f"Error: {e}"

def read_file(filename):
    filename = filename.strip()
    if not filename: return "Error: empty filename."
    try:
        path = _safe_path(filename)
        if not path.exists(): return f"'{filename}' not found."
        return _truncate(path.read_text())
    except Exception as e: return f"Error: {e}"

def web_search(query):
    query = query.strip()
    if not query: return "No query."
    if not DDG_AVAILABLE: return "Install duckduckgo-search."
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=5))
        if not results: return f"No results for '{query}'."
        lines = [f"Results for '{query}':\n"]
        for i, r in enumerate(results, 1):
            lines.append(f"{i}. {r['title']}\n   {r['href']}\n   {r['body']}\n")
        return _truncate("\n".join(lines))
    except Exception as e: return f"Error: {e}"

def list_files(_args=""):
    try:
        files = [f for f in sorted(SAFE_DIR.rglob("*")) if f.is_file()]
        if not files: return "Workspace empty."
        lines = ["Workspace:"]
        for f in files:
            lines.append(f"  {f.relative_to(SAFE_DIR)} ({f.stat().st_size}B)")
        return "\n".join(lines)
    except Exception as e: return f"Error: {e}"

def create_skill(args):
    if "|" not in args: return "Error: use '<n>|<python code with def run(args)->str>'."
    name, code = args.split("|", 1)
    return save_skill(name.strip(), code.strip())

def use_skill(args): return run_skill(args)
def show_skills(_args=""): return list_skills()
def remove_skill(name): return delete_skill(name)

TOOLS = {
    "run_python":   run_python,
    "calculator":   calculator,
    "write_file":   write_file,
    "read_file":    read_file,
    "web_search":   web_search,
    "list_files":   list_files,
    "create_skill": create_skill,
    "use_skill":    use_skill,
    "show_skills":  show_skills,
    "remove_skill": remove_skill,
}

TOOL_DESCRIPTIONS = {
    "run_python":   "Execute Python code.",
    "calculator":   "Evaluate math expression.",
    "write_file":   "Write file. Args: '<filename>|<content>'.",
    "read_file":    "Read file. Args: filename.",
    "web_search":   "Search the web. Args: query.",
    "list_files":   "List workspace files.",
    "create_skill": "Create reusable skill. Args: '<n>|<code with def run(args)->str>'.",
    "use_skill":    "Run a skill. Args: '<skill_name> <args>'.",
    "show_skills":  "List all learned skills.",
    "remove_skill": "Delete a skill. Args: name.",
}
