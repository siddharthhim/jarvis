import os
import asyncio
import logging
import hashlib
import json
import chromadb
from chromadb.utils import embedding_functions
from livekit.agents import function_tool
from pypdf import PdfReader
import docx
import pandas as pd

logger = logging.getLogger(__name__)

DESKTOP_DOCS = os.path.join(os.path.expanduser("~"), "Desktop", "Jarvis Documents")
SYSTEM_DOCS  = os.path.join(os.path.expanduser("~"), "Documents")
DB_PATH      = os.path.join(os.path.dirname(__file__), "jarvis_docs_db")   # FIX: separate path from memory DB
INDEX_STATE  = os.path.join(os.path.dirname(__file__), "jarvis_docs_index_state.json")

os.makedirs(DESKTOP_DOCS, exist_ok=True)

_client     = chromadb.PersistentClient(path=DB_PATH)
_ef         = embedding_functions.DefaultEmbeddingFunction()
_collection = _client.get_or_create_collection(
    name="jarvis_knowledge_base",
    embedding_function=_ef,
    metadata={"hnsw:space": "cosine"},
)

# ── Helpers ────────────────────────────────────────────────────────────────

def _file_hash(filepath: str) -> str:
    """MD5 of file content — used to skip unchanged files on re-index."""
    h = hashlib.md5()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _load_index_state() -> dict:
    if os.path.exists(INDEX_STATE):
        with open(INDEX_STATE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def _save_index_state(state: dict):
    with open(INDEX_STATE, "w", encoding="utf-8") as f:
        json.dump(state, f)


def chunk_text(text: str, max_chars: int = 1500, overlap: int = 200) -> list[str]:
    chunks, start = [], 0
    while start < len(text):
        end = min(start + max_chars, len(text))
        chunks.append(text[start:end])
        if end == len(text):
            break
        start += max_chars - overlap
    return chunks


def extract_pdf_text(filepath: str) -> str:
    text = ""
    try:
        reader = PdfReader(filepath)
        for page in reader.pages:
            content = page.extract_text()
            if content:
                text += content + "\n"
    except Exception as e:
        logger.error(f"Error reading PDF {filepath}: {e}")
    return text


def extract_docx_text(filepath: str) -> str:
    text = ""
    try:
        doc = docx.Document(filepath)
        for para in doc.paragraphs:
            text += para.text + "\n"
    except Exception as e:
        logger.error(f"Error reading DOCX {filepath}: {e}")
    return text


def extract_excel_text(filepath: str) -> str:
    text = ""
    try:
        df = pd.read_csv(filepath) if filepath.endswith(".csv") else pd.read_excel(filepath)
        text = df.to_string()
    except Exception as e:
        logger.error(f"Error reading Excel/CSV {filepath}: {e}")
    return text


def get_file_content(filepath: str) -> str:
    ext = os.path.splitext(filepath)[1].lower()
    if ext == ".pdf":
        return extract_pdf_text(filepath)
    elif ext == ".docx":
        return extract_docx_text(filepath)
    elif ext in (".xlsx", ".xls", ".csv"):
        return extract_excel_text(filepath)
    elif ext in (".txt", ".md"):
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()
    return ""


# ── Tools ──────────────────────────────────────────────────────────────────

@function_tool
async def index_documents() -> str:
    """
    Indexes documents from Desktop 'Jarvis Documents' and System 'Documents' folders.
    Skips files that haven't changed since the last index run (incremental).
    """
    global _collection
    try:
        targets = [DESKTOP_DOCS, SYSTEM_DOCS]
        index_state  = _load_index_state()   # FIX: track hashes for incremental updates
        indexed_new  = 0
        skipped      = 0

        for folder in targets:
            if not os.path.exists(folder):
                continue

            for root, _, files in os.walk(folder):
                for file in files:
                    if file.startswith("~$"):
                        continue
                    ext = os.path.splitext(file)[1].lower()
                    if ext not in (".pdf", ".docx", ".xlsx", ".xls", ".csv", ".txt", ".md"):
                        continue

                    path = os.path.join(root, file)
                    try:
                        current_hash = _file_hash(path)
                    except OSError as e:
                        logger.warning(f"Cannot read {path}: {e}")
                        continue

                    # FIX: skip unchanged files — no more full re-index every call
                    if index_state.get(path) == current_hash:
                        skipped += 1
                        continue

                    content = get_file_content(path)
                    if not content.strip():
                        continue

                    chunks = chunk_text(content)

                    # FIX: close over local variables with default args — no closure bug
                    def _make_adder(c, i, m):
                        def _add():
                            _collection.add(documents=c, ids=i, metadatas=m)
                        return _add

                    ids       = [f"{file}_{i}" for i in range(len(chunks))]
                    metadatas = [{"filename": file, "path": path, "source": folder}
                                 for _ in chunks]

                    try:
                        await asyncio.to_thread(_make_adder(chunks, ids, metadatas))
                        index_state[path] = current_hash
                        indexed_new += 1
                    except Exception as e:
                        logger.error(f"Failed to index {file}: {e}")

        _save_index_state(index_state)
        return (
            f"✅ Indexing complete, Sir. "
            f"Newly indexed: {indexed_new} files. Skipped (unchanged): {skipped} files."
        )

    except Exception as e:
        logger.exception(f"Indexing error: {e}")
        return f"❌ Indexing error, Sir: {e}"


@function_tool
async def search_documents(query: str) -> str:
    """
    Searches indexed documents for the given query.

    Args:
        query (str): Natural language search query.
    """
    try:
        count = _collection.count()
        if count == 0:
            return "Sir, knowledge base is empty. Please run index_documents first."

        def _query():
            return _collection.query(query_texts=[query], n_results=min(5, count))

        results = await asyncio.to_thread(_query)
        docs    = results.get("documents", [[]])[0]
        metas   = results.get("metadatas", [[]])[0]

        if not docs:
            return "Sir, no relevant documents found for that query."

        seen_files: dict[str, list[str]] = {}
        for doc, meta in zip(docs, metas):
            fname = meta.get("filename", "Unknown")
            seen_files.setdefault(fname, []).append(doc)

        response = "Search results:\n\n"
        for filename, snippets in seen_files.items():
            response += f"📄 {filename}\n"
            for snippet in snippets:
                clean = snippet.strip().replace("\n", " ")[:300]
                response += f"  ...{clean}...\n"
            response += "\n"

        return response.strip()

    except Exception as e:
        logger.exception(f"Search error: {e}")
        return f"❌ Search error, Sir: {e}"
