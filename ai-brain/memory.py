# memory.py
from __future__ import annotations
from datetime import datetime
from langchain_chroma import Chroma
from langchain_ollama import OllamaEmbeddings, OllamaLLM

embeddings = OllamaEmbeddings(model="nomic-embed-text")
db         = Chroma(persist_directory="./memory_db", embedding_function=embeddings)
llm       = OllamaLLM(model="llama3:latest")

IMPORTANCE_THRESHOLD = 4


def _score_importance(user_input: str, ai_response: str) -> int:
    prompt = f"""Rate how important this exchange is to remember (0-10).
0 = forgettable small talk, 10 = critical fact or decision.
Reply with ONLY a single integer.

User: {user_input[:300]}
AI:   {ai_response[:300]}

Score:"""
    try:
        for token in llm.invoke(prompt).strip().split():
            if token.isdigit():
                return min(10, max(0, int(token)))
    except Exception:
        pass
    return 5


def _summarise(user_input: str, ai_response: str) -> str:
    prompt = f"""Summarise this exchange in ONE concise sentence for memory storage.

User: {user_input[:400]}
AI:   {ai_response[:400]}

Summary:"""
    try:
        return llm.invoke(prompt).strip()
    except Exception:
        return f"User asked: {user_input[:100]}"


def save_memory(user_input: str, ai_response: str, force: bool = False) -> None:
    user_input  = user_input.strip()
    ai_response = ai_response.strip()
    if not user_input or not ai_response:
        return

    if not force:
        score = _score_importance(user_input, ai_response)
        print(f"💡 Importance: {score}/10")
        if score < IMPORTANCE_THRESHOLD:
            print(f"   → Skipping (below threshold {IMPORTANCE_THRESHOLD})")
            return

    summary  = _summarise(user_input, ai_response)
    metadata = {
        "user":      user_input[:500],
        "ai":        ai_response[:500],
        "timestamp": datetime.now().isoformat(),
        "summary":   summary,
    }
    try:
        db.add_texts([summary], metadatas=[metadata])
        print(f"💾 Saved: {summary[:80]}")
    except Exception as e:
        print(f"❌ Memory save failed: {e}")


def recall_memory(query: str, k: int = 4) -> list[str]:
    query = query.strip()
    if not query:
        return []
    try:
        count = db._collection.count()
    except Exception:
        count = 0
    if count == 0:
        return []
    try:
        results = db.similarity_search(query, k=min(k, count))
        return [r.page_content for r in results]
    except Exception as e:
        print(f"❌ Memory recall failed: {e}")
        return []


def get_user_profile() -> str:
    try:
        count = db._collection.count()
        if count == 0:
            return "No profile yet."
        summaries = db.get().get("documents", [])[:30]
        if not summaries:
            return "No profile yet."
        prompt = f"""Write a brief user profile (3-5 bullet points) from these memory summaries.
Focus on preferences, recurring topics, and key facts.

Memories:
{chr(10).join(f'- {s}' for s in summaries)}

Profile:"""
        return llm.invoke(prompt).strip()
    except Exception as e:
        return f"(Profile unavailable: {e})"
