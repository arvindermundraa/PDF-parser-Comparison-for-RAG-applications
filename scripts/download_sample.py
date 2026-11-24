#!/usr/bin/env python3
"""Download the sample PDF: NIST AI 100-1, "Artificial Intelligence Risk Management Framework".

It is a U.S. government publication (not subject to copyright in the United States), 48 pages,
with tables and figures, which makes it a fair test for PDF extraction.
"""
from pathlib import Path

import requests

URL = "https://nvlpubs.nist.gov/nistpubs/ai/NIST.AI.100-1.pdf"
TARGET = Path(__file__).resolve().parents[1] / "input" / "NIST.AI.100-1.pdf"


def main() -> None:
    if TARGET.exists():
        print(f"already present: {TARGET}")
        return
    TARGET.parent.mkdir(exist_ok=True)
    response = requests.get(URL, timeout=120, headers={"User-Agent": "pdf-parser-comparison"})
    response.raise_for_status()
    if not response.content.startswith(b"%PDF"):
        raise SystemExit("download did not return a PDF")
    TARGET.write_bytes(response.content)
    print(f"saved {TARGET} ({len(response.content) / 1e6:.1f} MB)")


if __name__ == "__main__":
    main()
