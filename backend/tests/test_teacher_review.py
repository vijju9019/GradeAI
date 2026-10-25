import pytest
from fastapi import HTTPException
from app.models.examination import Examination, ExamStatus
from app.models.question import Question
from app.models.submission import StudentSubmission, SubmissionStatus
from app.models.evaluation import ExtractedAnswer, EvaluationResult
from app.services.teacher_review import teacher_review_service

def test_teacher_mark_override_and_bounds_validation(db_session):
    teacher = db_session.query(StudentSubmission).first()
    # Create Exam
    exam = Examination(
        title="Test Midterm",
        subject="Computer Systems",
        class_name="CS",
        academic_year="2026",
        exam_date="2026-10-25",
        total_marks=20.0
    )
    db_session.add(exam)
    db_session.commit()

    q1 = Question(
        examination_id=exam.id,
        question_number="1",
        question_text="Define OS",
        max_marks=10.0,
        model_answer="An OS manages computer hardware and software."
    )
    db_session.add(q1)
    db_session.commit()

    sub = StudentSubmission(
        examination_id=exam.id,
        student_id="S101",
        student_name="Test Student",
        status=SubmissionStatus.EVALUATED.value
    )
    db_session.add(sub)
    db_session.commit()

    ans = ExtractedAnswer(
        submission_id=sub.id,
        question_id=q1.id,
        raw_answer_text="OS manages hardware."
    )
    db_session.add(ans)
    db_session.commit()

    eval_res = EvaluationResult(
        extracted_answer_id=ans.id,
        question_id=q1.id,
        suggested_marks=6.0,
        max_marks=10.0,
        confidence_level="medium"
    )
    db_session.add(eval_res)
    db_session.commit()

    # 1. Valid teacher override
    app_mark = teacher_review_service.override_question_mark(
        db=db_session,
        submission_id=sub.id,
        question_id=q1.id,
        teacher_marks=8.5,
        review_notes="Good answer, credited additional point.",
        reviewer_id=1
    )
    assert app_mark.teacher_marks == 8.5
    assert app_mark.is_overridden is True
    assert sub.total_approved_marks == 8.5

    # 2. Invalid override exceeding max marks (e.g. 15 on a 10 mark question) must fail with HTTPException
    with pytest.raises(HTTPException) as exc_info:
        teacher_review_service.override_question_mark(
            db=db_session,
            submission_id=sub.id,
            question_id=q1.id,
            teacher_marks=15.0,
            review_notes="Illegal marks",
            reviewer_id=1
        )
    assert exc_info.value.status_code == 400

    # 3. Negative marks must also fail
    with pytest.raises(HTTPException) as exc_info:
        teacher_review_service.override_question_mark(
            db=db_session,
            submission_id=sub.id,
            question_id=q1.id,
            teacher_marks=-1.0,
            review_notes="Negative marks",
            reviewer_id=1
        )
    assert exc_info.value.status_code == 400
