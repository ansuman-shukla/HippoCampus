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
from app.routers.subscription_router import router as subscription_router
from app.routers.admin_router import router as admin_router
from app.routers.monitoring_router import router as monitoring_router
from app.exceptions.global_exceptions import (
    global_exception_handler,
    AuthenticationError,
    create_error_response
)
from app.core.database_wrapper import get_database_health
from app.core.pinecone_wrapper import get_pinecone_health
from app.services.cron_service import start_cron_scheduler, stop_cron_scheduler, get_cron_status, get_cron_metrics

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

def clear_all_auth_cookies(response):
    """Clear all authentication cookies with proper domain settings"""
    logger.info(f"🧹 COOKIE CLEANUP: Clearing all authentication cookies")
    
    auth_cookie_names = [
        "access_token",
        "refresh_token", 
        "user_id",
        "user_name",
        "user_picture"
    ]
    
    for cookie_name in auth_cookie_names:
        try:
            # Clear with secure settings (matching how they were set)
            response.delete_cookie(
                key=cookie_name,
                path="/",
                samesite="none",
                secure=True
            )
            logger.info(f"   ├─ Cleared cookie: {cookie_name}")
        except Exception as e:
            logger.error(f"   ❌ Failed to clear cookie {cookie_name}: {str(e)}")
    
    logger.info(f"✅ COOKIE CLEANUP: All authentication cookies cleared")

# Create FastAPI app with enhanced error handling and comprehensive API documentation
app = FastAPI(
    title="HippoCampus API",
    description="""
## HippoCampus - I help you remember everything

A comprehensive knowledge management system with subscription-based limits for memories and summaries.

### Features

- **Memory Management**: Save and organize web content with vector search
- **AI Summaries**: Generate intelligent summaries of web content
- **Subscription Tiers**: Free and Pro plans with different limits
- **Admin Dashboard**: Complete subscription and user management
- **Monitoring**: Real-time metrics and health monitoring

### Subscription Tiers

#### Free Tier
- Up to 100 total memories (lifetime)
- Up to 5 summary pages per month

#### Pro Tier ($8/month)
- Unlimited memories
- Up to 100 summary pages per month
    """,
    version="1.0.0",
    contact={
        "name": "HippoCampus Support",
        "email": "support@hippocampus.ai",
    },
    license_info={
        "name": "MIT",
    },
    docs_url="/docs",           # Enable Swagger UI for development
    redoc_url="/redoc",         # Enable ReDoc for development  
    openapi_url="/openapi.json", # Enable OpenAPI JSON endpoint
    servers=[
        {
            "url": "https://hippocampus-backend.onrender.com",
            "description": "Production server"
        },
        {
            "url": "http://localhost:8000", 
            "description": "Development server"
        }
    ]
)

# CRON Scheduler Lifecycle Management
@app.on_event("startup")
async def startup_event():
    """
    FastAPI startup event - initialize CRON scheduler for subscription maintenance
    """
    logger.info("🚀 APPLICATION STARTUP: Initializing HippoCampus API services")
    
    try:
        # Start the CRON scheduler for subscription jobs
        logger.info("📅 STARTUP: Starting CRON scheduler for subscription maintenance")
        scheduler_result = start_cron_scheduler()
        
        if scheduler_result.get("status") == "started":
            logger.info("✅ STARTUP: CRON scheduler started successfully")
            logger.info(f"   ├─ Jobs registered: {scheduler_result.get('jobs_registered', 0)}")
            
            # Log registered jobs for monitoring
            jobs = scheduler_result.get("jobs", [])
            for job in jobs:
                logger.info(f"   ├─ Job: {job.get('name')} (ID: {job.get('id')})")
                logger.info(f"   │   └─ Next run: {job.get('next_run_time')}")
            
            logger.info(f"   └─ Scheduler operational and monitoring subscription lifecycle")
        else:
            logger.error("❌ STARTUP: Failed to start CRON scheduler")
            logger.error(f"   └─ Error: {scheduler_result.get('message', 'Unknown error')}")
            # Don't fail startup if scheduler fails - app can still function
            
    except Exception as e:
        logger.error(f"❌ STARTUP: Unexpected error starting CRON scheduler: {str(e)}")
        logger.error(f"   └─ Application will continue without background job scheduling")
    
    logger.info("✅ APPLICATION STARTUP: HippoCampus API initialization complete")

