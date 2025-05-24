from datetime import datetime
from typing import Optional , List, Dict
from app.core.pineConeDB import index, pc
from app.exceptions.httpExceptionsSave import *
from app.exceptions.httpExceptionsSearch import *
from app.exceptions.httpExceptionsSave import *
from langchain_core.documents import Document
from app.core.database import collection_notes 
from app.models.notesModel import *
from app.services.pinecone_service import *

async def get_all_notes_from_db(user_id: str):
    """
    Get all notes for a user.
    """
    notes = collection_notes.find({"user_id": user_id})
    return [note_model(note) for note in notes]


async def create_note(note: dict, namespace: str):
    """
    Create a new note for a user.
    """
    # Placeholder for actual implementation
    timestamp = datetime.now().strftime("%Y-%d-%m#%H-%M-%S")
    doc_id = f"{namespace}-{timestamp}"

    try:

        text_to_embed = f"{note.title}, {note.note}"
        print(f"Embedding text: {text_to_embed}")
        # Simulate embedding process
        metadata = {
            "doc_id": doc_id,
            "user_id": namespace,
            "title": note.title,
            "note": note.note,
            "type": "Note",
            "date": datetime.now().isoformat(),
        }

        embedding = pc.inference.embed(
            model="multilingual-e5-large",
            inputs=[text_to_embed],
            parameters={"input_type": "passage", "truncate": "END"}
        )

        vector = {
            "id": doc_id,
            "values": embedding[0]['values'],
            "metadata": metadata
        }

        index.upsert(
            vectors=[vector],
            namespace=namespace
        )

        await save_note_to_db(metadata)

        return {"status": "saved", "doc_id": doc_id}

    except Exception as e:
        raise DocumentStorageError(
            message="Failed to save document",
            user_id=namespace,
            doc_id=doc_id
        ) from e

    except Exception as e:
        raise Exception(f"Error creating note: {str(e)}")


async def search_notes(query: str, namespace: str) -> List[Dict]:
    """
    Search notes for a user based on a query.
    """
    return await search_vector_db(
        query=query,
        namespace=namespace,
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
    Delete an existing note for a user.
    """
    # Placeholder for actual implementation
    return await delete_from_vector_db(doc_id, namespace)

# ======Mongo DB Functions========

async def save_note_to_db(note_data: dict):
    """
    Save note data to the database.
    """
    try:
        print(f"Saving note to DB: {note_data}")
        collection_notes.insert_one(note_data)
        note_data["_id"] = str(note_data["_id"])
        return {"status": "saved", "note": note_data}

    except Exception as e:
        raise DatabaseError(f"Database error: {str(e)}")