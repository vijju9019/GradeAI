from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_teacher
from app.models.user import User
from app.models.examination import Examination
from app.models.submission import StudentSubmission, SubmissionStatus
from app.schemas.submission import (
    SubmissionCreate,
    SubmissionResponse
)

router = APIRouter()

@router.get("/examinations/{exam_id}/submissions", response_model=List[SubmissionResponse])
def list_submissions(
    exam_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_teacher)
):
    """List all student submissions for a specific exam."""
    exam = db.query(Examination).filter(Examination.id == exam_id).first()
    if not exam:
        raise HTTPException(status_code=404, detail="Examination not found")

    submissions = db.query(StudentSubmission).filter(
        StudentSubmission.examination_id == exam_id
    ).order_by(StudentSubmission.created_at.desc()).all()
    
    return submissions

@router.post("/examinations/{exam_id}/submissions", response_model=SubmissionResponse, status_code=status.HTTP_201_CREATED)
def create_submission(
    exam_id: int,
    sub_in: SubmissionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_teacher)
):
    """Create a new student submission container."""
    exam = db.query(Examination).filter(Examination.id == exam_id).first()
    if not exam:
        raise HTTPException(status_code=404, detail="Examination not found")

    # Check duplicate submission for same student in same exam
    existing = db.query(StudentSubmission).filter(
        StudentSubmission.examination_id == exam_id,
        StudentSubmission.student_id == sub_in.student_id
    ).first()
    if existing:
        raise HTTPException(
            status_code=400,
            detail=f"Submission for student ID '{sub_in.student_id}' already exists in this examination."
        )

    submission = StudentSubmission(
        examination_id=exam.id,
        student_id=sub_in.student_id,
        student_name=sub_in.student_name,
        student_roll_no=sub_in.student_roll_no,
        status=SubmissionStatus.UPLOADED.value
    )
    db.add(submission)
    db.commit()
    db.refresh(submission)
    return submission

@router.get("/submissions/{submission_id}", response_model=SubmissionResponse)
def get_submission(
    submission_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_teacher)
):
    """Get single submission with documents and extracted pages."""
    sub = db.query(StudentSubmission).filter(StudentSubmission.id == submission_id).first()
    if not sub:
        raise HTTPException(status_code=404, detail="Student submission not found")
    return sub

@router.delete("/submissions/{submission_id}", status_code=status.HTTP_200_OK)
def delete_submission(
    submission_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_teacher)
):
    """Delete a student submission and all related evaluation records."""
    sub = db.query(StudentSubmission).filter(StudentSubmission.id == submission_id).first()
    if not sub:
        raise HTTPException(status_code=404, detail="Student submission not found")
    
    student_name = sub.student_name
    db.delete(sub)
    db.commit()
    return {"message": f"Submission for '{student_name}' deleted successfully."}
