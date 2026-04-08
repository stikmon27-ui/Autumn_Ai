# ui.py
from __future__ import annotations
import sys
import threading
from pathlib import Path

import gradio as gr

from brain import think
from memory import recall_memory, get_user_profile, db
from tools import SAFE_DIR, TOOL_DESCRIPTIONS
from skills import list_skills, SKILLS_DIR, _SKILL_META, load_all_skills
from skill_ingestion import ingest_file, ingest_url

# ---------------------------------------------------------------------------
# Log capture
# ---------------------------------------------------------------------------

class _LogCapture:
    def __init__(self):
        self._lines = []
        self._lock  = threading.Lock()
    def write(self, text):
        if text.strip():
            with self._lock:
                self._lines.append(text.rstrip())
    def flush(self): pass
    def drain(self):
        with self._lock:
            out = "\n".join(self._lines)
            self._lines.clear()
            return out

_log = _LogCapture()

# ---------------------------------------------------------------------------
# Panel helpers
# ---------------------------------------------------------------------------

def _memory_panel():
    try:
        count = db._collection.count()
        if count == 0:
            return "*No memories yet.*"
        docs      = db.get()
        summaries = docs.get("documents", [])[-10:]
        metas     = docs.get("metadatas", [])[-10:]
        lines     = [f"**{count} memories**\n"]
        for s, m in zip(summaries, metas):
            ts = (m.get("timestamp", "")[:16] if m else "")
            lines.append(f"`{ts}` {s}")
        return "\n\n".join(lines)
    except Exception as e:
        return f"Error: {e}"

def _workspace_panel():
    try:
        files = sorted(f for f in SAFE_DIR.rglob("*") if f.is_file())
        if not files:
            return "*Workspace empty.*"
        lines = ["**Files:**\n"]
        for f in files:
            lines.append(f"📄 `{f.relative_to(SAFE_DIR)}` — {f.stat().st_size}B")
        return "\n".join(lines)
    except Exception as e:
        return f"Error: {e}"

def _skills_panel():
    load_all_skills()
    try:
        if not _SKILL_META:
            return "*No skills yet. Upload a file or URL to teach me!*"
        lines = [f"**{len(_SKILL_META)} skill(s) loaded:**\n"]
        for name, meta in _SKILL_META.items():
            lines.append(f"### 🧩 `{name}`")
            lines.append(f"**When I use it:** {meta['description']}")
            lines.append(f"**Args:** {meta['args']}\n")
        return "\n".join(lines)
    except Exception as e:
        return f"Error: {e}"

def _profile_panel():
    return get_user_profile()

# ---------------------------------------------------------------------------
# Agent runner
# ---------------------------------------------------------------------------

def run_agent(user_message, chat_pairs, use_planning):
    """
    chat_pairs: list of [user, assistant] pairs (Gradio 6 format)
    We convert to dict format for brain.py internally.
    """
    if not user_message.strip():
        return chat_pairs, "", _memory_panel(), _workspace_panel(), _skills_panel()

    # Convert Gradio pairs -> dict history for brain.py
    history = []
    for pair in chat_pairs:
        if pair[0]: history.append({"role": "user",      "content": pair[0]})
        if pair[1]: history.append({"role": "assistant",  "content": pair[1]})

    old_stdout = sys.stdout
    sys.stdout = _log
    try:
        response = think(user_message, history=history, use_planning=use_planning)
    except Exception as e:
        response = f"Agent error: {e}"
    finally:
        sys.stdout = old_stdout

    log = _log.drain()

    # Append new pair in Gradio format
    chat_pairs = chat_pairs + [[user_message, response]]

    return chat_pairs, log, _memory_panel(), _workspace_panel(), _skills_panel()

# ---------------------------------------------------------------------------
# Skill ingestion
# ---------------------------------------------------------------------------

def handle_file_upload(files):
    if not files:
        return "No files uploaded.", _skills_panel()
    results = []
    old_stdout = sys.stdout
    sys.stdout = _log
    try:
        for file in files:
            path = file.name if hasattr(file, "name") else str(file)
            result = ingest_file(path)
            results.append(result)
    finally:
        sys.stdout = old_stdout
    load_all_skills()
    return "\n\n".join(results), _skills_panel()

def handle_url_ingest(url):
    if not url.strip():
        return "No URL provided.", _skills_panel()
    old_stdout = sys.stdout
    sys.stdout = _log
    try:
        result = ingest_url(url.strip())
    except Exception as e:
        result = f"Error: {e}"
    finally:
        sys.stdout = old_stdout
    load_all_skills()
    return result, _skills_panel()

# ---------------------------------------------------------------------------
# CSS
# ---------------------------------------------------------------------------

CSS = """
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&family=Syne:wght@400;700;800&display=swap');
:root {
    --bg: #0d0f14; --surface: #141720; --border: #1e2230;
    --accent: #00e5ff; --accent2: #7c3aed; --text: #e2e8f0;
    --muted: #64748b; --radius: 10px;
    --mono: 'JetBrains Mono', monospace; --ui: 'Syne', sans-serif;
}
body, .gradio-container { background: var(--bg) !important; font-family: var(--ui) !important; color: var(--text) !important; }
#header { text-align: center; padding: 2rem 0 1.2rem; border-bottom: 1px solid var(--border); margin-bottom: 1.5rem; }
#header h1 { font-size: 2.2rem; font-weight: 800; background: linear-gradient(135deg, var(--accent), var(--accent2)); -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin: 0; }
#header p { color: var(--muted); font-size: 0.85rem; margin-top: 0.4rem; font-family: var(--mono); }
#thinking textarea { background: #080b10 !important; border: 1px solid var(--accent) !important; font-family: var(--mono) !important; font-size: 0.74rem !important; color: #a0ffcc !important; }
#user-input textarea { background: var(--surface) !important; border: 1px solid var(--border) !important; color: var(--text) !important; }
button.primary { background: linear-gradient(135deg, var(--accent2), #4f46e5) !important; border: none !important; color: white !important; font-weight: 700 !important; border-radius: var(--radius) !important; }
button.secondary { background: var(--surface) !important; border: 1px solid var(--border) !important; color: var(--muted) !important; border-radius: var(--radius) !important; }
::-webkit-scrollbar { width: 4px; }
::-webkit-scrollbar-thumb { background: var(--border); border-radius: 2px; }
"""

