from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_teacher
from app.models.user import User
from app.services.analytics_service import analytics_service
from app.schemas.analytics import (
    DashboardStatsResponse,
    MarksDistributionItem,
    QuestionDifficultyItem,
    SubjectPerformanceItem,
    RecentActivityItem
)

router = APIRouter()

@router.get("/dashboard-stats", response_model=DashboardStatsResponse)
def get_dashboard_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_teacher)
):
    """Retrieve database-derived summary KPIs."""
    return analytics_service.get_dashboard_stats(db)

@router.get("/marks-distribution", response_model=List[MarksDistributionItem])
def get_marks_distribution(
    exam_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_teacher)
):
    """Marks histogram data for chart visualizers."""
    return analytics_service.get_marks_distribution(db, exam_id)

@router.get("/subject-performance", response_model=List[SubjectPerformanceItem])
def get_subject_performance(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_teacher)
):
    """Performance breakdown by subject."""
    return analytics_service.get_subject_performance(db)

@router.get("/examinations/{exam_id}/difficulty", response_model=List[QuestionDifficultyItem])
def get_question_difficulty(
    exam_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_teacher)
):
    """Question-wise average score and difficulty assessment."""
    return analytics_service.get_question_difficulty_breakdown(db, exam_id)

@router.get("/recent-activity", response_model=List[RecentActivityItem])
def get_recent_activity(
    limit: int = 8,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_teacher)
):
    """Recent audit log entries."""
    return analytics_service.get_recent_activity(db, limit)
