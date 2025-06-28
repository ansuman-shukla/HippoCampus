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
  return 'https://hippocampus-cyfo.onrender.com';
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
  
  const defaultOptions: RequestInit = {
    credentials: 'include', // Always use cookies - backend handles auth
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
    ...options,
  };

  try {
    const response = await fetch(url, defaultOptions);
    
    // Backend automatically handles token refresh via middleware
    // No need for frontend token refresh logic
    
    return response;
  } catch (error) {
    console.error('API request failed:', error);
    throw error;
  }
};

/**
 * Login with Supabase - Backend will set httpOnly cookies automatically
 */
export const login = async (email: string, password: string): Promise<AuthResponse> => {
  try {
    // First authenticate with Supabase
    const { data, error } = await supabase.auth.signInWithPassword({
      email,
      password,
    });

    if (error) {
      return {
        success: false,
        error: error.message,
      };
    }

    if (!data.session?.access_token) {
      return {
        success: false,
        error: 'No session received from Supabase',
      };
    }

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

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      return {
        success: false,
        error: errorData.detail || 'Backend authentication failed',
      };
    }

    const result = await response.json();
    
    return {
      success: true,
      user: result.user,
      message: 'Login successful',
    };
  } catch (error) {
    console.error('Login error:', error);
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
 * Logout - Clear cookies via backend
 */
export const logout = async (): Promise<AuthResponse> => {
  try {
    // Call backend logout endpoint to clear httpOnly cookies
    const response = await fetch(`${getApiBaseUrl()}/auth/logout`, {
      method: 'POST',
      credentials: 'include',
    });

    // Also sign out from Supabase
    await supabase.auth.signOut();

    if (!response.ok) {
      console.warn('Backend logout failed, but Supabase logout succeeded');
    }

    return {
      success: true,
      message: 'Logged out successfully',
    };
  } catch (error) {
    console.error('Logout error:', error);
    // Even if backend fails, ensure Supabase logout
    await supabase.auth.signOut();
    return {
      success: true,
      message: 'Logged out (with some issues)',
    };
  }
};

/**
 * Get current authentication status from backend
 */
export const getAuthStatus = async (): Promise<AuthResponse> => {
  try {
    const response = await fetch(`${getApiBaseUrl()}/auth/status`, {
      method: 'GET',
      credentials: 'include', // Always use cookies - backend handles auth
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      if (response.status === 401) {
        return {
          success: false,
          error: 'Not authenticated',
        };
      }

      const errorData = await response.json().catch(() => ({}));
      return {
        success: false,
        error: errorData.detail || 'Failed to get auth status',
      };
    }

    const data = await response.json();
    
    // Check if user is authenticated based on backend response
    if (data.is_authenticated && data.user_id) {
      return {
        success: true,
        user: {
          id: data.user_id,
          email: data.user_email || '',
          // Add other user fields as needed
        },
      };
    }
    
    return {
      success: false,
      error: 'Not authenticated',
    };
  } catch (error) {
    console.error('Auth status check failed:', error);
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
 * Get user info from cookies (for display purposes)
 * Backend sets these as regular cookies for frontend access
 */
export const getUserFromCookies = (): Partial<AuthUser> | null => {
  try {
    if (isExtension()) {
      return null; // Extensions can't easily access cookies
    }

    const getCookie = (name: string): string | null => {
      const value = `; ${document.cookie}`;
      const parts = value.split(`; ${name}=`);
      if (parts.length === 2) {
        const cookieValue = parts.pop()?.split(';').shift();
        return cookieValue ? decodeURIComponent(cookieValue) : null;
      }
      return null;
    };

    const userId = getCookie('user_id');
    const userName = getCookie('user_name');
    const userPicture = getCookie('user_picture');

    if (!userId) return null;

    return {
      id: userId,
      full_name: userName || undefined,
      picture: userPicture || undefined,
    };
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
