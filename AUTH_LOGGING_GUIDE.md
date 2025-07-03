# Authentication Flow Logging Guide

## Overview

This document outlines the comprehensive logging system that has been added to track every step of the authentication flow in both frontend and backend components.

## Logging Structure

### 🔍 Log Format
All logs use emojis and structured formatting for easy identification:
- 🔍 **AUTH MIDDLEWARE**: Backend middleware operations
- 🔑 **JWT DECODE**: Token validation and decoding
- 🔄 **TOKEN REFRESH**: Token refresh operations
- 🔐 **AUTH LOGIN**: Login endpoint operations
- 🚪 **AUTH LOGOUT**: Logout operations
- 👤 **USER SERVICE**: User creation and validation
- 🍪 **COOKIE**: Cookie operations
- 🌐 **API CLIENT**: Frontend API requests
- 📡 **Network**: Network operations

### Log Levels
- `INFO`: Normal flow operations
- `WARN`: Non-critical issues (expired tokens, etc.)
- `ERROR`: Failures that affect functionality
- `DEBUG`: Detailed debugging information

## Authentication Flow Tracking

### 1. Frontend Request Initiation

**Location**: `frontend/src/utils/apiClient.ts` & `frontend/src/utils/authUtils.ts`

**What's Logged**:
- Request method, endpoint, and full URL
- Request headers and body information
- Request timing and performance metrics
- Response status and headers
- Error details and types

**Example Log Output**:
```
🌐 API CLIENT: Initiating POST request
   ├─ Endpoint: /bookmarks
   ├─ Full URL: http://localhost:8000/bookmarks
   ├─ Base URL: http://localhost:8000
   └─ Method: POST

🔧 API CLIENT: Request configuration
   ├─ Credentials: include
   ├─ Headers: {"Content-Type":"application/json"}
   ├─ Body present: true
   └─ Body length: 145 chars
```

### 2. Backend Request Receipt

**Location**: `backend/app/main.py` - Authorization Middleware

**What's Logged**:
- Incoming request details (method, path, IP, user-agent)
- Cookie and header analysis
- Public vs protected endpoint routing
- Token extraction and presence validation

**Example Log Output**:
```
🔍 AUTH MIDDLEWARE: Incoming POST request to /bookmarks
   ├─ User-Agent: Mozilla/5.0...
   ├─ Remote IP: 127.0.0.1
   └─ Content-Type: application/json

🔐 AUTH MIDDLEWARE: Protected endpoint - authentication required

🍪 AUTH MIDDLEWARE: Extracting tokens from request
   ├─ Access token present: true (length: 1247)
   └─ Refresh token present: true (length: 64)
```

### 3. Access Token Validation

**Location**: `backend/app/utils/jwt.py` - `decodeJWT` function

**What's Logged**:
- Token cleaning and format validation
- JWT secret configuration status
- Token decoding with algorithm details
- Payload analysis and claim validation
- Expiration and signature verification

**Example Log Output**:
```
🔑 JWT DECODE: Starting JWT token validation
   ├─ Original token length: 1247
   ├─ Cleaned token length: 1247
   ├─ JWT secret configured: true
   ├─ JWT secret length: 64
   ├─ Expected audience: authenticated
   ├─ Expected issuer: https://your-project.supabase.co/auth/v1
   └─ Supabase URL: https://your-project.supabase.co

🔍 JWT DECODE: Attempting to decode token with HS256 algorithm

✅ JWT DECODE: Token decoded successfully
   ├─ Payload keys: ['aud', 'exp', 'iat', 'iss', 'sub', 'email', 'user_metadata']
   ├─ Subject (user_id): 12345678-1234-1234-1234-123456789012
   ├─ Email: user@example.com
   ├─ Audience: authenticated
   ├─ Issuer: https://your-project.supabase.co/auth/v1
   ├─ Issued at: 1703123456
   └─ Expires at: 1703127056
```

### 4. Token Refresh Process

**Location**: `backend/app/utils/jwt.py` - `refresh_access_token` function

**What's Logged**:
- Refresh token validation and preparation
- Supabase API communication details
- Response validation and structure analysis
- New token reception and comparison

**Example Log Output**:
```
🔄 TOKEN REFRESH: Starting token refresh process
   ├─ Refresh token length: 64
   ├─ Refresh token prefix: abcd1234...
   ├─ Refresh endpoint: https://your-project.supabase.co/auth/v1/token?grant_type=refresh_token
   ├─ Supabase URL: https://your-project.supabase.co
   └─ Grant type: refresh_token

📡 TOKEN REFRESH: Sending refresh request to Supabase
   ├─ Timeout: 10.0 seconds
   └─ Request payload keys: ['refresh_token']

📨 TOKEN REFRESH: Response received from Supabase
   ├─ Response status: 200
   ├─ Response headers: ['content-type', 'content-length', ...]
   └─ Response size: 1247 bytes

🎯 TOKEN REFRESH: New tokens received
   ├─ New access token length: 1247
   ├─ New refresh token length: 64
   ├─ Token type: Bearer
   ├─ Expires in: 3600 seconds
   └─ Refresh token changed: false
```

