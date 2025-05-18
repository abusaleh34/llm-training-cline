"""
Application settings
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseSettings, Field, validator
import json
import os
from pathlib import Path


class DatabaseSettings(BaseSettings):
    """Database settings"""
    
    host: str = Field("localhost", env="DB_HOST")
    port: int = Field(5432, env="DB_PORT")
    name: str = Field("llm_platform", env="DB_NAME")
    user: str = Field("postgres", env="DB_USER")
    password: str = Field("postgres", env="DB_PASSWORD")
    
    @property
    def connection_string(self) -> str:
        """Get database connection string"""
        return f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.name}"


class APISettings(BaseSettings):
    """API settings"""
    
    host: str = Field("0.0.0.0", env="API_HOST")
    port: int = Field(8000, env="API_PORT")
    debug: bool = Field(False, env="API_DEBUG")
    api_prefix: str = Field("/api/v1", env="API_PREFIX")
    cors_origins: List[str] = Field(["*"], env="API_CORS_ORIGINS")
    
    @validator("cors_origins", pre=True)
    def parse_cors_origins(cls, v):
        """Parse CORS origins from string"""
        if isinstance(v, str):
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                return [i.strip() for i in v.split(",")]
        return v


class SecuritySettings(BaseSettings):
    """Security settings"""
    
    jwt_secret: str = Field("your-secret-key", env="JWT_SECRET")
    jwt_algorithm: str = Field("HS256", env="JWT_ALGORITHM")
    jwt_expiration_minutes: int = Field(60, env="JWT_EXPIRATION_MINUTES")
    api_key_prefix: str = Field("llm_", env="API_KEY_PREFIX")
    
    # Encryption settings
    encryption_master_key: str = Field("", env="ENCRYPTION_MASTER_KEY")
    
    # TLS/SSL settings
    ssl_cert_path: Optional[str] = Field(None, env="SSL_CERT_PATH")
    ssl_key_path: Optional[str] = Field(None, env="SSL_KEY_PATH")
    ssl_ca_path: Optional[str] = Field(None, env="SSL_CA_PATH")
    enable_https: bool = Field(False, env="ENABLE_HTTPS")


class StorageSettings(BaseSettings):
    """Storage settings"""
    
    document_storage_path: Path = Field("/app/documents", env="DOCUMENT_STORAGE_PATH")
    upload_dir: str = Field("uploads", env="UPLOAD_DIR")
    processed_dir: str = Field("processed", env="PROCESSED_DIR")
    temp_dir: str = Field("temp", env="TEMP_DIR")
    
    @validator("document_storage_path", pre=True)
    def create_storage_path(cls, v):
        """Create storage path if it doesn't exist"""
        path = Path(v)
        path.mkdir(parents=True, exist_ok=True)
        return path


class OCRSettings(BaseSettings):
    """OCR settings"""
    
    engine: str = Field("tesseract", env="OCR_ENGINE")
    languages: List[str] = Field(["eng", "ara"], env="OCR_LANGUAGES")
    
    @validator("languages", pre=True)
    def parse_languages(cls, v):
        """Parse languages from string"""
        if isinstance(v, str):
            return [i.strip() for i in v.split(",")]
        return v


class LogSettings(BaseSettings):
    """Log settings"""
    
    level: str = Field("INFO", env="LOG_LEVEL")
    rotation: str = Field("10 MB", env="LOG_ROTATION")


class ModelSettings(BaseSettings):
    """Model settings"""
    
    storage_path: Path = Field("/app/models", env="MODEL_STORAGE_PATH")
    cache_path: Path = Field("/app/cache", env="MODEL_CACHE_PATH")
    max_training_jobs: int = Field(2, env="MAX_TRAINING_JOBS")
    default_batch_size: int = Field(8, env="DEFAULT_BATCH_SIZE")
    default_learning_rate: float = Field(5e-5, env="DEFAULT_LEARNING_RATE")
    
    @validator("storage_path", "cache_path", pre=True)
    def create_path(cls, v):
        """Create path if it doesn't exist"""
        path = Path(v)
        path.mkdir(parents=True, exist_ok=True)
        return path


class VectorDBSettings(BaseSettings):
    """Vector database settings"""
    
    type: str = Field("milvus", env="VECTOR_DB_TYPE")
    host: str = Field("localhost", env="VECTOR_DB_HOST")
    port: int = Field(19530, env="VECTOR_DB_PORT")
    user: str = Field("root", env="VECTOR_DB_USER")
    password: str = Field("milvus", env="VECTOR_DB_PASSWORD")


class AgentSettings(BaseSettings):
    """Agent settings"""
    
    max_deployed_agents: int = Field(5, env="MAX_DEPLOYED_AGENTS")
    agent_timeout_seconds: int = Field(30, env="AGENT_TIMEOUT_SECONDS")
    default_temperature: float = Field(0.7, env="DEFAULT_TEMPERATURE")
    default_top_k: int = Field(50, env="DEFAULT_TOP_K")
    default_top_p: float = Field(0.95, env="DEFAULT_TOP_P")


class Settings(BaseSettings):
    """Application settings"""
    
    app_name: str = Field("LLM Training Platform", env="APP_NAME")
    version: str = Field("1.0.0", env="APP_VERSION")
    description: str = Field(
        "A privacy-focused on-premise platform for training and deploying AI agents using your organization's documents.",
        env="APP_DESCRIPTION"
    )
    environment: str = Field("development", env="ENVIRONMENT")
    
    # Sub-settings
    db: DatabaseSettings = DatabaseSettings()
    api: APISettings = APISettings()
    security: SecuritySettings = SecuritySettings()
    storage: StorageSettings = StorageSettings()
    ocr: OCRSettings = OCRSettings()
    log: LogSettings = LogSettings()
    model: ModelSettings = ModelSettings()
    vector_db: VectorDBSettings = VectorDBSettings()
    agent: AgentSettings = AgentSettings()
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


# Create settings instance
settings = Settings()
