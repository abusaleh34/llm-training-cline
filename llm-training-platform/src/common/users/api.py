"""
User management API for the LLM Training Platform.
"""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from src.common.auth.auth_handler import (
    get_current_admin_user,
    get_password_hash,
)
from src.common.auth.schemas import (
    User,
    UserCreate,
    UserUpdate,
)
from src.common.db.database import get_db
from src.common.models.user import User as UserModel, UserRole

router = APIRouter(prefix="/users", tags=["users"])


@router.get("", response_model=List[User])
async def read_users(
    skip: int = 0,
    limit: int = 100,
    role: Optional[str] = None,
    current_user: UserModel = Depends(get_current_admin_user),
    db: Session = Depends(get_db),
) -> List[User]:
    """
    Get users.
    
    Args:
        skip: Number of users to skip.
        limit: Maximum number of users to return.
        role: Filter by role.
        current_user: Current user.
        db: Database session.
        
    Returns:
        List[User]: Users.
    """
    query = db.query(UserModel)
    
    if role:
        query = query.filter(UserModel.role == role)
    
    return query.offset(skip).limit(limit).all()


@router.post("", response_model=User, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_create: UserCreate,
    current_user: UserModel = Depends(get_current_admin_user),
    db: Session = Depends(get_db),
) -> User:
    """
    Create user.
    
    Args:
        user_create: User create data.
        current_user: Current user.
        db: Database session.
        
    Returns:
        User: Created user.
        
    Raises:
        HTTPException: If username or email already exists.
    """
    # Check if username already exists
    db_user = db.query(UserModel).filter(UserModel.username == user_create.username).first()
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already exists",
        )
    
    # Check if email already exists
    db_user = db.query(UserModel).filter(UserModel.email == user_create.email).first()
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already exists",
        )
    
    # Create user
    hashed_password = get_password_hash(user_create.password)
    db_user = UserModel(
        username=user_create.username,
        email=user_create.email,
        full_name=user_create.full_name,
        hashed_password=hashed_password,
        role=UserRole(user_create.role),
        is_active=user_create.is_active,
    )
    
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    return db_user


@router.get("/{user_id}", response_model=User)
async def read_user(
    user_id: str,
    current_user: UserModel = Depends(get_current_admin_user),
    db: Session = Depends(get_db),
) -> User:
    """
    Get user.
    
    Args:
        user_id: User ID.
        current_user: Current user.
        db: Database session.
        
    Returns:
        User: User.
        
    Raises:
        HTTPException: If user is not found.
    """
    db_user = db.query(UserModel).filter(UserModel.id == user_id).first()
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    
    return db_user


@router.put("/{user_id}", response_model=User)
async def update_user(
    user_id: str,
    user_update: UserUpdate,
    current_user: UserModel = Depends(get_current_admin_user),
    db: Session = Depends(get_db),
) -> User:
    """
    Update user.
    
    Args:
        user_id: User ID.
        user_update: User update data.
        current_user: Current user.
        db: Database session.
        
    Returns:
        User: Updated user.
        
    Raises:
        HTTPException: If user is not found or email already exists.
    """
    db_user = db.query(UserModel).filter(UserModel.id == user_id).first()
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    
    # Check if email already exists
    if user_update.email and user_update.email != db_user.email:
        db_user_email = db.query(UserModel).filter(UserModel.email == user_update.email).first()
        if db_user_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already exists",
            )
    
    # Update user
    if user_update.email is not None:
        db_user.email = user_update.email
    if user_update.full_name is not None:
        db_user.full_name = user_update.full_name
    if user_update.is_active is not None:
        db_user.is_active = user_update.is_active
    if user_update.role is not None:
        db_user.role = UserRole(user_update.role)
    
    db.commit()
    db.refresh(db_user)
    
    return db_user


@router.delete("/{user_id}", response_model=User)
async def delete_user(
    user_id: str,
    current_user: UserModel = Depends(get_current_admin_user),
    db: Session = Depends(get_db),
) -> User:
    """
    Delete user.
    
    Args:
        user_id: User ID.
        current_user: Current user.
        db: Database session.
        
    Returns:
        User: Deleted user.
        
    Raises:
        HTTPException: If user is not found or is the current user.
    """
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete current user",
        )
    
    db_user = db.query(UserModel).filter(UserModel.id == user_id).first()
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    
    db.delete(db_user)
    db.commit()
    
    return db_user
