import pytest
from app.services.report_generator import report_generator
from app.models.examination import Examination
from app.models.question import Question
from app.models.submission import StudentSubmission, SubmissionStatus
from app.models.evaluation import ExtractedAnswer, EvaluationResult, ApprovedMark

def test_pdf_report_generation(db_session):
    exam = Examination(
        title="Operating Systems",
        subject="CSE",
        class_name="Sem V",
        academic_year="2026",
        exam_date="2026-10-25",
        total_marks=20.0
    )
    db_session.add(exam)
    db_session.commit()

    q1 = Question(
        examination_id=exam.id,
        question_number="1",
        question_text="Explain Paging",
        max_marks=20.0,
        model_answer="Paging divides memory into frames."
    )
    db_session.add(q1)
    db_session.commit()

    sub = StudentSubmission(
        examination_id=exam.id,
        student_id="STU-001",
        student_name="Alice Smith",
        status=SubmissionStatus.FINALIZED.value,
        total_approved_marks=18.0,
        percentage=90.0,
        is_finalized=True
    )
    db_session.add(sub)
    db_session.commit()

    ans = ExtractedAnswer(submission_id=sub.id, question_id=q1.id, raw_answer_text="Paging frames.")
    db_session.add(ans)
    db_session.commit()

    ev = EvaluationResult(
        extracted_answer_id=ans.id,
        question_id=q1.id,
        suggested_marks=16.0,
        max_marks=20.0,
        confidence_level="high"
    )
    db_session.add(ev)
    db_session.commit()

    app_m = ApprovedMark(
        evaluation_result_id=ev.id,
        submission_id=sub.id,
        question_id=q1.id,
        suggested_marks=16.0,
        teacher_marks=18.0,
        review_notes="Excellent understanding",
        is_overridden=True
    )
    db_session.add(app_m)
    db_session.commit()

    # Generate data
    data = report_generator.get_student_report_data(db_session, sub.id)
    assert data["student_name"] == "Alice Smith"
    assert data["total_approved_marks"] == 18.0
    assert data["percentage"] == 90.0

    # Generate PDF bytes
    pdf_bytes = report_generator.generate_pdf_report(data)
    assert isinstance(pdf_bytes, bytes)
    assert len(pdf_bytes) > 500
    assert pdf_bytes.startswith(b"%PDF")

    # Generate CSV
    csv_str = report_generator.generate_csv_report(db_session, exam.id)
    assert "Alice Smith" in csv_str
    assert "18.0" in csv_str

    # Generate Excel bytes
    excel_bytes = report_generator.generate_excel_report(db_session, exam.id)
    assert isinstance(excel_bytes, bytes)
    assert len(excel_bytes) > 500
