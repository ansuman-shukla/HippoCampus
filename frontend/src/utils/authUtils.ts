import { supabase } from '../supabaseClient';

// Types based on your backend authentication flow
export interface AuthUser {
  id: string;
  email: string;
  role?: string;
  full_name?: string;
  picture?: string;
  created_at?: string;
  last_sign_in_at?: string;
}

export interface AuthResponse {
  success: boolean;
  message?: string;
  user?: AuthUser;
  error?: string;
}

// Check if we're in a browser extension environment
const isExtension = (): boolean => {
  try {
    return !!(typeof (window as any).chrome !== 'undefined' && 
             (window as any).chrome.runtime && 
             (window as any).chrome.runtime.id);
  } catch {
    return false;
  }
};

// Get the appropriate API base URL (always the backend)
const getApiBaseUrl = (): string => {
  const baseUrl = import.meta.env.VITE_BACKEND_URL;
  return baseUrl.endsWith('/') ? baseUrl.slice(0, -1) : baseUrl;
};

/**
 * Clear all authentication data from local storage and cookies (comprehensive cleanup)
 */
const clearAllAuthData = async (): Promise<void> => {
  console.log('🧹 AUTH CLEANUP: Starting comprehensive auth data cleanup');
  
  // Clear localStorage items
  const authLocalStorageKeys = [
    'access_token',
    'refresh_token', 
    'user_id',
    'user_name',
    'user_picture',
    'session',
    'quotes'
  ];
  
  console.log('   ├─ Clearing localStorage items...');
  authLocalStorageKeys.forEach(key => {
    try {
      localStorage.removeItem(key);
      console.log(`   │  ✓ Cleared: ${key}`);
    } catch (error) {
      console.warn(`   │  ⚠️  Failed to clear ${key}:`, error);
    }
  });
  
  // Clear extension cookies if in extension environment
  if (isExtension() && typeof window !== 'undefined' && window.chrome && window.chrome.cookies) {
    console.log('   ├─ Clearing extension cookies...');
    try {
      const domains = [
        import.meta.env.VITE_BACKEND_URL,
        'https://extension-auth.vercel.app',
        'https://hippocampus-1.onrender.com',
        'http://127.0.0.1:8000'
      ];
      
      const cookieNames = ['access_token', 'refresh_token', 'user_id', 'user_name', 'user_picture'];
      
      for (const domain of domains) {
        for (const cookieName of cookieNames) {
          try {
            await window.chrome.cookies.remove({
              url: domain,
              name: cookieName
            });
            console.log(`   │  ✓ Cleared ${cookieName} from ${domain}`);
          } catch (error) {
            console.warn(`   │  ⚠️  Failed to clear ${cookieName} from ${domain}:`, error);
          }
        }
      }
    } catch (error) {
      console.warn('   │  ⚠️  Extension cookie clearing failed:', error);
    }
  }
  
  // Sign out from Supabase as well
  try {
    console.log('   ├─ Signing out from Supabase...');
    await supabase.auth.signOut();
    console.log('   │  ✓ Supabase signout completed');
  } catch (error) {
    console.warn('   │  ⚠️  Supabase signout failed:', error);
  }
  
  console.log('✅ AUTH CLEANUP: Comprehensive cleanup completed');
};

/**
 * Make authenticated API requests - cookies are handled automatically by the browser
 */
