from jose import jwt, JWTError
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
from app.routers.bookmarkRouters import router as bookmark_router
from app.utils.jwt import decodeJWT, create_tokens
from app.services.user_service import create_user_if_not_exists
from fastapi.middleware.cors import CORSMiddleware
from app.routers.get_quotes import router as get_quotes_router
from app.routers.notesRouter import router as notes_router
from app.routers.summaryRouter import router as summary_router
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

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create FastAPI app with enhanced error handling
app = FastAPI(
    title="HippoCampus API",
    description="Personal knowledge management system with graceful error handling",
    version="1.0.0"
)

@app.middleware("http")
async def authorisation_middleware(request: Request, call_next):
    """
    Enhanced authentication middleware with graceful error handling
    """
    try:
        access_token = request.cookies.get("access_token")
        refresh_token = request.cookies.get("refresh_token")

        if not access_token:
            logger.warning(f"Missing access token for {request.method} {request.url}")
            return create_error_response(
                "Access token is missing",
                status_code=401,
                error_type="auth_error"
            )

        if refresh_token:
            # token = await create_tokens(refresh_token)
            # return token
            pass

        # Validate the access token
        try:
            payload = await decodeJWT(access_token)
            user_id = payload.get("sub")

            if not user_id:
                logger.warning("Token payload missing user ID")
                return create_error_response(
                    "Invalid token payload",
                    status_code=401,
                    error_type="auth_error"
                )

        except JWTError as e:
            logger.warning(f"JWT validation failed: {str(e)}")
            return create_error_response(
                f"Invalid token: {str(e)}",
                status_code=401,
                error_type="auth_error"
            )

        # Create user if not exists (with error handling)
        try:
            await create_user_if_not_exists(payload)
        except Exception as e:
            logger.error(f"Error creating user: {str(e)}")
            # Don't fail the request if user creation fails
            # Just log the error and continue

        # Continue the request
        response = await call_next(request)

        # Post-processing: modify response (with error handling)
        try:
            if request.cookies.get("user_id") is None:
                response.set_cookie(
                    key="user_id",
                    value=user_id,
                    expires=int(time.time() + 3600),
                    httponly=True
                )

            if (request.cookies.get("user_name") is None or
                request.cookies.get("user_picture") is None):
                user_metadata = payload.get("user_metadata", {})
                full_name = user_metadata.get("full_name")
                picture = user_metadata.get("picture")

                if full_name:
                    response.set_cookie(
                        key="user_name",
                        value=full_name,
                        expires=int(time.time() + 3600),
                        httponly=True
                    )
                if picture:
                    response.set_cookie(
                        key="user_picture",
                        value=picture,
                        expires=int(time.time() + 3600),
                        httponly=True
                    )
        except Exception as e:
            logger.error(f"Error setting cookies: {str(e)}")
            # Don't fail the request if cookie setting fails

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