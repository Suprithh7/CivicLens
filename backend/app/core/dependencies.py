"""
Shared dependencies for dependency injection.
Includes database sessions, authentication, etc.
"""

from app.core.database import get_db

# Re-export for easy imports
__all__ = ["get_db"]
