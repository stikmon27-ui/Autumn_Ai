# Autumn_Ai

An autonomous AI agent powered by Llama 3 with self-learning capabilities, persistent memory, and skill ingestion.

## ⚡ Quick Start

```bash
# 1. Install dependencies
cd ai-brain
pip install -r requirements.txt

# 2. Start Ollama (in another terminal)
ollama serve

# 3. Run the app
python ui.py

# 4. Open browser
# http://0.0.0.0:7861
```

**See [QUICKSTART.md](QUICKSTART.md) for detailed setup instructions.**

## ✨ Features

- 🤖 **AI Chat** - Talk to Llama 3 powered by Ollama
- 🧩 **Skill Ingestion** - Teach AI from files, GitHub, and Kaggle
- 💾 **Persistent Memory** - Auto-save important conversations
- 🛠️ **Built-in Tools** - Python execution, web search, file management
- 🎨 **Beautiful UI** - Modern Gradio interface

## 📚 Documentation

- [QUICKSTART.md](QUICKSTART.md) - Get running in 5 minutes
- [SETUP.md](SETUP.md) - Complete setup and troubleshooting guide
- [FIXES.md](FIXES.md) - Detailed explanation of all bug fixes

## 🔧 All Issues Fixed

✅ Undefined prompt variables - Fixed
✅ Memory system errors - Fixed  
✅ Gradio interface issues - Fixed
✅ Missing dependencies - Added
✅ CSS styling - Fixed

The application is now fully functional and ready to use!

## 📁 Project Structure

```
ai-brain/
├── brain.py              # Core AI agent
├── memory.py             # Memory system
├── ui.py                 # Gradio interface
├── tools.py              # Built-in tools
├── skills.py             # Skill management
├── skill_ingestion.py    # File/URL learning
├── requirements.txt      # Dependencies
├── skills/               # Learned skills
└── memory_db/            # Persistent memory
```

## 🚀 Ready to Use!

All critical issues have been fixed. Run the validation script to confirm:

```bash
python validate.py
```

Then start the app and begin chatting! 🎉
