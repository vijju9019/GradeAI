from typing import List, Dict, Any
from pydantic import BaseModel, EmailStr, Field
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_teacher, get_current_admin
from app.core.config import settings, UPLOAD_DIR
from app.core.security import get_password_hash
from app.models.user import User, UserRole
from app.services.document_extractor import document_extractor
from app.ml.embeddings import embedding_service
from app.ml.trainable_scorer import trainable_scorer
from app.schemas.auth import UserResponse

router = APIRouter()

class SystemHealthResponse(BaseModel):
    status: str
    tesseract_ocr_available: bool
    embedding_model_ready: bool
    embedding_model_name: str
    trainable_scorer_trained: bool
    database_backend: str
    upload_dir: str

class ScoringWeightsUpdate(BaseModel):
    keyword_weight: float = Field(..., ge=0.0, le=1.0)
    cosine_weight: float = Field(..., ge=0.0, le=1.0)
    semantic_weight: float = Field(..., ge=0.0, le=1.0)
    rubric_weight: float = Field(..., ge=0.0, le=1.0)

class AdminUserCreate(BaseModel):
    email: EmailStr
    full_name: str
    password: str = Field(..., min_length=6)
    role: str = "teacher"

@router.get("/health", response_model=SystemHealthResponse)
def get_system_health():
    """Report real environment readiness, models, and OCR status honestly."""
    return {
        "status": "operational",
        "tesseract_ocr_available": document_extractor.is_ocr_available(),
        "embedding_model_ready": embedding_service.is_ready,
        "embedding_model_name": embedding_service.model_name,
        "trainable_scorer_trained": trainable_scorer.is_trained(),
        "database_backend": "SQLite (compatible with PostgreSQL)",
        "upload_dir": str(UPLOAD_DIR)
    }

@router.get("/scoring-weights")
def get_scoring_weights(current_user: User = Depends(get_current_teacher)):
    """Retrieve active weights for the hybrid scoring pipeline."""
    from app.services.nlp_evaluator import nlp_evaluator
    return {
        "keyword_weight": round(nlp_evaluator.weight_keyword, 2),
        "cosine_weight": round(nlp_evaluator.weight_cosine, 2),
        "semantic_weight": round(nlp_evaluator.weight_semantic, 2),
        "rubric_weight": round(nlp_evaluator.weight_rubric, 2)
    }

@router.put("/scoring-weights")
def update_scoring_weights(
    weights_in: ScoringWeightsUpdate,
    current_user: User = Depends(get_current_admin)
):
    """Update scoring weights across the evaluation engine."""
    from app.services.nlp_evaluator import nlp_evaluator
    nlp_evaluator.weight_keyword = weights_in.keyword_weight
    nlp_evaluator.weight_cosine = weights_in.cosine_weight
    nlp_evaluator.weight_semantic = weights_in.semantic_weight
    nlp_evaluator.weight_rubric = weights_in.rubric_weight
    
    # Re-normalize
    tot = (nlp_evaluator.weight_keyword + nlp_evaluator.weight_cosine +
           nlp_evaluator.weight_semantic + nlp_evaluator.weight_rubric)
    if tot > 0:
        nlp_evaluator.weight_keyword /= tot
        nlp_evaluator.weight_cosine /= tot
        nlp_evaluator.weight_semantic /= tot
        nlp_evaluator.weight_rubric /= tot

    return {
        "message": "Scoring weights updated successfully.",
        "weights": {
            "keyword_weight": round(nlp_evaluator.weight_keyword, 2),
            "cosine_weight": round(nlp_evaluator.weight_cosine, 2),
            "semantic_weight": round(nlp_evaluator.weight_semantic, 2),
            "rubric_weight": round(nlp_evaluator.weight_rubric, 2)
        }
    }

@router.get("/users", response_model=List[UserResponse])
def list_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Admin-only: list all system users."""
    return db.query(User).order_by(User.id).all()

@router.post("/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user_by_admin(
    user_in: AdminUserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Admin-only: create user accounts."""
    existing = db.query(User).filter(User.email == user_in.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="User already exists with this email.")

    user = User(
        email=user_in.email,
        full_name=user_in.full_name,
        hashed_password=get_password_hash(user_in.password),
        role=user_in.role if user_in.role in ["admin", "teacher"] else "teacher",
        is_active=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user
