from fastapi import APIRouter, Request, HTTPException
from app.services.summariseService import *

# Import the limiter from main app instead of creating a new one
# This ensures we use the user-aware key function from main.py
def get_limiter(request: Request):
    """Get the limiter instance from the app state"""
    return request.app.state.limiter

router = APIRouter(
    prefix="/summary",
    tags=["Summary"]
)

@router.post("/generate")
async def generate_web_summary(request: Request):
    """
    Generate a summary for the provided text.
    Rate limited to 5 requests per day per user.
    """
    # Apply rate limiting using the app's limiter
    limiter = get_limiter(request)
    await limiter.limit("5/day")(request)
    
    data = await request.json()
    try:
        content = data.get("content")
        if not content:
            raise HTTPException(status_code=400, detail="Content is required for summarization")

        summary = await generate_summary(content)
        return {"summary": summary}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating summary: {str(e)}") from e