@app.on_event("shutdown")
async def shutdown_event():
    """
    FastAPI shutdown event - gracefully stop CRON scheduler
    """
    logger.info("🛑 APPLICATION SHUTDOWN: Gracefully shutting down HippoCampus API services")
    
    try:
        # Stop the CRON scheduler
        logger.info("📅 SHUTDOWN: Stopping CRON scheduler")
        scheduler_result = stop_cron_scheduler()
        
        if scheduler_result.get("status") == "stopped":
            logger.info("✅ SHUTDOWN: CRON scheduler stopped successfully")
        else:
            logger.warning(f"⚠️ SHUTDOWN: CRON scheduler stop returned: {scheduler_result.get('message', 'Unknown result')}")
            
    except Exception as e:
        logger.error(f"❌ SHUTDOWN: Error stopping CRON scheduler: {str(e)}")
        logger.error(f"   └─ This may leave background processes running")
    
    logger.info("✅ APPLICATION SHUTDOWN: HippoCampus API shutdown complete")

@app.middleware("http")
async def authorisation_middleware(request: Request, call_next):
    """
    Enhanced authentication middleware with improved token refresh capability
    """
    # Log initial request details
    logger.info(f"🔍 AUTH MIDDLEWARE: Incoming {request.method} request to {request.url.path}")
    logger.info(f"   ├─ User-Agent: {request.headers.get('user-agent', 'Unknown')[:50]}...")
    logger.info(f"   ├─ Remote IP: {request.client.host if request.client else 'Unknown'}")
    logger.info(f"   └─ Content-Type: {request.headers.get('content-type', 'None')}")
    
    # Skip auth for health check, auth endpoints, quotes, and documentation
    if (request.url.path in ["/health", "/health/detailed", "/docs", "/redoc", "/openapi.json"] or 
        request.url.path.startswith("/auth/") or 
        request.url.path.startswith("/quotes") or
        request.url.path.startswith("/monitoring/health")):
        logger.info(f"✅ AUTH MIDDLEWARE: Skipping auth for public endpoint: {request.url.path}")
        return await call_next(request)
    
    logger.info(f"🔐 AUTH MIDDLEWARE: Protected endpoint - authentication required")
    
    try:
        # Extract tokens from cookies or headers
        logger.info(f"🍪 AUTH MIDDLEWARE: Extracting tokens from request")
        access_token = request.cookies.get("access_token") or request.headers.get("access_token")
        refresh_token = request.cookies.get("refresh_token") or request.headers.get("refresh_token")
        
        # Log token presence (without exposing actual tokens)
        logger.info(f"   ├─ Access token present: {bool(access_token)} (length: {len(access_token) if access_token else 0})")
        logger.info(f"   └─ Refresh token present: {bool(refresh_token)} (length: {len(refresh_token) if refresh_token else 0})")

        if not access_token:
            logger.warning(f"❌ AUTH MIDDLEWARE: Missing access token for {request.method} {request.url}")
            logger.warning(f"   ├─ Available cookies: {list(request.cookies.keys())}")
            logger.warning(f"   └─ Available headers: {list(request.headers.keys())}")
            return create_auth_error_response("Access token is missing")

        payload = None
        new_access_token = None
        new_refresh_token = None
        token_refreshed = False

        # Try to validate the current access token
        logger.info(f"🔍 AUTH MIDDLEWARE: Attempting to validate access token")
        try:
            logger.info(f"   ├─ Decoding JWT token...")
            payload = await decodeJWT(access_token)
            logger.info(f"   ├─ JWT decode successful")
            logger.info(f"   ├─ Token subject (user_id): {payload.get('sub', 'Missing')}")
            logger.info(f"   ├─ Token issuer: {payload.get('iss', 'Missing')}")
            logger.info(f"   ├─ Token audience: {payload.get('aud', 'Missing')}")
            logger.info(f"   ├─ Token expiry: {payload.get('exp', 'Missing')}")
            logger.info(f"   └─ Token issued at: {payload.get('iat', 'Missing')}")
            
            user_id, error_response = validate_user_id(payload)
            if error_response:
                logger.error(f"❌ AUTH MIDDLEWARE: User ID validation failed")
                return error_response
            
            logger.info(f"✅ AUTH MIDDLEWARE: Access token validation successful for user: {user_id}")

        except TokenExpiredError:
            logger.warning(f"⏰ AUTH MIDDLEWARE: Access token expired, attempting refresh...")
            logger.info(f"   ├─ Starting token refresh process")
            logger.info(f"   ├─ Refresh token available: {bool(refresh_token)}")
            
            # Handle token refresh
            logger.info(f"🔄 AUTH MIDDLEWARE: Initiating token refresh")
            new_access_token, new_refresh_token, error_response = await handle_token_refresh(refresh_token)
            if error_response:
                logger.error(f"❌ AUTH MIDDLEWARE: Token refresh failed")
                logger.error(f"   ├─ Error status: {error_response.status_code}")
                logger.error(f"   └─ Error detail: {getattr(error_response, 'body', 'Unknown error')}")
                
                # Check if this is a session expired error requiring re-authentication
                if error_response.status_code == 401 and "session_expired" in str(error_response.body):
                    logger.warning(f"🚫 AUTH MIDDLEWARE: Session expired - clearing all auth cookies")
                    # Clear all authentication cookies to force fresh login
                    clear_all_auth_cookies(error_response)
                return error_response
            
            logger.info(f"✅ AUTH MIDDLEWARE: Token refresh successful")
            logger.info(f"   ├─ New access token received: {bool(new_access_token)}")
            logger.info(f"   └─ New refresh token received: {bool(new_refresh_token)}")
            
            # Decode the new access token to get user info
            logger.info(f"🔍 AUTH MIDDLEWARE: Validating refreshed access token")
            payload = await decodeJWT(new_access_token)
            user_id, error_response = validate_user_id(payload, "refreshed token")
            if error_response:
                logger.error(f"❌ AUTH MIDDLEWARE: Refreshed token validation failed")
                return error_response
            
            logger.info(f"✅ AUTH MIDDLEWARE: Refreshed token validation successful for user: {user_id}")
            token_refreshed = True
            
        except JWTError as e:
            logger.warning(f"❌ AUTH MIDDLEWARE: JWT validation failed: {str(e)}")
            logger.warning(f"   ├─ Error type: {type(e).__name__}")
            logger.warning(f"   └─ Token format issues detected")
            return create_auth_error_response(f"Invalid token: {str(e)}")
            
        except HTTPException as e:
            logger.warning(f"❌ AUTH MIDDLEWARE: HTTP exception during token validation: {e.detail}")
            logger.warning(f"   ├─ Status code: {e.status_code}")
            logger.warning(f"   └─ Error detail: {e.detail}")
            return create_error_response(
                e.detail,
                status_code=e.status_code,
                error_type="auth_error"
            )

        # Create user if not exists (with error handling)
        logger.info(f"👤 AUTH MIDDLEWARE: Ensuring user exists in database")
        try:
            await create_user_if_not_exists(payload)
            logger.info(f"✅ AUTH MIDDLEWARE: User validation/creation successful")
        except Exception as e:
            logger.error(f"❌ AUTH MIDDLEWARE: Error creating/validating user: {str(e)}")
            logger.error(f"   └─ Continuing request despite user creation error")
            # Don't fail the request if user creation fails

        # Store user info in request state
        logger.info(f"📝 AUTH MIDDLEWARE: Storing user context in request state")
        request.state.user_id = user_id
        request.state.user_payload = payload
        logger.info(f"   ├─ User ID: {user_id}")
        logger.info(f"   └─ Payload keys: {list(payload.keys())}")
        
        # Continue the request
        logger.info(f"➡️  AUTH MIDDLEWARE: Proceeding to route handler")
        response = await call_next(request)
        logger.info(f"⬅️  AUTH MIDDLEWARE: Route handler completed, processing response")
        logger.info(f"   ├─ Response status: {response.status_code}")
        logger.info(f"   └─ Response headers: {list(response.headers.keys())}")

        # Update cookies if tokens were refreshed
        if token_refreshed:
            logger.info(f"🍪 AUTH MIDDLEWARE: Updating authentication cookies with refreshed tokens")
            update_token_cookies(response, new_access_token, new_refresh_token, refresh_token)

        # Set user-related cookies if not already set
        logger.info(f"🍪 AUTH MIDDLEWARE: Updating user information cookies")
        update_user_cookies(response, request, user_id, payload)

        logger.info(f"✅ AUTH MIDDLEWARE: Request processing completed successfully")
        return response

    except Exception as e:
        logger.error(f"💥 AUTH MIDDLEWARE: Unexpected error in auth middleware: {str(e)}", exc_info=True)
        logger.error(f"   ├─ Error type: {type(e).__name__}")
        logger.error(f"   ├─ Request path: {request.url.path}")
        logger.error(f"   └─ Request method: {request.method}")
        return create_error_response(
            "Authentication service temporarily unavailable",
            status_code=503,
            error_type="auth_service_error"
        )


