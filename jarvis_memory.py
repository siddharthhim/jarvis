import os
import uuid
import asyncio
import logging
from datetime import datetime
import chromadb
from chromadb.utils import embedding_functions
from livekit.agents import function_tool

logger = logging.getLogger(__name__)

# FIX: memory DB is now in its own directory, not shared with the docs DB
_DB_PATH            = os.path.join(os.path.dirname(__file__), "jarvis_memory_db")
_TRANSCRIPT_LOG_PATH = os.path.join(os.path.dirname(__file__), "jarvis_transcripts.log")

_client = chromadb.PersistentClient(path=_DB_PATH)
_ef     = embedding_functions.DefaultEmbeddingFunction()
_collection = _client.get_or_create_collection(
    name="jarvis_memories",
    embedding_function=_ef,
    metadata={"hnsw:space": "cosine"},
)

logger.info(f"Jarvis Memory: ChromaDB loaded. Memories: {_collection.count()}")


@function_tool
async def store_memory(content: str) -> str:
    """
    Stores a piece of information or user preference in Jarvis's long-term vector memory.
    Use when the user says 'remember that...', 'note this down', 'don't forget...',
    or shares a preference/fact they want Jarvis to retain across sessions.

    Args:
        content (str): The memory or fact to store.
    """
    try:
        timestamp = datetime.now().isoformat()
        # FIX: use uuid4 instead of timestamp string — collision-proof
        memory_id = f"mem_{uuid.uuid4().hex}"

        def _add():
            _collection.add(
                documents=[content],
                ids=[memory_id],
                metadatas=[{"timestamp": timestamp}],
            )

        await asyncio.to_thread(_add)
        logger.info(f"Memory stored [{memory_id}]: {content[:60]}")
        return "✅ याद रख लिया Sir! Memory save हो गई।"

    except Exception as e:
        logger.exception(f"Memory store error: {e}")
        return f"❌ Memory save नहीं हो पाई, Sir: {e}"


@function_tool
async def recall_memory(query: str) -> str:
    """
    Searches Jarvis's long-term memory for relevant past information or preferences.
    Use when the user asks 'do you remember...', 'what do you know about my...',
    or when context from past sessions is needed.

    Args:
        query (str): Topic or question to search memories for.
    """
    try:
        count = _collection.count()
        if count == 0:
            return "🧠 Sir, अभी कोई memory save नहीं है। पहले कुछ याद करवाएं।"

        def _query():
            return _collection.query(
                query_texts=[query],
                n_results=min(3, count),
            )

        results = await asyncio.to_thread(_query)
        docs  = results.get("documents", [[]])[0]
        metas = results.get("metadatas", [[]])[0]

        if not docs:
            return "🧠 Sir, इस topic के बारे में कोई memory नहीं मिली।"

        output = "🧠 मुझे याद है Sir:\n"
        for i, (doc, meta) in enumerate(zip(docs, metas), 1):
            ts = meta.get("timestamp", "Unknown time")
            output += f"{i}. {doc}\n   (Saved: {ts[:10]})\n"

        return output.strip()

    except Exception as e:
        logger.exception(f"Memory recall error: {e}")
        return f"❌ Memory recall नहीं हो पाई, Sir: {e}"


async def inject_relevant_memories(query: str) -> str:
    """
    Helper for V4 — call this before each LLM turn to proactively inject
    relevant memories into the system prompt context.

    Returns a formatted string to prepend to the system message, or empty string.
    """
    try:
        count = _collection.count()
        if count == 0:
            return ""

        def _query():
            return _collection.query(
                query_texts=[query],
                n_results=min(2, count),
                where=None,
            )

        results = await asyncio.to_thread(_query)
        docs = results.get("documents", [[]])[0]
        if not docs:
            return ""

        context = "Relevant memories from past sessions:\n"
        for doc in docs:
            context += f"- {doc}\n"
        return context.strip()

    except Exception:
        return ""


def log_transcript(transcript: str, speaker: str = "User"):
    """Background hook to log conversation transcripts."""
    try:
        timestamp  = datetime.now().isoformat()
        clean_text = " ".join(str(transcript).splitlines()).strip()
        line       = f"{timestamp}\t{speaker}\t{clean_text}\n"

        def _append_log():
            with open(_TRANSCRIPT_LOG_PATH, "a", encoding="utf-8") as f:
                f.write(line)

        try:
            loop = asyncio.get_running_loop()
            loop.create_task(asyncio.to_thread(_append_log))
        except RuntimeError:
            _append_log()

    except Exception as e:
        logger.exception(f"Transcript log error: {e}")
