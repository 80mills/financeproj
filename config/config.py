"""
Configuration settings for the Finance Project.
"""

import os
from typing import Dict, Any

class Config:
    """Base configuration class."""
    
    # Project settings
    PROJECT_NAME = "Finance Project"
    VERSION = "1.0.0"
    
    # Data settings
    DATA_DIR = "data"
    RAW_DATA_DIR = os.path.join(DATA_DIR, "raw")
    PROCESSED_DATA_DIR = os.path.join(DATA_DIR, "processed")
    
    # API settings
    API_BASE_URL = os.getenv("API_BASE_URL", "")
    API_KEY = os.getenv("API_KEY", "")
    
    # Database settings
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///finance.db")
    
    @classmethod
    def get_config(cls) -> Dict[str, Any]:
        """Get all configuration as a dictionary."""
        return {
            key: value for key, value in cls.__dict__.items()
            if not key.startswith('_') and key.isupper()
        } 