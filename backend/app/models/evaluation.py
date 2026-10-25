import json
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, Float, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base

class ExtractedAnswer(Base):
    __tablename__ = "extracted_answers"

    id = Column(Integer, primary_key=True, index=True)
    submission_id = Column(Integer, ForeignKey("student_submissions.id", ondelete="CASCADE"), nullable=False)
    question_id = Column(Integer, ForeignKey("questions.id", ondelete="CASCADE"), nullable=False)
    raw_answer_text = Column(Text, default="", nullable=False)
    corrected_answer_text = Column(Text, default="", nullable=False)
    segmentation_confidence = Column(Float, default=1.0, nullable=False)
    is_manually_mapped = Column(Boolean, default=False, nullable=False)
    is_missing = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    submission = relationship("StudentSubmission", back_populates="extracted_answers")
    question = relationship("Question", back_populates="extracted_answers")
    evaluation_result = relationship("EvaluationResult", uselist=False, back_populates="extracted_answer", cascade="all, delete-orphan")


class EvaluationResult(Base):
    __tablename__ = "evaluation_results"

    id = Column(Integer, primary_key=True, index=True)
    extracted_answer_id = Column(Integer, ForeignKey("extracted_answers.id", ondelete="CASCADE"), nullable=False)
    question_id = Column(Integer, ForeignKey("questions.id", ondelete="CASCADE"), nullable=False)
    
    suggested_marks = Column(Float, nullable=False)
    max_marks = Column(Float, nullable=False)
    confidence_level = Column(String(50), default="medium", nullable=False)  # high, medium, low
    confidence_score = Column(Float, default=0.5, nullable=False)
    
    keyword_coverage_score = Column(Float, default=0.0, nullable=False)
    cosine_similarity_score = Column(Float, default=0.0, nullable=False)
    semantic_similarity_score = Column(Float, default=0.0, nullable=False)
    rubric_score = Column(Float, default=0.0, nullable=False)
    
    _matched_keywords = Column("matched_keywords", Text, default="[]", nullable=False)
    _missing_keywords = Column("missing_keywords", Text, default="[]", nullable=False)
    _matched_concepts = Column("matched_concepts", Text, default="[]", nullable=False)
    _missing_concepts = Column("missing_concepts", Text, default="[]", nullable=False)
    _rubric_breakdown = Column("rubric_breakdown", Text, default="[]", nullable=False)
    _evidence_snippets = Column("evidence_snippets", Text, default="[]", nullable=False)
    _uncertainty_reasons = Column("uncertainty_reasons", Text, default="[]", nullable=False)
    
    evaluated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    extracted_answer = relationship("ExtractedAnswer", back_populates="evaluation_result")
    question = relationship("Question", back_populates="evaluation_results")
    approved_mark = relationship("ApprovedMark", uselist=False, back_populates="evaluation_result", cascade="all, delete-orphan")

    def _get_json(self, attr):
        try:
            val = getattr(self, attr)
            return json.loads(val) if val else []
        except Exception:
            return []

    def _set_json(self, attr, val):
        setattr(self, attr, json.dumps(val if val is not None else []))

    @property
    def matched_keywords(self): return self._get_json("_matched_keywords")
    @matched_keywords.setter
    def matched_keywords(self, val): self._set_json("_matched_keywords", val)

    @property
    def missing_keywords(self): return self._get_json("_missing_keywords")
    @missing_keywords.setter
    def missing_keywords(self, val): self._set_json("_missing_keywords", val)

    @property
    def matched_concepts(self): return self._get_json("_matched_concepts")
    @matched_concepts.setter
    def matched_concepts(self, val): self._set_json("_matched_concepts", val)

    @property
    def missing_concepts(self): return self._get_json("_missing_concepts")
    @missing_concepts.setter
    def missing_concepts(self, val): self._set_json("_missing_concepts", val)

    @property
    def rubric_breakdown(self): return self._get_json("_rubric_breakdown")
    @rubric_breakdown.setter
    def rubric_breakdown(self, val): self._set_json("_rubric_breakdown", val)

    @property
    def evidence_snippets(self): return self._get_json("_evidence_snippets")
    @evidence_snippets.setter
    def evidence_snippets(self, val): self._set_json("_evidence_snippets", val)

    @property
    def uncertainty_reasons(self): return self._get_json("_uncertainty_reasons")
    @uncertainty_reasons.setter
    def uncertainty_reasons(self, val): self._set_json("_uncertainty_reasons", val)


class ApprovedMark(Base):
    __tablename__ = "approved_marks"

    id = Column(Integer, primary_key=True, index=True)
    evaluation_result_id = Column(Integer, ForeignKey("evaluation_results.id", ondelete="CASCADE"), nullable=False)
    submission_id = Column(Integer, ForeignKey("student_submissions.id", ondelete="CASCADE"), nullable=False)
    question_id = Column(Integer, ForeignKey("questions.id", ondelete="CASCADE"), nullable=False)
    
    suggested_marks = Column(Float, nullable=False)
    teacher_marks = Column(Float, nullable=False)
    reviewer_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    review_notes = Column(Text, nullable=True)
    is_overridden = Column(Boolean, default=False, nullable=False)
    approved_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    evaluation_result = relationship("EvaluationResult", back_populates="approved_mark")
    submission = relationship("StudentSubmission", back_populates="approved_marks")
    question = relationship("Question", back_populates="approved_marks")
    reviewer = relationship("User", back_populates="approved_marks")


class ModelVersion(Base):
    __tablename__ = "model_versions"

    id = Column(Integer, primary_key=True, index=True)
    model_name = Column(String(255), nullable=False)
    model_type = Column(String(100), nullable=False)  # e.g., 'random_forest_regressor'
    file_path = Column(String(500), nullable=False)
    _metrics = Column("metrics", Text, default="{}", nullable=False)
    is_active = Column(Boolean, default=False, nullable=False)
    trained_by_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    @property
    def metrics(self):
        try:
            return json.loads(self._metrics) if self._metrics else {}
        except Exception:
            return {}

    @metrics.setter
    def metrics(self, val):
        self._metrics = json.dumps(val if val is not None else {})
