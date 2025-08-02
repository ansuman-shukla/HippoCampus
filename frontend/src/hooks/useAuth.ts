import { useState, useEffect, useCallback, useRef } from 'react';
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

  // Use a ref to track ongoing auth requests and prevent duplicates
  const authRequestRef = useRef<Promise<boolean> | null>(null);

  // Check authentication status from backend (single source of truth)
  // Backend middleware handles token validation, refresh, and user management automatically
  const checkAuthStatus = useCallback(async () => {
    console.log('🔍 STEP 1: Starting checkAuthStatus - Validating current authentication state');
    console.log('   ├─ Function: useAuth.checkAuthStatus()');
    console.log('   └─ Purpose: Check if user is authenticated with backend');

    // Check if there's already an ongoing auth request
    if (authRequestRef.current) {
      console.log('🔄 STEP 1A: Auth request already in progress, returning existing promise');
      console.log('   └─ This prevents duplicate API calls and improves performance');
      return await authRequestRef.current;
    }

    console.log('🔄 STEP 1B: No ongoing request, starting new auth check');
    console.log('   └─ Current state: isLoading =', authState.isLoading);

    // Create and store the auth request promise
    const authPromise = (async (): Promise<boolean> => {
      try {
        console.log('🔄 STEP 2: Setting loading state and clearing previous errors');
        setAuthState(prev => ({ ...prev, isLoading: true, error: null }));
        
        console.log('📡 STEP 3: Calling backend auth status endpoint');
        console.log('   ├─ Function: getAuthStatus() from authUtils');
        console.log('   └─ Target: Backend /auth/status endpoint');
        const authResult = await getAuthStatus();
        
        console.log('📊 STEP 4: Processing auth status response from backend');
        console.log('   ├─ Response success:', authResult.success);
        console.log('   ├─ User data present:', !!authResult.user);
        console.log('   └─ Error message:', authResult.error || 'None');
        
        if (authResult.success && authResult.user) {
          console.log('✅ STEP 5A: Authentication successful - updating state to authenticated');
          console.log('   ├─ User ID:', authResult.user.id);
          console.log('   ├─ User email:', authResult.user.email);
          console.log('   ├─ User name:', authResult.user.full_name || 'Not provided');
          console.log('   └─ Setting isAuthenticated = true');
          
          setAuthState({
            user: authResult.user as User,
            isLoading: false,
            isAuthenticated: true,
            error: null,
            tokenRefreshed: false
          });
          console.log('🎉 STEP 6A: Auth state updated successfully - user is authenticated');
          return true;
        } else {
          console.log('❌ STEP 5B: Authentication failed - updating state to unauthenticated');
          console.log('   ├─ Reason:', authResult.error || 'Unknown error');
          console.log('   └─ Setting isAuthenticated = false');
          
          setAuthState({
            user: null,
            isLoading: false,
            isAuthenticated: false,
            error: authResult.error || null,
            tokenRefreshed: false
          });
          console.log('🚫 STEP 6B: Auth state updated - user is not authenticated');
          return false;
        }
      } catch (error: any) {
        console.error('💥 STEP 7: Auth status check failed with error');
        console.error('   ├─ Error type:', error.constructor.name);
        console.error('   ├─ Error message:', error.message);
        console.error('   └─ Setting error state and isAuthenticated = false');
        
        setAuthState({
          user: null,
          isLoading: false,
          isAuthenticated: false,
          error: 'Failed to check authentication status',
          errorType: 'network_error',
          tokenRefreshed: false
        });
        console.log('🔄 STEP 8: Error state set - checkAuthStatus completed with failure');
        return false;
      } finally {
        // Clear the request ref when done
        authRequestRef.current = null;
        console.log('🧹 STEP 9: Cleared auth request reference - ready for new requests');
      }
    })();

    // Store the promise in the ref
    authRequestRef.current = authPromise;
    console.log('💾 STEP 1C: Stored auth request promise in ref for deduplication');
    
    // Return the promise result
    return await authPromise;
  }, []); // Remove dependency to prevent infinite loops

  // Sign in with Supabase
  const signIn = useCallback(async (email: string, password: string) => {
    console.log('🔐 STEP 10: Starting user sign-in process');
    console.log('   ├─ Function: useAuth.signIn()');
    console.log('   ├─ Email:', email);
    console.log('   ├─ Password length:', password.length);
    console.log('   └─ Purpose: Authenticate user with Supabase and setup backend session');

    try {
      console.log('🔄 STEP 11: Setting loading state for sign-in');
      setAuthState((prev: AuthState) => ({ ...prev, isLoading: true, error: null }));
      
      console.log('🔐 STEP 12: Calling Supabase authentication');
      console.log('   ├─ Function: supabase.auth.signInWithPassword()');
      console.log('   └─ Provider: Supabase');
      
      const { data, error } = await supabase.auth.signInWithPassword({
        email,
        password
      });

      console.log('📊 STEP 13: Processing Supabase authentication response');
      console.log('   ├─ Success:', !error);
      console.log('   ├─ Error:', error?.message || 'None');
      console.log('   ├─ Session received:', !!data.session);
      console.log('   └─ Access token present:', !!data.session?.access_token);

      if (error) {
        console.log('❌ STEP 14A: Supabase authentication failed');
        console.log('   ├─ Error message:', error.message);
        console.log('   └─ Setting error state');
        
        setAuthState((prev: AuthState) => ({ 
          ...prev, 
          isLoading: false, 
          error: error.message 
        }));
        console.log('🚫 STEP 15A: Sign-in failed - returning error result');
        return { success: false, error: error.message };
      }

      if (data.session?.access_token) {
        console.log('✅ STEP 14B: Supabase authentication successful');
        console.log('   ├─ Access token length:', data.session.access_token.length);
        console.log('   ├─ Refresh token present:', !!data.session.refresh_token);
        console.log('   └─ User ID:', data.session.user?.id);

        console.log('🍪 STEP 15B: Setting authentication cookies for backend');
        console.log('   ├─ Function: setAuthCookies()');
        console.log('   └─ Purpose: Transfer tokens to backend-accessible cookies');
        // Set tokens in cookies for backend communication
        await setAuthCookies(data.session.access_token, data.session.refresh_token);

        console.log('🔍 STEP 16B: Verifying authentication with backend');
        console.log('   ├─ Function: checkAuthStatus()');
        console.log('   └─ Purpose: Confirm backend can validate the tokens');
        // Verify authentication with backend (backend middleware will set secure httpOnly cookies)
        await checkAuthStatus();
        
        console.log('🎉 STEP 17B: Sign-in process completed successfully');
        return { success: true, data: data.session };
      }

      console.log('❌ STEP 14C: No session received from Supabase');
      console.log('🚫 STEP 15C: Sign-in failed - no session');
      return { success: false, error: 'No session received' };
    } catch (error: any) {
      console.error('💥 STEP 18: Sign-in process failed with exception');
      console.error('   ├─ Error type:', error.constructor.name);
      console.error('   ├─ Error message:', error.message);
      console.error('   └─ Setting error state');
      
      const errorMessage = error.message || 'Sign in failed';
      setAuthState((prev: AuthState) => ({ 
        ...prev, 
        isLoading: false, 
        error: errorMessage 
      }));
      console.log('🔄 STEP 19: Error state set - sign-in completed with failure');
      return { success: false, error: errorMessage };
    }
  }, [checkAuthStatus]);

  // Sign up with Supabase
  const signUp = useCallback(async (email: string, password: string, fullName?: string) => {
    console.log('📝 STEP 20: Starting user sign-up process');
    console.log('   ├─ Function: useAuth.signUp()');
    console.log('   ├─ Email:', email);
    console.log('   ├─ Password length:', password.length);
    console.log('   ├─ Full name:', fullName || 'Not provided');
    console.log('   └─ Purpose: Register new user with Supabase');

    try {
      console.log('🔄 STEP 21: Setting loading state for sign-up');
      setAuthState((prev: AuthState) => ({ ...prev, isLoading: true, error: null }));
      
      console.log('📝 STEP 22: Calling Supabase user registration');
      console.log('   ├─ Function: supabase.auth.signUp()');
      console.log('   └─ Including user metadata: full_name');
      
      const { data, error } = await supabase.auth.signUp({
        email,
        password,
        options: {
          data: {
            full_name: fullName
          }
        }
      });

      console.log('📊 STEP 23: Processing Supabase registration response');
      console.log('   ├─ Success:', !error);
      console.log('   ├─ Error:', error?.message || 'None');
      console.log('   ├─ User created:', !!data.user);
      console.log('   ├─ Session received:', !!data.session);
      console.log('   └─ Email confirmation required:', !!(data.user && !data.session));

      if (error) {
        console.log('❌ STEP 24A: Supabase registration failed');
        console.log('   ├─ Error message:', error.message);
        console.log('   └─ Setting error state');
        
        setAuthState((prev: AuthState) => ({ 
          ...prev, 
          isLoading: false, 
          error: error.message 
        }));
        console.log('🚫 STEP 25A: Sign-up failed - returning error result');
        return { success: false, error: error.message };
      }

      // For email confirmation flow
      if (data.user && !data.session) {
        console.log('📧 STEP 24B: Registration successful - email confirmation required');
        console.log('   ├─ User ID:', data.user.id);
        console.log('   ├─ Email:', data.user.email);
        console.log('   └─ Status: Awaiting email confirmation');
        
        setAuthState((prev: AuthState) => ({ ...prev, isLoading: false }));
        console.log('✉️  STEP 25B: Email confirmation flow - user must verify email');
        return { 
          success: true, 
          message: 'Check your email for confirmation link',
          needsEmailConfirmation: true
        };
      }

      // Auto sign-in after signup
      if (data.session?.access_token) {
        console.log('✅ STEP 24C: Registration successful with immediate session');
        console.log('   ├─ User ID:', data.user?.id);
        console.log('   ├─ Access token length:', data.session.access_token.length);
        console.log('   ├─ Refresh token present:', !!data.session.refresh_token);
        console.log('   └─ Auto sign-in enabled');

        console.log('🍪 STEP 25C: Setting authentication cookies for backend');
        console.log('   ├─ Function: setAuthCookies()');
        console.log('   └─ Purpose: Transfer tokens to backend-accessible cookies');
        await setAuthCookies(data.session.access_token, data.session.refresh_token);
        
        console.log('🔍 STEP 26C: Verifying authentication with backend');
        console.log('   ├─ Function: checkAuthStatus()');
        console.log('   └─ Purpose: Confirm backend can validate the tokens');
        await checkAuthStatus();
        
        console.log('🎉 STEP 27C: Sign-up and auto sign-in completed successfully');
        return { success: true, data: data.session };
      }

      console.log('❌ STEP 24D: No session received from Supabase');
      console.log('🚫 STEP 25D: Sign-up failed - no session');
      return { success: false, error: 'No session received' };
    } catch (error: any) {
      console.error('💥 STEP 28: Sign-up process failed with exception');
      console.error('   ├─ Error type:', error.constructor.name);
      console.error('   ├─ Error message:', error.message);
      console.error('   └─ Setting error state');
      
      const errorMessage = error.message || 'Sign up failed';
      setAuthState((prev: AuthState) => ({ 
        ...prev, 
        isLoading: false, 
        error: errorMessage 
      }));
      console.log('🔄 STEP 29: Error state set - sign-up completed with failure');
      return { success: false, error: errorMessage };
    }
  }, [checkAuthStatus]);

  // Sign out using comprehensive logout from authUtils
  const signOut = useCallback(async () => {
    console.log('🚪 STEP 30: Starting user sign-out process');
    console.log('   ├─ Function: useAuth.signOut()');
    console.log('   └─ Purpose: Complete logout from both frontend and backend');
    
    console.log('🔄 STEP 31: Setting loading state for sign-out');
    setAuthState((prev: AuthState) => ({ ...prev, isLoading: true }));
    
    try {
      console.log('🗑️  STEP 32: Calling comprehensive logout function');
      console.log('   ├─ Function: authUtilsLogout() from authUtils');
      console.log('   └─ Will clear backend cookies and local storage');
      
      // Use the comprehensive logout function from authUtils
      const result = await authUtilsLogout();
      
      console.log('📊 STEP 33: Processing logout result');
      console.log('   ├─ Logout success:', result.success);
      console.log('   ├─ Message:', result.message || 'None');
      console.log('   └─ Error:', result.error || 'None');
      
      console.log('🧹 STEP 34: Clearing local authentication state');
      console.log('   ├─ Setting user = null');
      console.log('   ├─ Setting isAuthenticated = false');
      console.log('   └─ Setting isLoading = false');
      
      // Always update auth state to logged out regardless of result
      setAuthState({
        user: null,
        isLoading: false,
        isAuthenticated: false,
        error: null
      });
      
      console.log('✅ STEP 35: Sign-out process completed successfully');
      console.log('✅ STEP 35: Sign-out process completed successfully');
      return result;
    } catch (error: any) {
      console.error('💥 STEP 36: Sign-out process failed with exception');
      console.error('   ├─ Error type:', error.constructor.name);
      console.error('   ├─ Error message:', error.message);
      console.error('   └─ Still clearing local state for consistency');
      
      // Still set state to logged out for consistency
      setAuthState({
        user: null,
        isLoading: false,
        isAuthenticated: false,
        error: null
      });
      
      console.log('🔄 STEP 37: Local state cleared despite error - sign-out completed with issues');
      return { 
        success: false, 
        error: error.message || 'Logout failed',
        localStateCleared: true
      };
    }
  }, []);

  // Manually refresh token (backend auto-refreshes via middleware)
  const refreshToken = useCallback(async () => {
    console.log('🔄 STEP 40: Starting manual token refresh process');
    console.log('   ├─ Function: useAuth.refreshToken()');
    console.log('   └─ Purpose: Manually refresh access token using refresh token');

    try {
      console.log('📡 STEP 41: Calling backend token refresh endpoint');
      console.log('   ├─ URL:', `${getBackendUrl()}/auth/refresh`);
      console.log('   ├─ Method: POST');
      console.log('   └─ Credentials: include (for cookies)');
      
      const response = await fetch(`${getBackendUrl()}/auth/refresh`, {
        method: 'POST',
        credentials: 'include', // Backend reads refresh_token from cookies
        headers: {
          'Content-Type': 'application/json',
        }
      });

      console.log('📊 STEP 42: Processing token refresh response');
      console.log('   ├─ Response status:', response.status);
      console.log('   ├─ Response OK:', response.ok);
      console.log('   └─ Status text:', response.statusText);

      if (response.ok) {
        console.log('✅ STEP 43A: Token refresh successful');
        console.log('   ├─ Backend automatically sets new cookies in response headers');
        console.log('   └─ Updating local auth state');
        
        console.log('🔍 STEP 44A: Checking updated auth status');
        console.log('   ├─ Function: checkAuthStatus()');
        console.log('   └─ Purpose: Update local state with refreshed tokens');
        // Backend automatically sets new cookies in response headers
        // Update auth state
        await checkAuthStatus();
        
        console.log('🎉 STEP 45A: Token refresh completed successfully');
        return { success: true };
      }

      console.log('❌ STEP 43B: Token refresh failed');
      const errorData = await response.json().catch(() => ({}));
      console.log('   ├─ Error data:', errorData);
      console.log('   ├─ Detail:', errorData.detail || 'Unknown error');
      console.log('   └─ Error type:', errorData.error_type || 'Unknown');
      
      console.log('🚫 STEP 44B: Returning refresh failure result');
      return { 
        success: false, 
        error: errorData.detail || 'Token refresh failed',
        error_type: errorData.error_type 
      };
    } catch (error: any) {
      console.error('💥 STEP 45: Token refresh failed with exception');
      console.error('   ├─ Error type:', error.constructor.name);
      console.error('   ├─ Error message:', error.message);
      console.error('   └─ Network or service error');
      
      console.log('🔄 STEP 46: Returning network error result');
      return { 
        success: false, 
        error: error.message,
        error_type: 'network_error'
      };
    }
  }, [checkAuthStatus]);

  // Helper function to set cookies across domains (matching backend expectations)
  const setAuthCookies = async (accessToken: string, refreshToken?: string) => {
    console.log('🍪 STEP 50: Starting authentication cookie setup');
    console.log('   ├─ Function: useAuth.setAuthCookies()');
    console.log('   ├─ Access token length:', accessToken.length);
    console.log('   ├─ Refresh token present:', !!refreshToken);
    console.log('   └─ Purpose: Transfer Supabase tokens to backend-accessible cookies');

    if (typeof window !== 'undefined' && window.chrome && window.chrome.cookies) {
      try {
        console.log('🌐 STEP 51: Setting up cookie configuration');
        // Set cookies for backend API domain with exact settings backend expects
        const apiUrl = import.meta.env.VITE_BACKEND_URL;
        const apiDomain = new URL(import.meta.env.VITE_BACKEND_URL).hostname;
        const isSecure = apiUrl.startsWith('https://');

        console.log('   ├─ API URL:', apiUrl);
        console.log('   ├─ API Domain:', apiDomain);
        console.log('   ├─ Secure connection:', isSecure);
        console.log('   └─ Cookie path: /');

        console.log('🔑 STEP 52: Setting access token cookie');
        console.log('   ├─ Cookie name: access_token');
        console.log('   ├─ Expires in: 3600 seconds (1 hour)');
        console.log('   └─ HttpOnly: false (Chrome extension limitation)');
        
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

        console.log('✅ STEP 53: Access token cookie set successfully');

        // Refresh token cookie (expires in 7 days, matching backend)
        if (refreshToken) {
          console.log('🔄 STEP 54: Setting refresh token cookie');
          console.log('   ├─ Cookie name: refresh_token');
          console.log('   ├─ Expires in: 604800 seconds (7 days)');
          console.log('   └─ HttpOnly: false (Chrome extension limitation)');
          
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
          console.log('✅ STEP 55: Refresh token cookie set successfully');
        } else {
          console.log('ℹ️  STEP 54: No refresh token provided, skipping refresh cookie');
        }

        console.log('🎉 STEP 56: Extension auth cookies setup completed for backend');

      } catch (error) {
        console.error('💥 STEP 57: Error setting auth cookies');
        console.error('   ├─ Error type:', (error as Error).constructor.name);
        console.error('   ├─ Error message:', (error as Error).message);
        console.error('   └─ This may affect backend authentication');
      }
    } else {
      console.warn('⚠️  STEP 51: Chrome extension API not available for cookie setting');
      console.warn('   └─ Running in non-extension environment');
    }
  };

  // Enhanced helper function to clear cookies across multiple domains
  const clearAuthCookies = async () => {
    console.log('🧹 STEP 60: Starting comprehensive cookie cleanup');
    console.log('   ├─ Function: useAuth.clearAuthCookies()');
    console.log('   └─ Purpose: Remove all authentication cookies from all domains');

    if (typeof window !== 'undefined' && window.chrome && window.chrome.cookies) {
      try {
        console.log('🌐 STEP 61: Identifying domains and cookies to clear');
        
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

        console.log('   ├─ Domains to clear:', domains.length);
        console.log('   ├─ Cookie types to clear:', authCookieNames.length);
        console.log('   └─ Total operations:', domains.length * authCookieNames.length);

        console.log('🗑️  STEP 62: Clearing cookies from all domains');
        for (const domain of domains) {
          console.log(`   ├─ Processing domain: ${domain}`);
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

        console.log('✅ STEP 63: Cookie cleanup completed - all domains processed');
      } catch (error) {
        console.error('❌ STEP 64: Error during cookie cleanup');
        console.error('   ├─ Error type:', (error as Error).constructor.name);
        console.error('   ├─ Error message:', (error as Error).message);
        console.error('   └─ Some cookies may not have been cleared');
      }
    } else {
      console.warn('⚠️  STEP 61: Chrome extension API not available for cookie clearing');
      console.warn('   └─ Running in non-extension environment');
    }
  };

  // Check for existing auth on mount and listen for auth changes
  useEffect(() => {
    console.log('🚀 STEP 70: Initializing useAuth hook');
    console.log('   ├─ Function: useAuth.useEffect()');
    console.log('   └─ Purpose: Setup auth state and event listeners');

    const initAuth = async () => {
      console.log('🔍 STEP 71: Starting initial authentication check');
      console.log('   ├─ Function: initAuth()');
      console.log('   └─ Backend is the source of truth for auth state');
      
      // Always check auth status with backend (backend is source of truth)
      // Backend middleware will handle token validation and refresh automatically
      await checkAuthStatus();
      console.log('✅ STEP 72: Initial authentication check completed');
    };

    console.log('📡 STEP 73: Setting up Supabase auth state listener');
    initAuth();

    // Listen for Supabase auth changes
    const { data: { subscription } } = supabase.auth.onAuthStateChange(
      async (event: string, session: any) => {
        console.log('📢 STEP 74: Supabase auth state change detected');
        console.log('   ├─ Event type:', event);
        console.log('   ├─ Session present:', !!session);
        console.log('   ├─ Access token present:', !!session?.access_token);
        console.log('   └─ User ID:', session?.user?.id || 'None');
        
        if (event === 'SIGNED_IN' && session?.access_token) {
          console.log('✅ STEP 75A: Processing SIGNED_IN event');
          console.log('   ├─ Setting authentication cookies');
          console.log('   └─ Checking auth status with backend');
          
          await setAuthCookies(session.access_token, session.refresh_token);
          await checkAuthStatus();
          
          console.log('🎉 STEP 76A: SIGNED_IN event processing completed');
        } else if (event === 'SIGNED_OUT') {
          console.log('🚪 STEP 75B: Processing SIGNED_OUT event');
          console.log('   ├─ Clearing authentication cookies');
          console.log('   ├─ Removing localStorage tokens');
          console.log('   └─ Setting auth state to logged out');
          
          await clearAuthCookies();
          localStorage.removeItem('access_token');
          localStorage.removeItem('refresh_token');
          setAuthState({
            user: null,
            isLoading: false,
            isAuthenticated: false,
            error: null
          });
          
          console.log('🧹 STEP 76B: SIGNED_OUT event processing completed');
        } else {
          console.log('ℹ️  STEP 75C: Other auth event - no action needed');
          console.log('   └─ Event:', event);
        }
      }
    );

    // Enhanced session monitoring for extension environment
    let cookieChangeListener: ((changeInfo: chrome.cookies.CookieChangeInfo) => void) | null = null;
    let messageListener: ((message: any, sender: any, sendResponse: any) => void) | null = null;

    console.log('🔧 STEP 77: Setting up Chrome extension event listeners');
    if (typeof window !== 'undefined' && window.chrome && window.chrome.cookies) {
      console.log('   ├─ Chrome extension API available');
      console.log('   ├─ Setting up cookie change listener');
      console.log('   └─ Setting up message listener');
      
      // Monitor backend cookie changes
      cookieChangeListener = (changeInfo: chrome.cookies.CookieChangeInfo) => {
        console.log('🍪 STEP 78: Cookie change detected');
        console.log('   ├─ Cookie name:', changeInfo.cookie.name);
        console.log('   ├─ Cookie domain:', changeInfo.cookie.domain);
        console.log('   ├─ Change type:', changeInfo.removed ? 'removed' : 'added/updated');
        console.log('   └─ Backend domain match:', changeInfo.cookie.domain.includes(new URL(import.meta.env.VITE_BACKEND_URL).hostname));
        
        if (changeInfo.cookie.name === "access_token" && 
            changeInfo.cookie.domain.includes(new URL(import.meta.env.VITE_BACKEND_URL).hostname)) {
          
          if (changeInfo.removed) {
            console.log('🚫 STEP 79A: Backend access token was removed');
            console.log('   ├─ Updating auth state to unauthenticated');
            console.log('   └─ Session has expired or user logged out');
            
            setAuthState(prev => ({
              ...prev,
              user: null,
              isAuthenticated: false,
              error: 'Session expired'
            }));
            
            console.log('🔄 STEP 80A: Auth state updated due to token removal');
          } else {
            console.log('✅ STEP 79B: Backend access token was added/updated');
            console.log('   └─ User may have authenticated');
          }
        }
      };

      // Listen for background script auth failure notifications
      messageListener = (message: any, _sender: any, sendResponse: any) => {
        console.log('📨 STEP 81: Message received from background script');
        console.log('   ├─ Message action:', message.action);
        console.log('   └─ Sender:', _sender?.id || 'Unknown');
        
        if (message.action === "authenticationFailed") {
          console.log('🚫 STEP 82: Authentication failure notification received');
          console.log('   ├─ Source: Background script');
          console.log('   ├─ Setting auth state to failed');
          console.log('   └─ User will need to re-authenticate');
          
          setAuthState({
            user: null,
            isLoading: false,
            isAuthenticated: false,
            error: 'Authentication failed. Please log in again.',
            errorType: 'session_expired'
          });
          
          console.log('📤 STEP 83: Sending acknowledgment to background script');
          sendResponse({ received: true });
          console.log('🔄 STEP 84: Auth failure handling completed');
        }
      };

      console.log('🎧 STEP 85: Registering Chrome extension event listeners');
      chrome.cookies.onChanged.addListener(cookieChangeListener);
      chrome.runtime.onMessage.addListener(messageListener);
      console.log('✅ STEP 86: Chrome extension listeners registered successfully');
    } else {
      console.log('ℹ️  STEP 77: Chrome extension API not available');
      console.log('   └─ Running in non-extension environment');
    }

    return () => {
      console.log('🧹 STEP 90: Cleaning up useAuth hook');
      console.log('   ├─ Function: useAuth cleanup');
      console.log('   └─ Purpose: Remove event listeners and subscriptions');
      
      console.log('📡 STEP 91: Unsubscribing from Supabase auth changes');
      subscription.unsubscribe();
      
      console.log('🔧 STEP 92: Removing Chrome extension event listeners');
      // Clean up extension-specific listeners
      if (cookieChangeListener && chrome.cookies?.onChanged) {
        console.log('   ├─ Removing cookie change listener');
        chrome.cookies.onChanged.removeListener(cookieChangeListener);
      }
      if (messageListener && chrome.runtime?.onMessage) {
        console.log('   ├─ Removing message listener');
        chrome.runtime.onMessage.removeListener(messageListener);
      }
      
      console.log('✅ STEP 93: useAuth hook cleanup completed');
    };
  }, []); // Remove checkAuthStatus dependency to prevent reinitialization

  console.log('📋 STEP 95: Returning useAuth hook interface');
  console.log('   ├─ Current auth state - User:', !!authState.user);
  console.log('   ├─ Current auth state - Authenticated:', authState.isAuthenticated);
  console.log('   ├─ Current auth state - Loading:', authState.isLoading);
  console.log('   └─ Current auth state - Error:', !!authState.error);

  return {
    ...authState,
    signIn,
    signUp,
    signOut,
    refreshToken,
    checkAuthStatus
  };
};
