from fastapi import APIRouter 
from app.services.quotesService import get_quotes

router = APIRouter(
    prefix="/quotes",
    tags=["quotes"]
)

@router.get("/")
async def get_random_quote():
    return get_quotes()
    
