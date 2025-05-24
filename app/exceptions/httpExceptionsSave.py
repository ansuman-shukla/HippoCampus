import logging
from fastapi import HTTPException
from typing import Optional
from datetime import datetime
from pydantic import ValidationError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DocumentSaveError(Exception):
    """Base exception for document saving failures"""
    def __init__(self, message: str, user_id: Optional[str] = None, doc_id: Optional[str] = None):
        super().__init__(message)
        self.user_id = user_id
        self.doc_id = doc_id

class InvalidURLError(DocumentSaveError):
    """Raised when a URL is malformed or unsupported"""
    pass

class VectorDBConnectionError(DocumentSaveError):
    """Raised when connection to vector database fails"""
    pass

class DocumentStorageError(DocumentSaveError):
    """Raised when document storage operation fails"""
    pass


class DatabaseError(DocumentSaveError):
    """Raised when a database operation fails"""
    pass