import json
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base

class Question(Base):
    __tablename__ = "questions"

    id = Column(Integer, primary_key=True, index=True)
    examination_id = Column(Integer, ForeignKey("examinations.id", ondelete="CASCADE"), nullable=False)
    question_number = Column(String(50), nullable=False)  # e.g., "1", "2(a)", "Q1"
    question_text = Column(Text, nullable=False)
    max_marks = Column(Float, nullable=False)
    model_answer = Column(Text, nullable=False)
    
    # Stored as JSON strings for cross-database compatibility (SQLite & PostgreSQL)
    _required_keywords = Column("required_keywords", Text, default="[]", nullable=False)
    _important_concepts = Column("important_concepts", Text, default="[]", nullable=False)
    _alternative_answers = Column("alternative_answers", Text, default="[]", nullable=False)
    
    order_index = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    examination = relationship("Examination", back_populates="questions")
    rubrics = relationship("MarkingRubric", back_populates="question", cascade="all, delete-orphan", order_by="MarkingRubric.order_index")
    extracted_answers = relationship("ExtractedAnswer", back_populates="question", cascade="all, delete-orphan")
    evaluation_results = relationship("EvaluationResult", back_populates="question", cascade="all, delete-orphan")
    approved_marks = relationship("ApprovedMark", back_populates="question", cascade="all, delete-orphan")

    @property
    def required_keywords(self):
        try:
            return json.loads(self._required_keywords) if self._required_keywords else []
        except Exception:
            return []

    @required_keywords.setter
    def required_keywords(self, val):
        self._required_keywords = json.dumps(val if val is not None else [])

    @property
    def important_concepts(self):
        try:
            return json.loads(self._important_concepts) if self._important_concepts else []
        except Exception:
            return []

    @important_concepts.setter
    def important_concepts(self, val):
        self._important_concepts = json.dumps(val if val is not None else [])

    @property
    def alternative_answers(self):
        try:
            return json.loads(self._alternative_answers) if self._alternative_answers else []
        except Exception:
            return []

    @alternative_answers.setter
    def alternative_answers(self, val):
        self._alternative_answers = json.dumps(val if val is not None else [])


class MarkingRubric(Base):
    __tablename__ = "marking_rubrics"

    id = Column(Integer, primary_key=True, index=True)
    question_id = Column(Integer, ForeignKey("questions.id", ondelete="CASCADE"), nullable=False)
    criterion_title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    allocated_marks = Column(Float, nullable=False)
    order_index = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    question = relationship("Question", back_populates="rubrics")
