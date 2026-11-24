"""Shared pieces for every extractor: the result type, PDF lookup and page rendering."""
from __future__ import annotations

import base64
from dataclasses import asdict, dataclass, field
from pathlib import Path

INPUT_DIR = Path("input")
OUTPUT_DIR = Path("outputs")


@dataclass
class ExtractionResult:
    method: str
    text: str
    seconds: float
    pages: int
    tables: int | None = None   # None means the method does not report tables
    images: int | None = None
    notes: str = ""
    extra: dict = field(default_factory=dict)

    @property
    def characters(self) -> int:
        return len(self.text)

    @property
    def words(self) -> int:
        return len(self.text.split())

    def summary(self) -> dict:
        d = asdict(self)
        d.pop("text")
        d.pop("extra")
        d["characters"] = self.characters
        d["words"] = self.words
        return d


class ExtractorUnavailable(RuntimeError):
    """Raised when a method cannot run here (missing package, server or API key)."""


def find_pdf(pdf: str | None = None, input_dir: Path = INPUT_DIR) -> Path:
    """Return the PDF to process: the given path, or the first PDF in input/."""
    if pdf:
        path = Path(pdf)
        if not path.is_file():
            raise FileNotFoundError(f"PDF not found: {path}")
        return path
    candidates = sorted(Path(input_dir).glob("*.pdf"))
    if not candidates:
        raise FileNotFoundError(
            f"No PDF in {input_dir}/. Run `python scripts/download_sample.py` or pass --pdf PATH."
        )
    return candidates[0]


def save_text(result: ExtractionResult, output_dir: Path = OUTPUT_DIR) -> Path:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / f"extracted_{result.method}.txt"
    path.write_text(result.text, encoding="utf-8")
    return path


def render_pages_png(pdf_path: Path, dpi: int = 110, max_pages: int | None = None) -> list[bytes]:
    """Render pages to PNG bytes with PyMuPDF (no poppler needed)."""
    import pymupdf

    pages = []
    with pymupdf.open(str(pdf_path)) as doc:
        for i, page in enumerate(doc):
            if max_pages is not None and i >= max_pages:
                break
            pages.append(page.get_pixmap(dpi=dpi).tobytes("png"))
    return pages


def b64(data: bytes) -> str:
    return base64.b64encode(data).decode()


VISION_PROMPT = (
    "Extract ALL text from this PDF page image and keep its structure. "
    "Write tables as markdown tables with every number preserved. "
    "Keep paragraphs as paragraphs. For figures, describe them and copy any visible text."
)
