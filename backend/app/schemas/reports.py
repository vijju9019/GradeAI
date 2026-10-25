from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel

class QuestionScorecardItem(BaseModel):
    question_number: str
    question_text: str
    max_marks: float
    suggested_marks: float
    teacher_marks: Optional[float] = None
    approved_marks: float
    status: str
    confidence_level: str
    review_notes: Optional[str] = None

class StudentReportResponse(BaseModel):
    submission_id: int
    examination_id: int
    exam_title: str
    subject: str
    class_name: str
    academic_year: str
    exam_date: str
    total_exam_marks: float
    student_id: str
    student_name: str
    student_roll_no: Optional[str] = None
    total_approved_marks: float
    percentage: float
    is_finalized: bool
    finalized_at: Optional[datetime] = None
    generated_at: datetime
    questions: List[QuestionScorecardItem] = []

class AuditLogResponse(BaseModel):
    id: int
    action: str
    entity_type: str
    entity_id: Optional[str] = None
    details: dict = {}
    timestamp: datetime
    user_name: Optional[str] = None

    class Config:
        from_attributes = True
