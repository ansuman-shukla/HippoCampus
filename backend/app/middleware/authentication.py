from jose import JWTError
from fastapi import Request, HTTPException
import time
from app.utils.jwt import decodeJWT, refresh_access_token, TokenExpiredError
from app.services.user_service import create_user_if_not_exists
import logging

logger = logging.getLogger(__name__)

async def auth_middleware(request: Request):
    """
    Authentication middleware with token refresh capability
    """
    # Get tokens from request
    access_token = request.cookies.get("access_token")
    refresh_token = request.cookies.get("refresh_token")

    if not access_token:
        raise HTTPException(status_code=401, detail="Access token is missing")
    
    payload = None
    
    try:
        # Try to validate the current access token
        payload = await decodeJWT(access_token)
        user_id = payload.get("sub")
        
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token payload")
            
    except TokenExpiredError:
        logger.info("Access token expired, attempting refresh...")
        
        # Try to refresh the token if we have a refresh token
        if not refresh_token:
            raise HTTPException(
                status_code=401, 
                detail="Access token expired and no refresh token available"
            )
        
        try:
            # Refresh the access token
            token_response = await refresh_access_token(refresh_token)
            new_access_token = token_response.get("access_token")
            
            if not new_access_token:
                raise HTTPException(status_code=401, detail="Token refresh failed")
            
            # Decode the new access token to get user info
            payload = await decodeJWT(new_access_token)
            user_id = payload.get("sub")
            
            if not user_id:
                raise HTTPException(status_code=401, detail="Invalid refreshed token payload")
            
            logger.info("Successfully refreshed access token")
            
            # Store the new token in request state for response processing
            request.state.new_access_token = new_access_token
            request.state.new_refresh_token = token_response.get("refresh_token", refresh_token)
            
        except Exception as refresh_error:
            logger.error(f"Token refresh failed: {str(refresh_error)}")
            raise HTTPException(status_code=401, detail="Token refresh failed")
    
    except JWTError as e:
        logger.warning(f"JWT validation failed: {str(e)}")
        raise HTTPException(status_code=401, detail=f"Invalid token: {str(e)}")
    
    # Create user if not exists
    await create_user_if_not_exists(payload)
    
    # Store user info in request state
    request.state.user_id = user_id
    request.state.payload = payload
    
    return request

    