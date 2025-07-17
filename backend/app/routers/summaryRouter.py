from fastapi import APIRouter, Request, HTTPException
from app.services.summariseService import *
from slowapi import Limiter
from slowapi.util import get_remote_address

# Initialize limiter for this router
limiter = Limiter(key_func=get_remote_address)


router = APIRouter(
    prefix="/summary",
    tags=["Summary"]
)

@router.post("/generate")
@limiter.limit("5/day")  # 5 summary generation requests per day per user
async def generate_web_summary(request: Request):
    """
    Generate a summary for the provided text.
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
