from datetime import datetime
from typing import Optional , List, Dict
from app.core.pinecone_wrapper import safe_index, safe_pc
from app.core.database_wrapper import safe_collection_notes
from app.exceptions.httpExceptionsSave import *
from app.exceptions.httpExceptionsSearch import *
from app.exceptions.global_exceptions import ExternalServiceError, DatabaseConnectionError
from langchain_core.documents import Document
from app.models.notesModel import *
from app.utils.space_extractor import extract_space_from_text, remove_space_pattern_from_text
from app.services.pinecone_service import *

async def get_all_notes_from_db(user_id: str):
    """
    Get all notes for a user with enhanced error handling.
    """
    try:
        if not user_id:
            raise ValidationError("User ID is required")

        notes = await safe_collection_notes.find({"user_id": user_id})
        return [note_model(note) for note in notes]

    except ValidationError:
        # Re-raise validation errors
        raise
    except DatabaseConnectionError as e:
        logger.error(f"Database connection error: {str(e)}")
        raise DatabaseError(f"Database connection failed: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error retrieving notes: {str(e)}", exc_info=True)
        raise DatabaseError(f"Error retrieving notes: {str(e)}")


async def create_note(note: dict, namespace: str):
    """
    Create a new note for a user using default namespace with metadata filtering.
    """
    # Placeholder for actual implementation
    timestamp = datetime.now().strftime("%Y-%d-%m#%H-%M-%S")
    doc_id = f"{namespace}-{timestamp}"

    try:
        # Extract space from note field
        space = extract_space_from_text(note.note) or "general"
        
        # Clean the note text for embedding (remove space pattern)
        clean_note = remove_space_pattern_from_text(note.note) if note.note else note.note
        text_to_embed = f"{note.title}, {clean_note}"
        print(f"Embedding text: {text_to_embed}")
        
        # Prepare metadata with space information and namespace for filtering
        metadata = {
            "doc_id": doc_id,
            "user_id": namespace,
            "namespace": namespace,  # Add namespace to metadata for filtering
            "title": note.title,
            "note": note.note,  # Keep original note with space pattern
            "type": "Note",
            "date": datetime.now().isoformat(),
            "space": space,  # Add extracted space
        }

        # Generate embeddings using safe wrapper
        embedding = await safe_pc.embed(
            model="multilingual-e5-large",
            inputs=[text_to_embed],
            parameters={"input_type": "passage", "truncate": "END"}
        )

        vector = {
            "id": doc_id,
            "values": embedding[0]['values'],
            "metadata": metadata
        }

        # Upsert using safe wrapper - store in default namespace
        await safe_index.upsert(
            vectors=[vector]
            # No namespace parameter = default namespace
        )

        await save_note_to_db(metadata)

        return {"status": "saved", "doc_id": doc_id}

    except (ValidationError, DocumentStorageError):
        # Re-raise our custom exceptions
        raise
    except ExternalServiceError as e:
        logger.error(f"Vector database service error: {str(e)}")
        raise DocumentStorageError(
            message="Vector database service unavailable",
            user_id=namespace,
            doc_id=doc_id
        ) from e
    except Exception as e:
        logger.error(f"Unexpected error creating note: {str(e)}", exc_info=True)
        raise DocumentStorageError(
            message="Failed to save note",
            user_id=namespace,
            doc_id=doc_id
        ) from e


async def search_notes(query: str, namespace: str , filter: dict = None) -> List[Dict]:
    """
    Search notes for a user based on a query.
    """
    return await search_vector_db(
        query=query,
        namespace=namespace,
        filter=filter
    )


async def update_note(note_id: str, note: dict, user_id: str):
    """
    Update an existing note for a user.
    """
    # Placeholder for actual implementation
    note["id"] = note_id
    note["user_id"] = user_id
    return note


async def delete_note(doc_id: str, namespace: str):
    """
    Delete an existing note for a user using metadata filtering.
    """
    try:
        # Delete from vector database using metadata filtering
        vector_result = await delete_from_vector_db(doc_id, namespace)
        
        # Delete from regular database  
        db_result = await delete_note_from_db(doc_id)
        
        return {
            "status": "success",
            "message": "Note deleted successfully",
            "doc_id": doc_id,
            "vector_result": vector_result,
            "db_result": db_result
        }
        
    except Exception as e:
        logger.error(f"Error deleting note: {str(e)}", exc_info=True)
        raise DocumentStorageError(
            message="Failed to delete note",
            user_id=namespace,
            doc_id=doc_id
        ) from e

# Add the missing delete_note_from_db function
async def delete_note_from_db(doc_id: str):
    """
    Delete note from database by doc_id.
    """
    try:
        result = await safe_collection_notes.delete_one({"doc_id": doc_id})
        if result.deleted_count == 0:
            logger.warning(f"No note found with doc_id: {doc_id}")
            return {"status": "not_found", "doc_id": doc_id}
        
        return {"status": "deleted", "doc_id": doc_id, "deleted_count": result.deleted_count}
        
    except DatabaseConnectionError as e:
        logger.error(f"Database connection error: {str(e)}")
        raise DatabaseError(f"Database connection failed: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error deleting note from database: {str(e)}", exc_info=True)
        raise DatabaseError(f"Error deleting note: {str(e)}")

# ======Mongo DB Functions========

async def save_note_to_db(note_data: dict):
    """
    Save note data to the database with enhanced error handling.
    """
    try:
        if not note_data:
            raise ValidationError("Note data is required")

        print(f"Saving note to DB: {note_data}")
        result = await safe_collection_notes.insert_one(note_data)

        if not result.inserted_id:
            raise DatabaseError("Failed to save note")

        note_data["_id"] = str(result.inserted_id)
        return {"status": "saved", "note": note_data}

    except ValidationError:
        # Re-raise validation errors
        raise
    except DatabaseConnectionError as e:
        logger.error(f"Database connection error: {str(e)}")
        raise DatabaseError(f"Database connection failed: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error saving note: {str(e)}", exc_info=True)
        raise DatabaseError(f"Database error: {str(e)}")