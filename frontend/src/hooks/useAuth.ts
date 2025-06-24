import { useState, useEffect } from 'react';
import { tokenManager, authUtils } from '../supabaseClient';

interface AuthState {
  isAuthenticated: boolean;
  isLoading: boolean;
  user: any;
  error: string | null;
}

export const useAuth = () => {
  const [authState, setAuthState] = useState<AuthState>({
    isAuthenticated: false,
    isLoading: true,
    user: null,
    error: null
  });

  const checkAuthStatus = async () => {
    try {
      setAuthState(prev => ({ ...prev, isLoading: true, error: null }));
      
      const isAuth = await tokenManager.ensureAuthenticated();
      
      if (isAuth) {
        const userData = await authUtils.getCurrentUser();
        setAuthState({
          isAuthenticated: true,
          isLoading: false,
          user: userData,
          error: null
        });
      } else {
        setAuthState({
          isAuthenticated: false,
          isLoading: false,
          user: null,
          error: null
        });
      }
    } catch (error) {
      console.error('Auth check failed:', error);
      setAuthState({
        isAuthenticated: false,
        isLoading: false,
        user: null,
        error: error instanceof Error ? error.message : 'Authentication check failed'
      });
    }
  };

  const signOut = async () => {
    try {
      await authUtils.signOut();
      setAuthState({
        isAuthenticated: false,
        isLoading: false,
        user: null,
        error: null
      });
    } catch (error) {
      console.error('Sign out failed:', error);
      setAuthState(prev => ({
        ...prev,
        error: error instanceof Error ? error.message : 'Sign out failed'
      }));
    }
  };

  const refreshAuth = async () => {
    try {
      const refreshed = await tokenManager.refreshToken();
      if (refreshed) {
        await checkAuthStatus();
      } else {
        setAuthState({
          isAuthenticated: false,
          isLoading: false,
          user: null,
          error: 'Token refresh failed'
        });
      }
    } catch (error) {
      console.error('Token refresh failed:', error);
      setAuthState(prev => ({
        ...prev,
        error: error instanceof Error ? error.message : 'Token refresh failed'
      }));
    }
  };

  useEffect(() => {
    checkAuthStatus();

    // Listen for auth events
    const handleAuthLogout = () => {
      setAuthState({
        isAuthenticated: false,
        isLoading: false,
        user: null,
        error: null
      });
    };

    window.addEventListener('auth:logout', handleAuthLogout);

    return () => {
      window.removeEventListener('auth:logout', handleAuthLogout);
    };
  }, []);

  return {
    ...authState,
    checkAuthStatus,
    signOut,
    refreshAuth
  };
};

export default useAuth;
