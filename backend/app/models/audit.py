import json
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    action = Column(String(100), nullable=False)  # e.g., "create_exam", "edit_marks", "finalize_submission"
    entity_type = Column(String(100), nullable=False)  # "submission", "exam", "question"
    entity_id = Column(String(100), nullable=True)
    _details = Column("details", Text, default="{}", nullable=False)
    ip_address = Column(String(50), nullable=True)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    user = relationship("User", back_populates="audit_logs")

    @property
    def details(self):
        try:
            return json.loads(self._details) if self._details else {}
        except Exception:
            return {}

    @details.setter
    def details(self, val):
        self._details = json.dumps(val if val is not None else {})
