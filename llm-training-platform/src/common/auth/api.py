"""
Authentication API for the LLM Training Platform.
"""

import secrets
from datetime import datetime, timedelta
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from src.common.auth.auth_handler import (
    authenticate_user,
    create_access_token,
    get_current_active_user,
    get_password_hash,
)
from src.common.auth.schemas import (
    Token,
    User,
    APIKey,
    APIKeyCreate,
    APIKeyWithValue,
)
from src.common.config.settings import settings
from src.common.db.database import get_db
from src.common.models.user import User as UserModel, APIKey as APIKeyModel

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/token", response_model=Token)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
) -> Token:
    """
    Get access token.
    
    Args:
        form_data: OAuth2 password request form.
        db: Database session.
        
    Returns:
        Token: Access token.
        
    Raises:
        HTTPException: If authentication fails.
    """
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = create_access_token(
        data={"sub": user.id},
    )
    
    return Token(access_token=access_token, token_type="bearer")


@router.get("/me", response_model=User)
async def read_users_me(current_user: UserModel = Depends(get_current_active_user)) -> User:
    """
    Get current user.
    
    Args:
        current_user: Current user.
        
    Returns:
        User: Current user.
    """
    return current_user


@router.post("/api-keys", response_model=APIKeyWithValue)
async def create_api_key(
    api_key_create: APIKeyCreate,
    current_user: UserModel = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> APIKeyWithValue:
    """
    Create API key.
    
    Args:
        api_key_create: API key create data.
        current_user: Current user.
        db: Database session.
        
    Returns:
        APIKeyWithValue: Created API key.
    """
    # Generate API key
    key = f"{settings.security.api_key_prefix}{secrets.token_hex(32)}"
    prefix = key[:8]
    
    # Calculate expiration date
    expires_at = None
    if api_key_create.expires_days:
        expires_at = datetime.utcnow() + timedelta(days=api_key_create.expires_days)
    
    # Create API key
    db_api_key = APIKeyModel(
        key=key,
        name=api_key_create.name,
        prefix=prefix,
        user_id=current_user.id,
        expires_at=expires_at,
    )
    
    db.add(db_api_key)
    db.commit()
    db.refresh(db_api_key)
    
    return APIKeyWithValue(
        id=db_api_key.id,
        name=db_api_key.name,
        prefix=db_api_key.prefix,
        is_active=db_api_key.is_active,
        created_at=db_api_key.created_at,
        updated_at=db_api_key.updated_at,
        expires_at=db_api_key.expires_at,
        user_id=db_api_key.user_id,
        key=key,
    )


@router.get("/api-keys", response_model=List[APIKey])
async def read_api_keys(
    current_user: UserModel = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> List[APIKey]:
    """
    Get API keys.
    
    Args:
        current_user: Current user.
        db: Database session.
        
    Returns:
        List[APIKey]: API keys.
    """
    return db.query(APIKeyModel).filter(APIKeyModel.user_id == current_user.id).all()


@router.get("/api-keys/{api_key_id}", response_model=APIKey)
async def read_api_key(
    api_key_id: str,
    current_user: UserModel = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> APIKey:
    """
    Get API key.
    
    Args:
        api_key_id: API key ID.
        current_user: Current user.
        db: Database session.
        
    Returns:
        APIKey: API key.
        
    Raises:
        HTTPException: If API key is not found.
    """
    db_api_key = db.query(APIKeyModel).filter(
        APIKeyModel.id == api_key_id,
        APIKeyModel.user_id == current_user.id,
    ).first()
    
    if not db_api_key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API key not found",
        )
    
    return db_api_key


@router.delete("/api-keys/{api_key_id}", response_model=APIKey)
async def delete_api_key(
    api_key_id: str,
    current_user: UserModel = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> APIKey:
    """
    Delete API key.
    
    Args:
        api_key_id: API key ID.
        current_user: Current user.
        db: Database session.
        
    Returns:
        APIKey: Deleted API key.
        
    Raises:
        HTTPException: If API key is not found.
    """
    db_api_key = db.query(APIKeyModel).filter(
        APIKeyModel.id == api_key_id,
        APIKeyModel.user_id == current_user.id,
    ).first()
    
    if not db_api_key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API key not found",
        )
    
    db.delete(db_api_key)
    db.commit()
    
    return db_api_key
