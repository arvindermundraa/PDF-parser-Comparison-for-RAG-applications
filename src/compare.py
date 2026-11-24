"""Run every available extractor on one PDF and write a results table."""
from __future__ import annotations

import json
import platform
from datetime import date
from pathlib import Path

from .common import ExtractionResult, ExtractorUnavailable, save_text

METHODS = ["pymupdf", "docling", "unstructured", "ollama_vision", "tamus_vision"]
LOCAL_METHODS = ["pymupdf", "docling", "unstructured", "ollama_vision"]


def run_method(method: str, pdf_path: Path, max_pages: int | None = None) -> ExtractionResult:
    if method == "pymupdf":
        from .extractors.pymupdf_extraction import extract
        return extract(pdf_path)
    if method == "docling":
        from .extractors.docling_extraction import extract
        return extract(pdf_path)
    if method == "unstructured":
        from .extractors.unstructured_extraction import extract
        return extract(pdf_path)
    if method == "ollama_vision":
        from .extractors.ollama_vision_extraction import extract
        return extract(pdf_path, max_pages=max_pages)
    if method == "tamus_vision":
        from .extractors.tamus_extraction import extract
        return extract(pdf_path, max_pages=max_pages)
    raise ValueError(f"unknown method: {method}")


def fmt(value) -> str:
    return "n/a" if value is None else f"{value:,}"


def results_markdown(pdf_name: str, rows: list[dict], skipped: dict[str, str]) -> str:
    lines = [
        "# Extraction comparison", "",
        f"PDF: `{pdf_name}`  ", f"Date: {date.today().isoformat()}  ",
        f"Machine: {platform.system()} {platform.machine()}, Python {platform.python_version()}", "",
        "| method | time (s) | pages | characters | words | tables | images | notes |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for r in rows:
        lines.append(f"| {r['method']} | {r['seconds']:.1f} | {r['pages']} | {fmt(r['characters'])} | "
                     f"{fmt(r['words'])} | {fmt(r['tables'])} | {fmt(r['images'])} | {r['notes']} |")
    for method, reason in skipped.items():
        lines.append(f"| {method} | not run | | | | | | {reason} |")
    lines += ["", "`n/a`: the method does not report that count in the mode used."]
    return "\n".join(lines) + "\n"


def compare(pdf_path: Path, methods: list[str], out_dir: Path = Path("outputs"),
            max_pages: int | None = None) -> tuple[list[dict], dict[str, str]]:
    rows, skipped = [], {}
    for method in methods:
        print(f"[{method}] running...", flush=True)
        try:
            result = run_method(method, pdf_path, max_pages)
        except ExtractorUnavailable as e:
            skipped[method] = str(e)
            print(f"[{method}] skipped: {e}")
            continue
        save_text(result, out_dir)
        rows.append(result.summary())
        print(f"[{method}] {result.seconds:.1f}s, {result.characters:,} characters")
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "results.json").write_text(json.dumps({"pdf": pdf_path.name, "results": rows,
                                                      "skipped": skipped}, indent=2))
    (out_dir / "results.md").write_text(results_markdown(pdf_path.name, rows, skipped))
    return rows, skipped
