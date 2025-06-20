import logging
import time
from typing import Optional, Any, Dict, List
from functools import wraps
from pinecone.exceptions import PineconeException
from app.exceptions.global_exceptions import ExternalServiceError
from app.core.pineConeDB import pc, index

logger = logging.getLogger(__name__)

class PineconeWrapper:
    """
    Pinecone wrapper with retry logic and graceful error handling
    """
    
    def __init__(self, max_retries: int = 3, retry_delay: float = 1.0):
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self._connection_healthy = True
        
    def check_connection(self) -> bool:
        """Check if Pinecone connection is healthy"""
        try:
            # Try to get index stats as a health check
            stats = index.describe_index_stats()
            self._connection_healthy = True
            return True
        except Exception as e:
            logger.warning(f"Pinecone connection check failed: {str(e)}")
            self._connection_healthy = False
            return False
    
    def retry_on_connection_error(self, func):
        """Decorator to retry Pinecone operations on connection errors"""
        @wraps(func)
        async def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(self.max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                    
                except PineconeException as e:
                    last_exception = e
                    logger.warning(
                        f"Pinecone error on attempt {attempt + 1}/{self.max_retries + 1}: {str(e)}"
                    )
                    
                    if attempt < self.max_retries:
                        wait_time = self.retry_delay * (2 ** attempt)  # Exponential backoff
                        logger.info(f"Retrying Pinecone operation in {wait_time} seconds...")
                        time.sleep(wait_time)
                    else:
                        logger.error(f"All Pinecone retry attempts failed: {str(e)}")
                        raise ExternalServiceError(
                            "Vector database service is temporarily unavailable",
                            details={"attempts": self.max_retries + 1, "error": str(e)}
                        )
                        
                except Exception as e:
                    logger.error(f"Unexpected error in Pinecone operation: {str(e)}")
                    # Don't retry on unexpected errors
                    raise ExternalServiceError(
                        "Vector database operation failed",
                        details={"error": str(e), "operation": func.__name__}
                    )
            
            # This should never be reached, but just in case
            if last_exception:
                raise ExternalServiceError(
                    "Vector database operation failed after all retries",
                    details={"error": str(last_exception)}
                )
                
        return wrapper
    
    @property
    def is_healthy(self) -> bool:
        """Check if the Pinecone connection is currently healthy"""
        return self._connection_healthy

# Create global Pinecone wrapper instance
pinecone_wrapper = PineconeWrapper()

class SafePineconeIndex:
    """
    Safe Pinecone index wrapper that handles errors gracefully
    """
    
    def __init__(self, index, wrapper: PineconeWrapper):
        self._index = index
        self._wrapper = wrapper
    
    @property
    def wrapper(self):
        return self._wrapper
    
    async def upsert(self, vectors: List[Dict], namespace: str = None, **kwargs):
        """Safely upsert vectors"""
        @self._wrapper.retry_on_connection_error
        async def _upsert():
            return self._index.upsert(vectors=vectors, namespace=namespace, **kwargs)
        return await _upsert()
    
    async def query(self, vector: List[float] = None, namespace: str = None, 
                   top_k: int = 10, include_metadata: bool = True, 
                   filter: Dict = None, **kwargs):
        """Safely query vectors"""
        @self._wrapper.retry_on_connection_error
        async def _query():
            return self._index.query(
                vector=vector,
                namespace=namespace,
                top_k=top_k,
                include_metadata=include_metadata,
                filter=filter,
                **kwargs
            )
        return await _query()
    
    async def delete(self, ids: List[str] = None, namespace: str = None, 
                    filter: Dict = None, **kwargs):
        """Safely delete vectors"""
        @self._wrapper.retry_on_connection_error
        async def _delete():
            return self._index.delete(ids=ids, namespace=namespace, filter=filter, **kwargs)
        return await _delete()
    
    async def describe_index_stats(self, **kwargs):
        """Safely get index statistics"""
        @self._wrapper.retry_on_connection_error
        async def _stats():
            return self._index.describe_index_stats(**kwargs)
        return await _stats()

class SafePineconeClient:
    """
    Safe Pinecone client wrapper for embedding operations
    """
    
    def __init__(self, client, wrapper: PineconeWrapper):
        self._client = client
        self._wrapper = wrapper
    
    async def embed(self, model: str, inputs: List[str], parameters: Dict = None, **kwargs):
        """Safely generate embeddings"""
        @self._wrapper.retry_on_connection_error
        async def _embed():
            return self._client.inference.embed(
                model=model,
                inputs=inputs,
                parameters=parameters or {},
                **kwargs
            )
        return await _embed()

# Create safe wrappers
safe_index = SafePineconeIndex(index, pinecone_wrapper)
safe_pc = SafePineconeClient(pc, pinecone_wrapper)

async def get_pinecone_health() -> Dict[str, Any]:
    """Get Pinecone health status"""
    try:
        is_healthy = pinecone_wrapper.check_connection()
        if is_healthy:
            stats = await safe_index.describe_index_stats()
            return {
                "status": "healthy",
                "connection_healthy": True,
                "index_stats": stats,
                "timestamp": time.time()
            }
        else:
            return {
                "status": "unhealthy",
                "connection_healthy": False,
                "timestamp": time.time()
            }
    except Exception as e:
        logger.error(f"Error checking Pinecone health: {str(e)}")
        return {
            "status": "error",
            "connection_healthy": False,
            "error": str(e),
            "timestamp": time.time()
        }
