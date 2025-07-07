from datetime import datetime
from typing import List, Optional, Dict
import logging
from app.core.pinecone_wrapper import safe_index, safe_pc
from langchain_core.documents import Document
from app.core.config import settings
from app.schema.link_schema import Link as LinkSchema
from app.utils.site_name_extractor import extract_site_name
from app.utils.space_extractor import extract_space_from_text, remove_space_pattern_from_text
from app.services.memories_service import save_memory_to_db
from app.exceptions.httpExceptionsSearch import *
from app.exceptions.httpExceptionsSave import *
from app.exceptions.global_exceptions import ExternalServiceError

# Configure logger
logger = logging.getLogger(__name__)

async def save_to_vector_db(obj: LinkSchema, namespace: str):
    """Save document to vector database using E5 embeddings with metadata filtering instead of namespaces"""

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
        # Extract site name and space from note field
        site_name = await extract_site_name(obj.link) or "Unknown Site"
        space = extract_space_from_text(obj.note) or "general"  # Extract space from note field only, default to "general"
        
        # Clean the note text for embedding (remove space pattern)
        clean_note = remove_space_pattern_from_text(obj.note) if obj.note else obj.note
        text_to_embed = f"{obj.title}, {clean_note}, {site_name}"

        metadata = {
            "doc_id": doc_id,
            "user_id": namespace,
            "namespace": namespace,  # Add namespace to metadata for filtering
            "title": obj.title,
            "note": obj.note,  # Keep original note with space pattern
            "source_url": obj.link,
            "site_name": site_name,
            "type": "Bookmark",
            "date": datetime.now().isoformat(),
            "space": space, #catagory that memory belongs to 
        }

        # Generate E5 embeddings using safe wrapper
        embedding = await safe_pc.embed(
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

        # Upsert using safe wrapper - store in default namespace
        await safe_index.upsert(
            vectors=[vector]
            # No namespace parameter = default namespace
        )

        # Save to database
        await save_memory_to_db(metadata)

        return {"status": "saved", "doc_id": doc_id}

    except (InvalidURLError, DocumentStorageError):
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
    """Search using E5 embeddings with metadata filtering for user isolation"""

    if not namespace:
        raise InvalidRequestError("Missing user uuid - please login")

    if not query or len(query.strip()) < 3:
        raise InvalidRequestError("Search query must be at least 3 characters")

    try:
        # Extract space from query if present
        query_space = extract_space_from_text(query)
        clean_query = remove_space_pattern_from_text(query)
        
        # Create user filter using metadata
        user_filter = {"namespace": {"$eq": namespace}}
        
        # If space was extracted from query, add it to filter using proper Pinecone syntax
        if query_space:
            space_filter = {"space": {"$eq": query_space}}
            # Combine user filter, space filter and existing filters
            filters_to_combine = [user_filter, space_filter]
            if filter:
                filters_to_combine.append(filter)
            filter = {"$and": filters_to_combine}
        else:
            # Just combine user filter with existing filter if present
            if filter:
                filter = {"$and": [user_filter, filter]}
            else:
                filter = user_filter
        
        # Generate query embedding using clean query (without space pattern)
        embedding = await safe_pc.embed(
            model="multilingual-e5-large",
            inputs=[clean_query],
            parameters={"input_type": "query", "truncate": "END"}
        )

        # Perform vector search using safe wrapper - search in default namespace with metadata filter
        results = await safe_index.query(
            vector=embedding[0]['values'],
            top_k=top_k,
            include_metadata=True,
            filter=filter
            # No namespace parameter = search in default namespace
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
                # Clean the note content for display (remove space pattern)
                clean_note = remove_space_pattern_from_text(metadata['note'])
                documents.append(Document(
                id=doc_id,
                page_content=f"Title: {metadata['title']}\nNote: {clean_note}\nSource: {metadata['source_url']}",
                metadata=metadata
            ))

            else:
                # For notes, clean the note content for display (remove space pattern)
                clean_note = remove_space_pattern_from_text(metadata['note'])
                documents.append(Document(
                id=doc_id,
                page_content=f"Title: {metadata['title']}\nNote: {clean_note}",
                metadata=metadata
            ))

        if not documents:
            raise SearchExecutionError("No documents found matching query")

        return documents

    except (InvalidRequestError, SearchExecutionError):
        # Re-raise our custom exceptions
        raise
    except ExternalServiceError as e:
        logger.error(f"Vector database service error: {str(e)}")
        raise SearchExecutionError(f"Vector database service unavailable: {str(e)}")
    except Exception as e:
        logger.error("Search failed", extra={"user_id": namespace}, exc_info=True)
        return []  # Return empty list if search fails gracefully

async def delete_from_vector_db(doc_id: str, namespace: str):
    """
    Delete document from vector database using metadata filtering instead of namespace isolation
    """
    logger.info(f"=== VECTOR DB DELETE STARTED ===")
    logger.info(f"delete_from_vector_db called with doc_id: '{doc_id}', namespace: '{namespace}'")
    
    try:
        # Input validation with detailed logging
        if not doc_id:
            logger.error(f"VALIDATION FAILED: doc_id is empty or None: '{doc_id}'")
            raise InvalidRequestError("Document ID is required")
        if not namespace:
            logger.error(f"VALIDATION FAILED: namespace is empty or None: '{namespace}'")
            raise InvalidRequestError("Namespace is required")
            
        logger.info(f"Input validation passed - doc_id: '{doc_id}', namespace: '{namespace}'")
        
        # Check vector database connection
        logger.info("Checking vector database connection...")
        try:
            # Test connection with index stats
            stats = await safe_index.describe_index_stats()
            logger.info(f"Vector DB connection successful. Index stats: {stats}")
        except Exception as conn_e:
            logger.error(f"Vector DB connection test failed: {str(conn_e)}")
            raise VectorDBConnectionError(f"Failed to connect to vector database: {str(conn_e)}")
        
        # Create metadata filter to ensure we only delete documents belonging to this user
        delete_filter = {
            "$and": [
                {"namespace": {"$eq": namespace}},
                {"doc_id": {"$eq": doc_id}}
            ]
        }
        
        # Perform the delete operation using metadata filter instead of namespace
        logger.info(f"Attempting to delete vector with id: '{doc_id}' for user: '{namespace}' using metadata filter")
        
        delete_result = await safe_index.delete(
            filter=delete_filter
            # No namespace parameter = delete from default namespace using filter
        )
        
        logger.info(f"Vector database delete operation completed. Result: {delete_result}")
        logger.info(f"=== VECTOR DB DELETE COMPLETED SUCCESSFULLY ===")
        
        return {"status": "deleted", "doc_id": doc_id, "namespace": namespace, "delete_result": delete_result}

    except InvalidRequestError as e:
        logger.error(f"VECTOR DB DELETE FAILED: Validation error - {str(e)}")
        # Re-raise validation errors
        raise
    except VectorDBConnectionError as e:
        logger.error(f"VECTOR DB DELETE FAILED: Connection error - {str(e)}")
        raise
    except ExternalServiceError as e:
        logger.error(f"VECTOR DB DELETE FAILED: External service error - {str(e)}")
        raise DocumentStorageError(
            message="Vector database service unavailable",
            user_id=namespace,
            doc_id=doc_id
        ) from e
    except Exception as e:
        logger.error(f"VECTOR DB DELETE FAILED: Unexpected error - doc_id: '{doc_id}', namespace: '{namespace}', error: {str(e)}", exc_info=True)
        raise DocumentStorageError(
            message="Failed to delete document from vector database",
            user_id=namespace,
            doc_id=doc_id
        ) from e