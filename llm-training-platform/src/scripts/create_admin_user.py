"""
Admin user creation script

This script creates an admin user for the platform.
"""

import sys
import os
import uuid
import getpass
from pathlib import Path

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from loguru import logger
from sqlalchemy.exc import SQLAlchemyError

from src.common.db.database import get_db_session
from src.common.models.user import User, UserRole
from src.common.auth.auth_handler import get_password_hash


def create_admin_user(username, password, email, full_name):
    """
    Create an admin user
    
    Args:
        username: Username
        password: Password
        email: Email address
        full_name: Full name
        
    Returns:
        User: Created user
    """
    try:
        with get_db_session() as db:
            # Check if user already exists
            existing_user = db.query(User).filter(User.username == username).first()
            if existing_user:
                logger.warning(f"User '{username}' already exists")
                return existing_user
            
            # Create user
            user = User(
                id=str(uuid.uuid4()),
                username=username,
                password_hash=get_password_hash(password),
                email=email,
                full_name=full_name,
                role=UserRole.ADMIN,
                is_active=True
            )
            
            db.add(user)
            db.commit()
            db.refresh(user)
            
            logger.info(f"Admin user '{username}' created successfully")
            return user
            
    except SQLAlchemyError as e:
        logger.error(f"Database error: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        raise


def main():
    """
    Main function
    """
    try:
        print("Create Admin User")
        print("----------------")
        
        # Get user input
        username = input("Username: ")
        email = input("Email: ")
        full_name = input("Full Name: ")
        
        # Get password securely
        while True:
            password = getpass.getpass("Password: ")
            if len(password) < 8:
                print("Password must be at least 8 characters long")
                continue
                
            password_confirm = getpass.getpass("Confirm Password: ")
            if password != password_confirm:
                print("Passwords do not match")
                continue
                
            break
        
        # Create admin user
        user = create_admin_user(username, password, email, full_name)
        
        print(f"\nAdmin user '{username}' created successfully")
        print(f"User ID: {user.id}")
        
    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\nError: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
