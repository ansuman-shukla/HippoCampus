from jose import JWTError
from fastapi import Request, HTTPException
import time
from app.utils.jwt import decodeJWT, create_tokens
from app.services.user_service import create_user_if_not_exists

async def auth_middleware(request: Request):
    # Get the access token from the request
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



    return request

    # Post-processing: modify response
    # add the user id in the response cokkies.get

    