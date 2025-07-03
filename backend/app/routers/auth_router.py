from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from app.utils.jwt import refresh_access_token, decodeJWT
import logging
import time

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["authentication"])

def set_secure_cookie(response, key, value, expires_seconds):
    """Set a secure cookie with proper attributes"""
    try:
        response.set_cookie(
            key=key,
            value=value,
            expires=int(time.time() + expires_seconds),
            httponly=True,
            secure=True,
            samesite="none"
        )
    except Exception as e:
        logger.error(f"Error setting {key} cookie: {str(e)}")

class LoginRequest(BaseModel):
    access_token: str
    refresh_token: str

@router.post("/login")
async def login(request: Request, login_details: LoginRequest):
    logger.info(f"🔐 AUTH LOGIN: Processing login request")
    logger.info(f"   ├─ Request IP: {request.client.host if request.client else 'Unknown'}")
    logger.info(f"   ├─ User-Agent: {request.headers.get('user-agent', 'Unknown')[:50]}...")
    logger.info(f"   ├─ Access token length: {len(login_details.access_token) if login_details.access_token else 0}")
    logger.info(f"   └─ Refresh token length: {len(login_details.refresh_token) if login_details.refresh_token else 0}")
    
    try:
        logger.info(f"🍪 AUTH LOGIN: Setting secure authentication cookies")
        # Set cookies using the same secure method as middleware
        response = JSONResponse(status_code=200, content={"message": "Login successful"})
        set_secure_cookie(response, "access_token", login_details.access_token, 3600)  # 1 hour
        set_secure_cookie(response, "refresh_token", login_details.refresh_token, 604800)  # 7 days
        
        logger.info(f"✅ AUTH LOGIN: Login successful - cookies set")
        logger.info(f"   ├─ Access token cookie expires in: 3600 seconds (1 hour)")
        logger.info(f"   └─ Refresh token cookie expires in: 604800 seconds (7 days)")
        
        return response
    except Exception as e:
        logger.error(f"❌ AUTH LOGIN: Login failed: {str(e)}")
        logger.error(f"   ├─ Error type: {type(e).__name__}")
        logger.error(f"   └─ This is likely a cookie setting error")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/refresh")
async def refresh_token_endpoint(request: Request):
    """
    Endpoint to manually refresh access token using refresh token
    """
    logger.info(f"🔄 AUTH REFRESH: Processing manual token refresh request")
    logger.info(f"   ├─ Request IP: {request.client.host if request.client else 'Unknown'}")
    logger.info(f"   └─ User-Agent: {request.headers.get('user-agent', 'Unknown')[:50]}...")
    
    try:
        logger.info(f"🍪 AUTH REFRESH: Extracting refresh token from request")
        refresh_token = request.cookies.get("refresh_token")
        logger.info(f"   ├─ Refresh token from cookies: {bool(refresh_token)}")
        
        if not refresh_token:
            logger.info(f"   ├─ No refresh token in cookies, checking request body")
            # Try to get from request body
            try:
                body = await request.json()
                refresh_token = body.get("refresh_token")
                logger.info(f"   ├─ Refresh token from body: {bool(refresh_token)}")
            except Exception as body_error:
                logger.warning(f"   ├─ Could not parse request body: {str(body_error)}")
                pass
        
        if not refresh_token:
            logger.error(f"❌ AUTH REFRESH: No refresh token found in cookies or body")
            raise HTTPException(
                status_code=400,
                detail="Refresh token is required"
            )
        
        logger.info(f"   └─ Refresh token length: {len(refresh_token)}")
        
        # Refresh the token
        logger.info(f"🔄 AUTH REFRESH: Calling token refresh service")
        token_data = await refresh_access_token(refresh_token)
        
        # Validate the new access token before setting cookies
        new_access_token = token_data.get("access_token")
        new_refresh_token = token_data.get("refresh_token", refresh_token)
        
        logger.info(f"🔍 AUTH REFRESH: Validating refreshed tokens")
        logger.info(f"   ├─ New access token received: {bool(new_access_token)}")
        logger.info(f"   └─ New refresh token received: {bool(new_refresh_token)}")
        
        if not new_access_token:
            logger.error(f"❌ AUTH REFRESH: No access token in refresh response")
            raise HTTPException(status_code=401, detail="Token refresh failed")
        
        # Verify the new token is valid
        logger.info(f"🔑 AUTH REFRESH: Verifying new access token")
        payload = await decodeJWT(new_access_token)
        user_id = payload.get("sub")
        if not user_id:
            logger.error(f"❌ AUTH REFRESH: Invalid refreshed token - no user ID")
            raise HTTPException(status_code=401, detail="Invalid refreshed token")
        
        logger.info(f"✅ AUTH REFRESH: Token validation successful for user: {user_id}")
        
        # Create response with new tokens
        response_data = {
            "success": True,
            "message": "Token refreshed successfully",
            "access_token": new_access_token,
            "refresh_token": new_refresh_token,
            "expires_in": token_data.get("expires_in"),
            "token_type": token_data.get("token_type", "Bearer")
        }
        
        logger.info(f"📝 AUTH REFRESH: Preparing response")
        logger.info(f"   ├─ Expires in: {response_data.get('expires_in')} seconds")
        logger.info(f"   └─ Token type: {response_data.get('token_type')}")
        
        response = JSONResponse(response_data)
        
        # Set new tokens using secure cookie method (consistent with middleware)
        logger.info(f"🍪 AUTH REFRESH: Setting new authentication cookies")
        set_secure_cookie(response, "access_token", new_access_token, 3600)  # 1 hour
        
        # Only set new refresh token if it's different from the original
        if new_refresh_token != refresh_token:
            logger.info(f"   ├─ Setting new refresh token (changed)")
            set_secure_cookie(response, "refresh_token", new_refresh_token, 604800)  # 7 days
        else:
            logger.info(f"   ├─ Refresh token unchanged, not updating cookie")
        
        logger.info(f"✅ AUTH REFRESH: Manual token refresh completed successfully for user: {user_id}")
        return response
        
    except HTTPException as http_error:
        logger.error(f"❌ AUTH REFRESH: HTTP exception during refresh")
        logger.error(f"   ├─ Status: {http_error.status_code}")
        logger.error(f"   └─ Detail: {http_error.detail}")
        raise
    except Exception as e:
        logger.error(f"💥 AUTH REFRESH: Unexpected error refreshing token: {str(e)}")
        logger.error(f"   ├─ Error type: {type(e).__name__}")
        logger.error(f"   └─ This indicates a system or configuration error")
        raise HTTPException(
            status_code=500,
            detail="Internal server error during token refresh"
        )

