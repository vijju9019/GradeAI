from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field
from app.schemas.question import QuestionResponse

class ExaminationBase(BaseModel):
    title: str
    subject: str
    class_name: str
    academic_year: str
    exam_date: str
    total_marks: float = Field(..., gt=0)
    duration_minutes: int = Field(180, gt=0)
    description: Optional[str] = None

class ExaminationCreate(ExaminationBase):
    pass

class ExaminationUpdate(BaseModel):
    title: Optional[str] = None
    subject: Optional[str] = None
    class_name: Optional[str] = None
    academic_year: Optional[str] = None
    exam_date: Optional[str] = None
    total_marks: Optional[float] = None
    duration_minutes: Optional[int] = None
    description: Optional[str] = None
    status: Optional[str] = None

class ExaminationResponse(ExaminationBase):
    id: int
    status: str
    created_by_id: Optional[int]
    created_at: datetime
    updated_at: datetime
    questions_count: int = 0
    submissions_count: int = 0

    class Config:
        from_attributes = True

class ExaminationDetailResponse(ExaminationResponse):
    questions: List[QuestionResponse] = []
