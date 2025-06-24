import { createClient, SupabaseClient } from "@supabase/supabase-js";

const SUPABASE_URL = import.meta.env.VITE_SUPABASE_URL;
const SUPABASE_KEY = import.meta.env.VITE_SUPABASE_ANON_KEY;
const API_BASE_URL = import.meta.env.VITE_API_URL || 'https://hippocampus-backend-vvv9.onrender.com';

export const supabase: SupabaseClient = createClient(SUPABASE_URL, SUPABASE_KEY, {
  auth: {
    persistSession: true,
    autoRefreshToken: true,
    detectSessionInUrl: true
  }
});

// Enhanced token management utilities with backend integration
export const tokenManager = {
  // Get tokens from localStorage and cookies
  getTokens: async () => {
    const session = await supabase.auth.getSession();
    return {
      access_token: session.data.session?.access_token || localStorage.getItem("access_token"),
      refresh_token: session.data.session?.refresh_token || localStorage.getItem("refresh_token")
    };
  },

  // Store tokens in both localStorage and cookies with enhanced error handling
  setTokens: async (accessToken: string, refreshToken: string) => {
    try {
      localStorage.setItem("access_token", accessToken);
      localStorage.setItem("refresh_token", refreshToken);
      
      // Enhanced cookie setting for backend compatibility
      const domains = [
        'hippocampus-backend-vvv9.onrender.com',
        'localhost',
        '.hippocampus-backend-vvv9.onrender.com',
        '127.0.0.1'
      ];
      
      const tabs = await chrome.tabs.query({ active: true, currentWindow: true });
      const tab = tabs[0];
      
      if (tab?.url) {
        for (const domain of domains) {
          try {
            // Set access token cookie
            await chrome.cookies.set({
              url: tab.url,
              name: 'access_token',
              value: accessToken,
              path: '/',
              domain: domain,
              secure: true,
              httpOnly: false,
              sameSite: 'no_restriction' as chrome.cookies.SameSiteStatus,
              expirationDate: Math.floor(Date.now() / 1000) + 3600 // 1 hour
            });

            // Set refresh token cookie
            await chrome.cookies.set({
              url: tab.url,
              name: 'refresh_token',
              value: refreshToken,
              path: '/',
              domain: domain,
              secure: true,
              httpOnly: false,
              sameSite: 'no_restriction' as chrome.cookies.SameSiteStatus,
              expirationDate: Math.floor(Date.now() / 1000) + 604800 // 7 days
            });

            console.log(`Successfully set cookies for domain: ${domain}`);
          } catch (error) {
            console.log(`Failed to set cookies for domain ${domain}:`, error);
          }
        }
      }

      // Also store in Chrome storage for background script access
      chrome.storage.local.set({
        access_token: accessToken,
        refresh_token: refreshToken,
        token_timestamp: Date.now()
      });

    } catch (error) {
      console.error('Error setting tokens:', error);
      throw error;
    }
  },

  // Enhanced token clearing with comprehensive cleanup
  clearTokens: async () => {
    try {
      // Clear localStorage
      localStorage.removeItem("access_token");
      localStorage.removeItem("refresh_token");
      
      // Clear Chrome storage
      chrome.storage.local.remove(['access_token', 'refresh_token', 'token_timestamp']);
      
      // Clear cookies from all domains
      const domains = [
        'hippocampus-backend-vvv9.onrender.com',
        'localhost',
        '.hippocampus-backend-vvv9.onrender.com',
        '127.0.0.1'
      ];
      
      const tabs = await chrome.tabs.query({ active: true, currentWindow: true });
      const tab = tabs[0];
      
      if (tab?.url) {
        for (const domain of domains) {
          try {
            await chrome.cookies.remove({
              url: tab.url,
              name: 'access_token'
            });

            await chrome.cookies.remove({
              url: tab.url,
              name: 'refresh_token'
            });

            await chrome.cookies.remove({
              url: tab.url,
              name: 'user_id'
            });

            await chrome.cookies.remove({
              url: tab.url,
              name: 'user_name'
            });

            await chrome.cookies.remove({
              url: tab.url,
              name: 'user_picture'
            });

            console.log(`Successfully cleared cookies for domain: ${domain}`);
          } catch (error) {
            console.log(`Failed to clear cookies for domain ${domain}:`, error);
          }
        }
      }

      // Call backend logout endpoint to ensure server-side cleanup
      try {
        await fetch(`${API_BASE_URL}/auth/logout`, {
          method: 'POST',
          credentials: 'include',
          headers: {
            'Content-Type': 'application/json'
          }
        });
        console.log('Backend logout successful');
      } catch (error) {
        console.log('Backend logout failed:', error);
      }

    } catch (error) {
      console.error('Error clearing tokens:', error);
    }
  },

  // Enhanced authentication check with backend verification
  isAuthenticated: async () => {
    try {
      const { access_token } = await tokenManager.getTokens();
      if (!access_token) return false;

      // Check with backend auth status endpoint
      const response = await fetch(`${API_BASE_URL}/auth/status`, {
        method: 'GET',
        credentials: 'include',
        headers: {
          'Authorization': `Bearer ${access_token}`,
          'Content-Type': 'application/json'
        }
      });

      if (response.ok) {
        const data = await response.json();
        return data.is_authenticated && data.token_valid;
      }

      return false;
    } catch (error) {
      console.error('Authentication check failed:', error);
      return false;
    }
  },

  // Enhanced token verification with backend integration
  verifyToken: async (): Promise<any> => {
    try {
      const { access_token } = await tokenManager.getTokens();
      if (!access_token) throw new Error('No access token available');

      const response = await fetch(`${API_BASE_URL}/auth/verify`, {
        method: 'GET',
        credentials: 'include',
        headers: {
          'Authorization': `Bearer ${access_token}`,
          'Content-Type': 'application/json'
        }
      });

      if (response.ok) {
        return await response.json();
      } else if (response.status === 401) {
        // Token invalid, try to refresh
        const refreshed = await tokenManager.refreshToken();
        if (refreshed) {
          // Retry verification with new token
          return await tokenManager.verifyToken();
        }
        throw new Error('Token verification failed');
      }
      
      throw new Error(`Verification failed with status: ${response.status}`);
    } catch (error) {
      console.error('Token verification error:', error);
      throw error;
    }
  },

  // Enhanced token refresh with backend integration
  refreshToken: async () => {
    try {
      const { refresh_token } = await tokenManager.getTokens();
      if (!refresh_token) {
        console.log('No refresh token available');
        return false;
      }

      const response = await fetch(`${API_BASE_URL}/auth/refresh`, {
        method: 'POST',
        credentials: 'include',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ refresh_token })
      });

      if (response.ok) {
        const data = await response.json();
        if (data.access_token && data.refresh_token) {
          await tokenManager.setTokens(data.access_token, data.refresh_token);
          console.log('Token refreshed successfully');
          return true;
        }
      } else {
        console.error('Token refresh failed:', response.status, await response.text());
        // If refresh fails, clear tokens and force re-login
        await tokenManager.clearTokens();
      }
      
      return false;
    } catch (error) {
      console.error('Token refresh error:', error);
      await tokenManager.clearTokens();
      return false;
    }
  },

  // Check authentication status and auto-refresh if needed
  ensureAuthenticated: async () => {
    try {
      const isAuth = await tokenManager.isAuthenticated();
      if (isAuth) return true;

      // Try to refresh if not authenticated
      const refreshed = await tokenManager.refreshToken();
      if (refreshed) {
        return await tokenManager.isAuthenticated();
      }

      return false;
    } catch (error) {
      console.error('Error ensuring authentication:', error);
      return false;
    }
  }
};