@router.post("/logout")
async def logout(request: Request):
    """
    Logout endpoint to clear authentication cookies
    """
    logger.info(f"🚪 AUTH LOGOUT: Processing logout request")
    logger.info(f"   ├─ Request IP: {request.client.host if request.client else 'Unknown'}")
    logger.info(f"   └─ User-Agent: {request.headers.get('user-agent', 'Unknown')[:50]}...")
    
    # Log current cookie state
    current_cookies = list(request.cookies.keys())
    auth_cookies_present = [cookie for cookie in current_cookies if cookie in ["access_token", "refresh_token", "user_id", "user_name", "user_picture"]]
    logger.info(f"   ├─ Total cookies present: {len(current_cookies)}")
    logger.info(f"   └─ Auth cookies to clear: {auth_cookies_present}")
    
    response = JSONResponse({
        "success": True,
        "message": "Logged out successfully"
    })
    
    # Clear authentication cookies with all possible attribute combinations
    # to ensure we remove any duplicate cookies
    auth_cookies = ["access_token", "refresh_token", "user_id", "user_name", "user_picture"]
    
    logger.info(f"🗑️  AUTH LOGOUT: Clearing authentication cookies")
    for cookie_name in auth_cookies:
        logger.info(f"   ├─ Clearing cookie: {cookie_name}")
        # Clear with different attribute combinations to catch all variations
        response.delete_cookie(cookie_name)
        response.delete_cookie(cookie_name, path="/")
        response.delete_cookie(cookie_name, samesite="none", secure=True)
        response.delete_cookie(cookie_name, path="/", samesite="none", secure=True)
    
    logger.info("✅ AUTH LOGOUT: User logged out successfully, all auth cookies cleared")
    return response

@router.get("/status")
async def auth_status(request: Request):
    """
    Check authentication status and validate current token
    """
    logger.info(f"🔍 AUTH STATUS: Checking authentication status")
    logger.info(f"   ├─ Request IP: {request.client.host if request.client else 'Unknown'}")
    logger.info(f"   └─ User-Agent: {request.headers.get('user-agent', 'Unknown')[:50]}...")
    
    access_token = request.cookies.get("access_token")
    refresh_token = request.cookies.get("refresh_token")
    
    logger.info(f"🍪 AUTH STATUS: Analyzing authentication state")
    logger.info(f"   ├─ Access token present: {bool(access_token)}")
    logger.info(f"   ├─ Refresh token present: {bool(refresh_token)}")
    logger.info(f"   ├─ Access token length: {len(access_token) if access_token else 0}")
    logger.info(f"   └─ Refresh token length: {len(refresh_token) if refresh_token else 0}")
    
    result = {
        "has_access_token": bool(access_token),
        "has_refresh_token": bool(refresh_token),
        "is_authenticated": False,
        "user_id": None,
        "token_valid": False
    }
    
    if access_token:
        logger.info(f"🔑 AUTH STATUS: Validating access token")
        try:
            payload = await decodeJWT(access_token)
            user_metadata = payload.get("user_metadata", {})
            
            logger.info(f"✅ AUTH STATUS: Token validation successful")
            logger.info(f"   ├─ User ID: {payload.get('sub')}")
            logger.info(f"   ├─ Email: {payload.get('email')}")
            logger.info(f"   ├─ Full name: {user_metadata.get('full_name')}")
            logger.info(f"   └─ Token expires: {payload.get('exp')}")
            
            result.update({
                "is_authenticated": True,
                "user_id": payload.get("sub"),
                "token_valid": True,
                "user_email": payload.get("email"),
                "user_name": user_metadata.get("full_name"),
                "full_name": user_metadata.get("full_name"),
                "user_picture": user_metadata.get("picture"),
                "picture": user_metadata.get("picture"),
                "token_expires": payload.get("exp")
            })
        except Exception as e:
            logger.warning(f"❌ AUTH STATUS: Token validation failed: {str(e)}")
            logger.warning(f"   ├─ Error type: {type(e).__name__}")
            logger.warning(f"   └─ Token may be expired or invalid")
            result["token_error"] = str(e)
    else:
        logger.info(f"ℹ️  AUTH STATUS: No access token to validate")
    
    logger.info(f"📊 AUTH STATUS: Status check completed")
    logger.info(f"   ├─ Authenticated: {result.get('is_authenticated')}")
    logger.info(f"   ├─ Token valid: {result.get('token_valid')}")
    logger.info(f"   └─ User ID: {result.get('user_id', 'None')}")
    
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