export const makeAuthenticatedRequest = async (
  endpoint: string,
  options: RequestInit = {}
): Promise<Response> => {
  const baseUrl = getApiBaseUrl();
  const url = `${baseUrl}${endpoint}`;
  
  console.log(`🔐 AUTH REQUEST: Starting authenticated request`);
  console.log(`   ├─ Endpoint: ${endpoint}`);
  console.log(`   ├─ Full URL: ${url}`);
  console.log(`   ├─ Method: ${options.method || 'GET'}`);
  console.log(`   └─ Extension env: ${isExtension()}`);
  
  const defaultOptions: RequestInit = {
    credentials: 'include', // Always use cookies - backend handles auth
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
    ...options,
  };

  console.log(`🔧 AUTH REQUEST: Request configuration`);
  console.log(`   ├─ Credentials: ${defaultOptions.credentials}`);
  console.log(`   ├─ Headers: ${JSON.stringify(defaultOptions.headers)}`);
  console.log(`   └─ Body present: ${!!defaultOptions.body}`);

  try {
    console.log(`📡 AUTH REQUEST: Sending authenticated request`);
    const startTime = performance.now();
    
    const response = await fetch(url, defaultOptions);
    
    const endTime = performance.now();
    const duration = Math.round(endTime - startTime);
    
    console.log(`📨 AUTH REQUEST: Response received`);
    console.log(`   ├─ Status: ${response.status} ${response.statusText}`);
    console.log(`   ├─ Response time: ${duration}ms`);
    console.log(`   └─ Content-Type: ${response.headers.get('content-type') || 'Unknown'}`);
    
    // Check for session expiration errors
    if (response.status === 401) {
      console.warn(`🚫 AUTH REQUEST: Unauthorized response (401)`);
      try {
        const errorData = await response.clone().json();
        console.warn(`   ├─ Error type: ${errorData.error_type || 'Unknown'}`);
        console.warn(`   └─ Error detail: ${errorData.detail || 'Unknown'}`);
        
        // Enhanced session expiration detection
        const isSessionExpired = (
          errorData.error_type === 'session_expired' ||
          errorData.error_type === 'auth_error' ||
          (errorData.detail && (
            errorData.detail.toLowerCase().includes('session expired') ||
            errorData.detail.toLowerCase().includes('token expired') ||
            errorData.detail.toLowerCase().includes('invalid refresh token') ||
            errorData.detail.toLowerCase().includes('already used') ||
            errorData.detail.toLowerCase().includes('please log in again')
          ))
        );
        
        if (isSessionExpired) {
          console.log('⚠️  AUTH REQUEST: Session expired, triggering complete cleanup...');
          await clearAllAuthData();
          console.log(`   └─ Redirecting to auth page`);
          // Trigger re-authentication by redirecting to auth
          window.location.href = '/auth';
          throw new Error('Session expired. Please log in again.');
        }
      } catch (jsonError) {
        // If we can't parse the error, but it's 401, likely auth issue
        console.log('⚠️  AUTH REQUEST: Authentication failed, treating as session expired');
        console.log(`   └─ JSON parse error: ${jsonError}`);
        // Clear auth data anyway for 401 errors
        await clearAllAuthData();
        window.location.href = '/auth';
        throw new Error('Authentication failed. Please log in again.');
      }
    }
    
    // Backend automatically handles token refresh via middleware
    // No need for frontend token refresh logic
    console.log(`✅ AUTH REQUEST: Request completed successfully`);
    
    return response;
  } catch (error: any) {
    console.error('💥 AUTH REQUEST: Request failed');
    console.error(`   ├─ Error type: ${error.constructor.name}`);
    console.error(`   ├─ Error message: ${error.message}`);
    console.error(`   └─ Full error:`, error);
    throw error;
  }
};

/**
 * Login with Supabase - Backend will set httpOnly cookies automatically
 */
