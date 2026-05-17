import os
import uuid
import asyncio
import logging
import logging.handlers
from datetime import datetime, timedelta

import chromadb
from chromadb.utils import embedding_functions
from livekit.agents import function_tool

logger = logging.getLogger(__name__)

# ── ChromaDB persistent client ────────────────────────────────────────────────
_DB_PATH = os.path.join(os.path.dirname(__file__), "jarvis_memory_db")
_TRANSCRIPT_LOG_PATH = os.path.join(os.path.dirname(__file__), "jarvis_transcripts.log")

_client = chromadb.PersistentClient(path=_DB_PATH)
_ef = embedding_functions.DefaultEmbeddingFunction()
_collection = _client.get_or_create_collection(
    name="jarvis_memories",
    embedding_function=_ef,
    metadata={"hnsw:space": "cosine"},
)
logger.info(f"Jarvis Memory: ChromaDB loaded from {_DB_PATH}. Memories: {_collection.count()}")

# ── Rotating transcript logger ────────────────────────────────────────────────
# Max 5MB per file, keeps 3 backups — prevents unbounded log growth
_transcript_handler = logging.handlers.RotatingFileHandler(
    _TRANSCRIPT_LOG_PATH,
    maxBytes=5 * 1024 * 1024,  # 5 MB
    backupCount=3,
    encoding="utf-8",
)
_transcript_logger = logging.getLogger("jarvis_transcript")
_transcript_logger.setLevel(logging.INFO)
_transcript_logger.addHandler(_transcript_handler)
_transcript_logger.propagate = False  # Don't bubble to root logger

# ── Credential masking filter ─────────────────────────────────────────────────
_SENSITIVE_KEYS = {"email_password", "password", "api_key", "token", "secret"}

class _SensitiveFilter(logging.Filter):
    """Redacts known sensitive keys from log records."""
    def filter(self, record: logging.LogRecord) -> bool:
        msg = str(record.getMessage())
        for key in _SENSITIVE_KEYS:
            if key in msg.lower():
                record.msg = "[REDACTED — sensitive data]"
                record.args = ()
        return True

logging.getLogger().addFilter(_SensitiveFilter())


# ── Tools ─────────────────────────────────────────────────────────────────────

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
        # ── Fixed: use uuid4 to avoid duplicate-ID collision on rapid calls ──
        memory_id = f"mem_{uuid.uuid4().hex}"

        def _add():
            _collection.add(
                documents=[content],
                ids=[memory_id],
                metadatas=[{"timestamp": timestamp}],
            )

        await asyncio.to_thread(_add)
        logger.info(f"Memory stored: {content[:60]}")
        return f"✅ याद रख लिया Sir! Memory save हो गई।"
    except Exception as e:
        logger.exception(f"Memory store error: {e}")
        return f"❌ Memory save नहीं हो पाई: {e}"


@function_tool
async def recall_memory(query: str) -> str:
    """
    Searches Jarvis's long-term memory for relevant past information or preferences.
    Use when the user asks 'do you remember...', 'what do you know about my...',
    'recall...', or when context from past sessions is needed.

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
        docs = results.get("documents", [[]])[0]
        metas = results.get("metadatas", [[]])[0]

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


@function_tool
async def forget_memory(keyword: str) -> str:
    """
    Deletes memories matching a keyword from Jarvis's long-term memory.
    Use when the user says 'forget that...', 'delete that memory', or wants to clear
    specific information Jarvis has stored.

    Args:
        keyword (str): Keyword or phrase to match against stored memories for deletion.
    """
    try:
        count = _collection.count()
        if count == 0:
            return "🧠 Sir, कोई memory नहीं है जिसे delete करूं।"

        def _find_and_delete():
            results = _collection.query(
                query_texts=[keyword],
                n_results=min(5, count),
            )
            ids = results.get("ids", [[]])[0]
            docs = results.get("documents", [[]])[0]
            if ids:
                _collection.delete(ids=ids)
            return ids, docs

        ids, docs = await asyncio.to_thread(_find_and_delete)
        if not ids:
            return f"🧠 Sir, '{keyword}' से related कोई memory नहीं मिली।"

        deleted_preview = "\n".join(f"- {d[:80]}" for d in docs)
        logger.info(f"Deleted {len(ids)} memories matching '{keyword}'")
        return f"🗑️ {len(ids)} memories delete कर दी Sir:\n{deleted_preview}"
    except Exception as e:
        logger.exception(f"Memory forget error: {e}")
        return f"❌ Memory delete नहीं हो पाई: {e}"


@function_tool
async def prune_old_memories(days: int = 30) -> str:
    """
    Removes memories older than the specified number of days to keep the memory store lean.
    Use when the user says 'clean up old memories' or 'prune stale data'.

    Args:
        days (int): Delete memories older than this many days. Default is 30.
    """
    try:
        count = _collection.count()
        if count == 0:
            return "🧠 Sir, memory store already empty है।"

        cutoff = (datetime.now() - timedelta(days=days)).isoformat()

        def _prune():
            all_items = _collection.get(include=["metadatas"])
            ids_to_delete = [
                item_id
                for item_id, meta in zip(all_items["ids"], all_items["metadatas"])
                if meta.get("timestamp", "9999") < cutoff
            ]
            if ids_to_delete:
                _collection.delete(ids=ids_to_delete)
            return len(ids_to_delete)

        deleted_count = await asyncio.to_thread(_prune)
        if deleted_count == 0:
            return f"✅ Sir, {days} दिनों से पुरानी कोई memory नहीं मिली।"
        return f"🗑️ {deleted_count} पुरानी memories delete हो गईं Sir ({days}+ days old)।"
    except Exception as e:
        logger.exception(f"Memory prune error: {e}")
        return f"❌ Memory prune नहीं हो पाई: {e}"


def log_transcript(transcript: str, speaker: str = "User"):
    """
    Background hook to log exact transcripts of the conversation.
    Uses a rotating file handler — never grows unbounded.
    """
    try:
        timestamp = datetime.now().isoformat()
        clean_text = " ".join(str(transcript).splitlines()).strip()
        _transcript_logger.info(f"{timestamp}\t{speaker}\t{clean_text}")
    except Exception as e:
        logger.exception(f"Transcript log error: {e}")
