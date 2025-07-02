from jose import jwt, JWTError
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
from app.routers.bookmarkRouters import router as bookmark_router
from app.utils.jwt import decodeJWT, refresh_access_token, TokenExpiredError
from app.services.user_service import create_user_if_not_exists
from fastapi.middleware.cors import CORSMiddleware
from app.routers.get_quotes import router as get_quotes_router
from app.routers.notesRouter import router as notes_router
from app.routers.summaryRouter import router as summary_router
from app.routers.auth_router import router as auth_router
from app.exceptions.global_exceptions import (
    global_exception_handler,
    AuthenticationError,
    create_error_response
)
from app.core.database_wrapper import get_database_health
from app.core.pinecone_wrapper import get_pinecone_health

load_dotenv()

import logging
import time
from datetime import datetime
import asyncio
from collections import defaultdict

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global refresh token locks to prevent race conditions
refresh_locks = defaultdict(asyncio.Lock)
active_refreshes = {}  # Store active refresh promises

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
    try:
        response.set_cookie(
            key=key,
            value=value,
            expires=int(time.time() + expires_seconds),
            httponly=True,
            secure=True,
            samesite="none"
        )
        logger.info(f"Updated {key} cookie")
    except Exception as e:
        logger.error(f"Error setting {key} cookie: {str(e)}")

def set_user_cookie(response, key, value, expires_seconds=3600):
    """Set a user-related cookie (less strict security for user info)"""
    try:
        response.set_cookie(
            key=key,
            value=value,
            expires=int(time.time() + expires_seconds),
            httponly=True
        )
    except Exception as e:
        logger.error(f"Error setting {key} cookie: {str(e)}")

def handle_token_refresh(refresh_token):
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
            
            # Check for "already used" error - this means we need to re-authenticate
            if "already_used" in error_detail.lower() or "already used" in error_detail:
                logger.warning("Refresh token already used - requiring re-authentication")
                # Create response that will clear cookies
                error_response = create_error_response(
                    "Session expired. Please log in again.",
                    status_code=401,
                    error_type="session_expired"
                )
                # Add flag to clear cookies
                error_response.headers["X-Clear-Auth"] = "true"
                return None, None, error_response
            
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
    try:
        # Set new access token
        if new_access_token:
            set_secure_cookie(response, "access_token", new_access_token, 3600)  # 1 hour
        
        # Set new refresh token if different
        if new_refresh_token and new_refresh_token != original_refresh_token:
            set_secure_cookie(response, "refresh_token", new_refresh_token, 604800)  # 7 days
            
    except Exception as e:
        logger.error(f"Error setting refreshed token cookies: {str(e)}")

def update_user_cookies(response, request, user_id, payload):
    """Update user-related cookies if not already set"""
    try:
        # Set user_id cookie if not already set
        if request.cookies.get("user_id") is None:
            set_user_cookie(response, "user_id", user_id)

        # Set user metadata cookies if not already set
        if (request.cookies.get("user_name") is None or
            request.cookies.get("user_picture") is None):
            user_metadata = payload.get("user_metadata", {})
            full_name = user_metadata.get("full_name")
            picture = user_metadata.get("picture")

            if full_name:
                set_user_cookie(response, "user_name", full_name)
            if picture:
                set_user_cookie(response, "user_picture", picture)
                
    except Exception as e:
        logger.error(f"Error setting user cookies: {str(e)}")

# Create FastAPI app with enhanced error handling
app = FastAPI(
    title="HippoCampus API",
    description="I help you remember everything",
    version="1.0.0"
)

