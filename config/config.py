"""
Configuration settings for the Finance Project.
"""

from pydantic_settings import BaseSettings
from typing import Optional
import os
from functools import lru_cache


class Settings(BaseSettings):
    # Application Settings
    APP_NAME: str = "Financial Management System"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    
    # API Settings
    API_PREFIX: str = "/api/v1"
    BACKEND_CORS_ORIGINS: list[str] = ["http://localhost:3000", "http://localhost:8000"]
    
    # Database Settings
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost/financedb"
    DATABASE_POOL_SIZE: int = 20
    DATABASE_MAX_OVERFLOW: int = 0
    
    # Redis Settings
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # Security Settings
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-here-change-in-production")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # Plaid Settings
    PLAID_CLIENT_ID: Optional[str] = None
    PLAID_SECRET: Optional[str] = None
    PLAID_ENV: str = "development"  # development, sandbox, or production
    PLAID_PRODUCTS: list[str] = ["transactions", "accounts", "liabilities", "investments"]
    PLAID_COUNTRY_CODES: list[str] = ["US"]
    
    # Celery Settings
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"
    
    # File Upload Settings
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10MB
    ALLOWED_FILE_TYPES: list[str] = [".csv", ".ofx", ".qfx", ".pdf", ".xlsx", ".xls"]
    
    # Workflow Settings
    MAX_WORKFLOW_NODES: int = 100
    WORKFLOW_EXECUTION_TIMEOUT: int = 300  # seconds
    
    # Logging Settings
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # Email Settings (for notifications)
    SMTP_HOST: Optional[str] = None
    SMTP_PORT: int = 587
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    SMTP_FROM: str = "noreply@financeapp.local"
    
    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 60
    
    # Feature Flags
    ENABLE_PLAID: bool = True
    ENABLE_MANUAL_IMPORT: bool = True
    ENABLE_WORKFLOW_AUTOMATION: bool = True
    ENABLE_EMAIL_NOTIFICATIONS: bool = False
    
    class Config:
        case_sensitive = True
        env_file = ".env"


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()


# Constants for the application
class EntityType:
    PERSONAL = "personal"
    BUSINESS = "business"
    LLC = "llc"
    CORPORATION = "corporation"


class AccountType:
    CHECKING = "checking"
    SAVINGS = "savings"
    CREDIT_CARD = "credit_card"
    LOAN = "loan"
    INVESTMENT = "investment"
    CASH = "cash"


class TransactionType:
    DEBIT = "debit"
    CREDIT = "credit"
    TRANSFER = "transfer"


class WorkflowNodeType:
    SOURCE = "source"
    DESTINATION = "destination"
    CONDITION = "condition"
    ACTION = "action"
    SCHEDULE = "schedule"
    SPLIT = "split"
    MERGE = "merge"


class WorkflowStatus:
    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    ARCHIVED = "archived"


class InterEntityTransferType:
    EQUITY_CONTRIBUTION = "equity_contribution"
    OWNER_DRAW = "owner_draw"
    DISTRIBUTION = "distribution"
    LOAN_TO_ENTITY = "loan_to_entity"
    LOAN_FROM_ENTITY = "loan_from_entity"
    EXPENSE_REIMBURSEMENT = "expense_reimbursement" 