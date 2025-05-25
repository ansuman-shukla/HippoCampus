from datetime import datetime
from typing import List, Optional, Dict
from app.core.pineConeDB import index, pc
from langchain_core.documents import Document
from app.core.config import settings
from app.schema.link_schema import Link as LinkSchema
from app.utils.site_name_extractor import extract_site_name
from app.services.memories_service import save_memory_to_db
from app.exceptions.httpExceptionsSearch import *
from app.exceptions.httpExceptionsSave import *

async def save_to_vector_db(obj: LinkSchema, namespace: str):
    """Save document to vector database using E5 embeddings"""
    
    # Convert timestamp to integer for cleaner ID
    timestamp = datetime.now().strftime("%Y-%d-%m#%H-%M-%S")
    doc_id = f"{namespace}-{timestamp}"

    print(f"Saving document with ID: {doc_id}")
    
    logger_context = {
        "user_id": namespace,
        "doc_id": doc_id,
        "url": obj.link
    }

    try:
        # Extract site name and prepare metadata
        site_name = await extract_site_name(obj.link) or "Unknown Site"
        text_to_embed = f"{obj.title}, {obj.note}, {site_name}"
        
        metadata = {
            "doc_id": doc_id,
            "user_id": namespace,
            "title": obj.title,
            "note": obj.note,
            "source_url": obj.link,
            "site_name": site_name,
            "type": "Bookmark",
            "date": datetime.now().isoformat(),
        }

        # Generate E5 embeddings
        embedding = pc.inference.embed(
            model="multilingual-e5-large",
            inputs=[text_to_embed],
            parameters={"input_type": "passage", "truncate": "END"}
        )

        # Prepare and upsert vector
        vector = {
            "id": doc_id,
            "values": embedding[0]['values'],
            "metadata": metadata
        }

        index.upsert(
            vectors=[vector],
            namespace=namespace
        )

        # Save to database
        await save_memory_to_db(metadata)

        return {"status": "saved", "doc_id": doc_id}

    except Exception as e:
        logger.error("Error saving document", extra=logger_context, exc_info=True)
        raise DocumentStorageError(
            message="Failed to save document",
            user_id=namespace,
            doc_id=doc_id
        ) from e

async def search_vector_db(
    query: str,
    namespace: Optional[str],
    filter: Optional[Dict] = None,
    top_k: int = 10
) -> List[Document]:
    """Search using E5 embeddings"""

    if not namespace:
        raise InvalidRequestError("Missing user uuid - please login")
    
    if not query or len(query.strip()) < 3:
        raise InvalidRequestError("Search query must be at least 3 characters")

    try:
        # Generate query embedding
        embedding = pc.inference.embed(
            model="multilingual-e5-large",
            inputs=[query],
            parameters={"input_type": "query", "truncate": "END"}
        )

        # Perform vector search
        results = index.query(
            namespace=namespace,
            vector=embedding[0]['values'],
            top_k=top_k,
            include_metadata=True,
            filter=filter
        )

        # Convert to Langchain documents format
        documents = []

        if documents is None:
            print("No documents found in the search results")

        for match in results['matches']:
            doc_id = match['id']
            metadata = match['metadata']
            print(f"{namespace} , Processing document ID: {doc_id} with metadata: {metadata}")


            if metadata.get('type') == 'Bookmark':
                documents.append(Document(
                id=doc_id,
                page_content=f"Title: {metadata['title']}\nNote: {metadata['note']}\nSource: {metadata['source_url']}",
                metadata=metadata
            ))
                
            else:
                documents.append(Document(
                id=doc_id,
                page_content=f"Title: {metadata['title']}\nNote: {metadata['note']}",
                metadata=metadata
            ))
        
        if not documents:
            raise SearchExecutionError("No documents found matching query")

        return documents

    except Exception as e:
        logger.error("Search failed", extra={"user_id": namespace}, exc_info=True)
        return []  #return an empty list if search fails

async def delete_from_vector_db(doc_id: str, namespace: str):
    try:
        index.delete(
            ids=[doc_id],
            namespace=namespace
        )

        return {"status": "deleted", "doc_id": doc_id}

    except Exception as e:
        logger.error("Error deleting document", extra={"user_id": namespace, "doc_id": doc_id}, exc_info=True)
        raise DocumentStorageError(
            message="Failed to delete document",
            user_id=namespace,
            doc_id=doc_id
        ) from e