from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.api.deps import get_db, get_current_teacher
from app.models.user import User
from app.models.examination import Examination, ExamStatus
from app.models.question import Question
from app.models.submission import StudentSubmission
from app.models.audit import AuditLog
from app.schemas.examination import (
    ExaminationCreate,
    ExaminationUpdate,
    ExaminationResponse,
    ExaminationDetailResponse
)

router = APIRouter()

@router.get("", response_model=List[ExaminationResponse])
def list_examinations(
    status_filter: Optional[str] = Query(None, alias="status"),
    subject: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_teacher)
):
    """List all examinations with counts."""
    query = db.query(Examination)
    if status_filter:
        query = query.filter(Examination.status == status_filter)
    if subject:
        query = query.filter(Examination.subject.ilike(f"%{subject}%"))

    exams = query.order_by(Examination.created_at.desc()).all()
    
    results = []
    for ex in exams:
        q_count = db.query(func.count(Question.id)).filter(Question.examination_id == ex.id).scalar() or 0
        s_count = db.query(func.count(StudentSubmission.id)).filter(StudentSubmission.examination_id == ex.id).scalar() or 0
        
        resp = ExaminationResponse.from_orm(ex)
        resp.questions_count = q_count
        resp.submissions_count = s_count
        results.append(resp)
        
    return results

@router.post("", response_model=ExaminationResponse, status_code=status.HTTP_201_CREATED)
def create_examination(
    exam_in: ExaminationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_teacher)
):
    """Create a new examination."""
    exam = Examination(
        title=exam_in.title,
        subject=exam_in.subject,
        class_name=exam_in.class_name,
        academic_year=exam_in.academic_year,
        exam_date=exam_in.exam_date,
        total_marks=exam_in.total_marks,
        duration_minutes=exam_in.duration_minutes,
        description=exam_in.description,
        status=ExamStatus.DRAFT.value,
        created_by_id=current_user.id
    )
    db.add(exam)
    db.commit()
    db.refresh(exam)

    db.add(AuditLog(
        user_id=current_user.id,
        action="create_examination",
        entity_type="examination",
        entity_id=str(exam.id),
        details={"title": exam.title, "total_marks": exam.total_marks}
    ))
    db.commit()

    resp = ExaminationResponse.from_orm(exam)
    resp.questions_count = 0
    resp.submissions_count = 0
    return resp

@router.get("/{exam_id}", response_model=ExaminationDetailResponse)
def get_examination(
    exam_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_teacher)
):
    """Get full details of an examination, including all questions and rubrics."""
    exam = db.query(Examination).filter(Examination.id == exam_id).first()
    if not exam:
        raise HTTPException(status_code=404, detail="Examination not found")

    q_count = len(exam.questions)
    s_count = len(exam.submissions)
    
    resp = ExaminationDetailResponse.from_orm(exam)
    resp.questions_count = q_count
    resp.submissions_count = s_count
    return resp

@router.put("/{exam_id}", response_model=ExaminationResponse)
def update_examination(
    exam_id: int,
    exam_in: ExaminationUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_teacher)
):
    """Update examination settings."""
    exam = db.query(Examination).filter(Examination.id == exam_id).first()
    if not exam:
        raise HTTPException(status_code=404, detail="Examination not found")

    update_data = exam_in.dict(exclude_unset=True)
    for field, val in update_data.items():
        setattr(exam, field, val)

    db.commit()
    db.refresh(exam)

    resp = ExaminationResponse.from_orm(exam)
    resp.questions_count = len(exam.questions)
    resp.submissions_count = len(exam.submissions)
    return resp

@router.delete("/{exam_id}", status_code=status.HTTP_200_OK)
def delete_examination(
    exam_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_teacher)
):
    """Delete an examination and all associated questions and submissions."""
    exam = db.query(Examination).filter(Examination.id == exam_id).first()
    if not exam:
        raise HTTPException(status_code=404, detail="Examination not found")

    title = exam.title
    db.delete(exam)
    db.commit()

    db.add(AuditLog(
        user_id=current_user.id,
        action="delete_examination",
        entity_type="examination",
        entity_id=str(exam_id),
        details={"deleted_title": title}
    ))
    db.commit()
    return {"message": f"Examination '{title}' successfully deleted."}
