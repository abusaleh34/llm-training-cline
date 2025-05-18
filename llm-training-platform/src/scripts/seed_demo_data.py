"""
Seed demo data for staging environment

This script creates sample data for testing purposes in the staging environment.
It creates users, documents, and other necessary data for QA testing.
"""

import os
import sys
import uuid
import random
from datetime import datetime, timedelta
from pathlib import Path

# Add the parent directory to the path so we can import the modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from sqlalchemy.orm import Session
from loguru import logger

from src.common.db.database import get_db
from src.common.models.user import User, UserRole
from src.common.models.document import Document, DocumentStatus
from src.common.config.settings import settings
from src.document_ingestion.utils.file_utils import create_directory_if_not_exists


def create_demo_users(db: Session):
    """Create demo users for testing"""
    logger.info("Creating demo users...")
    
    # Create a regular user if it doesn't exist
    user = db.query(User).filter(User.username == "user").first()
    if not user:
        user = User(
            id=str(uuid.uuid4()),
            username="user",
            email="user@example.com",
            full_name="Demo User",
            role=UserRole.USER,
            is_active=True
        )
        user.set_password("password")
        db.add(user)
        logger.info(f"Created regular user: {user.username}")
    
    # Create a manager user if it doesn't exist
    manager = db.query(User).filter(User.username == "manager").first()
    if not manager:
        manager = User(
            id=str(uuid.uuid4()),
            username="manager",
            email="manager@example.com",
            full_name="Demo Manager",
            role=UserRole.MANAGER,
            is_active=True
        )
        manager.set_password("password")
        db.add(manager)
        logger.info(f"Created manager user: {manager.username}")
    
    db.commit()
    return user, manager


def create_demo_documents(db: Session, user_id: str, count: int = 5):
    """Create demo documents for testing"""
    logger.info(f"Creating {count} demo documents...")
    
    documents = []
    document_types = ["contract", "letter", "report", "invoice", "memo"]
    languages = ["en", "ar"]
    
    # Create document directories
    upload_dir = Path(settings.document.upload_dir)
    processed_dir = Path(settings.document.processed_dir)
    create_directory_if_not_exists(upload_dir)
    create_directory_if_not_exists(processed_dir)
    
    for i in range(count):
        # Generate a unique ID for the document
        document_id = str(uuid.uuid4())
        
        # Create document directory
        doc_upload_dir = upload_dir / document_id
        doc_processed_dir = processed_dir / document_id
        create_directory_if_not_exists(doc_upload_dir)
        create_directory_if_not_exists(doc_processed_dir)
        
        # Create a dummy text file
        filename = f"demo_document_{i+1}.txt"
        file_path = doc_upload_dir / filename
        
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(f"This is a demo document {i+1} for testing purposes.\n")
            f.write(f"It contains some sample text that would be processed by the system.\n")
            f.write(f"Document ID: {document_id}\n")
        
        # Create a dummy processed text file
        processed_text_path = doc_processed_dir / "extracted_text.txt"
        with open(processed_text_path, "w", encoding="utf-8") as f:
            f.write(f"Processed text for demo document {i+1}.\n")
            f.write(f"This text has been extracted and processed by the system.\n")
            f.write(f"Document ID: {document_id}\n")
        
        # Create document record
        document = Document(
            id=document_id,
            filename=filename,
            file_path=str(file_path),
            processed_file_path=str(doc_processed_dir),
            file_type="txt",
            document_type=random.choice(document_types),
            language=random.choice(languages),
            status=DocumentStatus.PROCESSED,
            user_id=user_id,
            upload_date=datetime.now() - timedelta(days=random.randint(1, 30)),
            processing_started_date=datetime.now() - timedelta(days=random.randint(1, 29)),
            processing_completed_date=datetime.now() - timedelta(days=random.randint(0, 28)),
            page_count=random.randint(1, 10),
            word_count=random.randint(100, 1000)
        )
        
        db.add(document)
        documents.append(document)
        logger.info(f"Created demo document: {document.id} - {document.filename}")
    
    db.commit()
    return documents


def seed_demo_data():
    """Seed demo data for testing"""
    logger.info("Starting demo data seeding...")
    
    # Get database session
    db = next(get_db())
    
    try:
        # Create demo users
        user, manager = create_demo_users(db)
        
        # Create demo documents for the regular user
        documents = create_demo_documents(db, user.id, count=5)
        
        # Create demo documents for the manager
        manager_documents = create_demo_documents(db, manager.id, count=3)
        
        # Add more demo data here as needed
        # ...
        
        logger.info("Demo data seeding completed successfully")
        
    except Exception as e:
        logger.error(f"Error seeding demo data: {str(e)}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_demo_data()
