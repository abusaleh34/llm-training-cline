"""
Authentication handler for the LLM Training Platform.
"""

from datetime import datetime, timedelta
from typing import Dict, Optional, Any, Union

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from src.common.config.settings import settings
from src.common.db.database import get_db
from src.common.models.user import User, UserRole, APIKey

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.api.api_prefix}/auth/token")

# API key scheme
api_key_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.api.api_prefix}/auth/token", auto_error=False)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify password.
    
    Args:
        plain_password: Plain password.
        hashed_password: Hashed password.
        
    Returns:
        bool: True if password is correct, False otherwise.
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """
    Get password hash.
    
    Args:
        password: Plain password.
        
    Returns:
        str: Hashed password.
    """
    return pwd_context.hash(password)


def authenticate_user(db: Session, username: str, password: str) -> Optional[User]:
    """
    Authenticate user.
    
    Args:
        db: Database session.
        username: Username.
        password: Password.
        
    Returns:
        Optional[User]: User if authentication is successful, None otherwise.
    """
    user = db.query(User).filter(User.username == username).first()
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    if not user.is_active:
        return None
    
    # Update last login
    user.last_login = datetime.utcnow()
    db.commit()
    
    return user


def authenticate_api_key(db: Session, api_key: str) -> Optional[User]:
    """
    Authenticate API key.
    
    Args:
        db: Database session.
        api_key: API key.
        
    Returns:
        Optional[User]: User if authentication is successful, None otherwise.
    """
    if not api_key:
        return None
    
    # Get API key prefix (first 8 characters)
    prefix = api_key[:8]
    
    # Get API key from database
    db_api_key = db.query(APIKey).filter(APIKey.prefix == prefix, APIKey.key == api_key).first()
    if not db_api_key:
        return None
    
    # Check if API key is active
    if not db_api_key.is_active:
        return None
    
    # Check if API key is expired
    if db_api_key.expires_at and db_api_key.expires_at < datetime.utcnow():
        return None
    
    # Get user
    user = db.query(User).filter(User.id == db_api_key.user_id).first()
    if not user:
        return None
    
    # Check if user is active
    if not user.is_active:
        return None
    
    return user


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """
    Create access token.
    
    Args:
        data: Token data.
        expires_delta: Token expiration time.
        
    Returns:
        str: Access token.
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.security.jwt_expiration_minutes)
    
    to_encode.update({"exp": expire})
    
    encoded_jwt = jwt.encode(
        to_encode,
        settings.security.jwt_secret,
        algorithm=settings.security.jwt_algorithm,
    )
    
    return encoded_jwt


def get_current_user(
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme),
) -> User:
    """
    Get current user from token.
    
    Args:
        db: Database session.
        token: JWT token.
        
    Returns:
        User: Current user.
        
    Raises:
        HTTPException: If token is invalid or user is not found.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(
            token,
            settings.security.jwt_secret,
            algorithms=[settings.security.jwt_algorithm],
        )
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise credentials_exception
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Inactive user",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user


def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """
    Get current active user.
    
    Args:
        current_user: Current user.
        
    Returns:
        User: Current active user.
        
    Raises:
        HTTPException: If user is inactive.
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user",
        )
    return current_user


def get_current_admin_user(current_user: User = Depends(get_current_user)) -> User:
    """
    Get current admin user.
    
    Args:
        current_user: Current user.
        
    Returns:
        User: Current admin user.
        
    Raises:
        HTTPException: If user is not an admin.
    """
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )
    return current_user


def get_current_manager_user(current_user: User = Depends(get_current_user)) -> User:
    """
    Get current manager user.
    
    Args:
        current_user: Current user.
        
    Returns:
        User: Current manager user.
        
    Raises:
        HTTPException: If user is not a manager or admin.
    """
    if current_user.role not in [UserRole.ADMIN, UserRole.MANAGER]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )
    return current_user


def get_user_from_token_or_api_key(
    db: Session = Depends(get_db),
    token: Optional[str] = Depends(api_key_scheme),
) -> User:
    """
    Get user from token or API key.
    
    Args:
        db: Database session.
        token: JWT token or API key.
        
    Returns:
        User: Current user.
        
    Raises:
        HTTPException: If token or API key is invalid or user is not found.
    """
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Try to get user from token
    try:
        payload = jwt.decode(
            token,
            settings.security.jwt_secret,
            algorithms=[settings.security.jwt_algorithm],
        )
        user_id: str = payload.get("sub")
        if user_id:
            user = db.query(User).filter(User.id == user_id).first()
            if user and user.is_active:
                return user
    except JWTError:
        pass
    
    # Try to get user from API key
    user = authenticate_api_key(db, token)
    if user:
        return user
    
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
