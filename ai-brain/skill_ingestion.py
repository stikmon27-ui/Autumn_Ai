# skill_ingestion.py
"""
Skill ingestion pipeline.

Accepts:
  - Uploaded files: .md, .txt, .csv, .py, .json
  - GitHub URLs
  - Kaggle dataset URLs

Workflow:
  1. Extract raw content from the source
  2. Ask the LLM to read it and derive a skill (name, description, code)
  3. Save the skill so the agent uses it autonomously
"""
from __future__ import annotations
import csv
import io
import json
import os
import re
import tempfile
from pathlib import Path

import requests
from langchain_ollama import OllamaLLM

from skills import save_skill, SKILLS_DIR

llm = OllamaLLM(model="llama3:latest")

MAX_CONTENT_CHARS = 6_000   # cap fed to LLM to avoid context overflow


# ---------------------------------------------------------------------------
# Content extractors
# ---------------------------------------------------------------------------

def _extract_text_file(path: str) -> str:
    """Read .txt or .md files."""
    return Path(path).read_text(encoding="utf-8", errors="ignore")


def _extract_csv_file(path: str) -> str:
    """Read CSV and return a text summary + first 20 rows."""
    with open(path, newline="", encoding="utf-8", errors="ignore") as f:
        reader = csv.reader(f)
        rows   = list(reader)
    if not rows:
        return "Empty CSV."
    headers = rows[0]
    sample  = rows[1:21]
    lines   = [f"CSV with {len(rows)-1} rows and {len(headers)} columns.",
               f"Headers: {', '.join(headers)}", "", "First 20 rows:"]
    for row in sample:
        lines.append(str(row))
    return "\n".join(lines)


def _extract_json_file(path: str) -> str:
    """Read JSON and pretty-print a truncated version."""
    raw = Path(path).read_text(encoding="utf-8", errors="ignore")
    try:
        obj  = json.loads(raw)
        text = json.dumps(obj, indent=2)
    except Exception:
        text = raw
    return text


def _extract_py_file(path: str) -> str:
    """Read a Python file directly — used as skill code."""
    return Path(path).read_text(encoding="utf-8", errors="ignore")


def _extract_github_url(url: str) -> str:
    """
    Fetch a GitHub file or README.
    Converts github.com URLs to raw.githubusercontent.com.
    Also handles github.com/<user>/<repo> by fetching the README.
    """
    url = url.strip()

    # Already a raw URL
    if "raw.githubusercontent.com" in url:
        resp = requests.get(url, timeout=15)
        resp.raise_for_status()
        return resp.text

    # Convert blob URL:  github.com/user/repo/blob/branch/file
    url = re.sub(
        r"https?://github\.com/([^/]+)/([^/]+)/blob/(.+)",
        r"https://raw.githubusercontent.com/\1/\2/\3",
        url,
    )

    if "raw.githubusercontent.com" in url:
        resp = requests.get(url, timeout=15)
        resp.raise_for_status()
        return resp.text

    # Bare repo URL — try to fetch README via GitHub API
    m = re.match(r"https?://github\.com/([^/]+)/([^/]+)/?$", url)
    if m:
        user, repo = m.group(1), m.group(2)
        api_url = f"https://api.github.com/repos/{user}/{repo}/readme"
        headers = {"Accept": "application/vnd.github.v3.raw"}
        resp = requests.get(api_url, headers=headers, timeout=15)
        if resp.ok:
            return resp.text
        return f"Could not fetch README for {user}/{repo}: {resp.status_code}"

    # Try fetching as-is
    resp = requests.get(url, timeout=15)
    resp.raise_for_status()
    return resp.text


def _extract_kaggle_url(url: str) -> str:
    """
    Fetch a Kaggle dataset page and extract its description text.
    Note: downloading actual data requires kaggle API credentials.
    We fetch the dataset description from the Kaggle website.
    """
    url = url.strip()
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0 Safari/537.36"
        )
    }
    try:
        resp = requests.get(url, headers=headers, timeout=15)
        resp.raise_for_status()
        # Strip HTML tags crudely
        text = re.sub(r"<[^>]+>", " ", resp.text)
        text = re.sub(r"\s+", " ", text).strip()
        # Find the dataset description section
        match = re.search(r"(About this Dataset.{200,3000})", text, re.DOTALL | re.IGNORECASE)
        if match:
            return match.group(1)
        return text[:MAX_CONTENT_CHARS]
    except Exception as e:
        return f"Could not fetch Kaggle page: {e}"


# ---------------------------------------------------------------------------
# LLM skill synthesis
# ---------------------------------------------------------------------------

SKILL_SYNTHESIS_PROMPT = """You are an AI agent that learns by reading content and turning it into reusable Python skills.

Read the content below and create ONE useful Python skill from it.

Rules:
- The skill must define exactly one function:  def run(args: str) -> str
- The function must return a string result
- Use only the Python standard library (no pip installs)
- The skill should encapsulate the most useful, reusable thing from this content
- If the content is a Python file with a run() function already, adapt it directly
- If the content is data/CSV, create a skill that answers questions about it
- If the content is documentation, create a skill that applies the documented technique

Reply in this EXACT format and nothing else:

SKILL_NAME: <one_word_snake_case_name>
SKILL_DESCRIPTION: <one sentence — what it does and when the AI should use it automatically>
SKILL_ARGS: <what the args string should contain>
SKILL_CODE:
<complete Python code including the run() function>
END_SKILL

Content to learn from:
---
{content}
---
"""


