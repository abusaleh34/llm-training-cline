"""
Database connection and session management for the LLM Training Platform.
"""

from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session

from src.common.config.settings import settings

# Create SQLAlchemy engine
engine = create_engine(
    settings.db.connection_string,
    pool_pre_ping=True,
    echo=settings.environment == "development",
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create base class for models
Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """
    Get database session.
    
    Yields:
        Session: Database session.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """
    Initialize database.
    
    Creates all tables if they don't exist.
    """
    # Import models to ensure they are registered with the Base
    from src.common.models.user import User, APIKey
    from src.common.models.document import Document, DocumentPage
    
    # Create tables
    Base.metadata.create_all(bind=engine)
