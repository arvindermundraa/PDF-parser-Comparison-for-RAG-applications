"""RAG over extracted text: chunk -> embed (MiniLM) -> FAISS -> retrieve -> answer.

The answer step uses a local Ollama model when one is running, the TAMU AI API when a key is
set, and otherwise returns the retrieved passages only. Extraction and retrieval never need a key.
"""
from __future__ import annotations

import os
import re

PROMPT = """Answer the question using only the context below. If the context does not contain
the answer, say you don't know. Be brief.

Context:
{context}

Question: {question}
Answer:"""


def chunk_text(text: str, chunk_size: int = 1200, overlap: int = 150) -> list[str]:
    """Split on paragraph boundaries into chunks of about chunk_size characters."""
    if chunk_size <= overlap:
        raise ValueError("chunk_size must be larger than overlap")
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    chunks, current = [], ""
    for p in paragraphs:
        while len(p) > chunk_size:                       # very long paragraph: hard split
            head, p = p[:chunk_size], p[chunk_size - overlap:]
            if current:
                chunks.append(current)
                current = ""
            chunks.append(head)
        if current and len(current) + len(p) + 2 > chunk_size:
            chunks.append(current)
            current = current[-overlap:] if overlap else ""
        current = f"{current}\n\n{p}" if current else p
    if current.strip():
        chunks.append(current)
    return chunks


class Retriever:
    def __init__(self, chunks: list[str], model_name: str | None = None):
        import faiss
        from sentence_transformers import SentenceTransformer

        self.chunks = chunks
        self.model = SentenceTransformer(
            model_name or os.getenv("EMBEDDINGS_MODEL", "sentence-transformers/all-MiniLM-L12-v2"))
        vectors = self.model.encode(chunks, normalize_embeddings=True, show_progress_bar=False)
        self.index = faiss.IndexFlatIP(vectors.shape[1])      # cosine on normalized vectors
        self.index.add(vectors)

    def search(self, question: str, k: int = 3) -> list[tuple[float, str]]:
        q = self.model.encode([question], normalize_embeddings=True, show_progress_bar=False)
        scores, ids = self.index.search(q, min(k, len(self.chunks)))
        return [(float(s), self.chunks[i]) for s, i in zip(scores[0], ids[0]) if i >= 0]


def pick_llm():
    """Return (name, callable(prompt) -> str) or (None, None) when no LLM is reachable."""
    try:
        import ollama

        client = ollama.Client(host=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"))
        client.list()
        model = os.getenv("OLLAMA_MODEL", "llama3.1")
        return f"ollama:{model}", lambda p: client.generate(model=model, prompt=p)["response"]
    except Exception:
        pass
    try:
        from .tamus_client import get_tamus_client

        client = get_tamus_client()
        model = os.getenv("TAMUS_PDF_MODEL", "protected.claude-sonnet-4")
        return f"tamus:{model}", lambda p: client.chat(model, [{"role": "user", "content": p}])
    except ValueError:
        return None, None


def answer(retriever: Retriever, question: str, llm=None, k: int = 3) -> dict:
    hits = retriever.search(question, k)
    out = {"question": question, "passages": [{"score": round(s, 3), "text": t} for s, t in hits]}
    if llm:
        context = "\n\n".join(t for _, t in hits)
        out["answer"] = llm(PROMPT.format(context=context, question=question)).strip()
    return out
