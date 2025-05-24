from app.core.database import collection_memories
# from app.schema.link_schema import Memory_Schema
import logging
from typing import Dict, Any
from bson.errors import InvalidId 
from bson import ObjectId  # Changed this line
from app.models.bookmarkModels import *
from pymongo.errors import PyMongoError
from app.schema.bookmarksSchema import Memory_Schema
from app.exceptions.databaseExceptions import *

logger = logging.getLogger(__name__)

async def save_memory_to_db(memory_data: Memory_Schema):

    try:
    # Validate memory data
        if not memory_data:
            raise MemoryValidationError("Memory data cannot be empty")

        
        # Additional validation checks
        if not memory_data.get("title"):
            raise MemoryValidationError("Memory must have a title")
    
        # Save to database
        result = collection_memories.insert_one(memory_data)
        
        if not result.inserted_id:
            raise MemoryDatabaseError("Failed to save memory")

        # Fixed ObjectId usage
        memory_data["_id"] = str(result.inserted_id)
        logger.info(f"Successfully saved memory with id {result.inserted_id}")
        
        return {"status": "saved", "memory": memory_data}

    except PyMongoError as e:
        logger.error(f"Database error: {str(e)}")
        raise MemoryDatabaseError(f"Database error: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        raise MemoryServiceError(f"Error saving memory: {str(e)}")



async def get_all_bookmarks_from_db(user_id):
    try:
        results = collection_memories.find({"user_id": user_id})
        return bookmarkModels(results)
    except PyMongoError as e:
        logger.error(f"Database error: {str(e)}")
        raise MemoryDatabaseError(f"Database error: {str(e)}")
    

    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        raise MemoryServiceError(f"Error saving memory: {str(e)}")
    

async def delete_from_db(doc_id_pincone: str):
    try:
        result = collection_memories.delete_one({"doc_id": doc_id_pincone})
        if result.deleted_count == 0:
            raise MemoryNotFoundError(f"Memory with id {doc_id_pincone} not found")     #exception to be added in exceptions file
        return {"status": "deleted"}
    except PyMongoError as e:
        logger.error(f"Database error: {str(e)}")
        raise MemoryDatabaseError(f"Database error: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        raise MemoryServiceError(f"Error saving memory: {str(e)}")