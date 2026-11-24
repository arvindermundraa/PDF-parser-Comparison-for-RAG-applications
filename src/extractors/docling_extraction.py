"""Docling: layout model + table structure model, exported as markdown."""
from __future__ import annotations

import time
from pathlib import Path

from ..common import ExtractionResult, ExtractorUnavailable


def extract(pdf_path: Path, ocr: bool = False) -> ExtractionResult:
    try:
        from docling.datamodel.base_models import InputFormat
        from docling.datamodel.pipeline_options import PdfPipelineOptions
        from docling.document_converter import DocumentConverter, PdfFormatOption
    except ImportError as e:
        raise ExtractorUnavailable("docling is not installed (pip install docling)") from e

    options = PdfPipelineOptions()
    options.do_ocr = ocr                    # born-digital PDFs do not need OCR
    options.do_table_structure = True
    converter = DocumentConverter(
        format_options={InputFormat.PDF: PdfFormatOption(pipeline_options=options)}
    )
    start = time.perf_counter()
    doc = converter.convert(str(pdf_path)).document
    text = doc.export_to_markdown()
    seconds = time.perf_counter() - start
    return ExtractionResult("docling", text, seconds, len(doc.pages),
                            tables=len(doc.tables), images=len(doc.pictures),
                            notes="OCR on" if ocr else "OCR off")
