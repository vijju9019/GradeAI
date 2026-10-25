from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_teacher
from app.models.user import User
from app.services.teacher_review import teacher_review_service
from app.schemas.evaluation import (
    TeacherMarkOverrideRequest,
    BatchApproveRequest,
    FinalizeSubmissionRequest
)
from app.schemas.submission import SubmissionResponse

router = APIRouter()

@router.post("/submissions/{submission_id}/override")
def override_question_mark(
    submission_id: int,
    override_in: TeacherMarkOverrideRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_teacher)
):
    """
    Teacher overrides or approves an individual question score.
    Enforces valid range [0, question_max_marks], logs reviewer and audit history.
    """
    approved_mark = teacher_review_service.override_question_mark(
        db=db,
        submission_id=submission_id,
        question_id=override_in.question_id,
        teacher_marks=override_in.teacher_marks,
        review_notes=override_in.review_notes,
        reviewer_id=current_user.id
    )
    return {
        "message": "Question mark successfully updated.",
        "question_id": approved_mark.question_id,
        "teacher_marks": approved_mark.teacher_marks,
        "is_overridden": approved_mark.is_overridden
    }

@router.post("/submissions/{submission_id}/batch-approve", response_model=SubmissionResponse)
def batch_approve_submission(
    submission_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_teacher)
):
    """
    Teacher bulk approves all AI-suggested marks for the entire answer sheet.
    """
    submission = teacher_review_service.batch_approve_submission(
        db=db,
        submission_id=submission_id,
        reviewer_id=current_user.id
    )
    return submission

@router.post("/submissions/{submission_id}/finalize", response_model=SubmissionResponse)
def finalize_submission(
    submission_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_teacher)
):
    """
    Teacher finalizes and locks grades for the student submission.
    Requires all questions in the examination to be reviewed and approved.
    """
    submission = teacher_review_service.finalize_submission(
        db=db,
        submission_id=submission_id,
        reviewer_id=current_user.id
    )
    return submission
