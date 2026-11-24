"""PyMuPDF: text blocks in reading order, detected tables as markdown, image count."""
from __future__ import annotations

import time
from pathlib import Path

from ..common import ExtractionResult


def table_to_markdown(rows: list[list]) -> str:
    if not rows:
        return ""
    clean = [[("" if c is None else str(c)).replace("\n", " ").strip() for c in row] for row in rows]
    lines = ["| " + " | ".join(clean[0]) + " |", "| " + " | ".join("---" for _ in clean[0]) + " |"]
    lines += ["| " + " | ".join(row) + " |" for row in clean[1:]]
    return "\n".join(lines)


def extract(pdf_path: Path) -> ExtractionResult:
    import pymupdf

    start = time.perf_counter()
    parts, n_tables, n_images = [], 0, 0
    with pymupdf.open(str(pdf_path)) as doc:
        n_pages = len(doc)
        for number, page in enumerate(doc, start=1):
            parts.append(f"\n--- PAGE {number} ---\n")
            for block in page.get_text("blocks"):
                if block[6] == 0 and block[4].strip():      # type 0 = text block
                    parts.append(block[4].strip() + "\n")
            try:
                for table in page.find_tables().tables:
                    md = table_to_markdown(table.extract())
                    if md:
                        n_tables += 1
                        parts.append("\n[TABLE]\n" + md + "\n")
            except Exception:                               # table finder can fail on odd pages
                pass
            n_images += len(page.get_images(full=True))
    return ExtractionResult("pymupdf", "\n".join(parts), time.perf_counter() - start,
                            n_pages, tables=n_tables, images=n_images)
