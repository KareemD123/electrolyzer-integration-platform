"""
Application configuration using Pydantic Settings

This module loads configuration from environment variables and provides
a centralized settings object for the entire application.
"""
from pydantic_settings import BaseSettings
from typing import List
import json


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables
    
    All settings can be overridden by setting environment variables
    with the same name. For example, to change DEBUG, set DEBUG=False
    in your .env file.
    """
    
    # Application metadata
    APP_NAME: str = "Electrolyzer Integration Toolkit"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    
    # API configuration
    API_V1_PREFIX: str = "/api/v1"
    CORS_ORIGINS: List[str] = ["http://localhost:5173"]
    
    # Data storage
    DATA_DIR: str = "./app/data"
    
    class Config:
        env_file = ".env"
        case_sensitive = True
    
    @property
    def cors_origins_list(self) -> List[str]:
        """
        Parse CORS_ORIGINS if it's a JSON string
        
        This allows setting CORS_ORIGINS as either a JSON array string
        or a Python list in the .env file.
        """
        if isinstance(self.CORS_ORIGINS, str):
            try:
                return json.loads(self.CORS_ORIGINS)
            except json.JSONDecodeError:
                return [self.CORS_ORIGINS]
        return self.CORS_ORIGINS


# Create global settings instance
settings = Settings()
