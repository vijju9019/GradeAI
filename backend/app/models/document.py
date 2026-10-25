from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base

class UploadedDocument(Base):
    __tablename__ = "uploaded_documents"

    id = Column(Integer, primary_key=True, index=True)
    submission_id = Column(Integer, ForeignKey("student_submissions.id", ondelete="CASCADE"), nullable=False)
    original_filename = Column(String(255), nullable=False)
    stored_filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_size = Column(Integer, nullable=False)
    mime_type = Column(String(100), nullable=False)
    page_count = Column(Integer, default=1, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    submission = relationship("StudentSubmission", back_populates="documents")
    extracted_pages = relationship("ExtractedPage", back_populates="document", cascade="all, delete-orphan", order_by="ExtractedPage.page_number")


class ExtractedPage(Base):
    __tablename__ = "extracted_pages"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("uploaded_documents.id", ondelete="CASCADE"), nullable=False)
    page_number = Column(Integer, nullable=False)
    raw_text = Column(Text, default="", nullable=False)
    corrected_text = Column(Text, default="", nullable=False)
    extraction_method = Column(String(50), default="pdf_digital", nullable=False)  # pdf_digital, tesseract_ocr, manual
    is_poor_quality = Column(Boolean, default=False, nullable=False)
    quality_warning = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    document = relationship("UploadedDocument", back_populates="extracted_pages")
