import enum
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, Float, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
from app.core.database import Base

class ExamStatus(str, enum.Enum):
    DRAFT = "draft"
    READY = "ready"
    PROCESSING = "processing"
    REVIEW_PENDING = "review_pending"
    FINALIZED = "finalized"

class Examination(Base):
    __tablename__ = "examinations"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    subject = Column(String(255), nullable=False)
    class_name = Column(String(100), nullable=False)
    academic_year = Column(String(50), nullable=False)
    exam_date = Column(String(50), nullable=False)
    total_marks = Column(Float, nullable=False, default=100.0)
    duration_minutes = Column(Integer, default=180, nullable=False)
    description = Column(Text, nullable=True)
    status = Column(String(50), default=ExamStatus.DRAFT.value, nullable=False)
    
    created_by_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    creator = relationship("User", back_populates="examinations")
    questions = relationship("Question", back_populates="examination", cascade="all, delete-orphan", order_by="Question.order_index")
    submissions = relationship("StudentSubmission", back_populates="examination", cascade="all, delete-orphan")
