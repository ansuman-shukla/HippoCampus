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
    logger.info(f"🔑 JWT DECODE: Starting JWT token validation")
    
    # Clean the token input
    original_token_length = len(access_token) if access_token else 0
    access_token = access_token.strip()
    logger.info(f"   ├─ Original token length: {original_token_length}")
    logger.info(f"   ├─ Cleaned token length: {len(access_token)}")
    
    # Remove Bearer prefix if present
    if access_token.lower().startswith("bearer "):
        access_token = access_token[7:].strip()
        logger.info(f"   ├─ Removed Bearer prefix, final length: {len(access_token)}")

    if not access_token:
        logger.error(f"❌ JWT DECODE: Empty access token after cleaning")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing access token"
        )

    # Use the proper JWT secret for Supabase tokens
    jwt_secret = settings.SUPABASE_JWT_SECRET.strip()
    logger.info(f"   ├─ JWT secret configured: {bool(jwt_secret)}")
    logger.info(f"   ├─ JWT secret length: {len(jwt_secret) if jwt_secret else 0}")
    
    if not jwt_secret:
        logger.error("❌ JWT DECODE: Supabase JWT secret is missing in configuration")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Server configuration error"
        )

    expected_audience = "authenticated"
    expected_issuer = f"{settings.SUPABASE_URL}/auth/v1"
    logger.info(f"   ├─ Expected audience: {expected_audience}")
    logger.info(f"   ├─ Expected issuer: {expected_issuer}")
    logger.info(f"   └─ Supabase URL: {settings.SUPABASE_URL}")

    try:
        logger.info(f"🔍 JWT DECODE: Attempting to decode token with HS256 algorithm")
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
            audience=expected_audience,
            issuer=expected_issuer
        )

        logger.info(f"✅ JWT DECODE: Token decoded successfully")
        logger.info(f"   ├─ Payload keys: {list(payload.keys())}")
        logger.info(f"   ├─ Subject (user_id): {payload.get('sub', 'Missing')}")
        logger.info(f"   ├─ Email: {payload.get('email', 'Missing')}")
        logger.info(f"   ├─ Audience: {payload.get('aud', 'Missing')}")
        logger.info(f"   ├─ Issuer: {payload.get('iss', 'Missing')}")
        logger.info(f"   ├─ Issued at: {payload.get('iat', 'Missing')}")
        logger.info(f"   └─ Expires at: {payload.get('exp', 'Missing')}")

        # Validate required claims
        if 'sub' not in payload:
            logger.warning("❌ JWT DECODE: Token missing subject (user ID)")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token: missing user ID"
            )

        if 'exp' not in payload:
            logger.warning("❌ JWT DECODE: Token missing expiration claim")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has no expiration"
            )

        logger.info(f"✅ JWT DECODE: All required claims validated successfully")
        return payload

    except ExpiredSignatureError as e:
        logger.warning(f"⏰ JWT DECODE: Token has expired: {str(e)}")
        logger.warning(f"   └─ Raising TokenExpiredError for refresh handling")
        raise TokenExpiredError("Token has expired")
    except JWTError as e:
        logger.warning(f"❌ JWT DECODE: JWT decoding failed: {str(e)}")
        logger.warning(f"   ├─ Error type: {type(e).__name__}")
        logger.warning(f"   └─ This indicates token format or signature issues")
        # Enhanced error diagnostics
        debug_info = {
            "token_length": len(access_token),
            "secret_configured": bool(jwt_secret),
            "algorithm": "HS256",
            "expected_audience": expected_audience,
            "expected_issuer": expected_issuer
        }
        logger.debug(f"🔍 JWT DECODE: Debug info: {debug_info}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {str(e)}"
        )
    except Exception as e:
        logger.error(f"💥 JWT DECODE: Unexpected error during JWT decoding: {str(e)}")
        logger.error(f"   ├─ Error type: {type(e).__name__}")
        logger.error(f"   └─ This is likely a configuration or system error")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Token validation error"
        )
    


