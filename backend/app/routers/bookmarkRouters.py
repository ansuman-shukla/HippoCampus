# links.py - API endpoints
from fastapi import APIRouter , HTTPException , Request 
from app.exceptions.httpExceptionsSearch import *
from app.exceptions.httpExceptionsSave import *
from app.schema.link_schema import Link as link_schema
from typing import List, Optional, Dict
from langchain_core.documents import Document
from app.services.pinecone_service import *
from app.services.memories_service import *
from app.core.rate_limiter import limiter
from pydantic import BaseModel

# https://hippocampus-backend.onrender.com/links/save for saving links
# https://hippocampus-backend.onrender.com/links/search for searching links

router = APIRouter(
    prefix="/links",
    tags=["Links"]
)

class SearchRequest(BaseModel):
    query: str
    filter: Optional[Dict] = None

@router.post("/save")
@limiter.limit("10/minute")
async def save_link(
    link_data: link_schema,
    request: Request
):
    """Endpoint for saving links to vector database"""
    user_id = getattr(request.state, 'user_id', None)
    if not user_id:
        logger.warning("Unauthorized save attempt - missing user ID")
        raise HTTPException(status_code=401, detail="Authentication required")
    
    try:
        logger.info(f"Attempting to save document for user {user_id}")
        result = await save_to_vector_db(obj=link_data, namespace=user_id)
        logger.info(f"Successfully saved document for user {user_id}")
        return result
    except DocumentSaveError as e:
        logger.error(f"Document save failed for user {e.user_id}: {str(e)}", exc_info=True)
        status_code = 400 if isinstance(e, InvalidURLError) else 503
        raise HTTPException(status_code=status_code, detail=str(e))
    except ValidationError as e:
        logger.error(f"Invalid document data for user {user_id}: {str(e)}")
        raise HTTPException(status_code=422, detail="Invalid document format")
    except Exception as e:
        logger.critical(f"Unexpected error saving document for user {user_id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/search")
@limiter.limit("15/minute")
async def search_links(
    search_request: SearchRequest,
    request: Request,
):
    """API endpoint for document search"""
    user_id = getattr(request.state, 'user_id', None)
    if not user_id:
        logger.warning("Unauthorized search attempt - missing user ID")
        raise HTTPException(status_code=401, detail="Authentication required")

    try:
        logger.info(f"Attempting to search document for user {user_id}")
        result = await search_vector_db(query=search_request.query, namespace=user_id, filter=search_request.filter)
        logger.info(f"Successfully searched document for user {user_id}")
        return result
    except InvalidRequestError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except (MissingNamespaceError, SearchExecutionError) as e:
        raise HTTPException(status_code=404, detail=str(e))
    except VectorDBConnectionError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")

@router.delete("/delete")
@limiter.limit("15/minute")
async def delete_link(
    doc_id_pincone: str,
    request: Request
):
    """Delete a link/bookmark with comprehensive logging for debugging"""
    # Log the initial request details
    logger.info(f"=== DELETE REQUEST STARTED ===")
    logger.info(f"Received delete request for doc_id_pincone: '{doc_id_pincone}'")
    logger.info(f"Request URL: {request.url}")
    logger.info(f"Request method: {request.method}")
    logger.info(f"Query params: {dict(request.query_params)}")
    
    # Validate doc_id_pincone parameter
    if not doc_id_pincone or doc_id_pincone.strip() == "":
        logger.error(f"Empty doc_id_pincone received: '{doc_id_pincone}'")
        raise HTTPException(status_code=400, detail="Document ID is required and cannot be empty")
    
    if doc_id_pincone == "undefined" or doc_id_pincone == "null":
        logger.error(f"Invalid doc_id_pincone received: '{doc_id_pincone}' - Frontend is sending undefined/null value")
        raise HTTPException(status_code=400, detail="Invalid document ID: Frontend sent undefined/null value")
    
    logger.info(f"doc_id_pincone validation passed: '{doc_id_pincone}'")
    
    # Validate user authentication
    user_id = getattr(request.state, 'user_id', None)
    if not user_id:
        logger.warning("Unauthorized delete attempt - missing user ID")
        raise HTTPException(status_code=401, detail="Authentication required")
    
    logger.info(f"User authentication passed - user_id: '{user_id}'")
    
    try:
        logger.info(f"=== STARTING DELETE OPERATIONS ===")
        logger.info(f"Attempting to delete document '{doc_id_pincone}' for user '{user_id}'")
        
        # Step 1: Delete from vector database
        logger.info(f"STEP 1: Deleting from vector database...")
        vector_result = await delete_from_vector_db(doc_id=doc_id_pincone, namespace=user_id)
        logger.info(f"STEP 1 SUCCESS: Vector database deletion completed: {vector_result}")
        
        # Step 2: Delete from regular database
        logger.info(f"STEP 2: Deleting from regular database...")
        db_result = await delete_from_db(doc_id_pincone)
        logger.info(f"STEP 2 SUCCESS: Regular database deletion completed: {db_result}")
        
        logger.info(f"=== DELETE OPERATIONS COMPLETED SUCCESSFULLY ===")
        logger.info(f"Successfully deleted document '{doc_id_pincone}' for user '{user_id}'")
        
        return {
            "status": "success",
            "message": "Document deleted successfully",
            "doc_id": doc_id_pincone,
            "vector_result": vector_result,
            "db_result": db_result
        }
        
    except InvalidRequestError as e:
        logger.error(f"DELETE FAILED: Invalid request - {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except VectorDBConnectionError as e:
        logger.error(f"DELETE FAILED: Vector database connection error - {str(e)}")
        raise HTTPException(status_code=503, detail=f"Vector database unavailable: {str(e)}")
    except DocumentStorageError as e:
        logger.error(f"DELETE FAILED: Document storage error - {str(e)}")
        raise HTTPException(status_code=503, detail=f"Storage service error: {str(e)}")
    except Exception as e:
        logger.critical(f"DELETE FAILED: Unexpected error deleting document '{doc_id_pincone}' for user '{user_id}': {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error during deletion")

@router.get("/get")
@limiter.limit("20/minute")
async def get_all_bookmarks(request: Request):
    user_id = getattr(request.state, 'user_id', None)
    if not user_id:
        logger.warning("Unauthorized get attempt - missing user ID")
        raise HTTPException(status_code=401, detail="Authentication required")
    
    try:
        logger.info(f"Attempting to get all documents for user {user_id}")
        result = await get_all_bookmarks_from_db(user_id)
        logger.info(f"Successfully retrieved all documents for user {user_id}")
        return result
    except DocumentSaveError as e:
        logger.error(f"Document save failed for user {e.user_id}: {str(e)}", exc_info=True)
        status_code = 400 if isinstance(e, InvalidURLError) else 503
        raise HTTPException(status_code=status_code, detail=str(e))
    except ValidationError as e:
        logger.error(f"Invalid document data for user {user_id}: {str(e)}")
        raise HTTPException(status_code=422, detail="Invalid document format")  
    except Exception as e:
        logger.critical(f"Unexpected error saving document for user {user_id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")
    