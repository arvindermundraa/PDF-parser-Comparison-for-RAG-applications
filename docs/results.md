# Extraction comparison

PDF: `NIST.AI.100-1.pdf`  
Date: 2026-11-24  
Machine: Darwin arm64, Python 3.12.15

| method | time (s) | pages | characters | words | tables | images | notes |
|---|---|---|---|---|---|---|---|
| pymupdf | 7.3 | 48 | 126,205 | 19,184 | 14 | 10 |  |
| docling | 44.0 | 48 | 144,160 | 16,037 | 13 | 9 | OCR off |
| unstructured | 5.4 | 48 | 114,839 | 16,916 | n/a | n/a | strategy=fast, 605 elements |
| ollama_vision | not run | | | | | | Ollama server is not running (start it with `ollama serve`) |

`n/a`: the method does not report that count in the mode used.

## Retrieval check

| method | chunks | answer present in a chunk | hit@1 | hit@3 | hit@5 | MRR |
|---|---|---|---|---|---|---|
| pymupdf | 150 | 12/12 | 0.417 | 0.667 | 0.750 | 0.521 |
| docling | 167 | 12/12 | 0.333 | 0.583 | 0.583 | 0.431 |
| unstructured | 123 | 12/12 | 0.250 | 0.500 | 0.583 | 0.368 |

12 questions from `eval/questions.json`. A hit means one retrieved chunk contains every expected phrase.
Chunks: about 1,200 characters with 150 overlap. Embeddings: all-MiniLM-L12-v2. Index: FAISS inner product on normalized vectors.
