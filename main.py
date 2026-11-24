#!/usr/bin/env python3
"""PDF parser comparison for RAG.

  python main.py extract --method pymupdf        # one extractor -> outputs/extracted_<method>.txt
  python main.py compare                         # all available extractors -> outputs/results.md
  python main.py evaluate                        # retrieval hit rate per extractor (sample PDF)
  python main.py ask "What is the AI RMF Core?"  # retrieve (and answer, if an LLM is reachable)
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from dotenv import load_dotenv

from src.common import ExtractorUnavailable, find_pdf, save_text
from src.compare import LOCAL_METHODS, METHODS, compare, run_method


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("extract", help="run one extractor")
    p.add_argument("--method", choices=METHODS, default="pymupdf")
    p.add_argument("--pdf", help="PDF path (default: first PDF in input/)")
    p.add_argument("--max-pages", type=int, help="page limit for the vision methods")

    p = sub.add_parser("compare", help="run all available extractors and write a results table")
    p.add_argument("--pdf")
    p.add_argument("--methods", nargs="+", choices=METHODS, default=LOCAL_METHODS)
    p.add_argument("--max-pages", type=int)

    p = sub.add_parser("evaluate", help="retrieval hit rate per extractor, using eval/questions.json")
    p.add_argument("--pdf")
    p.add_argument("--methods", nargs="+", choices=METHODS, default=["pymupdf", "docling", "unstructured"])

    p = sub.add_parser("ask", help="answer a question from the PDF with retrieval")
    p.add_argument("question")
    p.add_argument("--pdf")
    p.add_argument("--method", choices=METHODS, default="pymupdf", help="extractor that feeds retrieval")
    p.add_argument("-k", type=int, default=3)
    return parser


def main(argv: list[str] | None = None) -> int:
    load_dotenv()
    args = build_parser().parse_args(argv)
    try:
        pdf = find_pdf(args.pdf)
    except FileNotFoundError as e:
        print(e, file=sys.stderr)
        return 2

    if args.command == "extract":
        try:
            result = run_method(args.method, pdf, args.max_pages)
        except ExtractorUnavailable as e:
            print(f"{args.method} cannot run here: {e}", file=sys.stderr)
            return 1
        path = save_text(result)
        print(f"{result.method}: {result.pages} pages, {result.characters:,} characters, "
              f"{result.seconds:.1f}s -> {path}")

    elif args.command == "compare":
        compare(pdf, args.methods, max_pages=args.max_pages)
        print("\n" + Path("outputs/results.md").read_text())

    elif args.command == "evaluate":
        from src.evaluate import evaluate_text, evaluation_markdown, load_questions

        # Extract with every method first, then load the embedding model and FAISS once.
        # (Running Docling's models after FAISS is loaded crashes on macOS: two OpenMP runtimes.)
        questions, texts, rows = load_questions(), {}, {}
        for method in args.methods:
            try:
                texts[method] = run_method(method, pdf).text
            except ExtractorUnavailable as e:
                print(f"{method} skipped: {e}", file=sys.stderr)
        for method, text in texts.items():
            rows[method] = evaluate_text(text, questions)
        table = evaluation_markdown(rows)
        Path("outputs").mkdir(exist_ok=True)
        Path("outputs/retrieval.md").write_text(table)
        Path("outputs/retrieval.json").write_text(json.dumps(rows, indent=2))
        print(table)

    elif args.command == "ask":
        from src.rag.pipeline import Retriever, answer, chunk_text, pick_llm

        text = run_method(args.method, pdf).text
        retriever = Retriever(chunk_text(text))
        name, llm = pick_llm()
        out = answer(retriever, args.question, llm, args.k)
        if llm:
            print(f"Answer ({name}): {out['answer']}\n")
        else:
            print("No LLM reachable (start Ollama to get a written answer). Top passages:\n")
        for i, passage in enumerate(out["passages"], start=1):
            print(f"[{i}] score {passage['score']}: {passage['text'][:300].strip()}...\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
