from typing import List, Optional, Dict
from pydantic import BaseModel

class DashboardStatsResponse(BaseModel):
    total_examinations: int
    total_students_evaluated: int
    total_documents_processed: int
    pending_teacher_reviews: int
    finalized_submissions: int
    average_approved_percentage: float
    ocr_success_rate: float
    teacher_override_rate: float

class MarksDistributionItem(BaseModel):
    range_label: str  # e.g., "0-20%", "21-40%", "41-60%", "61-80%", "81-100%"
    count: int

class QuestionDifficultyItem(BaseModel):
    question_number: str
    max_marks: float
    average_marks: float
    average_percentage: float
    difficulty: str  # "Easy", "Moderate", "Challenging"

class SubjectPerformanceItem(BaseModel):
    subject: str
    exam_count: int
    student_count: int
    average_score: float

class RecentExamItem(BaseModel):
    id: int
    title: str
    subject: str
    status: str
    submissions_count: int
    created_at: str

class RecentActivityItem(BaseModel):
    id: int
    action: str
    description: str
    timestamp: str
    user_name: Optional[str] = None