export const login = async (email: string, password: string): Promise<AuthResponse> => {
  console.log(`🔐 LOGIN: Starting login process`);
  console.log(`   ├─ Email: ${email}`);
  console.log(`   ├─ Password length: ${password.length} characters`);
  console.log(`   └─ Environment: ${isExtension() ? 'Extension' : 'Web'}`);
  
  try {
    console.log(`📡 LOGIN: Authenticating with Supabase`);
    // First authenticate with Supabase
    const { data, error } = await supabase.auth.signInWithPassword({
      email,
      password,
    });

    if (error) {
      console.error(`❌ LOGIN: Supabase authentication failed`);
      console.error(`   ├─ Error message: ${error.message}`);
      console.error(`   └─ Error details:`, error);
      return {
        success: false,
        error: error.message,
      };
    }

    console.log(`✅ LOGIN: Supabase authentication successful`);
    console.log(`   ├─ Session received: ${!!data.session}`);
    console.log(`   ├─ Access token present: ${!!data.session?.access_token}`);
    console.log(`   ├─ Refresh token present: ${!!data.session?.refresh_token}`);
    console.log(`   ├─ User ID: ${data.user?.id || 'Unknown'}`);
    console.log(`   ├─ User email: ${data.user?.email || 'Unknown'}`);
    console.log(`   └─ Token expires: ${data.session?.expires_at || 'Unknown'}`);

    if (!data.session?.access_token) {
      console.error(`❌ LOGIN: No access token in Supabase response`);
      return {
        success: false,
        error: 'No session received from Supabase',
      };
    }

    console.log(`🔄 LOGIN: Sending tokens to backend for cookie setup`);
    console.log(`   ├─ Backend URL: ${getApiBaseUrl()}`);
    console.log(`   ├─ Access token length: ${data.session.access_token.length}`);
    console.log(`   └─ Refresh token length: ${data.session.refresh_token?.length || 0}`);

    // Send tokens to backend for cookie setup
    const response = await fetch(`${getApiBaseUrl()}/auth/login`, {
      method: 'POST',
      credentials: 'include',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        access_token: data.session.access_token,
        refresh_token: data.session.refresh_token,
      }),
    });

    console.log(`📨 LOGIN: Backend login response received`);
    console.log(`   ├─ Status: ${response.status} ${response.statusText}`);
    console.log(`   ├─ Headers: ${JSON.stringify(Array.from(response.headers.entries()))}`);
    console.log(`   └─ Response OK: ${response.ok}`);

    if (!response.ok) {
      console.error(`❌ LOGIN: Backend authentication failed`);
      console.error(`   └─ Status: ${response.status}`);
      
      const errorData = await response.json().catch(() => ({}));
      console.error(`   └─ Error data:`, errorData);
      
      return {
        success: false,
        error: errorData.detail || 'Backend authentication failed',
      };
    }

    const result = await response.json();
    console.log(`✅ LOGIN: Backend authentication successful`);
    console.log(`   ├─ Response keys: ${Object.keys(result)}`);
    console.log(`   └─ Message: ${result.message || 'No message'}`);
    
    // Store user info in localStorage as backup for extensions
    if (result.user) {
      console.log(`💾 LOGIN: Storing user info in localStorage`);
      try {
        localStorage.setItem('user_id', result.user.id || '');
        if (result.user.full_name) {
          localStorage.setItem('user_name', result.user.full_name);
        }
        if (result.user.picture) {
          localStorage.setItem('user_picture', result.user.picture);
        }
        console.log(`   ├─ Stored user_id: ${result.user.id || 'Empty'}`);
        console.log(`   ├─ Stored user_name: ${result.user.full_name || 'Empty'}`);
        console.log(`   └─ Stored user_picture: ${!!result.user.picture}`);
      } catch (error) {
        console.warn('⚠️  LOGIN: Failed to store user info in localStorage:', error);
      }
    } else {
      console.log(`ℹ️  LOGIN: No user info in backend response to store`);
    }
    
    console.log(`🎉 LOGIN: Login process completed successfully`);
    return {
      success: true,
      user: result.user,
      message: 'Login successful',
    };
  } catch (error: any) {
    console.error('💥 LOGIN: Unexpected error during login:', error);
    console.error(`   ├─ Error type: ${error.constructor.name}`);
    console.error(`   └─ Error message: ${error.message}`);
    return {
      success: false,
      error: 'An unexpected error occurred during login',
    };
  }
};

/**
 * Signup with Supabase
 */
export const signup = async (
  email: string, 
  password: string, 
  userData?: { full_name?: string }
): Promise<AuthResponse> => {
  try {
    const { data, error } = await supabase.auth.signUp({
      email,
      password,
      options: {
        data: userData || {},
      },
    });

    if (error) {
      return {
        success: false,
        error: error.message,
      };
    }

    return {
      success: true,
      message: 'Signup successful. Please check your email for verification.',
      user: data.user ? {
        id: data.user.id,
        email: data.user.email || '',
        full_name: data.user.user_metadata?.full_name,
      } : undefined,
    };
  } catch (error) {
    console.error('Signup error:', error);
    return {
      success: false,
      error: 'An unexpected error occurred during signup',
    };
  }
};

/**
 * Logout - Clear cookies via backend and localStorage using comprehensive cleanup
 */
export const logout = async (): Promise<AuthResponse> => {
  console.log('🚪 LOGOUT: Starting logout process');
  
  try {
    // Call backend logout endpoint to clear httpOnly cookies
    console.log('   ├─ Calling backend logout endpoint...');
    const response = await fetch(`${getApiBaseUrl()}/auth/logout`, {
      method: 'POST',
      credentials: 'include',
    });

    console.log(`   ├─ Backend logout response: ${response.status}`);

    // Always perform comprehensive cleanup regardless of backend response
    console.log('   ├─ Performing comprehensive auth cleanup...');
    await clearAllAuthData();

    if (!response.ok) {
      console.warn('   ⚠️  Backend logout failed, but local cleanup completed');
      return {
        success: true,
        message: 'Logged out locally (backend logout failed)',
      };
    }

    console.log('✅ LOGOUT: Complete logout successful');
    return {
      success: true,
      message: 'Logged out successfully',
    };
  } catch (error) {
    console.error('💥 LOGOUT: Error during logout:', error);
    // Even if everything fails, ensure local cleanup
    console.log('   ├─ Performing emergency cleanup...');
    await clearAllAuthData();
    return {
      success: true,
      message: 'Logged out (with some issues, but local cleanup completed)',
    };
  }
};

/**
 * Get current authentication status from backend
 */
