# Autumn AI - Complete Setup Guide

## Overview
Autumn AI is an autonomous AI agent powered by Llama 3, self-learning capabilities, persistent memory, and skill ingestion. It runs as a web interface using Gradio.

## Prerequisites
- Python 3.8+
- Ollama with llama3 and nomic-embed-text models installed
- 8GB+ RAM recommended

## Setup Instructions

### 1. Install Ollama
First, ensure Ollama is installed and running:
```bash
# Install from https://ollama.ai or your package manager
ollama pull llama3:latest
ollama pull nomic-embed-text
```

### 2. Install Python Dependencies
```bash
cd /workspaces/Autumn_Ai/ai-brain
pip install -r requirements.txt
```

### 3. Run the Application
```bash
cd /workspaces/Autumn_Ai/ai-brain
python ui.py
```

The application will start on `http://0.0.0.0:7861`

## Features

### 1. Chat Interface
- Ask the AI anything and get responses
- Conversation history is maintained
- Thinking process is logged and displayed

### 2. Persistent Memory
- Important conversations are automatically saved to memory
- The AI recalls relevant past conversations
- Builds a user profile over time

### 3. Skill Ingestion
- Upload files (.md, .txt, .csv, .json, .py) to teach the AI new skills
- Provide GitHub URLs for the AI to learn from code repositories
- Point to Kaggle datasets for data analysis skills
- Skills are automatically created and used by the AI

### 4. Built-in Tools
- **run_python**: Execute Python code
- **calculator**: Evaluate math expressions
- **write_file**: Create/save files to workspace
- **read_file**: Read files from workspace
- **web_search**: Search the web using DuckDuckGo
- **list_files**: List workspace files
- **create_skill**: Create new reusable skills
- **use_skill**: Execute existing skills
- **show_skills**: List all learned skills
- **remove_skill**: Delete skills

## File Structure
```
ai-brain/
├── brain.py              # Core AI agent logic
├── memory.py             # Memory and recall system
├── ui.py                 # Gradio web interface
├── tools.py              # Built-in tools and utilities
├── skills.py             # Skill management system
├── skill_ingestion.py    # File/URL ingestion and skill synthesis
├── requirements.txt      # Python dependencies
├── skills/               # Directory for learned skills
└── memory_db/            # Persistent memory database (Chroma)
```

## Troubleshooting

### Issue: "AI doesn't respond"
1. Check Ollama is running: `ollama list`
2. Verify models are installed: `ollama show llama3:latest`
3. Check terminal for error messages

### Issue: "Memory not working"
1. Ensure `memory_db` directory exists and is writable
2. Check file permissions: `ls -la memory_db/`

### Issue: "Skills not loading"
1. Check `skills` directory exists: `ls -la skills/`
2. Look for error messages in the thinking log

### Issue: "Gradio interface not loading"
1. Check port 7861 is not in use: `lsof -i :7861`
2. Try a different port by editing ui.py line 310: change `server_port=7861`

## Advanced Configuration

### Change Ollama Model
Edit `brain.py` and `memory.py`:
```python
llm = OllamaLLM(model="mistral:latest")  # Use any available Ollama model
```

### Adjust Planning Behavior
Edit `brain.py`:
- `MAX_ITERATIONS = 8` - Maximum tool use iterations
- `use_planning=True` - Enable/disable automated planning

### Change Memory Threshold
Edit `memory.py`:
- `IMPORTANCE_THRESHOLD = 4` - Only save memories with score >= 4

## Usage Examples

### Chat
```
User: What's the capital of France?
AI: The capital of France is Paris... [detailed response]
```

### Teach a Skill
1. Click "📥 Teach me a skill"
2. Upload a Python file with a `run(args: str) -> str` function
3. The AI will automatically learn and use it

### Create a Skill Dynamically
```
User: create a skill that checks if a number is prime
AI: [creates and tests a prime-checking skill]
```

## Performance Tips
- Keep conversation history under 50 messages for faster responses
- Use the "Enable planning layer" toggle to control complexity
- Monitor memory size: large memory databases slow recall
- Delete unused skills to reduce context size

## API Reference

### Think Function
```python
from brain import think

response = think(
    user_input="Your question",
    history=[{"role": "user", "content": "..."}, ...],
    use_planning=True
)
```

### Memory Functions
```python
from memory import save_memory, recall_memory

recall_memory("query string", k=4)  # Get 4 relevant memories
save_memory("user input", "ai response", force=True)  # Force save
```

## Contributing
To modify or extend the AI:
1. Edit relevant Python files
2. Ensure syntax is correct: `python -m py_compile file.py`
3. Test changes by running ui.py
4. Check thinking log for errors

---

**Happy coding with Autumn AI!** 🤖✨
