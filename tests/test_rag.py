import pytest

from src.rag.pipeline import answer, chunk_text
from src.rag.tamus_client import get_tamus_client


def test_chunks_respect_size_and_cover_all_text():
    text = "\n\n".join(f"Paragraph {i} " + "word " * 40 for i in range(12))
    chunks = chunk_text(text, chunk_size=500, overlap=50)
    assert len(chunks) > 1
    assert all(len(c) <= 500 + 50 + 2 for c in chunks)
    for i in range(12):
        assert any(f"Paragraph {i} " in c for c in chunks)


def test_long_paragraph_is_split_with_overlap():
    chunks = chunk_text("x" * 2500, chunk_size=1000, overlap=100)
    assert len(chunks) == 3 and len(chunks[0]) == 1000


def test_chunk_text_empty_and_bad_settings():
    assert chunk_text("  \n\n ") == []
    with pytest.raises(ValueError):
        chunk_text("abc", chunk_size=10, overlap=10)


class FakeRetriever:
    def search(self, question, k=3):
        return [(0.9, "The budget for Q2 was 1850."), (0.2, "Unrelated.")][:k]


def test_answer_without_llm_returns_passages_only():
    out = answer(FakeRetriever(), "What was the Q2 budget?")
    assert "answer" not in out
    assert out["passages"][0] == {"score": 0.9, "text": "The budget for Q2 was 1850."}


def test_answer_passes_retrieved_context_to_the_llm():
    seen = {}

    def llm(prompt):
        seen["prompt"] = prompt
        return " 1850 "

    out = answer(FakeRetriever(), "What was the Q2 budget?", llm, k=1)
    assert out["answer"] == "1850"
    assert "The budget for Q2 was 1850." in seen["prompt"] and "Unrelated." not in seen["prompt"]


def test_tamus_client_needs_a_key_and_builds_the_endpoint(monkeypatch):
    monkeypatch.delenv("TAMUS_API_KEY", raising=False)
    with pytest.raises(ValueError):
        get_tamus_client()
    client = get_tamus_client(api_key="k", api_base="https://example.com/")
    assert client.url == "https://example.com/api/v1/chat/completions"
    assert client.headers["Authorization"] == "Bearer k"


def test_retriever_ranks_the_matching_chunk_first():
    pytest.importorskip("faiss")
    pytest.importorskip("sentence_transformers")
    from src.rag.pipeline import Retriever

    chunks = ["The rocket uses a parachute recovery system.",
              "The club treasurer reported a budget of 1850 dollars.",
              "Meetings are held every Tuesday evening."]
    hits = Retriever(chunks).search("How much money does the club have?", k=2)
    assert hits[0][1] == chunks[1]
