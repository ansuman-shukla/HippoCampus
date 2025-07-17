# Rate Limiting Implementation

## Overview

This FastAPI application now includes comprehensive rate limiting using SlowAPI (a FastAPI-compatible port of Flask-Limiter). The rate limiting is designed to:

- **Prevent API abuse** by limiting requests per user
- **Track usage per route + user** for granular control
- **Return 429 Too Many Requests** automatically when limits are exceeded
- **Use in-memory storage** (no Redis required for now)

## Rate Limits Configuration

### Bookmark Operations
- **POST `/links/save`**: 10 requests per minute per user ⬅️ **UPDATED**
- **GET `/links/get`**: 20 requests per minute per user
- **POST `/links/search`**: 15 requests per minute per user ⬅️ **NEW**
- **DELETE `/links/delete`**: 15 requests per minute per user ⬅️ **NEW**

### Notes Operations  
- **POST `/notes/`**: 15 requests per minute per user
- **GET `/notes/`**: 20 requests per minute per user
- **POST `/notes/search`**: 15 requests per minute per user ⬅️ **NEW**
- **PUT `/notes/{note_id}`**: 15 requests per minute per user ⬅️ **NEW**
- **DELETE `/notes/{note_id}`**: 15 requests per minute per user ⬅️ **NEW**

### Summary Operations
- **POST `/summary/generate`**: 5 requests per day per user

## Implementation Details

### 1. Key Function Strategy
The rate limiter uses a custom key function that:
- For **authenticated users**: `user:{user_id}:route:{route_path}`
- For **unauthenticated requests**: `ip:{client_ip}:route:{route_path}`

This ensures:
- Each user has independent rate limits
- Each route has separate rate limits
- Fallback to IP-based limiting for unauthenticated requests

### 2. Architecture

```
Request → Auth Middleware → Rate Limit Middleware → Route Handler
                ↓
        Sets user_id in request.state
                ↓
        Used by rate limiter for per-user tracking
```

### 3. Files Modified

#### Main Configuration (`app/main.py`)
- Added SlowAPI imports and middleware
- Created custom key function for per-user + per-route tracking
- Configured rate limiter with in-memory storage
- Added exception handler for 429 responses

#### Router Configurations
- **`app/routers/bookmarkRouters.py`**: Added limits to save/get endpoints
- **`app/routers/notesRouter.py`**: Added limits to create/get endpoints  
- **`app/routers/summaryRouter.py`**: Added daily limit to generate endpoint

### 4. Dependencies Added
- `slowapi` - Main rate limiting library

## Usage Examples

### Normal Operation
```bash
# Within limits - returns normal response
curl -X GET "http://localhost:8000/links/get" \
  -H "Authorization: Bearer <token>"
# Response: 200 OK with bookmark data
```

### Rate Limit Exceeded
```bash
# After exceeding 20 requests per minute
curl -X GET "http://localhost:8000/links/get" \
  -H "Authorization: Bearer <token>"
# Response: 429 Too Many Requests
# {
#   "error": "Too Many Requests: 20 per 1 minute"
# }
```

## Testing Rate Limits

To test the rate limiting functionality:

1. **Start the server**: `uvicorn app.main:app --reload`
2. **Make authenticated requests** to any protected endpoint
3. **Exceed the limits** for your user to trigger 429 responses

## Monitoring & Debugging

### Rate Limit Headers
SlowAPI automatically adds headers to responses:
- `X-RateLimit-Limit`: The rate limit ceiling
- `X-RateLimit-Remaining`: Requests remaining in current window
- `X-RateLimit-Reset`: Time when the rate limit resets

### Logs
Rate limit events are logged automatically by SlowAPI middleware.

## Scaling Considerations

### Current Setup (In-Memory)
- ✅ Simple setup, no external dependencies
- ✅ Fast performance for single server
- ❌ Not shared across multiple server instances
- ❌ Rate limits reset on server restart

### Future: Redis Backend
To scale across multiple servers, consider upgrading to Redis:

```python
# In main.py, replace the limiter initialization:
limiter = Limiter(
    key_func=get_user_route_key,
    storage_uri="redis://localhost:6379"
)
```

## Security Benefits

1. **DDoS Protection**: Prevents overwhelming the API with too many requests
2. **Resource Management**: Ensures fair usage across all users
3. **Cost Control**: Limits expensive operations like summary generation
4. **Abuse Prevention**: Makes it harder to scrape or attack the API

## Customization

### Adding New Rate Limits
To add rate limiting to a new endpoint:

```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@router.post("/new-endpoint")
@limiter.limit("10/minute")  # 10 requests per minute
async def new_endpoint(request: Request):
    # Your endpoint logic
    pass
```

### Changing Existing Limits
Modify the decorator values in the respective router files:

```python
@limiter.limit("25/minute")  # Changed from 15/minute to 25/minute
```

## Troubleshooting

### Common Issues

1. **Rate limits not working**
   - Check that SlowAPIMiddleware is added to the app
   - Verify the limiter is attached to app.state
   - Ensure decorators are applied correctly

2. **429 errors for legitimate users**
   - Review the rate limits - they might be too restrictive
   - Check if multiple users share the same IP (behind NAT)
   - Consider implementing different limits for different user tiers

3. **Rate limits reset unexpectedly**
   - In-memory storage resets on server restart
   - Consider switching to Redis for persistence

### Error Messages
- `RateLimitExceeded`: The user has exceeded their rate limit
- `Invalid rate limit`: Check the limit string format (e.g., "10/minute")

## Future Enhancements

1. **User-Tier Based Limits**: Different limits for premium vs free users
2. **Dynamic Rate Limits**: Adjust limits based on server load
3. **Redis Backend**: For multi-server deployments
4. **Custom Error Messages**: More user-friendly rate limit error responses
5. **Rate Limit Analytics**: Track and analyze rate limit patterns 