export const getAuthStatus = async (): Promise<AuthResponse> => {
  console.log('🔍 STEP 100: Starting backend authentication status check');
  console.log('   ├─ Function: authUtils.getAuthStatus()');
  console.log('   ├─ Target URL:', `${getApiBaseUrl()}/auth/status`);
  console.log('   ├─ Method: GET');
  console.log('   ├─ Credentials: include (for cookies)');
  console.log('   └─ Purpose: Validate current authentication with backend');

  try {
    console.log('⏱️  STEP 101: Setting up request with timeout protection');
    console.log('   ├─ Timeout duration: 10 seconds');
    console.log('   └─ Using Promise.race for timeout handling');
    
    // Create a timeout promise
    const timeoutPromise = new Promise<never>((_, reject) => {
      setTimeout(() => reject(new Error('Auth status check timeout')), 10000); // 10 second timeout
    });

    console.log('📡 STEP 102: Sending auth status request to backend');
    const fetchPromise = fetch(`${getApiBaseUrl()}/auth/status`, {
      method: 'GET',
      credentials: 'include', // Always use cookies - backend handles auth
      headers: {
        'Content-Type': 'application/json',
      },
    });

    const response = await Promise.race([fetchPromise, timeoutPromise]) as Response;

    console.log('� STEP 103: Processing backend auth status response');
    console.log('   ├─ Response status:', response.status);
    console.log('   ├─ Response OK:', response.ok);
    console.log('   ├─ Status text:', response.statusText);
    console.log('   └─ Headers received:', !!response.headers);

    if (!response.ok) {
      if (response.status === 401) {
        console.log('🚫 STEP 104A: Authentication failed - 401 Unauthorized');
        console.log('   ├─ User is not authenticated');
        console.log('   ├─ Tokens may be missing, expired, or invalid');
        console.log('   └─ Returning authentication failure');
        
        return {
          success: false,
          error: 'Not authenticated',
        };
      }

      console.error('❌ STEP 104B: Backend error during auth status check');
      const errorData = await response.json().catch(() => ({}));
      console.error('   ├─ Status code:', response.status);
      console.error('   ├─ Error data:', errorData);
      console.error('   └─ Error detail:', errorData.detail || 'Unknown error');
      
      return {
        success: false,
        error: errorData.detail || 'Failed to get auth status',
      };
    }

    console.log('✅ STEP 104C: Successful response - parsing auth data');
    const data = await response.json();
    console.log('   ├─ Response data keys:', Object.keys(data));
    console.log('   ├─ Is authenticated:', data.is_authenticated);
    console.log('   ├─ User ID present:', !!data.user_id);
    console.log('   ├─ User email present:', !!data.user_email);
    console.log('   └─ Token valid:', data.token_valid);
    
    // Check if user is authenticated based on backend response
    if (data.is_authenticated && data.user_id) {
      console.log('🎉 STEP 105A: User is authenticated - constructing user object');
      const user = {
        id: data.user_id,
        email: data.user_email || '',
        full_name: data.user_name || data.full_name,
        picture: data.user_picture || data.picture,
      };

      console.log('   ├─ User ID:', user.id);
      console.log('   ├─ User email:', user.email);
      console.log('   ├─ User name:', user.full_name || 'Not provided');
      console.log('   └─ User picture:', !!user.picture);

      console.log('💾 STEP 106A: Storing user info in localStorage for quick access');
      // Store user info in localStorage for quick access
      try {
        localStorage.setItem('user_id', user.id);
        if (user.full_name) localStorage.setItem('user_name', user.full_name);
        if (user.picture) localStorage.setItem('user_picture', user.picture);
        console.log('   ├─ Stored user_id:', user.id);
        console.log('   ├─ Stored user_name:', user.full_name || 'Not provided');
        console.log('   └─ Stored user_picture:', !!user.picture);
      } catch (error) {
        console.warn('⚠️  STEP 107A: Failed to store user info in localStorage:', error);
      }

      console.log('✅ STEP 108A: Authentication successful - returning user data');
      return {
        success: true,
        user,
      };
    }
    
    console.log('🚫 STEP 105B: User is not authenticated according to backend');
    console.log('   ├─ is_authenticated:', data.is_authenticated || false);
    console.log('   ├─ user_id present:', !!data.user_id);
    console.log('   └─ Returning authentication failure');
    
    return {
      success: false,
      error: 'Not authenticated',
    };
  } catch (error) {
    console.error('💥 STEP 109: Authentication status check failed with exception');
    console.error('   ├─ Error type:', (error as Error).constructor.name);
    console.error('   ├─ Error message:', (error as Error).message);
    console.error('   └─ This indicates network or service issues');
    
    return {
      success: false,
      error: 'Unable to check authentication status',
    };
  }
};

