import logging

logger = logging.getLogger(__name__)

class MemoryServiceError(Exception):
    """Base exception for memory service errors"""
    pass

class MemoryValidationError(MemoryServiceError):
    """Raised when memory data is invalid"""
    pass

class MemoryDatabaseError(MemoryServiceError):
    """Raised when database operations fail"""
    pass

class MemoryNotFoundError(MemoryServiceError):
    """Raised when a requested memory document cannot be found"""
    pass