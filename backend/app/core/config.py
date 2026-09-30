from typing import List, Union
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
import json
import os


class Settings(BaseSettings):
    PROJECT_NAME: str = "BidGuard AI"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://bidguard:bidguard@localhost:5432/bidguard"
    DATABASE_ECHO: bool = False

    # Security
    SECRET_KEY: str = "bidguard-ai-secret-development-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours

    # Uploads
    UPLOAD_DIR: str = "data/uploads"
    MAX_UPLOAD_SIZE_MB: int = 50
    MAX_DOCUMENT_SIZE_MB: int = 50

    # CORS
    ALLOWED_ORIGINS: Union[List[str], str] = ["http://localhost:3000", "http://localhost:5173", "http://127.0.0.1:5173"]

    # Hugging Face AI Model Stack
    DOCUMENT_MODEL: str = "microsoft/layoutlmv3-base"
    OCR_MODEL: str = "microsoft/trocr-small-printed"
    EMBEDDING_MODEL: str = "BAAI/bge-small-en-v1.5"
    RERANKER_MODEL: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"
    LLM_MODEL: str = "Qwen/Qwen2.5-1.5B-Instruct"
    HUGGINGFACE_API_KEY: Union[str, None] = None
    AI_DEVICE: str = "cpu"
    ENABLE_LOCAL_AI_MODELS: bool = True

    @field_validator("ALLOWED_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str):
            if v.startswith("[") and v.endswith("]"):
                try:
                    return json.loads(v)
                except Exception:
                    pass
            return [i.strip() for i in v.split(",") if i.strip()]
        elif isinstance(v, (list, tuple)):
            return [str(i) for i in v]
        return ["*"]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )


settings = Settings()
