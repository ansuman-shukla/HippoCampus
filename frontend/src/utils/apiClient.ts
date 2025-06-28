// API client for making authenticated requests to the backend
// Uses cookie-based authentication handled by backend middleware

const getApiBaseUrl = (): string => {
  // Always use the backend API URL for API calls
  return 'https://hippocampus-cyfo.onrender.com';
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
    
    // Backend middleware automatically handles:
    // - Token validation
    // - Token refresh when needed
    // - Setting new cookies in response headers
    // - User authentication state
    
    if (!response.ok) {
      let errorData: ApiError;
      try {
        errorData = await response.json();
      } catch {
        errorData = {
          detail: `HTTP ${response.status}: ${response.statusText}`,
          status_code: response.status
        };
      }
      
      const error = new Error(errorData.detail || 'Request failed');
      (error as any).status = response.status;
      (error as any).errorType = errorData.error_type;
      (error as any).statusCode = response.status;
      
      throw error;
    }
    
    // Try to parse JSON response
    const contentType = response.headers.get('content-type');
    if (contentType?.includes('application/json')) {
      return await response.json();
    }
    
    // Return response text for non-JSON responses
    return await response.text() as T;
  } catch (error) {
    console.error(`API request failed for ${endpoint}:`, error);
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
