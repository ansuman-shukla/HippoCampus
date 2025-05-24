from jose import jwt, JWTError, ExpiredSignatureError
from app.core.config import settings
from fastapi import HTTPException, status
import httpx
import logging

logger = logging.getLogger(__name__)

async def decodeJWT(access_token: str) -> dict:
    # Clean the token input
    access_token = access_token.strip()
    # logger.info(f"JWT secret: {settings.SUPABASE_ANON_KEY}")
    # logger.info(f"Decoding token: {access_token}")
    # Remove Bearer prefix if present
    if access_token.lower().startswith("bearer "):
        access_token = access_token[7:].strip()

    if not access_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing access token"
        )

    # Clean and verify JWT secret
    jwt_secret = settings.SUPABASE_ANON_KEY.strip()
    
    if not jwt_secret:
        logger.error("JWT secret is missing in configuration")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Server configuration error"
        )

    try:
        # Decode with additional validation parameters
        payload = jwt.decode(
            token=access_token,
            key=jwt_secret,
            algorithms=["HS256"],
            options={
                "verify_signature": True,
                "verify_aud": False,  # Temporarily disable audience validation
                "verify_exp": True,
            }
        )

        # Additional manual expiration check (redundant but safe)
        if 'exp' not in payload:
            logger.warning("Token missing expiration claim")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has no expiration"
            )

        return payload

    except ExpiredSignatureError as e:
        logger.warning(f"Expired token: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired"
        )
    except JWTError as e:
        logger.error(f"JWT decoding failed: {str(e)}")
        # Enhanced error diagnostics
        debug_info = {
            "token_length": len(access_token),
            "secret_prefix": jwt_secret[:3] + "..." if jwt_secret else None,
            "algorithm": "HS256",
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
    


async def create_tokens(refresh_token: str) -> dict:
    url = f"{settings.SUPABASE_URL}/auth/v1/token"
    headers = {
        "apikey": settings.SUPABASE_API_KEY,
        "Authorization": f"Bearer {settings.SUPABASE_ANON_KEY}",
        "Content-Type": "application/json"
    }
    data = {"refresh_token": refresh_token}

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(url, headers=headers, json=data)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"Supabase refresh failed: {e.response.text}")
            raise HTTPException(
                status_code=e.response.status_code,
                detail="Token refresh failed"
            )
        except httpx.RequestError as e:
            logger.error(f"Connection error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Unable to connect to auth service"
            )