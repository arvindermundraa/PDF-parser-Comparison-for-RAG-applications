import pymupdf
import pytest


@pytest.fixture()
def sample_pdf(tmp_path):
    """Two-page PDF built on the fly: a paragraph, a ruled 3x3 table, and a second page."""
    doc = pymupdf.open()
    page = doc.new_page()
    page.insert_text((72, 72), "Quarterly report for the Aggie Rocket Club.", fontsize=12)
    rows = [["Quarter", "Launches", "Budget"], ["Q1", "4", "1200"], ["Q2", "7", "1850"]]
    x0, y0, w, h = 72, 120, 120, 24
    for r in range(4):
        page.draw_line((x0, y0 + r * h), (x0 + 3 * w, y0 + r * h))
    for c in range(4):
        page.draw_line((x0 + c * w, y0), (x0 + c * w, y0 + 3 * h))
    for r, row in enumerate(rows):
        for c, cell in enumerate(row):
            page.insert_text((x0 + c * w + 6, y0 + r * h + 16), cell, fontsize=11)
    doc.new_page().insert_text((72, 72), "Second page mentions the parachute recovery system.")
    path = tmp_path / "sample.pdf"
    doc.save(str(path))
    doc.close()
    return path
