from fastapi import APIRouter, Request, HTTPException
from app.services.summariseService import *


router = APIRouter(
    prefix="/summary",
    tags=["Summary"]
)

@router.post("/generate")
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
