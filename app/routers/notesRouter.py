from fastapi import APIRouter, Depends , Request
from app.schema.notesSchema import NoteSchema
from app.services.notes_service import *


router = APIRouter(
    prefix="/notes",
    tags=["notes"]
)



@router.get("/")
async def get_all_notes(request: Request):
    """
    Get all notes for a user.
    """
    user_id = request.cookies.get("user_id")
    if not user_id:
        logger.warning("Unauthorized access attempt - missing user ID")
        raise HTTPException(status_code=401, detail="Authentication required")
    return await get_all_notes_from_db(user_id)

@router.post("/")
async def create_new_note(note: NoteSchema, request: Request):
    """
    Create a new note for a user.
    """
    user_id = request.cookies.get("user_id")
    if not user_id:
        logger.warning("Unauthorized access attempt - missing user ID")
        raise HTTPException(status_code=401, detail="Authentication required")
    return await create_note(note, user_id)

@router.put("/{note_id}")
async def update_existing_note(note_id: str, note: dict, request: Request):
    """
    Update an existing note for a user.
    """
    user_id = request.cookies.get("user_id")
    if not user_id:
        logger.warning("Unauthorized update attempt - missing user ID")
        raise HTTPException(status_code=401, detail="Authentication required")
    return await update_note(note_id, note, user_id)

@router.delete("/{note_id}")
async def delete_existing_note(request: Request, note_id: str):
    """
    Delete an existing note for a user.
    """
    user_id = request.cookies.get("user_id")
    if not user_id:
        logger.warning("Unauthorized delete attempt - missing user ID")
        raise HTTPException(status_code=401, detail="Authentication required")
    return await delete_note(note_id, user_id)

