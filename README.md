# PDF Parser Comparison for RAG

Which PDF parser should feed a retrieval-augmented generation (RAG) pipeline? This project runs
several parsers on the same document, measures speed and what each one captures (text, tables,
images), then checks the thing that matters for RAG: can a retriever find the right passage in
each parser's output?

Everything runs locally. No API key is needed for extraction, comparison or retrieval.

## Results

Sample document: NIST AI 100-1, *AI Risk Management Framework* (48 pages, tables and figures,
U.S. government publication). Apple Silicon laptop, CPU only, Python 3.12. Full output:
[`docs/results.md`](docs/results.md).

**Extraction**

| method | time (s) | characters | words | tables | images |
|---|---|---|---|---|---|
| PyMuPDF | 7.3 | 126,205 | 19,184 | 14 | 10 |
| Docling (OCR off) | 44.0 | 144,160 | 16,037 | 13 | 9 |
| Unstructured (`fast`) | 5.4 | 114,839 | 16,916 | n/a | n/a |
| Ollama vision | not run | | | | |

**Retrieval** (12 questions, top-5 chunks from FAISS)

| method | chunks | hit@1 | hit@3 | hit@5 | MRR |
|---|---|---|---|---|---|
| PyMuPDF | 150 | 0.417 | 0.667 | 0.750 | 0.521 |
| Docling | 167 | 0.333 | 0.583 | 0.583 | 0.431 |
| Unstructured (`fast`) | 123 | 0.250 | 0.500 | 0.583 | 0.368 |

What this shows, and what it does not:
- On this born-digital PDF, PyMuPDF was as fast as anything and gave the best retrieval. Docling
  took about 6 times longer; its markdown tables are cleaner to read but did not retrieve better here.
- Unstructured's `fast` strategy reads the text layer only, so it reports no tables or images. Its
  `hi_res` strategy does, but needs poppler and tesseract installed.
- The answer to every question is present in every parser's output (12/12). The differences come
  from how each parser's layout changes chunk boundaries, not from missing text.
- Twelve questions on one document is a small test. Treat the ranking as a pointer, not a benchmark.
  Scanned PDFs and complex multi-column layouts are where layout models like Docling usually help,
  and this sample does not test that.
- The Ollama vision row is "not run" because Ollama was not installed on the test machine. The
  code path is covered by a unit test that confirms it is skipped cleanly when no server is running.

## Run it

```bash
git clone https://github.com/arvindermundraa/PDF-parser-Comparison-for-RAG-applications.git
cd PDF-parser-Comparison-for-RAG-applications
python -m venv .venv && source .venv/bin/activate

pip install -r requirements-dev.txt      # small: PyMuPDF + pytest
pytest -q                                # 24 pass, 2 skip until the full install; then 26 pass
python scripts/download_sample.py        # NIST sample PDF -> input/
python main.py extract --method pymupdf  # -> outputs/extracted_pymupdf.txt

pip install -r requirements.txt          # full: Docling, Unstructured, FAISS, sentence-transformers
python main.py compare                   # all available parsers -> outputs/results.md
python main.py evaluate                  # retrieval hit rate per parser -> outputs/retrieval.md
python main.py ask "What does TEVV stand for?"
```

Use your own document with `--pdf path/to/file.pdf` on any command. `evaluate` uses questions
written for the sample PDF; edit `eval/questions.json` for another document.

### Optional LLM back ends

| Back end | What it adds | Setup |
|---|---|---|
| [Ollama](https://ollama.com) | Written answers for `ask` (`llama3.1`) and the `ollama_vision` extractor (`llama3.2-vision`) | `ollama serve`, then `ollama pull llama3.1 llama3.2-vision` |
| TAMU AI chat API | `tamus_vision` extractor and answers for `ask` | Texas A&M users only. `cp .env.example .env` and set `TAMUS_API_KEY` |

Without either, `ask` prints the top retrieved passages and every other command works unchanged.
A method that cannot run is reported as skipped with the reason; it never stops the run.

## How it works

```
PDF ──► extractor ──► text ──► chunks (1,200 chars, 150 overlap) ──► MiniLM embeddings ──► FAISS
        (one of 5)                                                                          │
                                                   question ──► embed ──► top-k chunks ◄────┘
                                                                              │
                                                              answer (Ollama / TAMU AI, optional)
```

| Path | Purpose |
|---|---|
| `main.py` | CLI: `extract`, `compare`, `evaluate`, `ask` |
| `src/common.py` | `ExtractionResult`, PDF lookup, page rendering for the vision methods |
| `src/extractors/` | One file per method: PyMuPDF, Docling, Unstructured, Ollama vision, TAMU AI vision |
| `src/compare.py` | Runs the available methods, writes the results table |
| `src/rag/pipeline.py` | Chunking, embeddings, FAISS index, optional answer step |
| `src/evaluate.py` | hit@k and MRR against `eval/questions.json` |
| `tests/` | 26 unit tests; PDFs are generated in the test, so no sample file or network is needed |
| `.github/workflows/ci.yml` | Runs the tests on every push |

## Tech stack

Python 3.12, PyMuPDF, Docling, Unstructured, sentence-transformers, FAISS, Ollama (optional),
pytest, GitHub Actions.

## Author

Arvinder Singh Mundra. Built as an individual project at Texas A&M University.

## License

MIT, see [LICENSE](LICENSE). The sample PDF is downloaded from nist.gov and is not included in
this repository.
