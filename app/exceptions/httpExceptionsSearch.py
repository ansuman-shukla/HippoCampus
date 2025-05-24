from fastapi import HTTPException

# Custom exceptions for business logic
class InvalidRequestError(Exception):
    """Raised when invalid parameters are provided"""
    pass

class VectorDBConnectionError(Exception):
    """Raised when connection to vector database fails"""
    pass

class MissingNamespaceError(Exception):
    """Raised when user namespace is not found"""
    pass

class SearchExecutionError(Exception):
    """Raised when search operation fails"""
    pass
