import os
import uuid
import asyncio
import logging
from datetime import datetime
from logging.handlers import RotatingFileHandler

from livekit.agents import function_tool

logger = logging.getLogger(__name__)

# ── Paths ──────────────────────────────────────────────────────────────────
_DB_PATH            = os.path.join(os.path.dirname(__file__), "jarvis_memory_db")
_TRANSCRIPT_LOG_PATH = os.path.join(os.path.dirname(__file__), "jarvis_transcripts.log")

# BUG FIX: transcript log now uses a RotatingFileHandler (10 MB, 3 backups)
# to prevent unbounded disk growth. Previously it used plain open("a") forever.
_transcript_logger = logging.getLogger("jarvis.transcripts")
_transcript_logger.setLevel(logging.INFO)
_transcript_logger.propagate = False
_t_handler = RotatingFileHandler(
    _TRANSCRIPT_LOG_PATH,
    maxBytes=10 * 1024 * 1024,  # 10 MB per file
    backupCount=3,
    encoding="utf-8",
)
_t_handler.setFormatter(logging.Formatter("%(message)s"))
_transcript_logger.addHandler(_t_handler)

# ── Lazy ChromaDB initialisation ───────────────────────────────────────────
# BUG FIX: original code initialised _client / _ef / _collection at import
# time, which crashed the whole agent if ChromaDB wasn't installed or the DB
# directory was corrupted. Now everything is initialised on first use inside
# _get_collection(), with a clear error if the dependency is missing.

_collection = None


def _get_collection():
    global _collection
    if _collection is not None:
        return _collection
    try:
        import chromadb
        from chromadb.utils import embedding_functions
        os.makedirs(_DB_PATH, exist_ok=True)
        client = chromadb.PersistentClient(path=_DB_PATH)
        ef = embedding_functions.DefaultEmbeddingFunction()
        _collection = client.get_or_create_collection(
            name="jarvis_memories",
            embedding_function=ef,
            metadata={"hnsw:space": "cosine"},
        )
        logger.info(f"Jarvis Memory: ChromaDB loaded. Memories: {_collection.count()}")
    except ImportError:
        raise RuntimeError(
            "chromadb is not installed. Run: pip install chromadb"
        )
    return _collection


# ── Tools ──────────────────────────────────────────────────────────────────

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
        collection = _get_collection()
        timestamp = datetime.now().isoformat()
        # BUG FIX: original used a timestamp-based ID which could collide
        # within the same millisecond under rapid calls. uuid4 is collision-free.
        memory_id = f"mem_{uuid.uuid4().hex}"

        def _add():
            collection.add(
                documents=[content],
                ids=[memory_id],
                metadatas=[{"timestamp": timestamp}],
            )

        await asyncio.to_thread(_add)
        logger.info(f"Memory stored [{memory_id}]: {content[:60]}")
        return "✅ याद रख लिया Sir! Memory save हो गई।"
    except Exception as e:
        logger.exception(f"Memory store error: {e}")
        return f"❌ Memory save नहीं हो पाई: {e}"


@function_tool
async def recall_memory(query: str, top_k: int = 5) -> str:
    """
    Searches Jarvis's long-term memory for relevant past information or preferences.
    Use when the user asks 'do you remember...', 'what do you know about my...',
    'recall...', or when context from past sessions is needed.

    Args:
        query (str): Topic or question to search memories for.
        top_k (int): Maximum number of results to return (default 5).
    """
    try:
        collection = _get_collection()
        count = collection.count()
        if count == 0:
            return "🧠 Sir, अभी कोई memory save नहीं है। पहले कुछ याद करवाएं।"

        # BUG FIX: original hardcoded n_results=min(3, count), always capping
        # at 3 regardless of how many relevant memories exist. Now uses top_k.
        n = min(top_k, count)

        def _query():
            return collection.query(
                query_texts=[query],
                n_results=n,
            )

        results = await asyncio.to_thread(_query)
        docs  = results.get("documents", [[]])[0]
        metas = results.get("metadatas",  [[]])[0]

        if not docs:
            return "🧠 इस topic के बारे में कोई memory नहीं मिली, Sir।"

        output = "🧠 मुझे याद है Sir:\n"
        for i, (doc, meta) in enumerate(zip(docs, metas), 1):
            ts = meta.get("timestamp", "Unknown time")
            output += f"{i}. {doc}\n   (Saved: {ts[:10]})\n"
        return output.strip()
    except Exception as e:
        logger.exception(f"Memory recall error: {e}")
        return f"❌ Memory recall नहीं हो पाई: {e}"


# ── Transcript logging ─────────────────────────────────────────────────────

def log_transcript(transcript: str, speaker: str = "User"):
    """
    Background hook to log conversation transcripts with automatic rotation.
    BUG FIX: was an unbounded append-only file; now uses RotatingFileHandler.
    """
    try:
        timestamp = datetime.now().isoformat()
        clean_text = " ".join(str(transcript).splitlines()).strip()
        line = f"{timestamp}\t{speaker}\t{clean_text}"

        def _write():
            _transcript_logger.info(line)

        try:
            loop = asyncio.get_running_loop()
            loop.create_task(asyncio.to_thread(_write))
        except RuntimeError:
            _write()
    except Exception as e:
        logger.exception(f"Transcript log error: {e}")
