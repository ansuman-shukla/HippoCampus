import logging
import time
from fastapi import HTTPException
from app.utils.jwt import decodeJWT, refresh_access_token
from app.exceptions.global_exceptions import create_error_response
from collections import defaultdict
import asyncio

logger = logging.getLogger(__name__)

# Global refresh token locks to prevent race conditions
refresh_locks = defaultdict(asyncio.Lock)
active_refreshes = {}  # Store active refresh promises


async def handle_token_refresh(refresh_token):
    """Handle token refresh logic with concurrency control and return new tokens"""
    async def _refresh():
        if not refresh_token:
            logger.warning("No refresh token available for token refresh")
            return None, None, create_auth_error_response(
                "Access token expired and no refresh token available"
            )
        
        # Use a lock per refresh token to prevent concurrent refreshes
        lock = refresh_locks[refresh_token]
        
        async with lock:
            # Check if there's already an active refresh for this token
            if refresh_token in active_refreshes:
                logger.info("Refresh already in progress, waiting for result...")
                try:
                    return await active_refreshes[refresh_token]
                except Exception as e:
                    logger.error(f"Waiting for active refresh failed: {str(e)}")
                    # Continue with new refresh attempt
            
            # Create refresh promise
            refresh_promise = asyncio.create_task(_do_refresh(refresh_token))
            active_refreshes[refresh_token] = refresh_promise
            
            try:
                result = await refresh_promise
                return result
            finally:
                # Clean up
                active_refreshes.pop(refresh_token, None)
                refresh_locks.pop(refresh_token, None)
    
    async def _do_refresh(refresh_token):
        try:
            # Refresh the access token
            token_response = await refresh_access_token(refresh_token)
            new_access_token = token_response.get("access_token")
            new_refresh_token = token_response.get("refresh_token", refresh_token)
            
            if not new_access_token:
                logger.error("Failed to get new access token from refresh response")
                return None, None, create_auth_error_response("Token refresh failed")
            
            # Validate the new access token
            payload = await decodeJWT(new_access_token)
            user_id, error_response = validate_user_id(payload, "refreshed token")
            if error_response:
                return None, None, error_response
            
            logger.info("Successfully refreshed access token")
            return new_access_token, new_refresh_token, None
            
        except HTTPException as refresh_error:
            error_detail = refresh_error.detail
            logger.error(f"Token refresh failed: {error_detail}")
            
            # Enhanced detection for refresh token issues
            is_token_invalid = False
            
            # Check for various token invalid scenarios
            if isinstance(error_detail, str):
                # Direct string check
                error_lower = error_detail.lower()
                is_token_invalid = (
                    "already_used" in error_lower or 
                    "already used" in error_lower or
                    "refresh_token_already_used" in error_lower or
                    "invalid refresh token" in error_lower or
                    "expired" in error_lower or
                    "revoked" in error_lower
                )
                
                # Also try to parse as JSON if it looks like JSON
                if error_detail.strip().startswith('{'):
                    try:
                        import json
                        error_json = json.loads(error_detail)
                        error_code = error_json.get("error_code", "")
                        error_msg = error_json.get("msg", "").lower()
                        
                        is_token_invalid = (
                            error_code == "refresh_token_already_used" or
                            "already used" in error_msg or
                            "invalid refresh token" in error_msg or
                            "expired" in error_msg
                        )
                        logger.info(f"   ├─ Parsed JSON error: code={error_code}, msg={error_msg}")
                    except json.JSONDecodeError:
                        pass  # Not JSON, use string check above
            
            if is_token_invalid:
                logger.warning("Refresh token is invalid/expired - requiring complete re-authentication")
                return None, None, create_error_response(
                    "Session expired. Please log in again.",
                    status_code=401,
                    error_type="session_expired"
                )
            
            return None, None, create_error_response(
                error_detail,
                status_code=refresh_error.status_code,
                error_type="auth_error"
            )
        except Exception as refresh_error:
            logger.error(f"Unexpected token refresh error: {str(refresh_error)}")
            return None, None, create_error_response(
                "Authentication service error",
                status_code=503,
                error_type="auth_service_error"
            )
    
    return _refresh()


def update_token_cookies(response, new_access_token, new_refresh_token, original_refresh_token):
    """Update access and refresh token cookies if tokens were refreshed"""
    logger.info(f"🔄 TOKEN COOKIES: Updating authentication cookies after refresh")
    logger.info(f"   ├─ New access token present: {bool(new_access_token)}")
    logger.info(f"   ├─ New refresh token present: {bool(new_refresh_token)}")
    logger.info(f"   └─ Refresh token changed: {new_refresh_token != original_refresh_token if new_refresh_token and original_refresh_token else 'Unknown'}")
    
    try:
        # Set new access token
        if new_access_token:
            logger.info(f"   ├─ Setting new access token cookie")
            set_secure_cookie(response, "access_token", new_access_token, 3600)  # 1 hour
        
        # Set new refresh token if different
        if new_refresh_token and new_refresh_token != original_refresh_token:
            logger.info(f"   ├─ Setting new refresh token cookie (token changed)")
            set_secure_cookie(response, "refresh_token", new_refresh_token, 604800)  # 7 days
        elif new_refresh_token:
            logger.info(f"   ├─ Refresh token unchanged, keeping existing cookie")
            
        logger.info(f"✅ TOKEN COOKIES: Token cookies updated successfully")
    except Exception as e:
        logger.error(f"❌ TOKEN COOKIES: Error setting refreshed token cookies: {str(e)}")
        logger.error(f"   └─ This may cause authentication issues")


