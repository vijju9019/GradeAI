import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.core.config import settings, UPLOAD_DIR
from app.core.database import Base, engine
from app.ml.embeddings import embedding_service
import app.models  # Ensure all models are registered

# API Routers
from app.api.v1.auth import router as auth_router
from app.api.v1.examinations import router as exam_router
from app.api.v1.questions import router as question_router
from app.api.v1.submissions import router as submission_router
from app.api.v1.documents import router as document_router
from app.api.v1.evaluation import router as eval_router
from app.api.v1.reviews import router as review_router
from app.api.v1.reports import router as report_router
from app.api.v1.analytics import router as analytics_router
from app.api.v1.admin import router as admin_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("gradeai")

import threading

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Create tables if not exist
    logger.info("Initializing database tables...")
    Base.metadata.create_all(bind=engine)
    logger.info("Database initialized successfully.")

    # Load embedding model in background thread so server starts instantly
    def load_embeddings_async():
        logger.info(f"Checking embedding service (model: {settings.EMBEDDING_MODEL_NAME})...")
        try:
            embedding_service.initialize_model(settings.EMBEDDING_MODEL_NAME)
        except Exception as e:
            logger.warning(f"Embedding model initialization deferred: {e}")

    thread = threading.Thread(target=load_embeddings_async, daemon=True)
    thread.start()

    yield
    logger.info("Shutting down GradeAI application.")

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="GradeAI: Production AI-Based Automated Exam Evaluation System with Teacher Review & Explainable Scoring.",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Development configuration
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files for document uploads
app.mount("/static/uploads", StaticFiles(directory=str(UPLOAD_DIR)), name="uploads")

# Include Routers
app.include_router(auth_router, prefix=f"{settings.API_V1_STR}/auth", tags=["Authentication"])
app.include_router(exam_router, prefix=f"{settings.API_V1_STR}/examinations", tags=["Examinations"])
app.include_router(question_router, prefix=settings.API_V1_STR, tags=["Questions & Rubrics"])
app.include_router(submission_router, prefix=settings.API_V1_STR, tags=["Student Submissions"])
app.include_router(document_router, prefix=settings.API_V1_STR, tags=["Documents & OCR"])
app.include_router(eval_router, prefix=settings.API_V1_STR, tags=["Evaluation Engine"])
app.include_router(review_router, prefix=f"{settings.API_V1_STR}/reviews", tags=["Teacher Review & Approval"])
app.include_router(report_router, prefix=f"{settings.API_V1_STR}/reports", tags=["Reports & Exports"])
app.include_router(analytics_router, prefix=f"{settings.API_V1_STR}/analytics", tags=["Analytics & KPIs"])
app.include_router(admin_router, prefix=f"{settings.API_V1_STR}/admin", tags=["Administration & Health"])

@app.get("/")
def root():
    return {
        "project": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "docs": "/docs",
        "status": "online"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
