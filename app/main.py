from jose import jwt, JWTError
from fastapi import FastAPI, Request, HTTPException 
from dotenv import load_dotenv
from app.routers.bookmarkRouters import router as bookmark_router
from fastapi import Request, HTTPException
from jose import JWTError
from app.utils.jwt import decodeJWT, create_tokens
from app.services.user_service import create_user_if_not_exists
from fastapi.middleware.cors import CORSMiddleware
from app.routers.get_quotes import router as get_quotes_router
from app.routers.notesRouter import router as notes_router
load_dotenv()
app = FastAPI() 

import logging
logger = logging.getLogger(__name__)

import time

@app.middleware("http")
async def authorisation_middleware(request: Request, call_next):
    access_token = request.cookies.get("access_token")
    refresh_token = request.cookies.get("refresh_token")
    
    if not access_token:
        raise HTTPException(status_code=401, detail="Access token is missing")
    
    if refresh_token:
        # token = await create_tokens(refresh_token)
        # return token
        pass

    # Validate the access token
    try:
        payload = await decodeJWT(access_token)
        user_id = payload.get("sub")
       
    except JWTError as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {str(e)}")
    
    await create_user_if_not_exists(payload)


    # Continue the request
    response = await call_next(request)

    # Post-processing: modify response
    if request.get("user_id") is None:
        response.set_cookie(key="user_id", value=user_id , expires=time.time() + 3600, httponly=True)

    if request.get("user_name") is None or request.get("user_picture") is None:
        user_metadata = payload.get("user_metadata", {})
        full_name = user_metadata.get("full_name")
        picture = user_metadata.get("picture")
        response.set_cookie(key="user_name", value=full_name , expires=time.time() + 3600, httponly=True)
        response.set_cookie(key="user_picture", value=picture , expires=time.time() + 3600, httponly=True)

    return response


app.add_middleware(
    CORSMiddleware,
    allow_origins=["chrome-extension://pbmpglcjfdjmjokffakahlncegdcefno"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(bookmark_router)
app.include_router(get_quotes_router)
app.include_router(notes_router)















# @app.get("/")
# async def root():
# async def auth_middleware(request: Request):
#     # Get the access token from the request
#     access_token = request.cookies.get("access_token")
#     refresh_token = request.cookies.get("refresh_token")

#     if not access_token:
#         raise HTTPException(status_code=401, detail="Access token is missing")
    
#     if refresh_token:
#         token = await create_tokens(refresh_token)
#         return token

#     # Validate the access token
#     try:
#         payload = await decodeJWT(access_token)
#         user_id = payload.get("sub")
       
#     except JWTError as e:
#         raise HTTPException(status_code=401, detail=f"Invalid token: {str(e)}")
    
#     create_user_if_not_exists(payload)


#     # Continue the request
#     request.state.user_id = user_id
#     return {"message": "Pls do /save to save a link or /search to search for a link"}