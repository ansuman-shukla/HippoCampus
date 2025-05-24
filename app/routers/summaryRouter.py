from fastapi import APIRouter, Request, HTTPException
from app.services.summariseService import *


router = APIRouter(
    prefix="/summary",
    tags=["Summary"]
)

@router.post("/generate")
async def generate_web_summary(corpus: str):
    """
    Generate a summary for the provided text.
    """
    try:
        if not corpus:
            raise HTTPException(status_code=400, detail="Text is required for summarization")

        summary = await generate_summary(corpus)
        return {"summary": summary}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating summary: {str(e)}") from e
