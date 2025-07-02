from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from app.utils.jwt import refresh_access_token, decodeJWT
import logging
import time

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["authentication"])

class LoginRequest(BaseModel):
    access_token: str
    refresh_token: str

@router.post("/login")
async def login(request: Request, login_details: LoginRequest):
    try:
        # Simulate cookie setting after successful login verification
        # Real implementation should verify tokens and then set cookies
        response = JSONResponse(status_code=200, content={"message": "Login successful"})
        response.set_cookie("access_token", login_details.access_token, httponly=True, max_age=3600)
        response.set_cookie("refresh_token", login_details.refresh_token, httponly=True, max_age=604800)
        return response
    except Exception as e:
        logger.error(f"Login failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/refresh")
async def refresh_token_endpoint(request: Request):
    """
    Endpoint to manually refresh access token using refresh token
    """
    try:
        refresh_token = request.cookies.get("refresh_token")
        
        if not refresh_token:
            # Try to get from request body
            try:
                body = await request.json()
                refresh_token = body.get("refresh_token")
            except:
                pass
        
        if not refresh_token:
            raise HTTPException(
                status_code=400,
                detail="Refresh token is required"
            )
        
        # Refresh the token
        token_data = await refresh_access_token(refresh_token)
        
        # Create response with new tokens
        response = JSONResponse({
            "success": True,
            "message": "Token refreshed successfully",
            "access_token": token_data.get("access_token"),
            "refresh_token": token_data.get("refresh_token"),
            "expires_in": token_data.get("expires_in"),
            "token_type": token_data.get("token_type", "Bearer")
        })
        
        # Set new tokens as cookies
        response.set_cookie(
            key="access_token",
            value=token_data.get("access_token"),
            httponly=True,
            secure=True,
            samesite="none",
            max_age=3600  # 1 hour
        )
        
        if token_data.get("refresh_token"):
            response.set_cookie(
                key="refresh_token",
                value=token_data.get("refresh_token"),
                httponly=True,
                secure=True,
                samesite="none",
                max_age=604800  # 7 days
            )
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error refreshing token: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error during token refresh"
        )

@router.post("/logout")
async def logout(request: Request):
    """
    Logout endpoint to clear authentication cookies
    """
    response = JSONResponse({
        "success": True,
        "message": "Logged out successfully"
    })
    
    # Clear authentication cookies
    response.delete_cookie("access_token", samesite="none", secure=True)
    response.delete_cookie("refresh_token", samesite="none", secure=True)
    response.delete_cookie("user_id")
    response.delete_cookie("user_name")
    response.delete_cookie("user_picture")
    
    return response

@router.get("/status")
async def auth_status(request: Request):
    """
    Check authentication status and validate current token
    """
    access_token = request.cookies.get("access_token")
    refresh_token = request.cookies.get("refresh_token")
    
    result = {
        "has_access_token": bool(access_token),
        "has_refresh_token": bool(refresh_token),
        "is_authenticated": False,
        "user_id": None,
        "token_valid": False
    }
    
    if access_token:
        try:
            payload = await decodeJWT(access_token)
            result.update({
                "is_authenticated": True,
                "user_id": payload.get("sub"),
                "token_valid": True,
                "user_email": payload.get("email"),
                "token_expires": payload.get("exp")
            })
        except Exception as e:
            logger.warning(f"Token validation failed in status check: {str(e)}")
            result["token_error"] = str(e)
    
    return result

@router.get("/verify")
async def verify_token(request: Request):
    """
    Verify the current access token and return user information
    """
    access_token = request.cookies.get("access_token")
    
    if not access_token:
        raise HTTPException(
            status_code=401,
            detail="No access token provided"
        )
    
    try:
        payload = await decodeJWT(access_token)
        return {
            "valid": True,
            "user_id": payload.get("sub"),
            "email": payload.get("email"),
            "expires": payload.get("exp"),
            "issued_at": payload.get("iat"),
            "user_metadata": payload.get("user_metadata", {})
        }
    except Exception as e:
        raise HTTPException(
            status_code=401,
            detail=f"Token verification failed: {str(e)}"
        )