def _synthesise_skill(content: str, source_hint: str = "") -> dict | None:
    """
    Ask the LLM to read content and produce a skill definition.
    Returns dict with keys: name, description, args, code
    """
    content = content[:MAX_CONTENT_CHARS]
    prompt  = SKILL_SYNTHESIS_PROMPT.format(content=content)

    try:
        response = llm.invoke(prompt)
    except Exception as e:
        return {"error": f"LLM error: {e}"}

    # Parse the structured response
    name  = re.search(r"SKILL_NAME:\s*(.+)", response)
    desc  = re.search(r"SKILL_DESCRIPTION:\s*(.+)", response)
    args  = re.search(r"SKILL_ARGS:\s*(.+)", response)
    code  = re.search(r"SKILL_CODE:\n(.*?)END_SKILL", response, re.DOTALL)

    if not all([name, desc, code]):
        return {"error": f"LLM did not return a valid skill format.\nRaw response:\n{response[:500]}"}

    return {
        "name":        name.group(1).strip().lower().replace(" ", "_"),
        "description": desc.group(1).strip() if desc else "A learned skill.",
        "args":        args.group(1).strip() if args else "varies",
        "code":        code.group(1).strip(),
    }


def _build_skill_source(parsed: dict) -> str:
    """Assemble the full skill file content from parsed LLM output."""
    return (
        f"# skill: {parsed['name']}\n"
        f"# description: {parsed['description']}\n"
        f"# args: {parsed['args']}\n\n"
        f"{parsed['code']}\n"
    )


# ---------------------------------------------------------------------------
# Public ingestion API
# ---------------------------------------------------------------------------

def ingest_file(file_path: str) -> str:
    """
    Learn a skill from an uploaded file.
    Supports: .md .txt .csv .json .py
    Returns a status message.
    """
    path = Path(file_path)
    ext  = path.suffix.lower()

    try:
        if ext in (".md", ".txt"):
            content = _extract_text_file(file_path)
        elif ext == ".csv":
            content = _extract_csv_file(file_path)
        elif ext == ".json":
            content = _extract_json_file(file_path)
        elif ext == ".py":
            # Python files might already be valid skills — try direct load first
            content = _extract_py_file(file_path)
            if "def run(" in content:
                dest = SKILLS_DIR / path.name
                dest.write_text(content, encoding="utf-8")
                from skills import load_skill
                ok = load_skill(dest)
                if ok:
                    return f"✅ Python skill '{path.stem}' loaded directly from file."
        else:
            return f"❌ Unsupported file type '{ext}'. Supported: .md .txt .csv .json .py"
    except Exception as e:
        return f"❌ Error reading file: {e}"

    print(f"📖 Read {len(content)} chars from '{path.name}'. Synthesising skill...")
    parsed = _synthesise_skill(content, source_hint=path.name)

    if "error" in parsed:
        return f"❌ Skill synthesis failed: {parsed['error']}"

    skill_source = _build_skill_source(parsed)
    result       = save_skill(parsed["name"], skill_source)
    return f"✅ Learned skill '{parsed['name']}' from '{path.name}'.\n📝 {parsed['description']}\n→ {result}"


def ingest_github(url: str) -> str:
    """
    Learn a skill from a GitHub URL (repo, file, or raw link).
    Returns a status message.
    """
    print(f"🐙 Fetching GitHub: {url}")
    try:
        content = _extract_github_url(url)
    except Exception as e:
        return f"❌ Failed to fetch GitHub URL: {e}"

    if not content.strip():
        return "❌ No content found at that GitHub URL."

    print(f"📖 Got {len(content)} chars. Synthesising skill...")
    parsed = _synthesise_skill(content, source_hint=url)

    if "error" in parsed:
        return f"❌ Skill synthesis failed: {parsed['error']}"

    skill_source = _build_skill_source(parsed)
    result       = save_skill(parsed["name"], skill_source)
    return f"✅ Learned skill '{parsed['name']}' from GitHub.\n📝 {parsed['description']}\n→ {result}"


def ingest_kaggle(url: str) -> str:
    """
    Learn a skill from a Kaggle dataset URL.
    Returns a status message.
    """
    print(f"📊 Fetching Kaggle: {url}")
    try:
        content = _extract_kaggle_url(url)
    except Exception as e:
        return f"❌ Failed to fetch Kaggle page: {e}"

    if not content.strip():
        return "❌ No content found at that Kaggle URL."

    print(f"📖 Got {len(content)} chars. Synthesising skill...")
    parsed = _synthesise_skill(content, source_hint=url)

    if "error" in parsed:
        return f"❌ Skill synthesis failed: {parsed['error']}"

    skill_source = _build_skill_source(parsed)
    result       = save_skill(parsed["name"], skill_source)
    return f"✅ Learned skill '{parsed['name']}' from Kaggle.\n📝 {parsed['description']}\n→ {result}"


def ingest_url(url: str) -> str:
    """
    Auto-detect URL type (GitHub vs Kaggle vs other) and ingest.
    """
    url = url.strip()
    if not url:
        return "❌ No URL provided."
    if "github.com" in url or "raw.githubusercontent.com" in url:
        return ingest_github(url)
    if "kaggle.com" in url:
        return ingest_kaggle(url)
    # Generic URL — try fetching as text
    try:
        resp = requests.get(url, timeout=15)
        resp.raise_for_status()
        content = resp.text[:MAX_CONTENT_CHARS]
        parsed  = _synthesise_skill(content, source_hint=url)
        if "error" in parsed:
            return f"❌ Skill synthesis failed: {parsed['error']}"
        skill_source = _build_skill_source(parsed)
        result       = save_skill(parsed["name"], skill_source)
        return f"✅ Learned skill '{parsed['name']}' from URL.\n📝 {parsed['description']}\n→ {result}"
    except Exception as e:
        return f"❌ Failed to fetch URL: {e}"
