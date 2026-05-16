import os
import asyncio
import logging
import chromadb
from chromadb.utils import embedding_functions
from livekit.agents import function_tool
from pypdf import PdfReader
import docx
import pandas as pd

logger = logging.getLogger(__name__)

DESKTOP_DOCS = os.path.join(os.path.expanduser("~"), "Desktop", "Jarvis Documents")
SYSTEM_DOCS = os.path.join(os.path.expanduser("~"), "Documents")
DB_PATH = os.path.join(os.path.dirname(__file__), "jarvis_memory_db")
os.makedirs(DESKTOP_DOCS, exist_ok=True)

_client = chromadb.PersistentClient(path=DB_PATH)
_ef = embedding_functions.DefaultEmbeddingFunction()
_collection = _client.get_or_create_collection(
    name="jarvis_knowledge_base",
    embedding_function=_ef,
    metadata={"hnsw:space": "cosine"},
)

def chunk_text(text, max_chars=1500, overlap=200):
    chunks = []
    start = 0
    while start < len(text):
        end = min(start + max_chars, len(text))
        chunks.append(text[start:end])
        if end == len(text):
            break
        start += max_chars - overlap
    return chunks

def extract_pdf_text(filepath):
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

def extract_docx_text(filepath):
    text = ""
    try:
        doc = docx.Document(filepath)
        for para in doc.paragraphs:
            text += para.text + "\n"
    except Exception as e:
        logger.error(f"Error reading Docx {filepath}: {e}")
    return text

def extract_excel_text(filepath):
    text = ""
    try:
        if filepath.endswith(".csv"):
            df = pd.read_csv(filepath)
        else:
            df = pd.read_excel(filepath)
        text = df.to_string()
    except Exception as e:
        logger.error(f"Error reading Excel/CSV {filepath}: {e}")
    return text

def get_file_content(filepath):
    ext = os.path.splitext(filepath)[1].lower()
    if ext == ".pdf":
        return extract_pdf_text(filepath)
    elif ext == ".docx":
        return extract_docx_text(filepath)
    elif ext in [".xlsx", ".xls", ".csv"]:
        return extract_excel_text(filepath)
    elif ext in [".txt", ".md"]:
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()
    return ""

@function_tool
async def index_documents() -> str:
    """Indexes documents from Desktop 'Jarvis Documents' and System 'Documents' folders."""
    global _collection
    try:
        targets = [DESKTOP_DOCS, SYSTEM_DOCS]
        indexed_count = 0
        try:
            _client.delete_collection("jarvis_knowledge_base")
        except:
            pass
        _collection = _client.get_or_create_collection(
            name="jarvis_knowledge_base",
            embedding_function=_ef,
            metadata={"hnsw:space": "cosine"},
        )
        for folder in targets:
            if not os.path.exists(folder):
                continue
            for root, dirs, files in os.walk(folder):
                for file in files:
                    if file.startswith("~$"): continue
                    ext = os.path.splitext(file)[1].lower()
                    if ext in [".pdf", ".docx", ".xlsx", ".xls", ".csv", ".txt"]:
                        path = os.path.join(root, file)
                        content = get_file_content(path)
                        if content.strip():
                            chunks = chunk_text(content)
                            ids = [f"{file}_{i}" for i in range(len(chunks))]
                            metadatas = [{"filename": file, "path": path, "source": folder} for _ in chunks]
                            def _add():
                                _collection.add(documents=chunks, ids=ids, metadatas=metadatas)
                            await asyncio.to_thread(_add)
                            indexed_count += 1
        return f"Indexing complete. Processed {indexed_count} documents."
    except Exception as e:
        logger.exception(f"Indexing error: {e}")
        return f"Indexing error: {e}"

@function_tool
async def search_documents(query: str) -> str:
    """Searches indexed documents for the given query."""
    try:
        count = _collection.count()
        if count == 0:
            return "Knowledge base is empty. Please run index_documents first."
        def _query():
            return _collection.query(query_texts=[query], n_results=5)
        results = await asyncio.to_thread(_query)
        docs = results.get("documents", [[]])[0]
        metas = results.get("metadatas", [[]])[0]
        if not docs:
            return "No relevant documents found."
        response = "Search results:\n\n"
        seen_files = {}
        for doc, meta in zip(docs, metas):
            fname = meta.get("filename", "Unknown")
            if fname not in seen_files:
                seen_files[fname] = []
            seen_files[fname].append(doc)
        for filename, snippets in seen_files.items():
            response += f"📄 **File: {filename}**\n"
            for snippet in snippets:
                clean_snippet = snippet.strip().replace("\n", " ")[:300]
                response += f"- ...{clean_snippet}...\n"
            response += "\n"
        return response.strip()
    except Exception as e:
        logger.exception(f"Search error: {e}")
        return f"Search error: {e}"