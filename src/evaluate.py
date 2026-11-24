"""Retrieval check: does each extractor's text let the retriever find the right passage?

Each question lists phrases that must all appear in one retrieved chunk for it to count as a hit.
The question set (eval/questions.json) was written for the NIST AI 100-1 sample PDF.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

QUESTIONS_PATH = Path(__file__).resolve().parents[1] / "eval" / "questions.json"


def normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text).lower()


def is_hit(chunk: str, expect: list[str]) -> bool:
    flat = normalize(chunk)
    return all(normalize(phrase) in flat for phrase in expect)


def first_hit_rank(chunks: list[str], expect: list[str]) -> int | None:
    """1-based rank of the first chunk containing every expected phrase."""
    for rank, chunk in enumerate(chunks, start=1):
        if is_hit(chunk, expect):
            return rank
    return None


def score(ranks: list[int | None], ks=(1, 3, 5)) -> dict:
    n = len(ranks)
    out = {f"hit@{k}": round(sum(1 for r in ranks if r and r <= k) / n, 3) for k in ks}
    out["mrr"] = round(sum(1 / r for r in ranks if r) / n, 3)
    return out


def evaluate_text(text: str, questions: list[dict], k: int = 5) -> dict:
    from .rag.pipeline import Retriever, chunk_text

    chunks = chunk_text(text)
    retriever = Retriever(chunks)
    ranks = [first_hit_rank([c for _, c in retriever.search(q["question"], k)], q["expect"])
             for q in questions]
    answerable = sum(1 for q in questions if any(is_hit(c, q["expect"]) for c in chunks))
    return {"chunks": len(chunks), "answerable": answerable, "questions": len(questions),
            **score(ranks), "ranks": ranks}


def evaluation_markdown(rows: dict[str, dict]) -> str:
    lines = ["## Retrieval check", "",
             "| method | chunks | answer present in a chunk | hit@1 | hit@3 | hit@5 | MRR |",
             "|---|---|---|---|---|---|---|"]
    for method, r in rows.items():
        lines.append(f"| {method} | {r['chunks']} | {r['answerable']}/{r['questions']} | "
                     f"{r['hit@1']:.3f} | {r['hit@3']:.3f} | {r['hit@5']:.3f} | {r['mrr']:.3f} |")
    return "\n".join(lines) + "\n"


def load_questions(path: Path = QUESTIONS_PATH) -> list[dict]:
    return json.loads(Path(path).read_text())
