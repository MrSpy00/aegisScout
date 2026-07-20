import os
import re
import json
import math
from pathlib import Path
from typing import List, Dict, Optional, Any
from aegisScout.core.config import get_settings
from aegisScout.utils.logger import get_logger

logger = get_logger("ai.local_rag")

KB_DIR = Path("data/knowledge_base")
INDEX_FILE = Path("data/kb_vectors.json")


def _get_kb_dir() -> Path:
    KB_DIR.mkdir(parents=True, exist_ok=True)
    return KB_DIR


def _clean_text(text: str) -> str:
    # Remove excessive whitespace
    return re.sub(r"\s+", " ", text).strip()


def chunk_text(text: str, chunk_size: int = 600, overlap: int = 100) -> List[str]:
    text = _clean_text(text)
    if len(text) <= chunk_size:
        return [text]
    
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        start += chunk_size - overlap
    return chunks


def parse_pdf(file_path: Path) -> str:
    try:
        import pypdf
        reader = pypdf.PdfReader(str(file_path))
        text = ""
        for page in reader.pages:
            t = page.extract_text()
            if t:
                text += t + "\n"
        return text
    except ImportError:
        logger.warning("pypdf library not found. Skipping PDF parsing. Install with `pip install pypdf`.")
        return ""
    except Exception as e:
        logger.error(f"Error parsing PDF {file_path}: {e}")
        return ""


def get_all_kb_files() -> List[Path]:
    kb_dir = _get_kb_dir()
    files = []
    for ext in ("*.txt", "*.md", "*.pdf"):
        files.extend(list(kb_dir.glob(ext)))
    return files


# ---------------------------------------------------------------------------
# Simple Pure-Python TF-IDF Engine
# ---------------------------------------------------------------------------

def tokenize(text: str) -> List[str]:
    # Clean, lowercase and split into words
    return re.findall(r"\w+", text.lower())


