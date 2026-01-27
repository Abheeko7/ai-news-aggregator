import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

load_dotenv()

def get_database_url() -> str:
    """
    Get database URL from environment.
    
    Supports two formats:
    1. DATABASE_URL (Render/Heroku style) - full connection string
    2. Individual POSTGRES_* variables (local development)
    """
    # First, check for DATABASE_URL (Render/cloud deployment)
    database_url = os.getenv("DATABASE_URL")
    if database_url:
        # Render uses postgres:// but SQLAlchemy needs postgresql://
        if database_url.startswith("postgres://"):
            database_url = database_url.replace("postgres://", "postgresql://", 1)
        return database_url
    
    # Fall back to individual variables (local development)
    user = os.getenv("POSTGRES_USER", "postgres")
    password = os.getenv("POSTGRES_PASSWORD", "postgres")
    host = os.getenv("POSTGRES_HOST", "localhost")
    port = os.getenv("POSTGRES_PORT", "5432")
    db = os.getenv("POSTGRES_DB", "ai_news_aggregator")
    return f"postgresql://{user}:{password}@{host}:{port}/{db}"

engine = create_engine(get_database_url())
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_session():
    return SessionLocal()