@app.middleware("http")
async def authorisation_middleware(request: Request, call_next):
    """
    Enhanced authentication middleware with improved token refresh capability
    """    # Skip auth for health check, auth endpoints, and documentation
    if request.url.path in ["/health", "/health/detailed", "/docs", "/redoc", "/openapi.json"] or request.url.path.startswith("/auth/"):
        return await call_next(request)
    
    try:
        # Extract tokens from cookies or headers
        access_token = request.cookies.get("access_token") or request.headers.get("access_token")
        refresh_token = request.cookies.get("refresh_token") or request.headers.get("refresh_token")

        if not access_token:
            logger.warning(f"Missing access token for {request.method} {request.url}")
            return create_auth_error_response("Access token is missing")

        payload = None
        new_access_token = None
        new_refresh_token = None
        token_refreshed = False

        # Try to validate the current access token
        try:
            payload = await decodeJWT(access_token)
            user_id, error_response = validate_user_id(payload)
            if error_response:
                return error_response

        except TokenExpiredError:
            logger.info("Access token expired, attempting refresh...")
            
            # Handle token refresh
            new_access_token, new_refresh_token, error_response = await handle_token_refresh(refresh_token)
            if error_response:
                # Check if this is a session expired error requiring re-authentication
                if (error_response.status_code == 401 and 
                    ("session_expired" in str(error_response.body) or 
                     error_response.headers.get("X-Clear-Auth") == "true")):
                    # Clear all auth-related cookies
                    logger.info("Session expired - clearing all auth cookies")
                    response = error_response
                    # Clear auth cookies with proper domain and security settings
                    response.delete_cookie("access_token", path="/", samesite="none", secure=True, httponly=True)
                    response.delete_cookie("refresh_token", path="/", samesite="none", secure=True, httponly=True)
                    response.delete_cookie("user_id", path="/", httponly=True)
                    response.delete_cookie("user_name", path="/", httponly=True)
                    response.delete_cookie("user_picture", path="/", httponly=True)
                    # Add header to signal frontend
                    response.headers["X-Auth-Required"] = "true"
                return error_response
            
            # Decode the new access token to get user info
            payload = await decodeJWT(new_access_token)
            user_id, error_response = validate_user_id(payload, "refreshed token")
            if error_response:
                return error_response
            
            token_refreshed = True
            
        except JWTError as e:
            logger.warning(f"JWT validation failed: {str(e)}")
            return create_auth_error_response(f"Invalid token: {str(e)}")
            
        except HTTPException as e:
            logger.warning(f"Token validation failed: {e.detail}")
            return create_error_response(
                e.detail,
                status_code=e.status_code,
                error_type="auth_error"
            )

        # Create user if not exists (with error handling)
        try:
            await create_user_if_not_exists(payload)
        except Exception as e:
            logger.error(f"Error creating user: {str(e)}")
            # Don't fail the request if user creation fails

        # Store user info in request state
        request.state.user_id = user_id
        request.state.user_payload = payload
        
        # Continue the request
        response = await call_next(request)

        # Update cookies if tokens were refreshed
        if token_refreshed:
            update_token_cookies(response, new_access_token, new_refresh_token, refresh_token)

        # Set user-related cookies if not already set
        update_user_cookies(response, request, user_id, payload)

        return response

    except Exception as e:
        logger.error(f"Unexpected error in auth middleware: {str(e)}", exc_info=True)
        return create_error_response(
            "Authentication service temporarily unavailable",
            status_code=503,
            error_type="auth_service_error"
        )


# Add global exception handler
app.add_exception_handler(Exception, global_exception_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["chrome-extension://pbmpglcjfdjmjokffakahlncegdcefno"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health check endpoints
@app.get("/health")
async def health_check():
    """Basic health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "HippoCampus API"
    }

@app.get("/health/detailed")
async def detailed_health_check():
    """Detailed health check including database and external services"""
    try:
        db_health = await get_database_health()
        pinecone_health = await get_pinecone_health()

        overall_status = "healthy"
        if (db_health.get("status") != "healthy" or
            pinecone_health.get("status") != "healthy"):
            overall_status = "degraded"

        return {
            "status": overall_status,
            "timestamp": datetime.now().isoformat(),
            "services": {
                "database": db_health,
                "vector_db": pinecone_health
            }
        }
    except Exception as e:
        logger.error(f"Error in detailed health check: {str(e)}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "timestamp": datetime.now().isoformat(),
                "error": "Health check failed"
            }
        )

app.include_router(bookmark_router)
app.include_router(get_quotes_router)
app.include_router(notes_router)
app.include_router(summary_router)
app.include_router(auth_router)
