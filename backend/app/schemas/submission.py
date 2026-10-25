from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class ExtractedPageResponse(BaseModel):
    id: int
    document_id: int
    page_number: int
    raw_text: str
    corrected_text: str
    extraction_method: str
    is_poor_quality: bool
    quality_warning: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True

class PageCorrectionRequest(BaseModel):
    page_id: int
    corrected_text: str

class UploadedDocumentResponse(BaseModel):
    id: int
    submission_id: int
    original_filename: str
    stored_filename: str
    file_size: int
    mime_type: str
    page_count: int
    created_at: datetime
    extracted_pages: List[ExtractedPageResponse] = []

    class Config:
        from_attributes = True

class AnswerMappingItem(BaseModel):
    question_id: int
    answer_text: str
    is_missing: bool = False

class AnswerMappingUpdateRequest(BaseModel):
    submission_id: int
    answers: List[AnswerMappingItem]

class SubmissionCreate(BaseModel):
    examination_id: int
    student_id: str
    student_name: str
    student_roll_no: Optional[str] = None

class SubmissionResponse(BaseModel):
    id: int
    examination_id: int
    student_id: str
    student_name: str
    student_roll_no: Optional[str]
    status: str
    total_suggested_marks: float
    total_approved_marks: float
    percentage: float
    is_finalized: bool
    finalized_at: Optional[datetime]
    created_at: datetime
    documents: List[UploadedDocumentResponse] = []

    class Config:
        from_attributes = True
