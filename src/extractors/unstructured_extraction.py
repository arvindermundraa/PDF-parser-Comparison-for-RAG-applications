"""Unstructured: partitions a PDF into typed elements (Title, NarrativeText, Table, ...)."""
from __future__ import annotations

import time
from collections import Counter
from pathlib import Path

from ..common import ExtractionResult, ExtractorUnavailable


def extract(pdf_path: Path, strategy: str = "fast") -> ExtractionResult:
    """strategy: "fast" (text layer only) or "hi_res" (layout model; needs poppler + tesseract)."""
    try:
        from unstructured.partition.pdf import partition_pdf
    except ImportError as e:
        raise ExtractorUnavailable(
            'unstructured is not installed (pip install "unstructured[pdf]")') from e

    start = time.perf_counter()
    kwargs = {"infer_table_structure": True} if strategy == "hi_res" else {}
    elements = partition_pdf(filename=str(pdf_path), strategy=strategy, **kwargs)
    seconds = time.perf_counter() - start

    kinds = Counter(type(e).__name__ for e in elements)
    parts, page = [], None
    for e in elements:
        number = getattr(e.metadata, "page_number", None)
        if number != page:
            page = number
            parts.append(f"\n--- PAGE {page} ---\n")
        html = getattr(e.metadata, "text_as_html", None)
        parts.append(f"[{type(e).__name__}] {html or e.text}")
    pages = max((getattr(e.metadata, "page_number", 0) or 0) for e in elements) if elements else 0
    return ExtractionResult(
        "unstructured", "\n".join(parts), seconds, pages,
        tables=kinds.get("Table", 0) if strategy == "hi_res" else None,
        images=kinds.get("Image", 0) if strategy == "hi_res" else None,
        notes=f"strategy={strategy}, {len(elements)} elements",
        extra={"element_types": dict(kinds)},
    )
