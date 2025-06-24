# Authentication System Setup Guide

This guide will help you set up the improved authentication system with Supabase integration and proper token refresh handling.

## 🔧 Configuration Setup

### 1. Environment Variables

Add the following variables to your `.env` file:

```env
# Supabase Configuration
SUPABASE_URL=your-supabase-project-url
SUPABASE_ANON_KEY=your-supabase-anon-key
SUPABASE_JWT_SECRET=your-supabase-jwt-secret

# Existing variables...
MONGODB_DB=your-db-name
MONGODB_URI=your-mongodb-uri
PINECONE_API_KEY=your-pinecone-key
PINECONE_INDEX=your-pinecone-index
GEMINI_API_KEY=your-gemini-key
MONGODB_COLLECTION_USER=users
MONGODB_COLLECTION_NOTES=notes
MONGODB_COLLECTION_MEMORIES=memories
```

### 2. Finding Your Supabase JWT Secret

1. Go to your Supabase dashboard
2. Navigate to **Settings** → **API**
3. Look for **JWT Settings** section
4. Copy the **JWT Secret** (not the anon key!)

## 🚀 Key Improvements Made

### 1. **Fixed JWT Token Validation**
- Now uses the correct Supabase JWT secret instead of anon key
- Proper audience and issuer validation
- Better error handling for expired tokens

### 2. **Enhanced Token Refresh Logic**
- Automatic token refresh in middleware when access token expires
- Proper error handling with fallback to login
- Manual refresh endpoint at `/auth/refresh`

### 3. **Improved Middleware**
- Skips authentication for health checks and auth endpoints
- Better error messages and logging
- Graceful handling of token refresh failures

### 4. **New Authentication Endpoints**
- `POST /auth/refresh` - Manually refresh tokens
- `POST /auth/logout` - Clear authentication cookies
- `GET /auth/status` - Check authentication status
- `GET /auth/verify` - Verify and get user info from token

### 5. **Frontend Token Management**
- Enhanced token manager with better error handling
- Multiple domain cookie setting for better compatibility
- Manual refresh functionality

## 🧪 Testing the System

Run the test script to verify everything is working:

```bash
cd backend
python test_auth.py
```

This will test:
- Configuration setup
- Health checks
- Auth endpoints
- Token validation
- Protected endpoint access

## 🔄 Authentication Flow

### 1. **Initial Authentication**
1. User authenticates through Supabase (frontend)
2. Frontend receives access_token and refresh_token
3. Tokens are stored in localStorage and cookies
4. Cookies are sent with API requests

### 2. **Token Refresh Process**
1. Backend middleware checks access token on each request
2. If token is expired, middleware automatically tries to refresh
3. New tokens are set as cookies in the response
4. Request continues with fresh token
5. If refresh fails, user gets 401 and must login again

### 3. **Manual Token Refresh**
Frontend can manually refresh tokens by calling:
```javascript
const success = await tokenManager.refreshToken();
```

## 🔒 Security Features

- **HttpOnly Cookies**: Tokens stored in secure, httpOnly cookies
- **Secure & SameSite**: Proper cookie security settings
- **Token Expiration**: Access tokens expire in 1 hour, refresh tokens in 7 days
- **Automatic Cleanup**: Failed refresh attempts clear invalid tokens
- **Comprehensive Logging**: All auth events are logged for debugging

## 🚨 Troubleshooting

### Common Issues:

1. **"Invalid token" errors**
   - Check if `SUPABASE_JWT_SECRET` is correctly set
   - Verify the JWT secret matches your Supabase project

2. **Token refresh failures**
   - Ensure refresh token is valid and not expired
   - Check Supabase project settings

3. **CORS issues**
   - Verify CORS settings in main.py
   - Check if your frontend domain is allowed

4. **Cookie issues**
   - Ensure cookies are set with proper domain
   - Check if secure/sameSite settings match your environment

### Debug Steps:

1. **Check logs** for detailed error messages
2. **Test health endpoint**: `GET /health`
3. **Check auth status**: `GET /auth/status`
4. **Verify token**: `GET /auth/verify`
5. **Run test script**: `python test_auth.py`

## 📝 API Endpoints

### Authentication Endpoints:
- `POST /auth/refresh` - Refresh access token
- `POST /auth/logout` - Logout and clear cookies
- `GET /auth/status` - Get authentication status
- `GET /auth/verify` - Verify token and get user info

### Protected Endpoints:
All your existing endpoints (save, search, etc.) now have improved auth handling with automatic token refresh.

## 🎯 Next Steps

1. **Test the system** with the provided test script
2. **Update your frontend** to handle the new token refresh logic
3. **Monitor logs** for any authentication issues
4. **Set up proper error handling** in your frontend for auth failures

The system is now much more robust and should handle token expiration gracefully without throwing errors to users!
