import { useState, useEffect, useCallback } from 'react';
import { supabase } from '../supabaseClient';
import { getAuthStatus } from '../utils/authUtils';

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
  const checkAuthStatus = useCallback(async () => {
    try {
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
  }, []);

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
        
        // Keep minimal backup in localStorage for extension functionality
        localStorage.setItem('access_token', data.session.access_token);
        if (data.session.refresh_token) {
          localStorage.setItem('refresh_token', data.session.refresh_token);
        }

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
        // Keep minimal backup in localStorage for extension functionality
        localStorage.setItem('access_token', data.session.access_token);
        if (data.session.refresh_token) {
          localStorage.setItem('refresh_token', data.session.refresh_token);
        }
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

  // Sign out
  const signOut = useCallback(async () => {
    try {
      setAuthState((prev: AuthState) => ({ ...prev, isLoading: true }));
      
      // Sign out from Supabase first
      await supabase.auth.signOut();
      
      // Call backend logout endpoint (clears all server-side cookies)
      // Backend clears: access_token, refresh_token, user_id, user_name, user_picture
      await fetch(`https://hippocampus-cyfo.onrender.com/auth/logout`, {
        method: 'POST',
        credentials: 'include',
        headers: {
          'Content-Type': 'application/json',
        }
      });

      // Clear localStorage backup
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
      localStorage.removeItem('quotes');

      // Clear extension cookies (if running in extension context)
      await clearAuthCookies();

      setAuthState({
        user: null,
        isLoading: false,
        isAuthenticated: false,
        error: null
      });

      return { success: true };
    } catch (error: any) {
      console.error('Sign out error:', error);
      // Even if there's an error, clear local state
      setAuthState({
        user: null,
        isLoading: false,
        isAuthenticated: false,
        error: null
      });
      // Clear localStorage anyway
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
      localStorage.removeItem('quotes');
      return { success: false, error: error.message };
    }
  }, []);

  // Manually refresh token (backend auto-refreshes via middleware)
  const refreshToken = useCallback(async () => {
    try {
      const response = await fetch(`https://hippocampus-cyfo.onrender.com/auth/refresh`, {
        method: 'POST',
        credentials: 'include', // Backend reads refresh_token from cookies
        headers: {
          'Content-Type': 'application/json',
        }
      });

      if (response.ok) {
        const data = await response.json();
        // Backend automatically sets new cookies in response headers
        // Update localStorage backup if new tokens provided
        if (data.access_token) {
          localStorage.setItem('access_token', data.access_token);
        }
        if (data.refresh_token) {
          localStorage.setItem('refresh_token', data.refresh_token);
        }
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
        const apiUrl = 'https://hippocampus-cyfo.onrender.com';
        const apiDomain = 'hippocampus-cyfo.onrender.com';

        // Access token cookie (expires in 1 hour, matching backend)
        await window.chrome.cookies.set({
          url: apiUrl,
          name: 'access_token',
          value: accessToken,
          path: '/',
          domain: apiDomain,
          secure: true,
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
            secure: true,
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

  // Helper function to clear cookies (matches backend cookie names exactly)
  const clearAuthCookies = async () => {
    if (typeof window !== 'undefined' && window.chrome && window.chrome.cookies) {
      try {
        const apiUrl = 'https://hippocampus-cyfo.onrender.com';
        
        // Clear all cookies that backend authentication middleware sets
        const authCookieNames = [
          'access_token',    // JWT access token
          'refresh_token',   // JWT refresh token
          'user_id',         // User ID (set by backend after token validation)
          'user_name',       // User full name (set by backend after token validation)
          'user_picture'     // User picture (set by backend after token validation)
        ];

        for (const name of authCookieNames) {
          await window.chrome.cookies.remove({
            url: apiUrl,
            name
          });
        }

        console.log('Extension auth cookies cleared');
      } catch (error) {
        console.error('Error clearing auth cookies:', error);
      }
    }
  };

  // Check for existing auth on mount and listen for Supabase auth changes
  useEffect(() => {
    const initAuth = async () => {
      // First check if we have tokens from external auth flow (like extension auth)
      const accessToken = localStorage.getItem('access_token');
      
      if (accessToken) {
        // Set cookies for backend communication (extension context only)
        await setAuthCookies(accessToken, localStorage.getItem('refresh_token') || undefined);
      }
      
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
          localStorage.setItem('access_token', session.access_token);
          if (session.refresh_token) {
            localStorage.setItem('refresh_token', session.refresh_token);
          }
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