def build_tfidf_index(chunks: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Builds a pure-Python TF-IDF index for the given chunks.
    """
    num_docs = len(chunks)
    if num_docs == 0:
        return {"idf": {}, "doc_vectors": []}

    # Document frequency
    df: Dict[str, int] = {}
    doc_tokens: List[List[str]] = []
    
    for chunk in chunks:
        tokens = tokenize(chunk["content"])
        doc_tokens.append(tokens)
        unique_tokens = set(tokens)
        for token in unique_tokens:
            df[token] = df.get(token, 0) + 1

    # Inverse document frequency
    idf: Dict[str, float] = {}
    for token, freq in df.items():
        idf[token] = math.log((1 + num_docs) / (1 + freq)) + 1.0

    # Doc vectors (TF-IDF weighted)
    doc_vectors = []
    for i, chunk in enumerate(chunks):
        tokens = doc_tokens[i]
        if not tokens:
            doc_vectors.append({})
            continue
            
        tf: Dict[str, float] = {}
        for token in tokens:
            tf[token] = tf.get(token, 0) + 1.0
            
        # Normalize term frequencies
        max_tf = max(tf.values())
        tfidf_vec = {}
        for token, count in tf.items():
            normalized_tf = count / max_tf
            tfidf_vec[token] = normalized_tf * idf[token]
            
        doc_vectors.append(tfidf_vec)

    return {"idf": idf, "doc_vectors": doc_vectors}


def tfidf_cosine_similarity(vec1: Dict[str, float], vec2: Dict[str, float]) -> float:
    intersection = set(vec1.keys()) & set(vec2.keys())
    if not intersection:
        return 0.0
        
    dot_product = sum(vec1[x] * vec2[x] for x in intersection)
    
    sum1 = sum(val ** 2 for val in vec1.values())
    sum2 = sum(val ** 2 for val in vec2.values())
    
    if sum1 == 0.0 or sum2 == 0.0:
        return 0.0
        
    return dot_product / (math.sqrt(sum1) * math.sqrt(sum2))


# ---------------------------------------------------------------------------
# API Embeddings lookup
# ---------------------------------------------------------------------------

def get_ollama_embedding(text: str, base_url: str, model: str) -> Optional[List[float]]:
    try:
        import httpx
        url = f"{base_url.rstrip('/')}/api/embeddings"
        resp = httpx.post(url, json={"model": model, "prompt": text}, timeout=10.0)
        if resp.status_code == 200:
            return resp.json().get("embedding")
    except Exception as e:
        logger.debug(f"Ollama embedding lookup failed: {e}")
    return None


def get_gemini_embedding(text: str, api_key: str) -> Optional[List[float]]:
    try:
        import httpx
        url = f"https://generativelanguage.googleapis.com/v1beta/models/text-embedding-004:embedContent?key={api_key}"
        payload = {
            "model": "models/text-embedding-004",
            "content": {"parts": [{"text": text}]}
        }
        resp = httpx.post(url, json=payload, timeout=10.0)
        if resp.status_code == 200:
            return resp.json().get("embedding", {}).get("values")
    except Exception as e:
        logger.debug(f"Gemini embedding lookup failed: {e}")
    return None


def get_vector_cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
    if len(vec1) != len(vec2) or not vec1:
        return 0.0
    dot_product = sum(a * b for a, b in zip(vec1, vec2))
    norm_a = math.sqrt(sum(a * a for a in vec1))
    norm_b = math.sqrt(sum(b * b for b in vec2))
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0
    return dot_product / (norm_a * norm_b)


# ---------------------------------------------------------------------------
# Core RAG functions
# ---------------------------------------------------------------------------

def index_knowledge_base() -> Dict[str, Any]:
    """
    Reads files from data/knowledge_base/, chunks them, calculates embeddings
    (or prepares TF-IDF weights) and saves the index to data/kb_vectors.json.
    """
    files = get_all_kb_files()
    logger.info(f"Indexing knowledge base. Found {len(files)} files.")
    
    chunks = []
    chunk_id_counter = 0
    
    for file_path in files:
        ext = file_path.suffix.lower()
        content = ""
        if ext in (".txt", ".md"):
            try:
                content = file_path.read_text(encoding="utf-8")
            except Exception as e:
                logger.error(f"Error reading text file {file_path}: {e}")
        elif ext == ".pdf":
            content = parse_pdf(file_path)
            
        if not content.strip():
            continue
            
        file_chunks = chunk_text(content)
        for chunk in file_chunks:
            chunks.append({
                "id": chunk_id_counter,
                "file_name": file_path.name,
                "content": chunk,
                "embedding": None
            })
            chunk_id_counter += 1

    if not chunks:
        # Write empty index
        INDEX_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(INDEX_FILE, "w", encoding="utf-8") as f:
            json.dump({"chunks": [], "tfidf": {}}, f, ensure_ascii=False, indent=2)
        return {"success": True, "files_indexed": 0, "chunks_indexed": 0}

    # Try to calculate API embeddings
    settings = get_settings()
    has_embeddings = False
    
    # 1. Check Ollama
    if settings.llm_primary_provider == "ollama" or settings.ollama_base_url:
        logger.info("Attempting to calculate embeddings using Ollama...")
        # Check if Ollama is responsive
        for chunk in chunks:
            emb = get_ollama_embedding(chunk["content"], settings.ollama_base_url, settings.ollama_model)
            if emb:
                chunk["embedding"] = emb
                has_embeddings = True
            else:
                break  # Failover to next
                
    # 2. Check Gemini
    if not has_embeddings and settings.gemini_api_key:
        logger.info("Attempting to calculate embeddings using Gemini...")
        for chunk in chunks:
            emb = get_gemini_embedding(chunk["content"], settings.gemini_api_key)
            if emb:
                chunk["embedding"] = emb
                has_embeddings = True
            else:
                break

    # Build backup/offline TF-IDF weights anyway
    logger.info("Building TF-IDF index for search...")
    tfidf_data = build_tfidf_index(chunks)

    # Save to disk
    INDEX_FILE.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "has_embeddings": has_embeddings,
        "chunks": chunks,
        "tfidf": tfidf_data
    }
    with open(INDEX_FILE, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    logger.info(f"Indexing complete. Indexed {len(files)} files, {len(chunks)} chunks. Embeddings calculated: {has_embeddings}")
    return {
        "success": True, 
        "files_indexed": len(files), 
        "chunks_indexed": len(chunks),
        "has_embeddings": has_embeddings
    }


def search_knowledge_base(query: str, top_k: int = 2) -> List[Dict[str, Any]]:
    """
    Search the indexed knowledge base using the most suitable similarity model.
    """
    if not INDEX_FILE.exists():
        return []
        
    try:
        with open(INDEX_FILE, "r", encoding="utf-8") as f:
            index = json.load(f)
    except Exception as e:
        logger.error(f"Failed to read index file: {e}")
        return []

    chunks = index.get("chunks", [])
    if not chunks:
        return []

    has_embeddings = index.get("has_embeddings", False)
    settings = get_settings()
    
    # Try embedding search if embeddings exist and model matches
    if has_embeddings:
        query_emb = None
        # Try Ollama query embedding
        if settings.llm_primary_provider == "ollama" or settings.ollama_base_url:
            query_emb = get_ollama_embedding(query, settings.ollama_base_url, settings.ollama_model)
        # Try Gemini query embedding
        if not query_emb and settings.gemini_api_key:
            query_emb = get_gemini_embedding(query, settings.gemini_api_key)
            
        if query_emb:
            scored_chunks = []
            for chunk in chunks:
                chunk_emb = chunk.get("embedding")
                if chunk_emb:
                    sim = get_vector_cosine_similarity(query_emb, chunk_emb)
                    scored_chunks.append((sim, chunk))
            
            scored_chunks.sort(key=lambda x: x[0], reverse=True)
            return [x[1] for x in scored_chunks[:top_k]]

    # Fall back to TF-IDF cosine similarity search
    logger.info("Executing TF-IDF search fallback...")
    tfidf_data = index.get("tfidf", {})
    idf = tfidf_data.get("idf", {})
    doc_vectors = tfidf_data.get("doc_vectors", [])
    
    if not idf or not doc_vectors:
        return []
        
    # Build query TF-IDF vector
    query_tokens = tokenize(query)
    if not query_tokens:
        return []
        
    query_tf = {}
    for token in query_tokens:
        query_tf[token] = query_tf.get(token, 0) + 1.0
        
    max_tf = max(query_tf.values())
    query_vector = {}
    for token, count in query_tf.items():
        if token in idf:
            query_vector[token] = (count / max_tf) * idf[token]

    scored_chunks = []
    for i, chunk in enumerate(chunks):
        if i < len(doc_vectors):
            doc_vec = doc_vectors[i]
            sim = tfidf_cosine_similarity(query_vector, doc_vec)
            scored_chunks.append((sim, chunk))

    scored_chunks.sort(key=lambda x: x[0], reverse=True)
    return [x[1] for x in scored_chunks[:top_k] if x[0] > 0.0]
