import enum
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
from app.core.database import Base

class SubmissionStatus(str, enum.Enum):
    UPLOADED = "uploaded"
    EXTRACTED = "extracted"
    SEGMENTED = "segmented"
    EVALUATED = "evaluated"
    REVIEWED = "reviewed"
    FINALIZED = "finalized"

class StudentSubmission(Base):
    __tablename__ = "student_submissions"

    id = Column(Integer, primary_key=True, index=True)
    examination_id = Column(Integer, ForeignKey("examinations.id", ondelete="CASCADE"), nullable=False)
    student_id = Column(String(100), nullable=False)  # e.g., "STU-2026-001"
    student_name = Column(String(255), nullable=False)
    student_roll_no = Column(String(100), nullable=True)
    
    status = Column(String(50), default=SubmissionStatus.UPLOADED.value, nullable=False)
    total_suggested_marks = Column(Float, default=0.0, nullable=False)
    total_approved_marks = Column(Float, default=0.0, nullable=False)
    percentage = Column(Float, default=0.0, nullable=False)
    is_finalized = Column(Boolean, default=False, nullable=False)
    finalized_at = Column(DateTime, nullable=True)
    
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    examination = relationship("Examination", back_populates="submissions")
    documents = relationship("UploadedDocument", back_populates="submission", cascade="all, delete-orphan")
    extracted_answers = relationship("ExtractedAnswer", back_populates="submission", cascade="all, delete-orphan")
    approved_marks = relationship("ApprovedMark", back_populates="submission", cascade="all, delete-orphan")
