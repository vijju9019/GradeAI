import pytest
from app.services.segmenter import answer_segmenter
from app.models.question import Question

def test_explicit_headers_segmentation():
    q1 = Question(id=101, question_number="1", question_text="What is RAM?", max_marks=5.0, model_answer="")
    q2 = Question(id=102, question_number="2", question_text="What is ROM?", max_marks=5.0, model_answer="")

    doc_text = (
        "Name: John Doe\n\n"
        "Q1: RAM is random access memory used for volatile temporary storage.\n\n"
        "Q2: ROM is read only memory used for permanent firmware storage.\n"
    )

    result = answer_segmenter.segment_answers(doc_text, [q1, q2])
    mapped = result["mapped_answers"]
    assert len(mapped) == 2
    assert mapped[0]["question_id"] == 101
    assert "random access memory" in mapped[0]["answer_text"]
    assert mapped[0]["confidence"] >= 0.90
    assert mapped[1]["question_id"] == 102
    assert "read only memory" in mapped[1]["answer_text"]

def test_missing_question_flagged():
    q1 = Question(id=1, question_number="1", question_text="Q1", max_marks=5.0, model_answer="")
    q2 = Question(id=2, question_number="2", question_text="Q2", max_marks=5.0, model_answer="")

    # Student only answered Q1
    doc_text = "Question 1: Here is my complete answer for the first question."
    result = answer_segmenter.segment_answers(doc_text, [q1, q2])
    mapped = result["mapped_answers"]
    assert mapped[0]["is_missing"] is False
    assert mapped[1]["is_missing"] is True
    assert any("Question 2" in w for w in result["warnings"])
