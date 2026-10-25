from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class RubricBreakdownItem(BaseModel):
    rubric_id: Optional[int] = None
    criterion_title: str
    allocated_marks: float
    awarded_marks: float
    met: bool
    explanation: str

class EvaluationResultResponse(BaseModel):
    id: int
    extracted_answer_id: int
    question_id: int
    question_number: Optional[str] = None
    question_text: Optional[str] = None
    max_marks: float
    suggested_marks: float
    confidence_level: str
    confidence_score: float
    keyword_coverage_score: float
    cosine_similarity_score: float
    semantic_similarity_score: float
    rubric_score: float
    matched_keywords: List[str] = []
    missing_keywords: List[str] = []
    matched_concepts: List[str] = []
    missing_concepts: List[str] = []
    rubric_breakdown: List[RubricBreakdownItem] = []
    evidence_snippets: List[str] = []
    uncertainty_reasons: List[str] = []
    evaluated_at: datetime
    
    # Teacher approved marks if present
    teacher_marks: Optional[float] = None
    review_notes: Optional[str] = None
    is_overridden: bool = False
    reviewer_name: Optional[str] = None
    approved_at: Optional[datetime] = None

    # Answers side-by-side
    student_answer: Optional[str] = None
    model_answer: Optional[str] = None

    class Config:
        from_attributes = True

class TeacherMarkOverrideRequest(BaseModel):
    question_id: int
    teacher_marks: float = Field(..., ge=0)
    review_notes: Optional[str] = None

class BatchApproveRequest(BaseModel):
    submission_id: int
    confirm_all: bool = True

class FinalizeSubmissionRequest(BaseModel):
    submission_id: int

class TrainModelRequest(BaseModel):
    model_name: Optional[str] = "gradeai_rf_regressor_v1"
    min_samples: int = Field(5, ge=3)
