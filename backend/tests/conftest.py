import sys
from pathlib import Path
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core.database import Base
from app.core.security import get_password_hash
from app.models.user import User, UserRole

TEST_DATABASE_URL = "sqlite:///:memory:"

@pytest.fixture(scope="function")
def db_session():
    engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    
    # Create test teacher and admin
    teacher = User(
        email="test_teacher@gradeai.edu",
        full_name="Test Teacher",
        hashed_password=get_password_hash("testpass123"),
        role=UserRole.TEACHER.value,
        is_active=True
    )
    admin = User(
        email="test_admin@gradeai.edu",
        full_name="Test Admin",
        hashed_password=get_password_hash("adminpass123"),
        role=UserRole.ADMIN.value,
        is_active=True
    )
    db.add(teacher)
    db.add(admin)
    db.commit()
    db.refresh(teacher)
    db.refresh(admin)

    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)
