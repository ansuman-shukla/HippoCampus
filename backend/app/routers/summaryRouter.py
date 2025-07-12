from fastapi import APIRouter, Request, HTTPException
from app.services.summariseService import *
from app.middleware.subscription_middleware import check_summary_middleware
from app.services.subscription_service import estimate_content_pages, increment_summary_pages
import logging

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/summary",
    tags=["Summary"]
)

@router.post("/generate")
async def generate_web_summary(request: Request):
    """
    Generate a summary for the provided text.
    Enforces subscription limits for summary page generation.
    """
    data = await request.json()
    try:
        content = data.get("content")
        if not content:
            raise HTTPException(status_code=400, detail="Content is required for summarization")

        # Estimate pages for subscription limit checking
        estimated_pages = estimate_content_pages(content)
        logger.info(f"📄 SUMMARY ROUTER: Estimated pages for content: {estimated_pages}")

        # Check subscription limits before generating summary
        await check_summary_middleware(request, estimated_pages)
        
        # Generate the summary
        summary = await generate_summary(content)
        
        # Increment summary page count after successful generation
        user_id = getattr(request.state, 'user_id', None)
        if user_id:
            try:
                updated_subscription = increment_summary_pages(user_id, estimated_pages)
                logger.info(f"✅ SUMMARY ROUTER: Updated summary pages for user {user_id}")
                logger.info(f"   └─ Monthly pages used: {updated_subscription['monthly_summary_pages_used']}")
            except Exception as e:
                logger.error(f"❌ SUMMARY ROUTER: Failed to increment summary pages: {str(e)}")
                # Don't fail the request if tracking fails, but log the error
        else:
            logger.warning(f"⚠️ SUMMARY ROUTER: No user_id found for tracking summary pages")

        return {
            "summary": summary,
            "pages_processed": estimated_pages
        }

    except HTTPException:
        # Re-raise HTTP exceptions (like 402 Payment Required from middleware)
        raise
    except Exception as e:
        logger.error(f"❌ SUMMARY ROUTER: Error generating summary: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error generating summary: {str(e)}") from e
