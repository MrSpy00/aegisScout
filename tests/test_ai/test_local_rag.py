import pytest
from pathlib import Path
from aegisScout.ai.local_rag import chunk_text, build_tfidf_index, search_knowledge_base, INDEX_FILE


def test_chunk_text():
    text = "Hello world! This is a simple test text that we want to chunk into smaller pieces."
    chunks = chunk_text(text, chunk_size=20, overlap=5)
    assert len(chunks) > 1
    assert "Hello world!" in chunks[0]


def test_pure_python_tfidf():
    chunks = [
        {"id": 0, "content": "Web design and development services with fast load times.", "file_name": "test1.txt"},
        {"id": 1, "content": "SEO audit and keyword optimization strategy for Google search ranking.", "file_name": "test2.txt"}
    ]
    index = build_tfidf_index(chunks)
    assert "web" in index["idf"]
    assert "seo" in index["idf"]
    assert len(index["doc_vectors"]) == 2
    # Ensure idf values are reasonable
    assert index["idf"]["web"] > 0
    assert index["idf"]["seo"] > 0