### 5. User Validation and Creation

**Location**: `backend/app/services/user_service.py`

**What's Logged**:
- JWT payload extraction and analysis
- User existence checking in database
- User creation operations
- Database operation results

**Example Log Output**:
```
👤 USER SERVICE: Checking/creating user from JWT payload
   ├─ User ID: 12345678-1234-1234-1234-123456789012
   ├─ Email: user@example.com
   ├─ Role: authenticated
   ├─ Issuer: https://your-project.supabase.co/auth/v1
   ├─ Created at: 2023-12-20T10:30:00Z
   └─ Last sign in: 2023-12-20T10:30:00Z

🔍 USER SERVICE: Checking if user exists in database
   └─ User ID: 12345678-1234-1234-1234-123456789012

✅ USER SERVICE: User already exists, skipping creation
```

### 6. Cookie Management

**Location**: `backend/app/main.py` - Cookie helper functions

**What's Logged**:
- Cookie setting operations with security attributes
- Token cookie updates after refresh
- User information cookie management
- Cookie update comparisons and decisions

**Example Log Output**:
```
🍪 AUTH MIDDLEWARE: Updating authentication cookies with refreshed tokens

🔄 TOKEN COOKIES: Updating authentication cookies after refresh
   ├─ New access token present: true
   ├─ New refresh token present: true
   └─ Refresh token changed: false

🍪 COOKIE: Setting secure cookie: access_token
   ├─ Cookie name: access_token
   ├─ Value length: 1247
   ├─ Expires in: 3600 seconds
   ├─ HttpOnly: true
   ├─ Secure: true
   └─ SameSite: none

✅ COOKIE: Successfully set access_token cookie
```

### 7. Response Processing

**Location**: `backend/app/main.py` - Middleware response handling

**What's Logged**:
- Route handler completion status
- Response preparation and cookie updates
- Final request processing status

**Example Log Output**:
```
➡️  AUTH MIDDLEWARE: Proceeding to route handler

⬅️  AUTH MIDDLEWARE: Route handler completed, processing response
   ├─ Response status: 200
   └─ Response headers: ['content-type', 'content-length', ...]

🍪 AUTH MIDDLEWARE: Updating user information cookies

✅ AUTH MIDDLEWARE: Request processing completed successfully
```

## Error Scenarios

### Token Expiration
```
⏰ JWT DECODE: Token has expired: Signature has expired
   └─ Raising TokenExpiredError for refresh handling

⏰ AUTH MIDDLEWARE: Access token expired, attempting refresh...
   ├─ Starting token refresh process
   ├─ Refresh token available: true
```

### Invalid Tokens
```
❌ JWT DECODE: JWT decoding failed: Invalid signature
   ├─ Error type: JWTError
   └─ This indicates token format or signature issues
```

### Refresh Token Failures
```
❌ TOKEN REFRESH: Supabase refresh failed
   ├─ Status code: 401
   ├─ Error response: {"error":"invalid_grant","error_description":"Invalid refresh token"}...
   └─ Full response size: 78 characters
```

### Session Expiration
```
🚫 AUTH MIDDLEWARE: Session expired - clearing all auth cookies

⚠️  AUTH REQUEST: Session expired, triggering re-authentication...
   ├─ Clearing local storage
   └─ Redirecting to auth page
```

## Using the Logs

### 1. Development Debugging
- Monitor console output for frontend logs
- Check backend logs for server-side authentication flow
- Use log structure to trace specific request flows

### 2. Production Monitoring
- Set up log aggregation for backend logs
- Monitor error patterns and frequencies
- Track authentication success/failure rates

### 3. Performance Analysis
- Use timing information to identify bottlenecks
- Monitor token refresh frequency
- Track database query performance

### 4. Security Auditing
- Monitor failed authentication attempts
- Track token refresh patterns
- Identify potential security issues

## Log Configuration

### Backend (Python)
The logging is configured in `backend/app/main.py`:
```python
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

### Frontend (TypeScript)
Console logging is used throughout the frontend components. In production, you may want to:
- Disable debug logs
- Send logs to monitoring services
- Filter sensitive information

## Troubleshooting Common Issues

### 1. No Logs Appearing
- Check log level configuration
- Verify logger initialization
- Ensure console/log output is not suppressed

### 2. Missing Context
- Look for the request ID or user ID to correlate logs
- Use timestamps to follow the chronological flow
- Check both frontend and backend logs together

### 3. Authentication Failures
- Start by checking token presence and format
- Verify JWT secret configuration
- Check Supabase service status and configuration
- Review cookie settings and browser restrictions

## Best Practices

1. **Log Correlation**: Use user IDs and request identifiers to correlate logs across services
2. **Sensitive Data**: Never log complete tokens or passwords, only metadata
3. **Performance**: Monitor log volume in production to avoid performance impact
4. **Retention**: Configure appropriate log retention policies
5. **Monitoring**: Set up alerts for authentication failure patterns

This comprehensive logging system provides complete visibility into the authentication flow, making debugging, monitoring, and security auditing significantly easier. 