# Authentication Issue Fix: "Refresh Token Already Used"

## Problem Description

Users were experiencing authentication failures when returning to the application after a long period (e.g., a day), with backend logs showing:

```
Invalid Refresh Token: Already Used
```

## Root Cause Analysis

### 1. Supabase Refresh Token Rotation
- Supabase implements refresh token rotation for security
- When a refresh token is used, it becomes permanently invalid
- A new refresh token is issued with each refresh

### 2. Race Condition in Browser Extension
The browser extension made simultaneous requests when opened:
```javascript
// background.js - BEFORE FIX
Promise.all([
  fetch('/links/get'),  // Request 1
  fetch('/notes/')      // Request 2  
])
```

When both access tokens were expired:
1. **Request 1** → middleware detects expired token → calls `refresh_access_token()`
2. **Request 2** → **simultaneously** calls `refresh_access_token()` with **same refresh token**
3. Only first refresh succeeds, second gets "already used" error

### 3. Missing Concurrency Control
- No mechanism to prevent multiple simultaneous refresh attempts
- No queuing of requests during token refresh
- No proper handling of "already used" errors

## Solution Implemented

### 1. Backend: Added Refresh Token Locking (`main.py`)

```python
# Global refresh token locks to prevent race conditions
refresh_locks = defaultdict(asyncio.Lock)
active_refreshes = {}

async def handle_token_refresh(refresh_token):
    """Handle token refresh with concurrency control"""
    lock = refresh_locks[refresh_token]
    
    async with lock:
        # Check if refresh already in progress
        if refresh_token in active_refreshes:
            return await active_refreshes[refresh_token]
        
        # Perform refresh
        refresh_promise = asyncio.create_task(_do_refresh(refresh_token))
        active_refreshes[refresh_token] = refresh_promise
        
        try:
            return await refresh_promise
        finally:
            # Cleanup
            active_refreshes.pop(refresh_token, None)
            refresh_locks.pop(refresh_token, None)
```

### 2. Backend: Enhanced Error Handling

```python
# Detect "already used" errors and trigger re-authentication
if "already_used" in error_detail.lower():
    return create_error_response(
        "Session expired. Please log in again.",
        status_code=401,
        error_type="session_expired"
    )
```

### 3. Frontend: Sequential Request Pattern (`background.js`)

```javascript
// BEFORE: Simultaneous requests (race condition)
Promise.all([fetch('/links/get'), fetch('/notes/')])

// AFTER: Sequential requests
async function fetchAllData() {
  const linksData = await fetch('/links/get');  // Refresh happens here
  const notesData = await fetch('/notes/');     // Uses refreshed token
}
```

### 4. Frontend: Session Expiration Detection (`authUtils.ts`)

```typescript
if (response.status === 401) {
  const errorData = await response.clone().json();
  if (errorData.error_type === 'session_expired') {
    localStorage.removeItem('user_name');
    window.location.href = '/auth';  // Trigger re-authentication
  }
}
```

## Benefits of the Fix

1. **Eliminates Race Conditions**: Only one refresh attempt per token
2. **Proper Concurrency**: Multiple requests wait for single refresh
3. **Graceful Fallback**: "Already used" errors trigger re-authentication
4. **Better UX**: Users are automatically redirected to login when needed
5. **Resource Efficiency**: Avoids unnecessary duplicate refresh attempts

## Testing

After implementing this fix:

1. ✅ Multiple simultaneous requests no longer cause refresh conflicts
2. ✅ "Already used" errors are properly handled with re-authentication
3. ✅ Users can successfully return after long periods of inactivity
4. ✅ Extension works correctly when opened after token expiration

## Prevention

- **Backend**: Refresh token locking prevents concurrent refresh attempts
- **Frontend**: Sequential API calls reduce race condition likelihood  
- **Error Handling**: Proper fallback to re-authentication flow
- **Monitoring**: Enhanced logging for debugging auth issues 