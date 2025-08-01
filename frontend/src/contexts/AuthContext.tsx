import React, { createContext, useContext, useState, useEffect, useCallback, ReactNode } from 'react';
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

interface AuthContextType extends AuthState {
  signIn: (email: string, password: string) => Promise<any>;
  signUp: (email: string, password: string, fullName?: string) => Promise<any>;
  signOut: () => Promise<any>;
  refreshToken: () => Promise<any>;
  checkAuthStatus: () => Promise<boolean>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

// Global auth check state to prevent multiple concurrent calls
let globalAuthCheckInProgress = false;
let globalAuthCheckPromise: Promise<boolean> | null = null;
let silentAuthCheck: Promise<boolean> | null = null;

export const AuthProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [authState, setAuthState] = useState<AuthState>({
    user: null,
    isLoading: false,  // Start with loading false - auth check happens eagerly
    isAuthenticated: true,  // Start as authenticated to prevent intro page flash, will correct if needed
    error: null,
    tokenRefreshed: false
  });

  console.log('🌐 AUTH_CONTEXT: Provider render with state:', {
    isAuthenticated: authState.isAuthenticated,
    isLoading: authState.isLoading,
    hasUser: !!authState.user,
    error: authState.error,
    timestamp: new Date().toISOString()
  });

  // Silent background auth check that doesn't show loading states
  const silentBackgroundAuthCheck = useCallback(async () => {
    if (silentAuthCheck) {
      return await silentAuthCheck;
    }

    silentAuthCheck = (async () => {
      try {
        console.log('🔍 AUTH_CONTEXT: Starting silent background auth check');
        const authResult = await getAuthStatus();
        
        if (authResult.success && authResult.user) {
          console.log('✅ AUTH_CONTEXT: Silent auth check successful');
          console.log('   ├─ User:', authResult.user);
          console.log('   └─ Updating global authentication state...');
          
          const newState = {
            user: authResult.user as User,
            isAuthenticated: true,
            error: null,
            isLoading: false,
            tokenRefreshed: false
          };
          
          setAuthState(newState);
          console.log('   ├─ Global auth state updated');
          console.log('   └─ New isAuthenticated value:', newState.isAuthenticated);
          
          return true;
        } else {
          console.log('❌ AUTH_CONTEXT: Silent auth check failed:', authResult.error);
          const newState = {
            user: null,
            isAuthenticated: false,
            error: authResult.error || null,
            isLoading: false,
            tokenRefreshed: false
          };
          setAuthState(newState);
          return false;
        }
      } catch (error: any) {
        console.error('💥 AUTH_CONTEXT: Silent auth check failed:', error);
        const newState = {
          user: null,
          isAuthenticated: false,
          error: 'Authentication failed',
          isLoading: false,
          tokenRefreshed: false
        };
        setAuthState(newState);
        return false;
      } finally {
        silentAuthCheck = null;
      }
    })();

    return await silentAuthCheck;
  }, []);

