from datetime import datetime, timezone
import logging
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.submission import StudentSubmission, SubmissionStatus
from app.models.question import Question
from app.models.evaluation import ExtractedAnswer, EvaluationResult, ApprovedMark
from app.models.examination import Examination, ExamStatus
from app.models.audit import AuditLog

logger = logging.getLogger(__name__)

class TeacherReviewService:
    def override_question_mark(
        self,
        db: Session,
        submission_id: int,
        question_id: int,
        teacher_marks: float,
        review_notes: Optional[str],
        reviewer_id: int
    ) -> ApprovedMark:
        """
        Record teacher review/override for a specific question.
        Enforces 0 <= teacher_marks <= max_marks.
        """
        # Validate submission
        submission = db.query(StudentSubmission).filter(StudentSubmission.id == submission_id).first()
        if not submission:
            raise HTTPException(status_code=404, detail="Student submission not found")

        # Validate question
        question = db.query(Question).filter(Question.id == question_id).first()
        if not question:
            raise HTTPException(status_code=404, detail="Question not found")

        # Validate mark bounds
        if teacher_marks < 0 or teacher_marks > question.max_marks:
            raise HTTPException(
                status_code=400,
                detail=f"Awarded marks ({teacher_marks}) must be between 0 and the maximum marks ({question.max_marks}) for Question {question.question_number}."
            )

        # Find evaluation result
        extracted_answer = db.query(ExtractedAnswer).filter(
            ExtractedAnswer.submission_id == submission_id,
            ExtractedAnswer.question_id == question_id
        ).first()

        if not extracted_answer or not extracted_answer.evaluation_result:
            raise HTTPException(
                status_code=400,
                detail="Evaluation result does not exist for this question. Please run evaluation first."
            )

        eval_res = extracted_answer.evaluation_result
        suggested_marks = eval_res.suggested_marks
        is_overridden = abs(suggested_marks - teacher_marks) > 0.01

        # Check existing approved mark
        approved_mark = db.query(ApprovedMark).filter(
            ApprovedMark.evaluation_result_id == eval_res.id
        ).first()

        now = datetime.now(timezone.utc)
        if approved_mark:
            approved_mark.teacher_marks = teacher_marks
            approved_mark.review_notes = review_notes
            approved_mark.is_overridden = is_overridden
            approved_mark.reviewer_id = reviewer_id
            approved_mark.approved_at = now
        else:
            approved_mark = ApprovedMark(
                evaluation_result_id=eval_res.id,
                submission_id=submission_id,
                question_id=question_id,
                suggested_marks=suggested_marks,
                teacher_marks=teacher_marks,
                reviewer_id=reviewer_id,
                review_notes=review_notes,
                is_overridden=is_overridden,
                approved_at=now
            )
            db.add(approved_mark)

        db.flush()
        # Recalculate submission totals
        self._recalculate_submission_totals(db, submission)

        # Audit log
        audit = AuditLog(
            user_id=reviewer_id,
            action="override_mark",
            entity_type="question_evaluation",
            entity_id=str(eval_res.id),
            details={
                "submission_id": submission_id,
                "question_number": question.question_number,
                "suggested_marks": suggested_marks,
                "teacher_marks": teacher_marks,
                "review_notes": review_notes
            }
        )
        db.add(audit)
        db.commit()
        db.refresh(approved_mark)
        return approved_mark

    def batch_approve_submission(
        self,
        db: Session,
        submission_id: int,
        reviewer_id: int
    ) -> StudentSubmission:
        """
        Approve all unreviewed questions for a submission using the AI-suggested marks.
        """
        submission = db.query(StudentSubmission).filter(StudentSubmission.id == submission_id).first()
        if not submission:
            raise HTTPException(status_code=404, detail="Student submission not found")

        answers = db.query(ExtractedAnswer).filter(ExtractedAnswer.submission_id == submission_id).all()
        now = datetime.now(timezone.utc)

        for ans in answers:
            if not ans.evaluation_result:
                continue
            eval_res = ans.evaluation_result
            approved_mark = db.query(ApprovedMark).filter(ApprovedMark.evaluation_result_id == eval_res.id).first()
            if not approved_mark:
                # Approve suggested marks
                app_mark = ApprovedMark(
                    evaluation_result_id=eval_res.id,
                    submission_id=submission_id,
                    question_id=ans.question_id,
                    suggested_marks=eval_res.suggested_marks,
                    teacher_marks=eval_res.suggested_marks,
                    reviewer_id=reviewer_id,
                    review_notes="Auto-approved suggested marks upon teacher review.",
                    is_overridden=False,
                    approved_at=now
                )
                db.add(app_mark)

        db.flush()
        self._recalculate_submission_totals(db, submission)
        submission.status = SubmissionStatus.REVIEWED.value

        # Log
        db.add(AuditLog(
            user_id=reviewer_id,
            action="batch_approve_submission",
            entity_type="submission",
            entity_id=str(submission_id),
            details={"submission_id": submission_id}
        ))
        db.commit()
        db.refresh(submission)
        return submission

    def finalize_submission(
        self,
        db: Session,
        submission_id: int,
        reviewer_id: int
    ) -> StudentSubmission:
        """
        Lock and finalize submission marks after teacher verification.
        Requires all questions in the exam to have an approved mark.
        """
        submission = db.query(StudentSubmission).filter(StudentSubmission.id == submission_id).first()
        if not submission:
            raise HTTPException(status_code=404, detail="Student submission not found")

        # Verify all questions have approved marks
        questions = db.query(Question).filter(Question.examination_id == submission.examination_id).all()
        approved_marks = db.query(ApprovedMark).filter(ApprovedMark.submission_id == submission_id).all()

        approved_q_ids = {m.question_id for m in approved_marks}
        missing_q = [q.question_number for q in questions if q.id not in approved_q_ids]

        if missing_q:
            raise HTTPException(
                status_code=400,
                detail=f"Cannot finalize submission: questions {', '.join(missing_q)} have not been reviewed and approved yet."
            )

        self._recalculate_submission_totals(db, submission)
        submission.is_finalized = True
        submission.status = SubmissionStatus.FINALIZED.value
        submission.finalized_at = datetime.now(timezone.utc)

        # Check if all submissions for the exam are finalized
        exam = db.query(Examination).filter(Examination.id == submission.examination_id).first()
        if exam:
            all_subs = db.query(StudentSubmission).filter(StudentSubmission.examination_id == exam.id).all()
            if all(s.is_finalized for s in all_subs) and all_subs:
                exam.status = ExamStatus.FINALIZED.value

        db.add(AuditLog(
            user_id=reviewer_id,
            action="finalize_submission",
            entity_type="submission",
            entity_id=str(submission_id),
            details={"approved_total": submission.total_approved_marks, "percentage": submission.percentage}
        ))
        db.commit()
        db.refresh(submission)
        return submission

    def _recalculate_submission_totals(self, db: Session, submission: StudentSubmission):
        exam = db.query(Examination).filter(Examination.id == submission.examination_id).first()
        total_exam_marks = float(exam.total_marks) if exam and exam.total_marks > 0 else 100.0

        approved_marks = db.query(ApprovedMark).filter(ApprovedMark.submission_id == submission.id).all()
        total_approved = sum(m.teacher_marks for m in approved_marks)

        # Suggested marks sum
        answers = db.query(ExtractedAnswer).filter(ExtractedAnswer.submission_id == submission.id).all()
        total_suggested = sum(a.evaluation_result.suggested_marks for a in answers if a.evaluation_result)

        submission.total_suggested_marks = round(total_suggested, 2)
        submission.total_approved_marks = round(total_approved, 2)
        submission.percentage = round((total_approved / total_exam_marks) * 100, 2) if total_exam_marks > 0 else 0.0


teacher_review_service = TeacherReviewService()