// Enhanced auth state change listener with error handling
supabase.auth.onAuthStateChange(async (event, session) => {
  console.log('Supabase auth state changed:', event, session?.user?.id);
  
  try {
    if (event === 'SIGNED_IN' && session) {
      console.log('User signed in, setting tokens');
      await tokenManager.setTokens(session.access_token, session.refresh_token);
    } else if (event === 'SIGNED_OUT') {
      console.log('User signed out, clearing tokens');
      await tokenManager.clearTokens();
    } else if (event === 'TOKEN_REFRESHED' && session) {
      console.log('Supabase token refreshed, updating stored tokens');
      await tokenManager.setTokens(session.access_token, session.refresh_token);
    } else if (event === 'USER_UPDATED' && session) {
      console.log('User data updated');
      // Update tokens in case user metadata changed
      await tokenManager.setTokens(session.access_token, session.refresh_token);
    }
  } catch (error) {
    console.error('Error handling auth state change:', error);
  }
});

// Auth utilities for components
export const authUtils = {
  // Sign out from both Supabase and backend
  signOut: async () => {
    try {
      // Clear tokens first
      await tokenManager.clearTokens();
      
      // Sign out from Supabase
      await supabase.auth.signOut();
      
      console.log('Complete sign out successful');
    } catch (error) {
      console.error('Error during sign out:', error);
      // Even if there's an error, ensure tokens are cleared
      await tokenManager.clearTokens();
    }
  },

  // Check if user needs to re-authenticate
  needsReauth: async () => {
    try {
      const isAuth = await tokenManager.ensureAuthenticated();
      return !isAuth;
    } catch (error) {
      console.error('Error checking auth status:', error);
      return true;
    }
  },

  // Get current user info from backend
  getCurrentUser: async () => {
    try {
      const userData = await tokenManager.verifyToken();
      return userData;
    } catch (error) {
      console.error('Error getting current user:', error);
      return null;
    }
  }
};
