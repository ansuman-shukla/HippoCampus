from app.core.database_wrapper import safe_collection_memories
import logging
from typing import Dict, Any
from bson.errors import InvalidId
from bson import ObjectId
from app.models.bookmarkModels import *
from pymongo.errors import PyMongoError
# Removed Memory_Schema import since we're using dict instead
from app.exceptions.databaseExceptions import *
from app.exceptions.global_exceptions import DatabaseConnectionError

logger = logging.getLogger(__name__)

async def save_memory_to_db(memory_data: dict):
    """
    Save memory data to database with enhanced error handling
    """
    try:
        # Validate memory data
        if not memory_data:
            raise MemoryValidationError("Memory data cannot be empty")

        # Additional validation checks
        if not memory_data.get("title"):
            raise MemoryValidationError("Memory must have a title")

        # Save to database using safe wrapper
        result = await safe_collection_memories.insert_one(memory_data)

        if not result.inserted_id:
            raise MemoryDatabaseError("Failed to save memory")

        # Fixed ObjectId usage
        memory_data["_id"] = str(result.inserted_id)
        logger.info(f"Successfully saved memory with id {result.inserted_id}")

        return {"status": "saved", "memory": memory_data}

    except (MemoryValidationError, MemoryDatabaseError):
        # Re-raise our custom exceptions
        raise
    except DatabaseConnectionError as e:
        logger.error(f"Database connection error: {str(e)}")
        raise MemoryDatabaseError(f"Database connection failed: {str(e)}")
    except PyMongoError as e:
        logger.error(f"Database error: {str(e)}")
        raise MemoryDatabaseError(f"Database error: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error saving memory: {str(e)}", exc_info=True)
        raise MemoryServiceError(f"Error saving memory: {str(e)}")



async def get_all_bookmarks_from_db(user_id):
    """
    Get all bookmarks for a user with enhanced error handling
    """
    try:
        if not user_id:
            raise MemoryValidationError("User ID is required")

        results = await safe_collection_memories.find({"user_id": user_id})
        return bookmarkModels(results)

    except MemoryValidationError:
        # Re-raise validation errors
        raise
    except DatabaseConnectionError as e:
        logger.error(f"Database connection error: {str(e)}")
        raise MemoryDatabaseError(f"Database connection failed: {str(e)}")
    except PyMongoError as e:
        logger.error(f"Database error: {str(e)}")
        raise MemoryDatabaseError(f"Database error: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error retrieving bookmarks: {str(e)}", exc_info=True)
        raise MemoryServiceError(f"Error retrieving bookmarks: {str(e)}")


async def delete_from_db(doc_id_pincone: str):
    """
    Delete a memory document with enhanced error handling and comprehensive logging
    """
    logger.info(f"=== DATABASE DELETE STARTED ===")
    logger.info(f"delete_from_db called with doc_id_pincone: '{doc_id_pincone}'")
    
    try:
        # Input validation with detailed logging
        if not doc_id_pincone:
            logger.error(f"VALIDATION FAILED: doc_id_pincone is empty or None: '{doc_id_pincone}'")
            raise MemoryValidationError("Document ID is required")

        logger.info(f"Input validation passed - doc_id_pincone: '{doc_id_pincone}'")
        
        # Check database connection
        logger.info("Checking database connection...")
        try:
            # Test connection with a simple operation
            await safe_collection_memories.find_one({"doc_id": doc_id_pincone})
            logger.info("Database connection successful")
        except Exception as conn_e:
            logger.error(f"Database connection test failed: {str(conn_e)}")
            raise DatabaseConnectionError(f"Failed to connect to database: {str(conn_e)}")
        
        # Perform the delete operation
        logger.info(f"Attempting to delete document with doc_id: '{doc_id_pincone}' from memories collection")
        
        result = await safe_collection_memories.delete_one({"doc_id": doc_id_pincone})
        
        logger.info(f"Database delete operation completed. Deleted count: {result.deleted_count}")
        
        if result.deleted_count == 0:
            logger.warning(f"DOCUMENT NOT FOUND: No document found with doc_id: '{doc_id_pincone}'")
            raise MemoryNotFoundError(f"Memory with id {doc_id_pincone} not found")

        logger.info(f"=== DATABASE DELETE COMPLETED SUCCESSFULLY ===")
        logger.info(f"Successfully deleted memory with id '{doc_id_pincone}' (deleted_count: {result.deleted_count})")
        
        return {"status": "deleted", "doc_id": doc_id_pincone, "deleted_count": result.deleted_count}

    except (MemoryValidationError, MemoryNotFoundError) as e:
        logger.error(f"DATABASE DELETE FAILED: {type(e).__name__} - {str(e)}")
        # Re-raise our custom exceptions
        raise
    except DatabaseConnectionError as e:
        logger.error(f"DATABASE DELETE FAILED: Database connection error - {str(e)}")
        raise MemoryDatabaseError(f"Database connection failed: {str(e)}")
    except PyMongoError as e:
        logger.error(f"DATABASE DELETE FAILED: PyMongo error - {str(e)}")
        raise MemoryDatabaseError(f"Database error: {str(e)}")
    except Exception as e:
        logger.error(f"DATABASE DELETE FAILED: Unexpected error deleting memory '{doc_id_pincone}': {str(e)}", exc_info=True)
        raise MemoryServiceError(f"Error deleting memory: {str(e)}")