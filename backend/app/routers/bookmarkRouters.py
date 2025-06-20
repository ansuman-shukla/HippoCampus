# links.py - API endpoints
from fastapi import APIRouter , HTTPException , Request 
from app.exceptions.httpExceptionsSearch import *
from app.exceptions.httpExceptionsSave import *
from app.schema.link_schema import Link as link_schema
from typing import List
from langchain_core.documents import Document
from app.services.pinecone_service import *
from app.services.memories_service import *

# https://hippocampus-backend.onrender.com/links/save for saving links
# https://hippocampus-backend.onrender.com/links/search for searching links

router = APIRouter(
    prefix="/links",
    tags=["Links"]
)

@router.post("/save")
async def save_link(
    link_data: link_schema,
    request: Request
):
    """Endpoint for saving links to vector database"""
    user_id = request.cookies.get("user_id")
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
async def search_links(
    query: str,
    request: Request,
    filter: dict = None,
):
    """API endpoint for document search"""

    user_id = request.cookies.get("user_id")
    if not user_id:
        logger.warning("Unauthorized save attempt - missing user ID")
        raise HTTPException(status_code=401, detail="Authentication required")

    try:
        logger.info(f"Attempting to search document for user {user_id}")
        result = await search_vector_db(query=query, namespace=user_id, filter=filter)
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
async def delete_link(
    doc_id_pincone: str,
    request: Request
):
    user_id = request.cookies.get("user_id")
    if not user_id:
        logger.warning("Unauthorized save attempt - missing user ID")
        raise HTTPException(status_code=401, detail="Authentication required")
    
    try:
        logger.info(f"Attempting to delete document for user {user_id}")
        result = await delete_from_vector_db(doc_id=doc_id_pincone, namespace=user_id)
        await delete_from_db(doc_id_pincone)
        logger.info(f"Successfully deleted document for user {user_id}")
        return result
    except DocumentSaveError as e:
        logger.error(f"Document save failed for user {e.user_id}: {str(e)}", exc_info=True)
        status_code = 400 if isinstance(e, InvalidURLError) else 503
        raise HTTPException(status_code=status_code, detail=str(e))
    except ValidationError as e:
        logger.error(f"Invalid document data for user {user_id}: {str(e)}")
        raise HTTPException(status_code=422, detail="Invalid document format")
    


@router.get("/get")
async def get_all_bookmarks(request: Request):
    user_id = request.cookies.get("user_id")
    if not user_id:
        logger.warning("Unauthorized save attempt - missing user ID")
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
    