import { tokenManager } from '../supabaseClient';

interface ApiOptions {
  method?: string;
  headers?: Record<string, string>;
  body?: any;
  retryAttempts?: number;
}

interface ApiResponse<T = any> {
  success: boolean;
  data?: T;
  error?: string;
  status: number;
}

class ApiClient {
  private baseUrl: string;
  private maxRetries: number = 1;

  constructor(baseUrl: string) {
    this.baseUrl = baseUrl;
  }

  private async makeRequest(endpoint: string, options: ApiOptions = {}): Promise<Response> {
    const { access_token } = await tokenManager.getTokens();
    
    if (!access_token) {
      throw new Error('No access token available');
    }

    const url = `${this.baseUrl}${endpoint}`;
    const headers = {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${access_token}`,
      ...options.headers
    };

    const config: RequestInit = {
      method: options.method || 'GET',
      headers,
      credentials: 'include', // Include cookies for backend auth
    };

    if (options.body) {
      config.body = JSON.stringify(options.body);
    }

    return fetch(url, config);
  }

  async request<T = any>(endpoint: string, options: ApiOptions = {}): Promise<ApiResponse<T>> {
    let lastError: Error | null = null;
    const maxAttempts = options.retryAttempts ?? this.maxRetries;

    for (let attempt = 0; attempt <= maxAttempts; attempt++) {
      try {
        const response = await this.makeRequest(endpoint, options);
        
        // Handle authentication errors
        if (response.status === 401) {
          const errorData = await response.json().catch(() => ({}));
          
          // Check if it's a token expiration error that can be refreshed
          if (errorData.error_type === 'auth_error' && attempt < maxAttempts) {
            console.log(`Authentication failed on attempt ${attempt + 1}, trying to refresh token...`);
            
            // Try to refresh the token
            const refreshed = await tokenManager.refreshToken();
            
            if (refreshed) {
              console.log('Token refreshed successfully, retrying request...');
              continue; // Retry the request with new token
            } else {
              console.log('Token refresh failed, redirecting to login...');
              await tokenManager.clearTokens();
              // Redirect to login or emit event for app to handle
              window.dispatchEvent(new CustomEvent('auth:logout'));
              throw new Error('Authentication failed - please login again');
            }
          }
          
          // If it's not a retryable auth error or we've exhausted retries
          return {
            success: false,
            error: errorData.detail || 'Authentication failed',
            status: response.status
          };
        }

        // Handle other HTTP errors
        if (!response.ok) {
          const errorData = await response.json().catch(() => ({}));
          return {
            success: false,
            error: errorData.detail || errorData.message || `Request failed with status ${response.status}`,
            status: response.status
          };
        }

        // Success response
        const data = await response.json();
        return {
          success: true,
          data,
          status: response.status
        };

      } catch (error) {
        lastError = error as Error;
        console.error(`API request attempt ${attempt + 1} failed:`, error);
        
        // If this is the last attempt or it's not a network error, throw
        if (attempt === maxAttempts || !this.isRetryableError(error as Error)) {
          break;
        }
        
        // Wait before retry (exponential backoff)
        await this.delay(Math.pow(2, attempt) * 1000);
      }
    }

    // All attempts failed
    throw lastError || new Error('Request failed after all retry attempts');
  }

  private isRetryableError(error: Error): boolean {
    // Only retry network errors, not auth or validation errors
    return error.message.includes('fetch') || 
           error.message.includes('network') ||
           error.message.includes('timeout');
  }

  private delay(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  async get<T = any>(endpoint: string, options: Omit<ApiOptions, 'method'> = {}): Promise<ApiResponse<T>> {
    return this.request<T>(endpoint, { ...options, method: 'GET' });
  }

  async post<T = any>(endpoint: string, body?: any, options: Omit<ApiOptions, 'method' | 'body'> = {}): Promise<ApiResponse<T>> {
    return this.request<T>(endpoint, { ...options, method: 'POST', body });
  }

  async put<T = any>(endpoint: string, body?: any, options: Omit<ApiOptions, 'method' | 'body'> = {}): Promise<ApiResponse<T>> {
    return this.request<T>(endpoint, { ...options, method: 'PUT', body });
  }

  async delete<T = any>(endpoint: string, options: Omit<ApiOptions, 'method'> = {}): Promise<ApiResponse<T>> {
    return this.request<T>(endpoint, { ...options, method: 'DELETE' });
  }

  // Health check method
  async healthCheck(): Promise<boolean> {
    try {
      const response = await fetch(`${this.baseUrl}/health`, {
        method: 'GET',
        headers: { 'Content-Type': 'application/json' }
      });
      return response.ok;
    } catch (error) {
      console.error('Health check failed:', error);
      return false;
    }
  }

  // Get auth status
  async getAuthStatus(): Promise<any> {
    try {
      const response = await fetch(`${this.baseUrl}/auth/status`, {
        method: 'GET',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' }
      });
      
      if (response.ok) {
        return await response.json();
      }
      return null;
    } catch (error) {
      console.error('Auth status check failed:', error);
      return null;
    }
  }
}

// Create and export the API client instance
export const apiClient = new ApiClient(import.meta.env.VITE_API_URL || 'https://hippocampus-backend-vvv9.onrender.com');

export default apiClient;
