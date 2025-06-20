import logging
import time
from typing import Optional, Any, Dict
from functools import wraps
from pymongo.errors import PyMongoError, ConnectionFailure, ServerSelectionTimeoutError
from app.exceptions.global_exceptions import DatabaseConnectionError
from app.core.database import client, db, collection, collection_memories, collection_notes

logger = logging.getLogger(__name__)

class DatabaseWrapper:
    """
    Database wrapper with connection retry logic and graceful error handling
    """
    
    def __init__(self, max_retries: int = 3, retry_delay: float = 1.0):
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self._connection_healthy = True
        
    def check_connection(self) -> bool:
        """Check if database connection is healthy"""
        try:
            # Simple ping to check connection
            client.admin.command('ping')
            self._connection_healthy = True
            return True
        except Exception as e:
            logger.warning(f"Database connection check failed: {str(e)}")
            self._connection_healthy = False
            return False
    
    def retry_on_connection_error(self, func):
        """Decorator to retry database operations on connection errors"""
        @wraps(func)
        async def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(self.max_retries + 1):
                try:
                    # Check connection before attempting operation
                    if not self.check_connection():
                        raise DatabaseConnectionError("Database connection is not healthy")
                    
                    return await func(*args, **kwargs)
                    
                except (ConnectionFailure, ServerSelectionTimeoutError) as e:
                    last_exception = e
                    logger.warning(
                        f"Database connection error on attempt {attempt + 1}/{self.max_retries + 1}: {str(e)}"
                    )
                    
                    if attempt < self.max_retries:
                        wait_time = self.retry_delay * (2 ** attempt)  # Exponential backoff
                        logger.info(f"Retrying in {wait_time} seconds...")
                        time.sleep(wait_time)
                    else:
                        logger.error(f"All database retry attempts failed: {str(e)}")
                        raise DatabaseConnectionError(
                            "Database service is temporarily unavailable",
                            details={"attempts": self.max_retries + 1, "error": str(e)}
                        )
                        
                except PyMongoError as e:
                    logger.error(f"Database operation error: {str(e)}")
                    raise DatabaseConnectionError(
                        "Database operation failed",
                        details={"error": str(e), "operation": func.__name__}
                    )
                    
                except Exception as e:
                    logger.error(f"Unexpected error in database operation: {str(e)}")
                    raise
            
            # This should never be reached, but just in case
            if last_exception:
                raise DatabaseConnectionError(
                    "Database operation failed after all retries",
                    details={"error": str(last_exception)}
                )
                
        return wrapper
    
    @property
    def is_healthy(self) -> bool:
        """Check if the database connection is currently healthy"""
        return self._connection_healthy

# Create global database wrapper instance
db_wrapper = DatabaseWrapper()

class SafeCollection:
    """
    Safe collection wrapper that handles database errors gracefully
    """
    
    def __init__(self, collection, wrapper: DatabaseWrapper):
        self._collection = collection
        self._wrapper = wrapper
    
    @property
    def wrapper(self):
        return self._wrapper
    
    async def insert_one(self, document: Dict[str, Any], **kwargs):
        """Safely insert a document"""
        @self._wrapper.retry_on_connection_error
        async def _insert():
            return self._collection.insert_one(document, **kwargs)
        return await _insert()
    
    async def find_one(self, filter_dict: Dict[str, Any] = None, **kwargs):
        """Safely find one document"""
        @self._wrapper.retry_on_connection_error
        async def _find_one():
            return self._collection.find_one(filter_dict or {}, **kwargs)
        return await _find_one()
    
    async def find(self, filter_dict: Dict[str, Any] = None, **kwargs):
        """Safely find documents"""
        @self._wrapper.retry_on_connection_error
        async def _find():
            return list(self._collection.find(filter_dict or {}, **kwargs))
        return await _find()
    
    async def update_one(self, filter_dict: Dict[str, Any], update: Dict[str, Any], **kwargs):
        """Safely update one document"""
        @self._wrapper.retry_on_connection_error
        async def _update():
            return self._collection.update_one(filter_dict, update, **kwargs)
        return await _update()
    
    async def delete_one(self, filter_dict: Dict[str, Any], **kwargs):
        """Safely delete one document"""
        @self._wrapper.retry_on_connection_error
        async def _delete():
            return self._collection.delete_one(filter_dict, **kwargs)
        return await _delete()
    
    async def count_documents(self, filter_dict: Dict[str, Any] = None, **kwargs):
        """Safely count documents"""
        @self._wrapper.retry_on_connection_error
        async def _count():
            return self._collection.count_documents(filter_dict or {}, **kwargs)
        return await _count()

# Create safe collection wrappers
safe_collection = SafeCollection(collection, db_wrapper)
safe_collection_memories = SafeCollection(collection_memories, db_wrapper)
safe_collection_notes = SafeCollection(collection_notes, db_wrapper)

async def get_database_health() -> Dict[str, Any]:
    """Get database health status"""
    try:
        is_healthy = db_wrapper.check_connection()
        return {
            "status": "healthy" if is_healthy else "unhealthy",
            "connection_healthy": is_healthy,
            "timestamp": time.time()
        }
    except Exception as e:
        logger.error(f"Error checking database health: {str(e)}")
        return {
            "status": "error",
            "connection_healthy": False,
            "error": str(e),
            "timestamp": time.time()
        }
