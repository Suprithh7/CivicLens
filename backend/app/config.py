from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    """
    Application configuration using Pydantic Settings.
    Reads from environment variables or .env file.
    """
    
    # Application
    APP_NAME: str = "CivicLens AI"
    APP_VERSION: str = "0.1.0"
    ENVIRONMENT: str = "development"
    
    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./civiclens.db"
    
    # CORS
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:5173"
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_DIR: str = "logs"
    LOG_TO_FILE: bool = True
    LOG_TO_CONSOLE: bool = True
    LOG_JSON_FORMAT: bool = False
    
    @property
    def cors_origins_list(self) -> List[str]:
        """Convert comma-separated CORS origins to list."""
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# Global settings instance
settings = Settings()

