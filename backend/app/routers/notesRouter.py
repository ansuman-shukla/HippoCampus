from fastapi import APIRouter, Depends , Request, HTTPException
from app.schema.notesSchema import NoteSchema
from app.services.notes_service import *
from app.exceptions.global_exceptions import create_error_response
from app.core.rate_limiter import limiter
import logging

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/notes",
    tags=["notes"]
)

@router.get("/")
@limiter.limit("20/minute")
async def get_all_notes(request: Request):
    """
    Get all notes for a user with enhanced error handling.
    """
    try:
        user_id = getattr(request.state, 'user_id', None)
        if not user_id:
            logger.warning("Unauthorized access attempt - missing user ID")
            return create_error_response(
                "Authentication required",
                status_code=401,
                error_type="auth_error"
            )

        logger.info(f"Retrieving all notes for user {user_id}")
        result = await get_all_notes_from_db(user_id)
        logger.info(f"Successfully retrieved {len(result)} notes for user {user_id}")
        return result

    except ValidationError as e:
        logger.error(f"Validation error: {str(e)}")
        return create_error_response(
            str(e),
            status_code=422,
            error_type="validation_error"
        )
    except DatabaseError as e:
        logger.error(f"Database error retrieving notes: {str(e)}")
        return create_error_response(
            "Unable to retrieve notes at this time",
            status_code=503,
            error_type="database_error"
        )
    except Exception as e:
        logger.error(f"Unexpected error retrieving notes: {str(e)}", exc_info=True)
        return create_error_response(
            "An unexpected error occurred",
            status_code=500,
            error_type="internal_error"
        )

@router.post("/")
@limiter.limit("15/minute")
async def create_new_note(note: NoteSchema, request: Request):
    """
    Create a new note for a user with enhanced error handling.
    """
    try:
        user_id = getattr(request.state, 'user_id', None)
        if not user_id:
            logger.warning("Unauthorized access attempt - missing user ID")
            return create_error_response(
                "Authentication required",
                status_code=401,
                error_type="auth_error"
            )

        logger.info(f"Creating new note for user {user_id}")
        result = await create_note(note, user_id)
        logger.info(f"Successfully created note for user {user_id}")
        return result

    except ValidationError as e:
        logger.error(f"Validation error creating note: {str(e)}")
        return create_error_response(
            str(e),
            status_code=422,
            error_type="validation_error"
        )
    except DocumentStorageError as e:
        logger.error(f"Storage error creating note: {str(e)}")
        return create_error_response(
            "Unable to save note at this time",
            status_code=503,
            error_type="storage_error"
        )
    except Exception as e:
        logger.error(f"Unexpected error creating note: {str(e)}", exc_info=True)
        return create_error_response(
            "An unexpected error occurred",
            status_code=500,
            error_type="internal_error"
        )

@router.put("/{note_id}")
@limiter.limit("15/minute")
async def update_existing_note(note_id: str, note: dict, request: Request):
    """
    Update an existing note for a user.
    """
    user_id = getattr(request.state, 'user_id', None)
    if not user_id:
        logger.warning("Unauthorized update attempt - missing user ID")
        raise HTTPException(status_code=401, detail="Authentication required")
    return await update_note(note_id, note, user_id)

@router.post("/search")
@limiter.limit("15/minute")
async def search_notes_by_query(request: Request, query: str , filter: dict = None):
    """
    Search notes for a user based on a query string.
    """
    user_id = getattr(request.state, 'user_id', None)
    if not user_id:
        logger.warning("Unauthorized search attempt - missing user ID")
        raise HTTPException(status_code=401, detail="Authentication required")
    return await search_notes(query=query, namespace=user_id, filter=filter)

@router.delete("/{note_id}")
@limiter.limit("15/minute")
async def delete_existing_note(request: Request, note_id: str):
    """
    Delete an existing note for a user.
    """
    user_id = getattr(request.state, 'user_id', None)
    if not user_id:
        logger.warning("Unauthorized delete attempt - missing user ID")
        raise HTTPException(status_code=401, detail="Authentication required")
    return await delete_note(note_id, user_id)

