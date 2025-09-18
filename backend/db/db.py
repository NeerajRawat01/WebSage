from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.orm import Session
import os

# Load from env (Docker will inject DATABASE_URL from .env)
DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# Ensure all feature models are imported so Base.metadata is complete for Alembic
try:
    from app import feature_models  # noqa: F401
except Exception:
    # During certain tooling or when app package isn't available, skip
    feature_models = None

# Dependency for FastAPI routes
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
