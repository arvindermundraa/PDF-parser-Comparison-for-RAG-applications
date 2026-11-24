# Changelog

## 2026-11-24
- Every command takes `--pdf`; without it the first PDF in `input/` is used. Hard-coded file
  paths are gone.
- Sample document is now NIST AI 100-1, fetched by `scripts/download_sample.py`. The research
  paper used during development was removed because it is copyrighted.
- All extractors return the same `ExtractionResult`, so `compare` can build one table.
- New `evaluate` command: retrieval hit@k and MRR per extractor on 12 questions.
- New `ask` command: retrieval with an optional answer from Ollama or the TAMU AI API.
- TAMU AI is optional. With no key the method is skipped and nothing else is affected.
- The vision methods render pages with PyMuPDF, so poppler is no longer required for them.
- `requirements.txt` rewritten and tested on a clean Python 3.12 environment;
  `requirements-dev.txt` holds the small set that tests and CI need.
- Added 26 unit tests and a GitHub Actions workflow.
- Removed generated outputs, temporary images, editor settings and `.env` from the repository.
- Replaced `IMPLEMENTATION_COMPLETE.md` and `OLLAMA_ISSUE_SUMMARY.md` with this file.

## 2026-01
- Reorganized into `src/extractors` and `src/rag` with a single `main.py` entry point.
- Added standalone TAMU AI extraction and Ollama vision extraction.
- Known issue from this period: the Ollama vision model caused GPU (Metal) errors on some Macs,
  so that extractor was kept out of the "run all" command. It is still opt-in today: `compare`
  includes it only when an Ollama server is running.

## 2025-12
- First version: page images sent to a hosted vision model, LangChain + FAISS retrieval,
  comparison against Docling, PyMuPDF and Unstructured.
