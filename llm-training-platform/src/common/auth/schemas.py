"""
Authentication schemas for the LLM Training Platform.
"""

from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, EmailStr, Field, validator


class Token(BaseModel):
    """Token schema."""
    
    access_token: str
    token_type: str


class TokenData(BaseModel):
    """Token data schema."""
    
    sub: Optional[str] = None
    exp: Optional[datetime] = None


class UserBase(BaseModel):
    """User base schema."""
    
    username: str
    email: EmailStr
    full_name: str
    is_active: bool = True


class UserCreate(UserBase):
    """User create schema."""
    
    password: str = Field(..., min_length=8)
    role: str = "USER"
    
    @validator("role")
    def validate_role(cls, v):
        """Validate role."""
        if v not in ["ADMIN", "MANAGER", "USER"]:
            raise ValueError("Invalid role")
        return v


class UserUpdate(BaseModel):
    """User update schema."""
    
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    is_active: Optional[bool] = None
    role: Optional[str] = None
    
    @validator("role")
    def validate_role(cls, v):
        """Validate role."""
        if v is not None and v not in ["ADMIN", "MANAGER", "USER"]:
            raise ValueError("Invalid role")
        return v


class UserInDB(UserBase):
    """User in database schema."""
    
    id: str
    role: str
    created_at: datetime
    updated_at: datetime
    last_login: Optional[datetime] = None
    
    class Config:
        """Pydantic config."""
        
        orm_mode = True


class User(UserInDB):
    """User schema."""
    
    pass


class APIKeyBase(BaseModel):
    """API key base schema."""
    
    name: str


class APIKeyCreate(APIKeyBase):
    """API key create schema."""
    
    expires_days: Optional[int] = None


class APIKeyInDB(APIKeyBase):
    """API key in database schema."""
    
    id: str
    prefix: str
    is_active: bool
    created_at: datetime
    updated_at: datetime
    expires_at: Optional[datetime] = None
    user_id: str
    
    class Config:
        """Pydantic config."""
        
        orm_mode = True


class APIKey(APIKeyInDB):
    """API key schema."""
    
    pass


class APIKeyWithValue(APIKey):
    """API key with value schema."""
    
    key: str
