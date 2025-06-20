from app.core.database_wrapper import safe_collection_memories
import logging
from typing import Dict, Any
from bson.errors import InvalidId
from bson import ObjectId
from app.models.bookmarkModels import *
from pymongo.errors import PyMongoError
from app.schema.bookmarksSchema import Memory_Schema
from app.exceptions.databaseExceptions import *
from app.exceptions.global_exceptions import DatabaseConnectionError

logger = logging.getLogger(__name__)

async def save_memory_to_db(memory_data: Memory_Schema):
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
    Delete a memory document with enhanced error handling
    """
    try:
        if not doc_id_pincone:
            raise MemoryValidationError("Document ID is required")

        result = await safe_collection_memories.delete_one({"doc_id": doc_id_pincone})

        if result.deleted_count == 0:
            raise MemoryNotFoundError(f"Memory with id {doc_id_pincone} not found")

        logger.info(f"Successfully deleted memory with id {doc_id_pincone}")
        return {"status": "deleted"}

    except (MemoryValidationError, MemoryNotFoundError):
        # Re-raise our custom exceptions
        raise
    except DatabaseConnectionError as e:
        logger.error(f"Database connection error: {str(e)}")
        raise MemoryDatabaseError(f"Database connection failed: {str(e)}")
    except PyMongoError as e:
        logger.error(f"Database error: {str(e)}")
        raise MemoryDatabaseError(f"Database error: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error deleting memory: {str(e)}", exc_info=True)
        raise MemoryServiceError(f"Error deleting memory: {str(e)}")