from fastapi import APIRouter, Request, HTTPException
from app.services.summariseService import *
from app.core.rate_limiter import limiter

router = APIRouter(
    prefix="/summary",
    tags=["Summary"]
)

@router.post("/generate")
@limiter.limit("5/day")
async def generate_web_summary(request: Request):
    """
    Generate a summary for the provided text.
    Rate limited to 5 requests per day per user.
    """
    data = await request.json()
    try:
        content = data.get("content")
        if not content:
            raise HTTPException(status_code=400, detail="Content is required for summarization")

        summary = await generate_summary(content)
        return {"summary": summary}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating summary: {str(e)}") from e
