"""Ollama vision model: each page is rendered to an image and transcribed locally."""
from __future__ import annotations

import os
import time
from pathlib import Path

from ..common import VISION_PROMPT, ExtractionResult, ExtractorUnavailable, b64, render_pages_png


def extract(pdf_path: Path, model: str | None = None, max_pages: int | None = None) -> ExtractionResult:
    model = model or os.getenv("OLLAMA_VISION_MODEL", "llama3.2-vision")
    try:
        import ollama
    except ImportError as e:
        raise ExtractorUnavailable("ollama package is not installed (pip install ollama)") from e
    client = ollama.Client(host=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"))
    try:
        client.list()
    except Exception as e:
        raise ExtractorUnavailable("Ollama server is not running (start it with `ollama serve`)") from e

    start = time.perf_counter()
    images = render_pages_png(pdf_path, max_pages=max_pages)
    parts = []
    for number, png in enumerate(images, start=1):
        reply = client.chat(model=model, options={"temperature": 0},
                            messages=[{"role": "user", "content": VISION_PROMPT, "images": [b64(png)]}])
        parts.append(f"\n--- PAGE {number} ---\n{reply['message']['content']}")
    return ExtractionResult("ollama_vision", "\n".join(parts), time.perf_counter() - start,
                            len(images), notes=f"model={model}")