  // Check authentication status from backend
  const checkAuthStatus = useCallback(async () => {
    if (globalAuthCheckInProgress && globalAuthCheckPromise) {
      console.log('🔄 AUTH_CONTEXT: Global auth check already in progress, waiting for result');
      return await globalAuthCheckPromise;
    }

    globalAuthCheckPromise = (async () => {
      try {
        globalAuthCheckInProgress = true;
        console.log('🔍 AUTH_CONTEXT: Starting auth status check');
        setAuthState(prev => ({ ...prev, isLoading: true, error: null }));
      
        const authResult = await getAuthStatus();
      
        if (authResult.success && authResult.user) {
          console.log('✅ AUTH_CONTEXT: Auth status check successful');
          setAuthState({
            user: authResult.user as User,
            isLoading: false,
            isAuthenticated: true,
            error: null,
            tokenRefreshed: false
          });
          return true;
        } else {
          console.log('❌ AUTH_CONTEXT: Auth status check failed:', authResult.error);
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
        console.error('💥 AUTH_CONTEXT: Auth status check failed:', error);
        setAuthState({
          user: null,
          isLoading: false,
          isAuthenticated: false,
          error: 'Failed to check authentication status',
          errorType: 'network_error',
          tokenRefreshed: false
        });
        return false;
      } finally {
        globalAuthCheckInProgress = false;
        globalAuthCheckPromise = null;
      }
    })();

    return await globalAuthCheckPromise;
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
        await setAuthCookies(data.session.access_token, data.session.refresh_token);
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

      if (data.user && !data.session) {
        setAuthState((prev: AuthState) => ({ ...prev, isLoading: false }));
        return { 
          success: true, 
          message: 'Check your email for confirmation link',
          needsEmailConfirmation: true
        };
      }

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
    console.log('🚪 AUTH_CONTEXT: Starting signOut process');
    setAuthState((prev: AuthState) => ({ ...prev, isLoading: true }));
    
    try {
      const result = await authUtilsLogout();
      
      setAuthState({
        user: null,
        isLoading: false,
        isAuthenticated: false,
        error: null
      });
      
      console.log('✅ AUTH_CONTEXT: SignOut completed successfully');
      return result;
    } catch (error: any) {
      console.error('💥 AUTH_CONTEXT: SignOut failed:', error);
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

  // Manually refresh token
  const refreshToken = useCallback(async () => {
    try {
      const response = await fetch(`${getBackendUrl()}/auth/refresh`, {
        method: 'POST',
        credentials: 'include',
        headers: {
          'Content-Type': 'application/json',
        }
      });

      if (response.ok) {
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

  // Helper function to set cookies
  const setAuthCookies = async (accessToken: string, refreshToken?: string) => {
    if (typeof window !== 'undefined' && window.chrome && window.chrome.cookies) {
      try {
        const apiUrl = import.meta.env.VITE_BACKEND_URL;
        const apiDomain = new URL(import.meta.env.VITE_BACKEND_URL).hostname;
        const isSecure = apiUrl.startsWith('https://');

        await window.chrome.cookies.set({
          url: apiUrl,
          name: 'access_token',
          value: accessToken,
          path: '/',
          domain: apiDomain,
          secure: isSecure,
          sameSite: 'no_restriction' as chrome.cookies.SameSiteStatus,
          httpOnly: false,
          expirationDate: Math.floor(Date.now() / 1000) + 3600
        });

        if (refreshToken) {
          await window.chrome.cookies.set({
            url: apiUrl,
            name: 'refresh_token',
            value: refreshToken,
            path: '/',
            domain: apiDomain,
            secure: isSecure,
            sameSite: 'no_restriction' as chrome.cookies.SameSiteStatus,
            httpOnly: false,
            expirationDate: Math.floor(Date.now() / 1000) + 604800
          });
        }

        console.log('Extension auth cookies set for backend');
      } catch (error) {
        console.error('Error setting auth cookies:', error);
      }
    }
  };

  // Initialize authentication on mount
  useEffect(() => {
    const initAuth = async () => {
      await silentBackgroundAuthCheck();
    };

    initAuth();

    // Listen for Supabase auth changes
    const { data: { subscription } } = supabase.auth.onAuthStateChange(
      async (event: string, session: any) => {
        console.log('Supabase auth event:', event);
        
        if (event === 'SIGNED_IN' && session?.access_token && !globalAuthCheckInProgress) {
          console.log('🔑 AUTH_CONTEXT: Processing SIGNED_IN event');
          await setAuthCookies(session.access_token, session.refresh_token);
        } else if (event === 'SIGNED_OUT') {
          console.log('🚪 AUTH_CONTEXT: Processing SIGNED_OUT event');
          setAuthState({
            user: null,
            isLoading: false,
            isAuthenticated: false,
            error: null
          });
        } else if (event === 'INITIAL_SESSION') {
          console.log('🔄 AUTH_CONTEXT: INITIAL_SESSION event (ignoring to prevent redundant checks)');
        }
      }
    );

    return () => {
      subscription.unsubscribe();
    };
  }, [silentBackgroundAuthCheck]);

  const contextValue: AuthContextType = {
    ...authState,
    signIn,
    signUp,
    signOut,
    refreshToken,
    checkAuthStatus
  };

  return (
    <AuthContext.Provider value={contextValue}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  
  console.log('🌐 USE_AUTH_CONTEXT: Hook called with global state:', {
    isAuthenticated: context.isAuthenticated,
    isLoading: context.isLoading,
    hasUser: !!context.user,
    error: context.error,
    timestamp: new Date().toISOString()
  });
  
  return context;
};
