import logging
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from pymongo.errors import PyMongoError, ConnectionFailure, ServerSelectionTimeoutError
from pinecone.exceptions import PineconeException
from jose import JWTError
from pydantic import ValidationError
import traceback
from typing import Union
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ApplicationError(Exception):
    """Base application exception"""
    def __init__(self, message: str, status_code: int = 500, details: dict = None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        self.timestamp = datetime.now().isoformat()

class DatabaseConnectionError(ApplicationError):
    """Database connection related errors"""
    def __init__(self, message: str = "Database connection failed", details: dict = None):
        super().__init__(message, status_code=503, details=details)

class ExternalServiceError(ApplicationError):
    """External service related errors"""
    def __init__(self, message: str = "External service unavailable", details: dict = None):
        super().__init__(message, status_code=503, details=details)

class AuthenticationError(ApplicationError):
    """Authentication related errors"""
    def __init__(self, message: str = "Authentication failed", details: dict = None):
        super().__init__(message, status_code=401, details=details)

class ValidationError(ApplicationError):
    """Validation related errors"""
    def __init__(self, message: str = "Validation failed", details: dict = None):
        super().__init__(message, status_code=422, details=details)

async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Global exception handler that catches all unhandled exceptions
    and returns appropriate JSON responses instead of crashing the app.
    """
    
    # Log the exception with full traceback
    logger.error(
        f"Unhandled exception in {request.method} {request.url}: {str(exc)}",
        exc_info=True,
        extra={
            "method": request.method,
            "url": str(request.url),
            "client": request.client.host if request.client else "unknown",
            "user_agent": request.headers.get("user-agent", "unknown")
        }
    )
    
    # Handle specific exception types
    if isinstance(exc, ApplicationError):
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": exc.message,
                "details": exc.details,
                "timestamp": exc.timestamp,
                "type": "application_error"
            }
        )
    
    elif isinstance(exc, HTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": exc.detail,
                "timestamp": datetime.now().isoformat(),
                "type": "http_error"
            }
        )
    
    elif isinstance(exc, StarletteHTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": exc.detail,
                "timestamp": datetime.now().isoformat(),
                "type": "http_error"
            }
        )
    
    elif isinstance(exc, RequestValidationError):
        return JSONResponse(
            status_code=422,
            content={
                "error": "Validation error",
                "details": exc.errors(),
                "timestamp": datetime.now().isoformat(),
                "type": "validation_error"
            }
        )
    
    elif isinstance(exc, (ConnectionFailure, ServerSelectionTimeoutError, PyMongoError)):
        return JSONResponse(
            status_code=503,
            content={
                "error": "Database service temporarily unavailable",
                "message": "Please try again later",
                "timestamp": datetime.now().isoformat(),
                "type": "database_error"
            }
        )
    
    elif isinstance(exc, PineconeException):
        return JSONResponse(
            status_code=503,
            content={
                "error": "Vector database service temporarily unavailable",
                "message": "Please try again later",
                "timestamp": datetime.now().isoformat(),
                "type": "vector_db_error"
            }
        )
    
    elif isinstance(exc, JWTError):
        return JSONResponse(
            status_code=401,
            content={
                "error": "Authentication failed",
                "message": "Invalid or expired token",
                "timestamp": datetime.now().isoformat(),
                "type": "auth_error"
            }
        )
    
    # Handle any other unexpected exceptions
    else:
        # Log critical error for investigation
        logger.critical(
            f"Unexpected exception: {type(exc).__name__}: {str(exc)}",
            exc_info=True,
            extra={
                "exception_type": type(exc).__name__,
                "traceback": traceback.format_exc()
            }
        )
        
        return JSONResponse(
            status_code=500,
            content={
                "error": "Internal server error",
                "message": "An unexpected error occurred. Please try again later.",
                "timestamp": datetime.now().isoformat(),
                "type": "internal_error"
            }
        )

def create_error_response(
    message: str, 
    status_code: int = 500, 
    details: dict = None,
    error_type: str = "error"
) -> JSONResponse:
    """Helper function to create consistent error responses"""
    return JSONResponse(
        status_code=status_code,
        content={
            "error": message,
            "details": details or {},
            "timestamp": datetime.now().isoformat(),
            "type": error_type
        }
    )
