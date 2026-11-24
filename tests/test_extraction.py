import json

import pytest

import main as cli
from src.common import ExtractionResult, ExtractorUnavailable, find_pdf, render_pages_png, save_text
from src.compare import compare, results_markdown, run_method
from src.extractors.pymupdf_extraction import extract, table_to_markdown


def test_pymupdf_reads_text_from_every_page(sample_pdf):
    result = extract(sample_pdf)
    assert result.pages == 2
    assert "Aggie Rocket Club" in result.text
    assert "parachute recovery system" in result.text
    assert "--- PAGE 2 ---" in result.text


def test_pymupdf_finds_the_table_and_keeps_its_numbers(sample_pdf):
    result = extract(sample_pdf)
    assert result.tables == 1
    assert "| Q2 | 7 | 1850 |" in result.text


def test_table_to_markdown_handles_none_and_newlines():
    md = table_to_markdown([["a", None], ["line\nbreak", "2"]])
    assert md.splitlines() == ["| a |  |", "| --- | --- |", "| line break | 2 |"]
    assert table_to_markdown([]) == ""


def test_result_counts_and_summary_leave_out_the_text():
    r = ExtractionResult("x", "one two three", 0.5, 1)
    assert (r.characters, r.words) == (13, 3)
    assert "text" not in r.summary() and r.summary()["words"] == 3


def test_find_pdf_explicit_first_in_folder_and_missing(sample_pdf, tmp_path):
    assert find_pdf(str(sample_pdf)) == sample_pdf
    assert find_pdf(None, input_dir=sample_pdf.parent) == sample_pdf
    with pytest.raises(FileNotFoundError):
        find_pdf(str(tmp_path / "nope.pdf"))
    empty = tmp_path / "empty"
    empty.mkdir()
    with pytest.raises(FileNotFoundError, match="download_sample"):
        find_pdf(None, input_dir=empty)


def test_save_text_writes_one_file_per_method(sample_pdf, tmp_path):
    path = save_text(extract(sample_pdf), tmp_path / "out")
    assert path.name == "extracted_pymupdf.txt" and "Rocket" in path.read_text()


def test_render_pages_respects_page_limit(sample_pdf):
    pages = render_pages_png(sample_pdf, max_pages=1)
    assert len(pages) == 1 and pages[0].startswith(b"\x89PNG")


def test_tamus_is_optional_without_a_key(sample_pdf, monkeypatch):
    monkeypatch.delenv("TAMUS_API_KEY", raising=False)
    with pytest.raises(ExtractorUnavailable, match="TAMUS_API_KEY"):
        run_method("tamus_vision", sample_pdf)


def test_blank_tamus_key_counts_as_missing(sample_pdf, monkeypatch):
    monkeypatch.setenv("TAMUS_API_KEY", "  ")
    with pytest.raises(ExtractorUnavailable):
        run_method("tamus_vision", sample_pdf)


def test_ollama_is_skipped_when_no_server(sample_pdf, monkeypatch):
    pytest.importorskip("ollama")
    monkeypatch.setenv("OLLAMA_BASE_URL", "http://127.0.0.1:9")     # nothing listens here
    with pytest.raises(ExtractorUnavailable, match="Ollama"):
        run_method("ollama_vision", sample_pdf)


def test_unknown_method_is_rejected(sample_pdf):
    with pytest.raises(ValueError):
        run_method("magic", sample_pdf)


def test_compare_writes_table_and_records_skipped_methods(sample_pdf, tmp_path, monkeypatch):
    monkeypatch.delenv("TAMUS_API_KEY", raising=False)
    rows, skipped = compare(sample_pdf, ["pymupdf", "tamus_vision"], out_dir=tmp_path)
    assert [r["method"] for r in rows] == ["pymupdf"]
    assert "tamus_vision" in skipped
    data = json.loads((tmp_path / "results.json").read_text())
    assert data["results"][0]["tables"] == 1
    table = (tmp_path / "results.md").read_text()
    assert "| pymupdf |" in table and "| tamus_vision | not run |" in table


def test_results_markdown_marks_unreported_counts():
    row = {"method": "m", "seconds": 1.234, "pages": 2, "characters": 1500, "words": 200,
           "tables": None, "images": 3, "notes": ""}
    assert "| m | 1.2 | 2 | 1,500 | 200 | n/a | 3 |" in results_markdown("a.pdf", [row], {})


def test_cli_extract_and_missing_pdf(sample_pdf, tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    assert cli.main(["extract", "--pdf", str(sample_pdf)]) == 0
    assert (tmp_path / "outputs" / "extracted_pymupdf.txt").exists()
    assert cli.main(["extract", "--pdf", "missing.pdf"]) == 2
    assert "not found" in capsys.readouterr().err
