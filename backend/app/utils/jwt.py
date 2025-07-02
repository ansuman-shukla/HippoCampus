from jose import jwt, JWTError, ExpiredSignatureError
from app.core.config import settings
from fastapi import HTTPException, status
import httpx
import logging

logger = logging.getLogger(__name__)


class TokenExpiredError(Exception):
    """Custom exception for expired tokens that can be refreshed"""
    pass

async def decodeJWT(access_token: str) -> dict:
    """
    Decode Supabase JWT token using the proper JWT secret
    """
    # Clean the token input
    access_token = access_token.strip()
    
    # Remove Bearer prefix if present
    if access_token.lower().startswith("bearer "):
        access_token = access_token[7:].strip()

    if not access_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing access token"
        )

    # Use the proper JWT secret for Supabase tokens
    jwt_secret = settings.SUPABASE_JWT_SECRET.strip()
    
    if not jwt_secret:
        logger.error("Supabase JWT secret is missing in configuration")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Server configuration error"
        )

    try:
        # Decode with Supabase-specific settings
        payload = jwt.decode(
            token=access_token,
            key=jwt_secret,
            algorithms=["HS256"],
            options={
                "verify_signature": True,
                "verify_aud": True,  # Supabase tokens have audience
                "verify_exp": True,
                "verify_iss": True,  # Supabase tokens have issuer
            },
            # Expected audience and issuer for Supabase
            audience="authenticated",
            issuer=f"{settings.SUPABASE_URL}/auth/v1"
        )

        # Validate required claims
        if 'sub' not in payload:
            logger.warning("Token missing subject (user ID)")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token: missing user ID"
            )

        if 'exp' not in payload:
            logger.warning("Token missing expiration claim")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has no expiration"
            )

        return payload

    except ExpiredSignatureError as e:
        logger.warning(f"Expired token: {str(e)}")
        raise TokenExpiredError("Token has expired")
    except JWTError as e:
        logger.warning(f"JWT decoding failed: {str(e)}")
        # Enhanced error diagnostics
        debug_info = {
            "token_length": len(access_token),
            "secret_configured": bool(jwt_secret),
            "algorithm": "HS256",
            "expected_audience": "authenticated",
            "expected_issuer": settings.SUPABASE_URL
        }
        logger.debug(f"Decoding debug info: {debug_info}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Unexpected error during JWT decoding: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Token validation error"
        )
    


async def refresh_access_token(refresh_token: str) -> dict:
    """
    Refresh access token using Supabase refresh token
    Returns new access token and refresh token
    """
    if not refresh_token or not refresh_token.strip():
        logger.error("Empty refresh token provided")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )
    
    # Use the correct Supabase refresh token endpoint format
    url = f"{settings.SUPABASE_URL}/auth/v1/token?grant_type=refresh_token"
    headers = {
        "apikey": settings.SUPABASE_ANON_KEY,
        "Content-Type": "application/json"
    }
    data = {
        "refresh_token": refresh_token.strip()
    }

    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            logger.info(f"Attempting to refresh access token for token: {refresh_token[:8]}...")
            response = await client.post(url, headers=headers, json=data)
            
            # Log response details for debugging
            logger.info(f"Refresh response status: {response.status_code}")
            
            if response.status_code == 200:
                token_data = response.json()
                
                # Validate response structure
                if "access_token" not in token_data:
                    logger.error(f"Invalid refresh response structure: {list(token_data.keys())}")
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail="Invalid refresh token response from auth service"
                    )
                
                logger.info("Successfully refreshed access token")
                return token_data
            else:
                # Handle error responses
                error_text = response.text
                logger.error(f"Supabase refresh failed with status {response.status_code}: {error_text}")
                
                try:
                    error_json = response.json()
                    error_code = error_json.get("error_code", "")
                    detail = error_json.get("error_description", error_json.get("msg", "Invalid refresh token"))
                    
                    # Check for various refresh token failure scenarios
                    if any(phrase in error_code.lower() for phrase in ["already_used", "invalid_grant", "revoked", "expired"]):
                        detail = "Session expired. Please log in again."
                
                except Exception:
                    detail = "Invalid refresh token"
                
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail=detail
                )
            
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error during refresh: {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token refresh failed"
            )
        except httpx.RequestError as e:
            logger.error(f"Request to auth service failed: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Authentication service is unavailable"
            )


# Legacy function for backward compatibility
async def verify_and_refresh_token(access_token: str, refresh_token: str) -> dict:
    """
    Legacy function - use refresh_access_token instead
    """
    return await refresh_access_token(refresh_token)