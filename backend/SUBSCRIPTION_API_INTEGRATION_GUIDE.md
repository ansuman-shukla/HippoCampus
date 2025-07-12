# HippoCampus Subscription API Integration Guide

## Overview

This guide provides comprehensive documentation for integrating with the HippoCampus subscription system. The API provides subscription management, admin tools, and monitoring capabilities with comprehensive authentication and authorization.

## Table of Contents

1. [Authentication](#authentication)
2. [Subscription Management](#subscription-management)
3. [Admin Interface](#admin-interface)
4. [Monitoring & Analytics](#monitoring--analytics)
5. [Error Handling](#error-handling)
6. [Code Examples](#code-examples)
7. [Best Practices](#best-practices)
8. [Testing Guide](#testing-guide)

---

## Authentication

### Overview

All subscription endpoints require user authentication via session cookies or authorization headers. Admin endpoints require additional admin privileges.

### Authentication Methods

1. **Session Cookies** (Recommended for web apps)
   - `access_token`: JWT access token (1 hour expiry)
   - `refresh_token`: JWT refresh token (7 days expiry)
   - `user_id`: User identifier for convenience

2. **Authorization Headers** (For API clients)
   ```http
   Authorization: Bearer YOUR_ACCESS_TOKEN
   ```

### Authentication Flow

```javascript
// Check authentication status
const checkAuth = async () => {
  try {
    const response = await fetch('/subscription/status', {
      method: 'GET',
      credentials: 'include' // Include cookies
    });
    
    if (response.status === 401) {
      // Redirect to login
      window.location.href = '/login';
      return;
    }
    
    const data = await response.json();
    return data;
  } catch (error) {
    console.error('Auth check failed:', error);
  }
};
```

---

## Subscription Management

### Base URL
All subscription endpoints are prefixed with `/subscription`

### Available Endpoints

#### 1. Get Subscription Status
**GET** `/subscription/status`

Retrieve current subscription information for the authenticated user.

```javascript
const getSubscriptionStatus = async () => {
  const response = await fetch('/subscription/status', {
    method: 'GET',
    credentials: 'include'
  });
  
  if (!response.ok) {
    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
  }
  
  return await response.json();
};

// Example response
{
  "user_id": "user_12345",
  "subscription_tier": "free",
  "subscription_status": "active",
  "subscription_start_date": "2024-01-01T00:00:00Z",
  "subscription_end_date": null,
  "total_memories_saved": 25,
  "monthly_summary_pages_used": 3,
  "monthly_summary_reset_date": "2024-01-01T00:00:00Z"
}
```

#### 2. Get Usage Statistics
**GET** `/subscription/usage`

Get detailed usage statistics and limits.

```javascript
const getUsageStatistics = async () => {
  const response = await fetch('/subscription/usage', {
    method: 'GET',
    credentials: 'include'
  });
  
  return await response.json();
};

// Example response
{
  "user_id": "user_12345",
  "subscription_tier": "free",
  "memories_used": 25,
  "memories_limit": 100,
  "summary_pages_used": 3,
  "summary_pages_limit": 5,
  "can_save_memory": true,
  "can_generate_summary": true,
  "monthly_reset_date": "2024-02-01T00:00:00Z",
  "memories_percentage": 25.0,
  "summary_pages_percentage": 60.0
}
```

#### 3. Upgrade to Pro
**POST** `/subscription/upgrade`

Upgrade user subscription from Free to Pro tier.

```javascript
const upgradeSubscription = async (upgradeData) => {
  const response = await fetch('/subscription/upgrade', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    credentials: 'include',
    body: JSON.stringify(upgradeData)
  });
  
  return await response.json();
};

// Example request
const upgradeData = {
  "user_id": "user_12345",
  "target_tier": "pro",
  "payment_method_id": "pm_1234567890",
  "billing_email": "user@example.com"
};

// Example response
{
  "success": true,
  "message": "Subscription upgraded to Pro successfully",
  "subscription": {
    "tier": "pro",
    "status": "active",
    "start_date": "2024-01-15T10:30:00Z",
    "end_date": "2024-02-15T10:30:00Z",
    "billing_email": "user@example.com"
  },
  "benefits": {
    "unlimited_memories": true,
    "monthly_summary_pages": 100,
    "ai_dashboard_access": true
  }
}
```

#### 4. Downgrade to Free
**POST** `/subscription/downgrade`

Cancel Pro subscription and downgrade to Free tier.

```javascript
const downgradeSubscription = async () => {
  const response = await fetch('/subscription/downgrade', {
    method: 'POST',
    credentials: 'include'
  });
  
  return await response.json();
};

// Example response
{
  "success": true,
  "message": "Subscription downgraded to Free successfully",
  "subscription": {
    "tier": "free",
    "status": "cancelled",
    "end_date": "2024-01-15T10:30:00Z"
  },
  "new_limits": {
    "memories": 100,
    "monthly_summary_pages": 5,
    "ai_dashboard_access": false
  },
  "note": "Your existing memories are preserved, but you may be limited in saving new ones."
}
```

### Subscription Limits

| Feature | Free Tier | Pro Tier |
|---------|-----------|----------|
| Memories | 100 total | Unlimited |
| Summary Pages | 5/month | 100/month |
| Priority Support | ❌ | ✅ |
| Advanced Analytics | ❌ | ✅ |

---

## Admin Interface

### Base URL
All admin endpoints are prefixed with `/admin`

### Authentication
Admin endpoints require both user authentication AND admin privileges. Check admin status:

```javascript
const checkAdminStatus = async () => {
  try {
    const response = await fetch('/admin/analytics', {
      method: 'GET',
      credentials: 'include'
    });
    
    return response.status !== 403;
  } catch (error) {
    return false;
  }
};
```

### Available Endpoints

#### 1. List All Users
**GET** `/admin/users?page=1&page_size=50`

Get paginated list of all users with subscription details.

```javascript
const getAllUsers = async (page = 1, pageSize = 50) => {
  const response = await fetch(`/admin/users?page=${page}&page_size=${pageSize}`, {
    method: 'GET',
    credentials: 'include'
  });
  
  if (response.status === 403) {
    throw new Error('Admin privileges required');
  }
  
  return await response.json();
};
```

#### 2. Get User Details
**GET** `/admin/users/{user_id}/subscription`

Get detailed subscription information for a specific user.

```javascript
const getUserDetails = async (userId) => {
  const response = await fetch(`/admin/users/${userId}/subscription`, {
    method: 'GET',
    credentials: 'include'
  });
  
  return await response.json();
};
```

#### 3. Manual User Operations

```javascript
// Upgrade user
const adminUpgradeUser = async (userId, upgradeData) => {
  const response = await fetch(`/admin/users/${userId}/upgrade`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include',
    body: JSON.stringify(upgradeData)
  });
  
  return await response.json();
};

// Downgrade user
const adminDowngradeUser = async (userId, reason) => {
  const response = await fetch(`/admin/users/${userId}/downgrade?reason=${encodeURIComponent(reason)}`, {
    method: 'POST',
    credentials: 'include'
  });
  
  return await response.json();
};

// Extend subscription
const adminExtendSubscription = async (userId, extensionData) => {
  const response = await fetch(`/admin/users/${userId}/extend`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include',
    body: JSON.stringify(extensionData)
  });
  
  return await response.json();
};

// Reset usage
const adminResetUsage = async (userId, resetData) => {
  const response = await fetch(`/admin/users/${userId}/reset-usage`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include',
    body: JSON.stringify(resetData)
  });
  
  return await response.json();
};
```

#### 4. Analytics Dashboard
**GET** `/admin/analytics`

Get comprehensive business analytics.

```javascript
const getAdminAnalytics = async () => {
  const response = await fetch('/admin/analytics', {
    method: 'GET',
    credentials: 'include'
  });
  
  return await response.json();
};

// Example response
{
  "total_users": 1250,
  "free_users": 1100,
  "pro_users": 150,
  "active_subscriptions": 140,
  "expired_subscriptions": 8,
  "cancelled_subscriptions": 2,
  "total_memories_saved": 45000,
  "total_summary_pages_used": 2500,
  "average_memories_per_user": 36.0,
  "conversion_rate": 12.0,
  "revenue_estimate": 1200.0
}
```

---

## Monitoring & Analytics

### Base URL
All monitoring endpoints are prefixed with `/monitoring`

### Available Endpoints

#### 1. Health Check
**GET** `/monitoring/health`

Check system health status (public endpoint).

```javascript
const checkSystemHealth = async () => {
  const response = await fetch('/monitoring/health');
  return await response.json();
};
```

#### 2. Monitoring Metrics (Admin Only)

```javascript
// Memory usage patterns
const getMemoryUsage = async (daysBack = 30) => {
  const response = await fetch(`/monitoring/metrics/memory-usage?days_back=${daysBack}`, {
    credentials: 'include'
  });
  return await response.json();
};

// Summary generation trends
const getSummaryTrends = async (daysBack = 30) => {
  const response = await fetch(`/monitoring/metrics/summary-trends?days_back=${daysBack}`, {
    credentials: 'include'
  });
  return await response.json();
};

// Conversion rates
const getConversionRates = async (daysBack = 30) => {
  const response = await fetch(`/monitoring/metrics/conversion-rates?days_back=${daysBack}`, {
    credentials: 'include'
  });
  return await response.json();
};

// Comprehensive report
const getComprehensiveReport = async (daysBack = 30) => {
  const response = await fetch(`/monitoring/metrics/comprehensive?days_back=${daysBack}`, {
    credentials: 'include'
  });
  return await response.json();
};
```

#### 3. Dashboard Data
**GET** `/monitoring/dashboard`

Get optimized data for dashboard display.

```javascript
const getDashboardData = async () => {
  const response = await fetch('/monitoring/dashboard', {
    credentials: 'include'
  });
  return await response.json();
};
```

---

## Error Handling

### Common HTTP Status Codes

| Status | Meaning | Action |
|--------|---------|--------|
| 200 | Success | Process response |
| 400 | Bad Request | Check request parameters |
| 401 | Unauthorized | Redirect to login |
| 402 | Payment Required | Show upgrade prompt |
| 403 | Forbidden | Show access denied |
| 404 | Not Found | Handle missing resource |
| 500 | Server Error | Show error message |

### Error Response Format

```javascript
// Standard error response
{
  "detail": "Error message",
  "error_type": "auth_error",
  "status_code": 401
}

// Subscription limit error (402)
{
  "detail": "Memory limit exceeded. Upgrade to Pro for unlimited memories.",
  "error_type": "subscription_limit",
  "status_code": 402,
  "upgrade_info": {
    "current_tier": "free",
    "limit_type": "memories",
    "current_usage": 100,
    "limit": 100
  }
}
```

### Error Handling Example

```javascript
const handleApiError = (error, response) => {
  switch (response.status) {
    case 401:
      // Redirect to login
      window.location.href = '/login';
      break;
      
    case 402:
      // Show upgrade prompt
      showUpgradeModal(error.upgrade_info);
      break;
      
    case 403:
      // Show access denied
      showErrorMessage('You do not have permission to access this resource.');
      break;
      
    case 500:
      // Show generic error
      showErrorMessage('An unexpected error occurred. Please try again later.');
      break;
      
    default:
      showErrorMessage(error.detail || 'An error occurred');
  }
};

const apiCall = async (url, options) => {
  try {
    const response = await fetch(url, options);
    
    if (!response.ok) {
      const error = await response.json();
      handleApiError(error, response);
      return null;
    }
    
    return await response.json();
  } catch (error) {
    console.error('API call failed:', error);
    showErrorMessage('Network error. Please check your connection.');
    return null;
  }
};
```

---

## Code Examples

### React Integration

```jsx
import React, { useState, useEffect } from 'react';

const SubscriptionDashboard = () => {
  const [subscriptionData, setSubscriptionData] = useState(null);
  const [usageData, setUsageData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loadSubscriptionData = async () => {
      try {
        const [subscription, usage] = await Promise.all([
          fetch('/subscription/status', { credentials: 'include' }),
          fetch('/subscription/usage', { credentials: 'include' })
        ]);

        if (subscription.ok && usage.ok) {
          setSubscriptionData(await subscription.json());
          setUsageData(await usage.json());
        }
      } catch (error) {
        console.error('Failed to load subscription data:', error);
      } finally {
        setLoading(false);
      }
    };

    loadSubscriptionData();
  }, []);

  const handleUpgrade = async () => {
    const upgradeData = {
      user_id: subscriptionData.user_id,
      target_tier: "pro",
      payment_method_id: "pm_example",
      billing_email: "user@example.com"
    };

    const response = await fetch('/subscription/upgrade', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify(upgradeData)
    });

    if (response.ok) {
      // Reload subscription data
      window.location.reload();
    }
  };

  if (loading) return <div>Loading...</div>;

  return (
    <div className="subscription-dashboard">
      <h2>Subscription Status</h2>
      <div className="tier-info">
        <p>Current Tier: {subscriptionData?.subscription_tier}</p>
        <p>Status: {subscriptionData?.subscription_status}</p>
      </div>

      <div className="usage-info">
        <h3>Usage Statistics</h3>
        <div className="usage-item">
          <span>Memories: {usageData?.memories_used}/{usageData?.memories_limit === -1 ? 'Unlimited' : usageData?.memories_limit}</span>
          <div className="progress-bar">
            <div 
              className="progress-fill" 
              style={{ width: `${usageData?.memories_percentage || 0}%` }}
            />
          </div>
        </div>
        
        <div className="usage-item">
          <span>Summary Pages: {usageData?.summary_pages_used}/{usageData?.summary_pages_limit}</span>
          <div className="progress-bar">
            <div 
              className="progress-fill" 
              style={{ width: `${usageData?.summary_pages_percentage || 0}%` }}
            />
          </div>
        </div>
      </div>

      {subscriptionData?.subscription_tier === 'free' && (
        <button onClick={handleUpgrade} className="upgrade-button">
          Upgrade to Pro - $8/month
        </button>
      )}
    </div>
  );
};

export default SubscriptionDashboard;
```

### Vue.js Integration

```vue
<template>
  <div class="subscription-panel">
    <div v-if="loading">Loading...</div>
    <div v-else>
      <h3>{{ subscription.subscription_tier.toUpperCase() }} Plan</h3>
      
      <div class="usage-stats">
        <div class="stat">
          <label>Memories</label>
          <div class="stat-bar">
            <div 
              class="stat-fill" 
              :style="{ width: usage.memories_percentage + '%' }"
            ></div>
          </div>
          <span>{{ usage.memories_used }}/{{ usage.memories_limit === -1 ? '∞' : usage.memories_limit }}</span>
        </div>
        
        <div class="stat">
          <label>Summary Pages</label>
          <div class="stat-bar">
            <div 
              class="stat-fill" 
              :style="{ width: usage.summary_pages_percentage + '%' }"
            ></div>
          </div>
          <span>{{ usage.summary_pages_used }}/{{ usage.summary_pages_limit }}</span>
        </div>
      </div>

      <button 
        v-if="subscription.subscription_tier === 'free'" 
        @click="upgradeToPro"
        class="upgrade-btn"
      >
        Upgrade to Pro
      </button>
    </div>
  </div>
</template>

<script>
export default {
  name: 'SubscriptionPanel',
  data() {
    return {
      subscription: null,
      usage: null,
      loading: true
    };
  },
  async mounted() {
    await this.loadData();
  },
  methods: {
    async loadData() {
      try {
        const [subResponse, usageResponse] = await Promise.all([
          this.$http.get('/subscription/status'),
          this.$http.get('/subscription/usage')
        ]);
        
        this.subscription = subResponse.data;
        this.usage = usageResponse.data;
      } catch (error) {
        console.error('Failed to load subscription data:', error);
      } finally {
        this.loading = false;
      }
    },
    
    async upgradeToPro() {
      try {
        const response = await this.$http.post('/subscription/upgrade', {
          user_id: this.subscription.user_id,
          target_tier: 'pro',
          payment_method_id: 'pm_example',
          billing_email: 'user@example.com'
        });
        
        if (response.data.success) {
          await this.loadData(); // Refresh data
          this.$emit('upgrade-success');
        }
      } catch (error) {
        console.error('Upgrade failed:', error);
        this.$emit('upgrade-error', error);
      }
    }
  }
};
</script>
```

---

## Best Practices

### 1. Authentication Management

```javascript
class AuthManager {
  constructor() {
    this.retryCount = 0;
    this.maxRetries = 3;
  }

  async makeAuthenticatedRequest(url, options = {}) {
    const defaultOptions = {
      credentials: 'include',
      headers: {
        'Content-Type': 'application/json',
        ...options.headers
      },
      ...options
    };

    try {
      const response = await fetch(url, defaultOptions);
      
      if (response.status === 401 && this.retryCount < this.maxRetries) {
        this.retryCount++;
        // Token might be expired, try to refresh
        await this.refreshTokens();
        return this.makeAuthenticatedRequest(url, options);
      }
      
      this.retryCount = 0; // Reset on success
      return response;
    } catch (error) {
      console.error('Request failed:', error);
      throw error;
    }
  }

  async refreshTokens() {
    // Implement token refresh logic
    const response = await fetch('/auth/refresh', {
      method: 'POST',
      credentials: 'include'
    });
    
    if (!response.ok) {
      // Refresh failed, redirect to login
      window.location.href = '/login';
    }
  }
}
```

### 2. Subscription State Management

```javascript
class SubscriptionStore {
  constructor() {
    this.state = {
      subscription: null,
      usage: null,
      loading: false,
      error: null
    };
    this.listeners = [];
  }

  subscribe(listener) {
    this.listeners.push(listener);
    return () => {
      const index = this.listeners.indexOf(listener);
      if (index > -1) {
        this.listeners.splice(index, 1);
      }
    };
  }

  notify() {
    this.listeners.forEach(listener => listener(this.state));
  }

  async loadSubscriptionData() {
    this.state.loading = true;
    this.notify();

    try {
      const [subscription, usage] = await Promise.all([
        this.fetchSubscription(),
        this.fetchUsage()
      ]);

      this.state.subscription = subscription;
      this.state.usage = usage;
      this.state.error = null;
    } catch (error) {
      this.state.error = error.message;
    } finally {
      this.state.loading = false;
      this.notify();
    }
  }

  async fetchSubscription() {
    const response = await fetch('/subscription/status', {
      credentials: 'include'
    });
    
    if (!response.ok) {
      throw new Error(`Failed to fetch subscription: ${response.statusText}`);
    }
    
    return response.json();
  }

  async fetchUsage() {
    const response = await fetch('/subscription/usage', {
      credentials: 'include'
    });
    
    if (!response.ok) {
      throw new Error(`Failed to fetch usage: ${response.statusText}`);
    }
    
    return response.json();
  }
}
```

### 3. Error Boundary Implementation

```jsx
class SubscriptionErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    console.error('Subscription component error:', error, errorInfo);
    
    // Report to monitoring service
    if (window.analytics) {
      window.analytics.track('Subscription Error', {
        error: error.message,
        stack: error.stack,
        component: errorInfo.componentStack
      });
    }
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="error-fallback">
          <h3>Something went wrong with the subscription system</h3>
          <p>Please refresh the page or contact support if the problem persists.</p>
          <button onClick={() => window.location.reload()}>
            Refresh Page
          </button>
        </div>
      );
    }

    return this.props.children;
  }
}
```

---

## Testing Guide

### Unit Tests

```javascript
// Jest tests for subscription API
describe('Subscription API', () => {
  beforeEach(() => {
    fetch.resetMocks();
  });

  test('should fetch subscription status', async () => {
    const mockResponse = {
      user_id: 'test_user',
      subscription_tier: 'free',
      total_memories_saved: 25
    };

    fetch.mockResponseOnce(JSON.stringify(mockResponse));

    const result = await getSubscriptionStatus();
    
    expect(fetch).toHaveBeenCalledWith('/subscription/status', {
      method: 'GET',
      credentials: 'include'
    });
    
    expect(result).toEqual(mockResponse);
  });

  test('should handle subscription upgrade', async () => {
    const upgradeData = {
      user_id: 'test_user',
      target_tier: 'pro'
    };

    const mockResponse = {
      success: true,
      message: 'Subscription upgraded successfully'
    };

    fetch.mockResponseOnce(JSON.stringify(mockResponse));

    const result = await upgradeSubscription(upgradeData);
    
    expect(fetch).toHaveBeenCalledWith('/subscription/upgrade', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify(upgradeData)
    });
    
    expect(result.success).toBe(true);
  });

  test('should handle 402 payment required error', async () => {
    const errorResponse = {
      detail: 'Memory limit exceeded',
      error_type: 'subscription_limit',
      status_code: 402
    };

    fetch.mockRejectOnce(new Response(JSON.stringify(errorResponse), {
      status: 402
    }));

    try {
      await getSubscriptionStatus();
    } catch (error) {
      expect(error.status).toBe(402);
    }
  });
});
```

### Integration Tests

```javascript
// Cypress integration tests
describe('Subscription Flow', () => {
  beforeEach(() => {
    cy.login('test@example.com', 'password');
  });

  it('should display subscription status', () => {
    cy.visit('/dashboard');
    
    cy.intercept('GET', '/subscription/status', {
      fixture: 'subscription-free.json'
    }).as('getStatus');
    
    cy.intercept('GET', '/subscription/usage', {
      fixture: 'usage-free.json'
    }).as('getUsage');
    
    cy.wait(['@getStatus', '@getUsage']);
    
    cy.get('[data-testid="subscription-tier"]').should('contain', 'FREE');
    cy.get('[data-testid="memories-used"]').should('contain', '25/100');
    cy.get('[data-testid="upgrade-button"]').should('be.visible');
  });

  it('should upgrade subscription', () => {
    cy.visit('/dashboard');
    
    cy.intercept('POST', '/subscription/upgrade', {
      fixture: 'upgrade-success.json'
    }).as('upgrade');
    
    cy.get('[data-testid="upgrade-button"]').click();
    cy.get('[data-testid="payment-form"]').should('be.visible');
    
    // Fill payment form
    cy.get('[data-testid="billing-email"]').type('test@example.com');
    cy.get('[data-testid="payment-method"]').select('Credit Card');
    
    cy.get('[data-testid="confirm-upgrade"]').click();
    
    cy.wait('@upgrade');
    
    cy.get('[data-testid="success-message"]').should('be.visible');
    cy.get('[data-testid="subscription-tier"]').should('contain', 'PRO');
  });

  it('should handle upgrade errors', () => {
    cy.visit('/dashboard');
    
    cy.intercept('POST', '/subscription/upgrade', {
      statusCode: 402,
      body: { detail: 'Payment failed' }
    }).as('upgradeError');
    
    cy.get('[data-testid="upgrade-button"]').click();
    cy.get('[data-testid="confirm-upgrade"]').click();
    
    cy.wait('@upgradeError');
    
    cy.get('[data-testid="error-message"]').should('contain', 'Payment failed');
  });
});
```

---

## API Reference Quick Links

### Subscription Endpoints
- `GET /subscription/status` - Get subscription status
- `GET /subscription/usage` - Get usage statistics  
- `POST /subscription/upgrade` - Upgrade to Pro
- `POST /subscription/downgrade` - Downgrade to Free

### Admin Endpoints
- `GET /admin/users` - List all users
- `GET /admin/users/{id}/subscription` - Get user details
- `POST /admin/users/{id}/upgrade` - Admin upgrade user
- `POST /admin/users/{id}/downgrade` - Admin downgrade user
- `POST /admin/users/{id}/extend` - Extend subscription
- `POST /admin/users/{id}/reset-usage` - Reset usage counters
- `GET /admin/analytics` - Get analytics

### Monitoring Endpoints
- `GET /monitoring/health` - System health check
- `GET /monitoring/metrics/memory-usage` - Memory usage patterns
- `GET /monitoring/metrics/summary-trends` - Summary trends
- `GET /monitoring/metrics/conversion-rates` - Conversion analytics
- `GET /monitoring/dashboard` - Dashboard data
- `GET /monitoring/alerts` - Active alerts
- `POST /monitoring/cache/clear` - Clear cache

---

## Support & Documentation

- **API Documentation**: Available at `/docs` (Swagger UI) and `/redoc` (ReDoc)
- **Health Check**: `/monitoring/health` for system status
- **Support Email**: support@hippocampus.ai
- **Status Page**: Coming soon

For additional help or questions about integration, please contact our development team or refer to the interactive API documentation at `/docs`. 