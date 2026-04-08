# Autumn AI - Quick Start Guide

## What Was Fixed

Your Autumn AI application had several critical bugs that prevented it from working:

1. **Undefined `SYSTEM_PROMPT` variable** - In brain.py, it should use `ULTIMATE_HOMIE_PROMPT`
2. **Undefined `SOUL_PROMPT` variable** - This was causing crashes  
3. **Wrong variable name `_llm`** - Should be `llm` in memory.py
4. **CSS not applied** - Fixed Gradio CSS parameter placement
5. **Missing dependencies** - Added `requests` and `langchain-core` to requirements.txt

**All issues are now fixed!** ✅

---

## Getting Started (5 Minutes)

### Step 1: Install Dependencies
```bash
cd Autumn_Ai/ai-brain
pip install -r requirements.txt
```

### Step 2: Start Ollama (in another terminal)
```bash
ollama serve
```

Then in the same terminal, ensure models are ready:
```bash
ollama pull llama3:latest
ollama pull nomic-embed-text
```

### Step 3: Run Autumn AI
```bash
cd Autumn_Ai/ai-brain
python ui.py
```

### Step 4: Open in Browser
Go to: **http://0.0.0.0:7861**

---

## What You Can Do Now

### 💬 Chat with AI
Simply type a message and the AI will respond. For example:
- "Hello, who are you?"
- "What's 2 + 2?"
- "Explain how neural networks work"

### 🧩 Teach New Skills
Click **"📥 Teach me a skill"** to:
- Upload Python files
- Link GitHub repositories
- Share Kaggle datasets

The AI automatically learns and uses new skills!

### 🧠 Persistent Memory
- Your important conversations are automatically saved
- The AI remembers past interactions
- Your profile is built over time

### 🛠️ Built-in Tools
The AI has access to tools like:
- Run Python code
- Search the web
- Work with files
- Create new skills

---

## Troubleshooting

### "Connection refused" or "Cannot connect to Ollama"
→ Make sure `ollama serve` is running in another terminal

### "ModuleNotFoundError"
→ Run: `pip install -r requirements.txt`

### "No response from AI"
→ Check the Thinking Log tab for error messages
→ Verify Ollama models are installed: `ollama list`

### "Port 7861 already in use"
→ Edit `ui.py` line 310, change `server_port=7861` to another port like `7862`

---

## Next Steps

1. **Explore the interface** - Test different questions and tasks
2. **Teach a skill** - Upload a file to give the AI new capabilities
3. **Check memory** - See what the AI remembers about you
4. **Read documentation** - See `SETUP.md` for detailed info

---

## Files Modified

✅ **brain.py** - Fixed undefined prompt variables
✅ **memory.py** - Fixed variable name errors  
✅ **ui.py** - Fixed CSS parameter placement
✅ **requirements.txt** - Added missing dependencies

## Documentation Added

📄 **SETUP.md** - Complete setup and usage guide
📄 **FIXES.md** - Detailed explanation of all fixes
✅ **validate.py** - Automatic validation script

---

**You're all set!** 🚀 Autumn AI is now ready to use.

For advanced configuration, see `SETUP.md`.