async def refresh_access_token(refresh_token: str) -> dict:
    """
    Refresh access token using Supabase refresh token
    Returns new access token and refresh token
    """
    logger.info(f"🔄 TOKEN REFRESH: Starting token refresh process")
    
    if not refresh_token or not refresh_token.strip():
        logger.error("❌ TOKEN REFRESH: Empty refresh token provided")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )
    
    refresh_token = refresh_token.strip()
    logger.info(f"   ├─ Refresh token length: {len(refresh_token)}")
    logger.info(f"   ├─ Refresh token prefix: {refresh_token[:8]}...")
    
    # Use the correct Supabase refresh token endpoint format
    url = f"{settings.SUPABASE_URL}/auth/v1/token?grant_type=refresh_token"
    logger.info(f"   ├─ Refresh endpoint: {url}")
    logger.info(f"   ├─ Supabase URL: {settings.SUPABASE_URL}")
    logger.info(f"   └─ Grant type: refresh_token")
    
    headers = {
        "apikey": settings.SUPABASE_ANON_KEY,
        "Content-Type": "application/json"
    }
    logger.info(f"🌐 TOKEN REFRESH: Preparing request headers")
    logger.info(f"   ├─ API key configured: {bool(settings.SUPABASE_ANON_KEY)}")
    logger.info(f"   ├─ API key length: {len(settings.SUPABASE_ANON_KEY) if settings.SUPABASE_ANON_KEY else 0}")
    logger.info(f"   └─ Content-Type: application/json")
    
    data = {
        "refresh_token": refresh_token
    }

    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            logger.info(f"📡 TOKEN REFRESH: Sending refresh request to Supabase")
            logger.info(f"   ├─ Timeout: 10.0 seconds")
            logger.info(f"   └─ Request payload keys: {list(data.keys())}")
            
            response = await client.post(url, headers=headers, json=data)
            
            # Log response details for debugging
            logger.info(f"📨 TOKEN REFRESH: Response received from Supabase")
            logger.info(f"   ├─ Response status: {response.status_code}")
            logger.info(f"   ├─ Response headers: {list(response.headers.keys())}")
            logger.info(f"   └─ Response size: {len(response.content)} bytes")
            
            if response.status_code == 200:
                logger.info(f"✅ TOKEN REFRESH: Successful response from Supabase")
                token_data = response.json()
                
                logger.info(f"🔍 TOKEN REFRESH: Validating response structure")
                logger.info(f"   ├─ Response keys: {list(token_data.keys())}")
                
                # Validate response structure
                if "access_token" not in token_data:
                    logger.error(f"❌ TOKEN REFRESH: Invalid refresh response structure")
                    logger.error(f"   ├─ Expected 'access_token' key missing")
                    logger.error(f"   └─ Available keys: {list(token_data.keys())}")
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail="Invalid refresh token response from auth service"
                    )
                
                # Log token information (without exposing full tokens)
                new_access_token = token_data.get("access_token", "")
                new_refresh_token = token_data.get("refresh_token", "")
                expires_in = token_data.get("expires_in", "Unknown")
                token_type = token_data.get("token_type", "Bearer")
                
                logger.info(f"🎯 TOKEN REFRESH: New tokens received")
                logger.info(f"   ├─ New access token length: {len(new_access_token)}")
                logger.info(f"   ├─ New refresh token length: {len(new_refresh_token)}")
                logger.info(f"   ├─ Token type: {token_type}")
                logger.info(f"   ├─ Expires in: {expires_in} seconds")
                logger.info(f"   └─ Refresh token changed: {new_refresh_token != refresh_token}")
                
                logger.info("✅ TOKEN REFRESH: Token refresh completed successfully")
                return token_data
            else:
                # Handle error responses
                error_text = response.text
                logger.error(f"❌ TOKEN REFRESH: Supabase refresh failed")
                logger.error(f"   ├─ Status code: {response.status_code}")
                logger.error(f"   ├─ Error response: {error_text[:200]}...")
                logger.error(f"   └─ Full response size: {len(error_text)} characters")
                
                try:
                    error_json = response.json()
                    error_code = error_json.get("error", "unknown_error")
                    detail = error_json.get("error_description", error_json.get("msg", "Invalid refresh token"))
                    logger.error(f"   ├─ Error code: {error_code}")
                    logger.error(f"   └─ Error description: {detail}")
                except Exception as json_error:
                    logger.error(f"   └─ Could not parse error JSON: {str(json_error)}")
                    detail = "Invalid refresh token"
                
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail=detail
                )
            
        except httpx.HTTPStatusError as e:
            logger.error(f"❌ TOKEN REFRESH: HTTP status error during refresh")
            logger.error(f"   ├─ Error type: {type(e).__name__}")
            logger.error(f"   ├─ Status code: {e.response.status_code if e.response else 'Unknown'}")
            logger.error(f"   └─ Error message: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token refresh failed"
            )
        except httpx.RequestError as e:
            logger.error(f"💥 TOKEN REFRESH: Request error - auth service unavailable")
            logger.error(f"   ├─ Error type: {type(e).__name__}")
            logger.error(f"   ├─ Error message: {str(e)}")
            logger.error(f"   └─ This indicates network or service issues")
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