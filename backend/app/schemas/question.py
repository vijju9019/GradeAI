from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field

class RubricBase(BaseModel):
    criterion_title: str
    description: Optional[str] = None
    allocated_marks: float = Field(..., gt=0)
    order_index: int = 0

class RubricCreate(RubricBase):
    pass

class RubricResponse(RubricBase):
    id: int
    question_id: int
    created_at: datetime

    class Config:
        from_attributes = True


class QuestionBase(BaseModel):
    question_number: str
    question_text: str
    max_marks: float = Field(..., gt=0)
    model_answer: str
    required_keywords: List[str] = []
    important_concepts: List[str] = []
    alternative_answers: List[str] = []
    order_index: int = 0

class QuestionCreate(QuestionBase):
    rubrics: List[RubricCreate] = []

class QuestionUpdate(BaseModel):
    question_number: Optional[str] = None
    question_text: Optional[str] = None
    max_marks: Optional[float] = None
    model_answer: Optional[str] = None
    required_keywords: Optional[List[str]] = None
    important_concepts: Optional[List[str]] = None
    alternative_answers: Optional[List[str]] = None
    order_index: Optional[int] = None
    rubrics: Optional[List[RubricCreate]] = None

class QuestionResponse(QuestionBase):
    id: int
    examination_id: int
    created_at: datetime
    updated_at: datetime
    rubrics: List[RubricResponse] = []

    class Config:
        from_attributes = True
