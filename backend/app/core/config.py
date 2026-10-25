import os
from pathlib import Path
from typing import List

# Application Paths
BASE_DIR = Path(__file__).resolve().parent.parent.parent
WORKSPACE_DIR = BASE_DIR.parent
DATA_DIR = BASE_DIR / "data"
UPLOAD_DIR = DATA_DIR / "uploads"
PROCESSED_DIR = DATA_DIR / "processed"
REPORTS_DIR = DATA_DIR / "reports"
MODELS_DIR = DATA_DIR / "models"

for dir_path in [DATA_DIR, UPLOAD_DIR, PROCESSED_DIR, REPORTS_DIR, MODELS_DIR]:
    dir_path.mkdir(parents=True, exist_ok=True)


class Settings:
    PROJECT_NAME: str = "GradeAI — Automated Exam Evaluation System"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # Security
    SECRET_KEY: str = os.getenv("GRADEAI_SECRET_KEY", "gradeai_super_secret_dev_key_2026_academic_secure")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours
    
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", f"sqlite:///{DATA_DIR / 'gradeai.db'}")
    
    # CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "*"
    ]
    
    # NLP & Scoring Config
    EMBEDDING_MODEL_NAME: str = os.getenv("EMBEDDING_MODEL_NAME", "all-MiniLM-L6-v2")
    DEFAULT_KEYWORD_WEIGHT: float = 0.30
    DEFAULT_COSINE_WEIGHT: float = 0.25
    DEFAULT_SEMANTIC_WEIGHT: float = 0.30
    DEFAULT_RUBRIC_WEIGHT: float = 0.15
    
    # Confidence Thresholds
    CONFIDENCE_HIGH_THRESHOLD: float = 0.75
    CONFIDENCE_MEDIUM_THRESHOLD: float = 0.50
    
    # File Limits
    MAX_UPLOAD_SIZE_BYTES: int = 25 * 1024 * 1024  # 25 MB
    ALLOWED_EXTENSIONS: set = {".pdf", ".png", ".jpg", ".jpeg", ".txt"}
    
    # OCR config
    TESSERACT_CMD: str = os.getenv("TESSERACT_CMD", "tesseract")


settings = Settings()
