from src.evaluate import evaluation_markdown, first_hit_rank, is_hit, load_questions, score


def test_hit_ignores_case_and_line_breaks_but_needs_every_phrase():
    chunk = "GOVERN 1.1: Legal and\nregulatory   requirements are understood."
    assert is_hit(chunk, ["govern 1.1", "legal and regulatory requirements"])
    assert not is_hit(chunk, ["GOVERN 1.1", "MAP 5.1"])


def test_first_hit_rank_is_one_based_or_none():
    chunks = ["nothing here", "MEASURE 2.7 security", "MEASURE 2.7 again"]
    assert first_hit_rank(chunks, ["MEASURE 2.7"]) == 2
    assert first_hit_rank(chunks, ["MANAGE 4.1"]) is None


def test_score_hit_rates_and_mrr():
    s = score([1, 3, None, 5])
    assert s == {"hit@1": 0.25, "hit@3": 0.5, "hit@5": 0.75, "mrr": round((1 + 1 / 3 + 1 / 5) / 4, 3)}


def test_question_file_is_well_formed():
    questions = load_questions()
    assert len(questions) >= 10
    assert all(q["question"].endswith("?") and q["expect"] for q in questions)


def test_markdown_row():
    row = {"chunks": 10, "answerable": 11, "questions": 12, "hit@1": 0.5, "hit@3": 0.75,
           "hit@5": 1.0, "mrr": 0.6}
    assert "| pymupdf | 10 | 11/12 | 0.500 | 0.750 | 1.000 | 0.600 |" in evaluation_markdown({"pymupdf": row})