# ---------------------------------------------------------------------------
# Layout
# ---------------------------------------------------------------------------

with gr.Blocks(title="AI Agent", css=CSS) as demo:
    # State stores Gradio-format pairs: [[user, assistant], ...]
    chat_state = gr.State([])

    gr.HTML("""
    <div id="header">
        <h1>⟡ Autonomous AI Agent</h1>
        <p>Llama 3 · Self-Learning · Persistent Memory · Skill Ingestion</p>
    </div>
    """)

    with gr.Row():
        # Left — chat
        with gr.Column(scale=3):
            chatbot = gr.Chatbot(label="", height=420)

            with gr.Row():
                user_input = gr.Textbox(
                    placeholder="Ask anything, give a task, or say 'create a skill that...'",
                    show_label=False, lines=2, scale=5, elem_id="user-input",
                )
                with gr.Column(scale=1, min_width=120):
                    send_btn  = gr.Button("Send",  variant="primary")
                    clear_btn = gr.Button("Clear", variant="secondary")

            use_planning = gr.Checkbox(label="Enable planning layer", value=True)

            with gr.Accordion("📥 Teach me a skill", open=False):
                gr.Markdown("Upload a file or paste a URL — I'll learn from it automatically.")
                with gr.Tabs():
                    with gr.Tab("📄 Upload File"):
                        gr.Markdown("Supports: `.md` `.txt` `.csv` `.json` `.py`")
                        file_upload   = gr.File(label="Drop files here", file_count="multiple",
                                                file_types=[".md",".txt",".csv",".json",".py"])
                        upload_btn    = gr.Button("Learn from file(s)", variant="primary")
                        upload_status = gr.Markdown("")

                    with gr.Tab("🐙 GitHub URL"):
                        github_url    = gr.Textbox(placeholder="https://github.com/user/repo", show_label=False)
                        github_btn    = gr.Button("Learn from GitHub", variant="primary")
                        github_status = gr.Markdown("")

                    with gr.Tab("📊 Kaggle URL"):
                        kaggle_url    = gr.Textbox(placeholder="https://www.kaggle.com/datasets/...", show_label=False)
                        kaggle_btn    = gr.Button("Learn from Kaggle", variant="primary")
                        kaggle_status = gr.Markdown("")

        # Right — panels
        with gr.Column(scale=2):
            gr.Markdown("**🧠 Thinking Log**")
            thinking_log = gr.Textbox(label="", lines=10, interactive=False,
                                      elem_id="thinking", placeholder="Agent reasoning appears here...")
            with gr.Tabs():
                with gr.Tab("🧩 Skills"):
                    skills_md  = gr.Markdown(value=_skills_panel())
                    refresh_sk = gr.Button("Refresh", variant="secondary", size="sm")
                with gr.Tab("💾 Memory"):
                    memory_md  = gr.Markdown(value=_memory_panel())
                with gr.Tab("📁 Workspace"):
                    ws_md      = gr.Markdown(value=_workspace_panel())
                with gr.Tab("👤 Profile"):
                    profile_md = gr.Markdown("Click refresh.")
                    refresh_pr = gr.Button("Refresh", variant="secondary", size="sm")

    # ── Events ──

    def on_send(msg, pairs, planning):
        updated_pairs, log, mem, wsp, skl = run_agent(msg, pairs, planning)
        return updated_pairs, updated_pairs, log, mem, wsp, skl, ""

    send_btn.click(
        fn=on_send,
        inputs=[user_input, chat_state, use_planning],
        outputs=[chatbot, chat_state, thinking_log, memory_md, ws_md, skills_md, user_input],
    )
    user_input.submit(
        fn=on_send,
        inputs=[user_input, chat_state, use_planning],
        outputs=[chatbot, chat_state, thinking_log, memory_md, ws_md, skills_md, user_input],
    )

    def on_clear():
        return [], [], "", _memory_panel(), _workspace_panel(), _skills_panel()

    clear_btn.click(
        fn=on_clear,
        outputs=[chatbot, chat_state, thinking_log, memory_md, ws_md, skills_md],
    )

    upload_btn.click(fn=handle_file_upload, inputs=[file_upload],
                     outputs=[upload_status, skills_md])
    github_btn.click(fn=handle_url_ingest,  inputs=[github_url],
                     outputs=[github_status, skills_md])
    kaggle_btn.click(fn=handle_url_ingest,  inputs=[kaggle_url],
                     outputs=[kaggle_status, skills_md])

    refresh_sk.click(fn=_skills_panel,  outputs=[skills_md])
    refresh_pr.click(fn=_profile_panel, outputs=[profile_md])

if __name__ == "__main__":
  demo.launch(server_name="0.0.0.0", server_port=7861, share=False)
