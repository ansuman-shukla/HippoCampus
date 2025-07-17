import { useState, useEffect, useCallback } from 'react';
import { supabase } from '../supabaseClient';
import { getAuthStatus, logout as authUtilsLogout } from '../utils/authUtils';

// Helper function to get clean backend URL
const getBackendUrl = (): string => {
  const baseUrl = import.meta.env.VITE_BACKEND_URL;
  return baseUrl.endsWith('/') ? baseUrl.slice(0, -1) : baseUrl;
};

export interface User {
  id: string;
  email: string;
  full_name?: string;
  picture?: string;
  role?: string;
  created_at?: string;
  last_sign_in_at?: string;
}

export interface AuthState {
  user: User | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  error: string | null;
  tokenRefreshed?: boolean;
  errorType?: string;
}

export const useAuth = () => {
  const [authState, setAuthState] = useState<AuthState>({
    user: null,
    isLoading: true,
    isAuthenticated: false,
    error: null,
    tokenRefreshed: false
  });

  // Check authentication status from backend (single source of truth)
  // Backend middleware handles token validation, refresh, and user management automatically
  const checkAuthStatus = useCallback(async (forceCheck: boolean = false) => {
    // Prevent multiple simultaneous auth checks unless forced
    if (authState.isLoading && !forceCheck) {
      console.log('Auth check already in progress, skipping (use forceCheck=true to override)');
      return false;
    }

    try {
      setAuthState(prev => ({ ...prev, isLoading: true, error: null }));
      
      const authResult = await getAuthStatus();
      
      if (authResult.success && authResult.user) {
        setAuthState({
          user: authResult.user as User,
          isLoading: false,
          isAuthenticated: true,
          error: null,
          tokenRefreshed: false
        });
        return true;
      } else {
        setAuthState({
          user: null,
          isLoading: false,
          isAuthenticated: false,
          error: authResult.error || null,
          tokenRefreshed: false
        });
        return false;
      }
    } catch (error: any) {
      console.error('Auth status check failed:', error);
      setAuthState({
        user: null,
        isLoading: false,
        isAuthenticated: false,
        error: 'Failed to check authentication status',
        errorType: 'network_error',
        tokenRefreshed: false
      });
      return false;
    }
  }, [authState.isLoading]);

  // Sign in with Supabase
  const signIn = useCallback(async (email: string, password: string) => {
    try {
      setAuthState((prev: AuthState) => ({ ...prev, isLoading: true, error: null }));
      
      const { data, error } = await supabase.auth.signInWithPassword({
        email,
        password
      });

      if (error) {
        setAuthState((prev: AuthState) => ({ 
          ...prev, 
          isLoading: false, 
          error: error.message 
        }));
        return { success: false, error: error.message };
      }

      if (data.session?.access_token) {
        // Set tokens in cookies for backend communication
        await setAuthCookies(data.session.access_token, data.session.refresh_token);

        // Verify authentication with backend (backend middleware will set secure httpOnly cookies)
        await checkAuthStatus();
        return { success: true, data: data.session };
      }

      return { success: false, error: 'No session received' };
    } catch (error: any) {
      const errorMessage = error.message || 'Sign in failed';
      setAuthState((prev: AuthState) => ({ 
        ...prev, 
        isLoading: false, 
        error: errorMessage 
      }));
      return { success: false, error: errorMessage };
    }
  }, [checkAuthStatus]);

  // Sign up with Supabase
  const signUp = useCallback(async (email: string, password: string, fullName?: string) => {
    try {
      setAuthState((prev: AuthState) => ({ ...prev, isLoading: true, error: null }));
      
      const { data, error } = await supabase.auth.signUp({
        email,
        password,
        options: {
          data: {
            full_name: fullName
          }
        }
      });

      if (error) {
        setAuthState((prev: AuthState) => ({ 
          ...prev, 
          isLoading: false, 
          error: error.message 
        }));
        return { success: false, error: error.message };
      }

      // For email confirmation flow
      if (data.user && !data.session) {
        setAuthState((prev: AuthState) => ({ ...prev, isLoading: false }));
        return { 
          success: true, 
          message: 'Check your email for confirmation link',
          needsEmailConfirmation: true
        };
      }

      // Auto sign-in after signup
      if (data.session?.access_token) {
        await setAuthCookies(data.session.access_token, data.session.refresh_token);
        await checkAuthStatus();
        return { success: true, data: data.session };
      }

      return { success: false, error: 'No session received' };
    } catch (error: any) {
      const errorMessage = error.message || 'Sign up failed';
      setAuthState((prev: AuthState) => ({ 
        ...prev, 
        isLoading: false, 
        error: errorMessage 
      }));
      return { success: false, error: errorMessage };
    }
  }, [checkAuthStatus]);

  // Sign out using comprehensive logout from authUtils
  const signOut = useCallback(async () => {
    console.log('🚪 USE_AUTH: Starting signOut process');
    setAuthState((prev: AuthState) => ({ ...prev, isLoading: true }));
    
    try {
      // Use the comprehensive logout function from authUtils
      const result = await authUtilsLogout();
      
      // Always update auth state to logged out regardless of result
      setAuthState({
        user: null,
        isLoading: false,
        isAuthenticated: false,
        error: null
      });
      
      console.log('✅ USE_AUTH: SignOut completed successfully');
      return result;
    } catch (error: any) {
      console.error('💥 USE_AUTH: SignOut failed:', error);
      // Still set state to logged out for consistency
      setAuthState({
        user: null,
        isLoading: false,
        isAuthenticated: false,
        error: null
      });
      
      return { 
        success: false, 
        error: error.message || 'Logout failed',
        localStateCleared: true
      };
    }
  }, []);

  // Manually refresh token (backend auto-refreshes via middleware)
  const refreshToken = useCallback(async () => {
    try {
      const response = await fetch(`${getBackendUrl()}/auth/refresh`, {
        method: 'POST',
        credentials: 'include', // Backend reads refresh_token from cookies
        headers: {
          'Content-Type': 'application/json',
        }
      });

      if (response.ok) {
        // Backend automatically sets new cookies in response headers
        // Update auth state
        await checkAuthStatus();
        return { success: true };
      }

      const errorData = await response.json().catch(() => ({}));
      return { 
        success: false, 
        error: errorData.detail || 'Token refresh failed',
        error_type: errorData.error_type 
      };
    } catch (error: any) {
      console.error('Token refresh error:', error);
      return { 
        success: false, 
        error: error.message,
        error_type: 'network_error'
      };
    }
  }, [checkAuthStatus]);

  // Helper function to set cookies across domains (matching backend expectations)
  const setAuthCookies = async (accessToken: string, refreshToken?: string) => {
    if (typeof window !== 'undefined' && window.chrome && window.chrome.cookies) {
      try {
        // Set cookies for backend API domain with exact settings backend expects
        const apiUrl = import.meta.env.VITE_BACKEND_URL;
        const apiDomain = new URL(import.meta.env.VITE_BACKEND_URL).hostname;
        const isSecure = apiUrl.startsWith('https://');

        // Access token cookie (expires in 1 hour, matching backend)
        await window.chrome.cookies.set({
          url: apiUrl,
          name: 'access_token',
          value: accessToken,
          path: '/',
          domain: apiDomain,
          secure: isSecure,
          sameSite: 'no_restriction' as chrome.cookies.SameSiteStatus,
          httpOnly: false, // Chrome extension can't set httpOnly, backend middleware handles security
          expirationDate: Math.floor(Date.now() / 1000) + 3600 // 1 hour
        });

        // Refresh token cookie (expires in 7 days, matching backend)
        if (refreshToken) {
          await window.chrome.cookies.set({
            url: apiUrl,
            name: 'refresh_token',
            value: refreshToken,
            path: '/',
            domain: apiDomain,
            secure: isSecure,
            sameSite: 'no_restriction' as chrome.cookies.SameSiteStatus,
            httpOnly: false, // Chrome extension can't set httpOnly, backend middleware handles security
            expirationDate: Math.floor(Date.now() / 1000) + 604800 // 7 days
          });
        }

        console.log('Extension auth cookies set for backend');

      } catch (error) {
        console.error('Error setting auth cookies:', error);
      }
    }
  };

  // Enhanced helper function to clear cookies across multiple domains
  const clearAuthCookies = async () => {
    if (typeof window !== 'undefined' && window.chrome && window.chrome.cookies) {
      try {
        console.log('🧹 CLEAR_COOKIES: Clearing auth cookies across all domains');
        
        // All domains where cookies might exist
        const domains = [
          import.meta.env.VITE_BACKEND_URL,
          'https://extension-auth.vercel.app',
          'https://hippocampus-1.onrender.com',
          'http://127.0.0.1:8000'
        ];
        
        // All possible auth cookie names
        const authCookieNames = [
          'access_token',    // JWT access token
          'refresh_token',   // JWT refresh token
          'user_id',         // User ID
          'user_name',       // User full name
          'user_picture'     // User picture
        ];

        for (const domain of domains) {
          console.log(`   ├─ Clearing cookies from: ${domain}`);
          for (const name of authCookieNames) {
            try {
              await window.chrome.cookies.remove({
                url: domain,
                name
              });
              console.log(`   │  ✓ Cleared ${name} from ${domain}`);
            } catch (error) {
              console.warn(`   │  ⚠️  Failed to clear ${name} from ${domain}:`, error);
            }
          }
        }

        console.log('✅ CLEAR_COOKIES: All domains processed');
      } catch (error) {
        console.error('❌ CLEAR_COOKIES: Error clearing auth cookies:', error);
      }
    }
  };

  // Check for existing auth on mount and listen for Supabase auth changes
  useEffect(() => {
    const initAuth = async () => {
      // Always check auth status with backend (backend is source of truth)
      // Backend middleware will handle token validation and refresh automatically
      await checkAuthStatus();
    };

    initAuth();

    // Listen for Supabase auth changes
    const { data: { subscription } } = supabase.auth.onAuthStateChange(
      async (event: string, session: any) => {
        console.log('Supabase auth event:', event);
        
        if (event === 'SIGNED_IN' && session?.access_token) {
          await setAuthCookies(session.access_token, session.refresh_token);
          await checkAuthStatus();
        } else if (event === 'SIGNED_OUT') {
          await clearAuthCookies();
          localStorage.removeItem('access_token');
          localStorage.removeItem('refresh_token');
          setAuthState({
            user: null,
            isLoading: false,
            isAuthenticated: false,
            error: null
          });
        }
      }
    );

    return () => {
      subscription.unsubscribe();
    };
  }, [checkAuthStatus]);

  return {
    ...authState,
    signIn,
    signUp,
    signOut,
    refreshToken,
    checkAuthStatus
  };
};
