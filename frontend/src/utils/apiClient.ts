// API client for making authenticated requests to the backend
// Uses cookie-based authentication handled by backend middleware

import { logout } from './authUtils';

const getApiBaseUrl = (): string => {
  // Always use the backend API URL for API calls
  const baseUrl = import.meta.env.VITE_BACKEND_URL;
  return baseUrl.endsWith('/') ? baseUrl.slice(0, -1) : baseUrl;
};

// Enhanced error response interface matching backend error format
interface ApiError {
  detail: string;
  error_type?: string;
  status_code?: number;
}


/**
 * Make authenticated requests - backend handles token validation and refresh automatically
 */
export const makeRequest = async <T = any>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> => {
  const baseUrl = getApiBaseUrl();
  const url = `${baseUrl}${endpoint}`;
  
  console.log(`🌐 API CLIENT: Initiating ${options.method || 'GET'} request`);
  console.log(`   ├─ Endpoint: ${endpoint}`);
  console.log(`   ├─ Full URL: ${url}`);
  console.log(`   ├─ Base URL: ${baseUrl}`);
  console.log(`   └─ Method: ${options.method || 'GET'}`);
  
  const defaultOptions: RequestInit = {
    credentials: 'include', // Always use cookies - backend handles auth
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
    ...options,
  };

  console.log(`🔧 API CLIENT: Request configuration`);
  console.log(`   ├─ Credentials: ${defaultOptions.credentials}`);
  console.log(`   ├─ Headers: ${JSON.stringify(defaultOptions.headers)}`);
  console.log(`   ├─ Body present: ${!!defaultOptions.body}`);
  console.log(`   └─ Body length: ${defaultOptions.body ? String(defaultOptions.body).length : 0} chars`);

  try {
    console.log(`📡 API CLIENT: Sending request to backend`);
    const startTime = performance.now();
    
    const response = await fetch(url, defaultOptions);
    
    const endTime = performance.now();
    const duration = Math.round(endTime - startTime);
    
    console.log(`📨 API CLIENT: Response received from backend`);
    console.log(`   ├─ Status: ${response.status} ${response.statusText}`);
    console.log(`   ├─ Response time: ${duration}ms`);
    console.log(`   ├─ Content-Type: ${response.headers.get('content-type') || 'Unknown'}`);
    console.log(`   └─ Headers: ${JSON.stringify(Array.from(response.headers.entries()))}`);
    
    // Backend middleware automatically handles:
    // - Token validation
    // - Token refresh when needed
    // - Setting new cookies in response headers
    // - User authentication state
    
    if (!response.ok) {
      console.error(`❌ API CLIENT: Request failed with status ${response.status}`);
      
      // Handle 401 Unauthorized responses by automatically logging out the user
      if (response.status === 401) {
        console.warn(`🚫 API CLIENT: Unauthorized response (401) - triggering automatic logout`);
        
        try {
          // Clear all authentication data and cookies
          await logout();
          console.log(`🔄 API CLIENT: Logout completed, redirecting to auth page`);
          
          // Redirect to auth page for re-authentication
          if (typeof window !== 'undefined') {
            window.location.href = '/auth';
          }
          
          // Throw a specific error for 401 responses
          throw new Error('Session expired. Please log in again.');
        } catch (logoutError) {
          console.error(`💥 API CLIENT: Logout failed during 401 handling:`, logoutError);
          // Still redirect to auth page even if logout fails
          if (typeof window !== 'undefined') {
            window.location.href = '/auth';
          }
          throw new Error('Authentication failed. Please log in again.');
        }
      }
      
      let errorData: ApiError;
      try {
        errorData = await response.json();
        console.error(`   ├─ Error detail: ${errorData.detail}`);
        console.error(`   ├─ Error type: ${errorData.error_type || 'Unknown'}`);
        console.error(`   └─ Status code: ${errorData.status_code || response.status}`);
      } catch (jsonError) {
        console.error(`   ├─ Could not parse error JSON: ${jsonError}`);
        errorData = {
          detail: `HTTP ${response.status}: ${response.statusText}`,
          status_code: response.status
        };
        console.error(`   └─ Using fallback error: ${errorData.detail}`);
      }
      
      const error = new Error(errorData.detail || 'Request failed');
      (error as any).status = response.status;
      (error as any).errorType = errorData.error_type;
      (error as any).statusCode = response.status;
      
      console.error(`💥 API CLIENT: Throwing error for failed request`);
      throw error;
    }
    
    // Try to parse JSON response
    const contentType = response.headers.get('content-type');
    console.log(`📋 API CLIENT: Processing response data`);
    
    if (contentType?.includes('application/json')) {
      console.log(`   ├─ Parsing JSON response`);
      const jsonData = await response.json();
      console.log(`   ├─ JSON keys: ${typeof jsonData === 'object' ? Object.keys(jsonData) : 'N/A'}`);
      console.log(`   └─ Response size: ${JSON.stringify(jsonData).length} chars`);
      console.log(`✅ API CLIENT: Request completed successfully`);
      return jsonData;
    }
    
    // Return response text for non-JSON responses
    console.log(`   ├─ Parsing text response`);
    const textData = await response.text();
    console.log(`   ├─ Text length: ${textData.length} chars`);
    console.log(`   └─ Text preview: ${textData.substring(0, 100)}...`);
    console.log(`✅ API CLIENT: Request completed successfully`);
    return textData as T;
  } catch (error: any) {
    console.error(`💥 API CLIENT: Request failed for ${endpoint}`);
    console.error(`   ├─ Error type: ${error.constructor.name}`);
    console.error(`   ├─ Error message: ${error.message}`);
    console.error(`   ├─ Status: ${error.status || 'Unknown'}`);
    console.error(`   └─ Error type: ${error.errorType || 'Unknown'}`);
    console.error('Full error:', error);
    throw error;
  }
};

// Convenience methods for different HTTP verbs
export const api = {
  get: <T = any>(endpoint: string, params?: Record<string, any>) => {
    const url = params ? `${endpoint}?${new URLSearchParams(params)}` : endpoint;
    return makeRequest<T>(url, { method: 'GET' });
  },
  
  post: <T = any>(endpoint: string, data?: any) => 
    makeRequest<T>(endpoint, {
      method: 'POST',
      body: data ? JSON.stringify(data) : undefined,
    }),
  
  put: <T = any>(endpoint: string, data?: any) => 
    makeRequest<T>(endpoint, {
      method: 'PUT',
      body: data ? JSON.stringify(data) : undefined,
    }),
  
  delete: <T = any>(endpoint: string) => 
    makeRequest<T>(endpoint, { method: 'DELETE' }),
  
  patch: <T = any>(endpoint: string, data?: any) => 
    makeRequest<T>(endpoint, {
      method: 'PATCH',
      body: data ? JSON.stringify(data) : undefined,
    }),
};

// Authentication-specific API calls
export const authApi = {
  // Login with tokens (sets httpOnly cookies)
  login: (accessToken: string, refreshToken: string) => 
    api.post('/auth/login', { access_token: accessToken, refresh_token: refreshToken }),
  
  // Logout (clears all auth cookies)
  logout: () => api.post('/auth/logout'),
  
  // Get current auth status
  status: () => api.get('/auth/status'),
  
  // Verify current token
  verify: () => api.get('/auth/verify'),
  
  // Manually refresh token (usually not needed - middleware handles this)
  refresh: () => api.post('/auth/refresh'),
};

// Export the main client
export default api;