/**
 * Verify current token (rarely needed as backend middleware handles this)
 */
export const verifyToken = async (): Promise<AuthResponse> => {
  try {
    const response = await fetch(`${getApiBaseUrl()}/auth/verify`, {
      method: 'GET',
      credentials: 'include',
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      return {
        success: false,
        error: errorData.detail || 'Token verification failed',
      };
    }

    const data = await response.json();
    
    return {
      success: true,
      user: data.user,
    };
  } catch (error) {
    console.error('Token verification failed:', error);
    return {
      success: false,
      error: 'Token verification failed',
    };
  }
};

/**
 * Manually refresh token (usually not needed as backend handles this automatically)
 */
export const refreshToken = async (): Promise<AuthResponse> => {
  try {
    const response = await fetch(`${getApiBaseUrl()}/auth/refresh`, {
      method: 'POST',
      credentials: 'include',
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      return {
        success: false,
        error: errorData.detail || 'Token refresh failed',
      };
    }

    const data = await response.json();
    
    return {
      success: true,
      user: data.user,
      message: 'Token refreshed successfully',
    };
  } catch (error) {
    console.error('Token refresh failed:', error);
    return {
      success: false,
      error: 'Token refresh failed',
    };
  }
};

/**
 * Check if user is authenticated (simple cookie check)
 * Note: This is a basic check. The backend middleware does the real authentication.
 */
export const isAuthenticated = (): boolean => {
  try {
    // In browser extension, we might not have access to httpOnly cookies
    if (isExtension()) {
      // For extension, we'll need to check via API call
      return false; // Default to false, components should call getAuthStatus()
    }
    
    // For web app, check if cookies exist (though they're httpOnly)
    // This is just a basic check - real auth is handled by backend
    return document.cookie.includes('access_token');
  } catch {
    return false;
  }
};

/**
 * Get user info from cookies and localStorage (for display purposes)
 * Backend sets these as regular cookies for frontend access, localStorage as fallback
 */
export const getUserFromCookies = (): Partial<AuthUser> | null => {
  try {
    const getCookie = (name: string): string | null => {
      const value = `; ${document.cookie}`;
      const parts = value.split(`; ${name}=`);
      if (parts.length === 2) {
        const cookieValue = parts.pop()?.split(';').shift();
        return cookieValue ? decodeURIComponent(cookieValue) : null;
      }
      return null;
    };

    const getFromStorage = (key: string): string | null => {
      try {
        return localStorage.getItem(key);
      } catch {
        return null;
      }
    };

    // Try cookies first, then localStorage as fallback
    const userId = getCookie('user_id') || getFromStorage('user_id');
    const userEmail = getCookie('user_email');
    const userName = getCookie('user_name') || getCookie('username') || getCookie('full_name') || getFromStorage('user_name');
    const userPicture = getCookie('user_picture') || getCookie('picture') || getFromStorage('user_picture');

    if (!userId) return null;

    return {
      id: userId,
      email: userEmail || undefined,
      full_name: userName || undefined,
      picture: userPicture || undefined,
    };
  } catch {
    return null;
  }
};

/**
 * Get username specifically (helper function for quick access)
 */
export const getUsername = (): string | null => {
  try {
    // Check localStorage first (works in all environments)
    const fromStorage = localStorage.getItem('user_name');
    if (fromStorage) return fromStorage;

    // Check cookies as fallback (doesn't work in extensions)
    if (!isExtension()) {
      const getCookie = (name: string): string | null => {
        const value = `; ${document.cookie}`;
        const parts = value.split(`; ${name}=`);
        if (parts.length === 2) {
          const cookieValue = parts.pop()?.split(';').shift();
          return cookieValue ? decodeURIComponent(cookieValue) : null;
        }
        return null;
      };

      return getCookie('user_name') || getCookie('username') || getCookie('full_name');
    }

    return null;
  } catch {
    return null;
  }
};

// Export utility function for API calls
export const api = {
  get: (endpoint: string) => makeAuthenticatedRequest(endpoint, { method: 'GET' }),
  post: (endpoint: string, data?: any) => 
    makeAuthenticatedRequest(endpoint, {
      method: 'POST',
      body: data ? JSON.stringify(data) : undefined,
    }),
  put: (endpoint: string, data?: any) => 
    makeAuthenticatedRequest(endpoint, {
      method: 'PUT',
      body: data ? JSON.stringify(data) : undefined,
    }),
  delete: (endpoint: string) => makeAuthenticatedRequest(endpoint, { method: 'DELETE' }),
};