# Add global exception handler
app.add_exception_handler(Exception, global_exception_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "chrome-extension://pbmpglcjfdjmjokffakahlncegdcefno",  # Chrome extension
        "http://localhost:5173",  # Admin frontend dev server
        "http://localhost:4173",  # Admin frontend preview
        "http://127.0.0.1:5173",  # Admin frontend dev server (alternative)
        "http://127.0.0.1:4173",  # Admin frontend preview (alternative)
    ],
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
        cron_health = get_cron_status()

        overall_status = "healthy"
        if (db_health.get("status") != "healthy" or
            pinecone_health.get("status") != "healthy" or
            not cron_health.get("scheduler_running", False)):
            overall_status = "degraded"

        return {
            "status": overall_status,
            "timestamp": datetime.now().isoformat(),
            "services": {
                "database": db_health,
                "vector_db": pinecone_health,
                "cron_scheduler": {
                    "status": "healthy" if cron_health.get("scheduler_running", False) else "unhealthy",
                    "scheduler_running": cron_health.get("scheduler_running", False),
                    "jobs_count": cron_health.get("jobs_count", 0),
                    "jobs": cron_health.get("jobs", [])
                }
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

@app.get("/health/cron")
async def cron_health_check():
    """CRON scheduler specific health check and status"""
    try:
        cron_status = get_cron_status()
        cron_metrics = get_cron_metrics()
        
        return {
            "status": "healthy" if cron_status.get("scheduler_running", False) else "unhealthy",
            "timestamp": datetime.now().isoformat(),
            "scheduler": cron_status,
            "metrics": cron_metrics
        }
    except Exception as e:
        logger.error(f"Error in CRON health check: {str(e)}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "timestamp": datetime.now().isoformat(),
                "error": "CRON health check failed"
            }
        )

app.include_router(bookmark_router)
app.include_router(get_quotes_router)
app.include_router(notes_router)
app.include_router(summary_router)
app.include_router(auth_router)
app.include_router(subscription_router)
app.include_router(admin_router)
app.include_router(monitoring_router)