def update_user_cookies(response, request, user_id, payload):
    """Update user-related cookies if not already set or different"""
    logger.info(f"👤 USER COOKIES: Updating user information cookies")
    logger.info(f"   ├─ User ID: {user_id}")
    
    try:
        # Set user_id cookie if not already set or different
        current_user_id = request.cookies.get("user_id")
        logger.info(f"   ├─ Current user_id cookie: {current_user_id}")
        logger.info(f"   ├─ New user_id: {user_id}")
        
        if current_user_id != user_id:
            logger.info(f"   ├─ User ID changed, updating cookie")
            set_user_cookie(response, "user_id", user_id)
        else:
            logger.info(f"   ├─ User ID unchanged")

        # Set user metadata cookies if not already set or different
        user_metadata = payload.get("user_metadata", {})
        full_name = user_metadata.get("full_name")
        picture = user_metadata.get("picture")

        current_user_name = request.cookies.get("user_name")
        current_user_picture = request.cookies.get("user_picture")
        
        logger.info(f"   ├─ Full name from token: {full_name}")
        logger.info(f"   ├─ Current user_name cookie: {current_user_name}")
        logger.info(f"   ├─ Picture from token: {bool(picture)}")
        logger.info(f"   └─ Current user_picture cookie: {bool(current_user_picture)}")

        if full_name and current_user_name != full_name:
            logger.info(f"   ├─ User name changed, updating cookie")
            set_user_cookie(response, "user_name", full_name)
        else:
            logger.info(f"   ├─ User name unchanged")
            
        if picture and current_user_picture != picture:
            logger.info(f"   ├─ User picture changed, updating cookie")
            set_user_cookie(response, "user_picture", picture)
        else:
            logger.info(f"   ├─ User picture unchanged")
            
        logger.info(f"✅ USER COOKIES: User cookies updated successfully")
    except Exception as e:
        logger.error(f"❌ USER COOKIES: Error setting user cookies: {str(e)}")
        logger.error(f"   └─ This may affect user experience but not authentication")


# Helper functions for authentication middleware

def validate_user_id(payload, context="token"):
    """Validate that user ID exists in token payload"""
    user_id = payload.get("sub")
    if not user_id:
        logger.warning(f"{context} payload missing user ID")
        return None, create_error_response(
            f"Invalid {context} payload",
            status_code=401,
            error_type="auth_error"
        )
    return user_id, None


def create_auth_error_response(message, status_code=401):
    """Create a standardized authentication error response"""
    return create_error_response(
        message,
        status_code=status_code,
        error_type="auth_error"
    )


def set_secure_cookie(response, key, value, expires_seconds):
    """Set a secure cookie with standard security options"""
    logger.info(f"🍪 COOKIE: Setting secure cookie: {key}")
    logger.info(f"   ├─ Cookie name: {key}")
    logger.info(f"   ├─ Value length: {len(value) if value else 0}")
    logger.info(f"   ├─ Expires in: {expires_seconds} seconds")
    logger.info(f"   ├─ HttpOnly: True")
    logger.info(f"   ├─ Secure: True")
    logger.info(f"   └─ SameSite: none")
    
    try:
        response.set_cookie(
            key=key,
            value=value,
            expires=int(time.time() + expires_seconds),
            httponly=True,
            secure=True,
            samesite="none"
        )
        logger.info(f"✅ COOKIE: Successfully set {key} cookie")
    except Exception as e:
        logger.error(f"❌ COOKIE: Error setting {key} cookie: {str(e)}")
        logger.error(f"   ├─ Error type: {type(e).__name__}")
        logger.error(f"   └─ This may affect authentication")


def set_user_cookie(response, key, value, expires_seconds=3600):
    """Set a user-related cookie (less strict security for user info)"""
    logger.info(f"👤 USER COOKIE: Setting user cookie: {key}")
    logger.info(f"   ├─ Cookie name: {key}")
    logger.info(f"   ├─ Value: {value}")
    logger.info(f"   ├─ Expires in: {expires_seconds} seconds")
    logger.info(f"   └─ HttpOnly: True")
    
    try:
        response.set_cookie(
            key=key,
            value=value,
            expires=int(time.time() + expires_seconds),
            httponly=True
        )
        logger.info(f"✅ USER COOKIE: Successfully set {key} cookie")
    except Exception as e:
        logger.error(f"❌ USER COOKIE: Error setting {key} cookie: {str(e)}")
        logger.error(f"   └─ Error type: {type(e).__name__}")


