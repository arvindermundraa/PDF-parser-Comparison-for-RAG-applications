"""Optional: TAMU AI chat API (OpenAI-compatible) as a hosted vision model.

Only Texas A&M users can get a key, so nothing else in the project depends on this method.
"""
from __future__ import annotations

import os
import time
from pathlib import Path

from ..common import VISION_PROMPT, ExtractionResult, ExtractorUnavailable, b64, render_pages_png
from ..rag.tamus_client import get_tamus_client


def extract(pdf_path: Path, max_pages: int | None = None) -> ExtractionResult:
    try:
        client = get_tamus_client()
    except ValueError as e:
        raise ExtractorUnavailable("TAMUS_API_KEY is not set (optional, TAMU users only)") from e
    model = os.getenv("TAMUS_PDF_MODEL", "protected.claude-sonnet-4")

    start = time.perf_counter()
    images = render_pages_png(pdf_path, dpi=150, max_pages=max_pages)
    parts = []
    for number, png in enumerate(images, start=1):
        text = client.chat(model=model, messages=[{"role": "user", "content": [
            {"type": "text", "text": VISION_PROMPT},
            {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64(png)}"}},
        ]}])
        parts.append(f"\n--- PAGE {number} ---\n{text}")
    return ExtractionResult("tamus_vision", "\n".join(parts), time.perf_counter() - start,
                            len(images), notes=f"model={model}")
