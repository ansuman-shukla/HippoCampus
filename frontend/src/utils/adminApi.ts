import { makeAuthenticatedRequest } from './authUtils';

// Admin API interfaces matching backend schema
export interface AdminUser {
  user_id: string;
  email: string;
  full_name?: string;
  subscription_tier: 'free' | 'pro';
  subscription_status: 'active' | 'expired' | 'cancelled';
  subscription_start_date?: string;
  subscription_end_date?: string;
  total_memories_saved: number;
  monthly_summary_pages_used: number;
  created_at?: string;
  last_sign_in_at?: string;
}

export interface AdminUserListResponse {
  users: AdminUser[];
  total_users: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface AdminUserDetail extends AdminUser {
  monthly_summary_reset_date?: string;
  days_remaining?: number;
  is_expired: boolean;
}

export interface AdminAnalytics {
  total_users: number;
  free_users: number;
  pro_users: number;
  active_subscriptions: number;
  expired_subscriptions: number;
  cancelled_subscriptions: number;
  total_memories_saved: number;
  total_summary_pages_used: number;
  average_memories_per_user: number;
  conversion_rate: number;
  revenue_estimate: number;
}

export interface AdminActionResponse {
  success: boolean;
  message: string;
  user_id: string;
  action: string;
  details: Record<string, any>;
}

// Admin API service functions
export const adminApi = {
  /**
   * Get paginated list of all users with subscription details
   */
  async getUsers(page: number = 1, pageSize: number = 50): Promise<AdminUserListResponse> {
    console.log(`📊 ADMIN API: Getting users - page ${page}, size ${pageSize}`);
    
    const response = await makeAuthenticatedRequest(
      `/admin/users?page=${page}&page_size=${pageSize}`,
      { method: 'GET' }
    );
    
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || `Failed to fetch users: ${response.status}`);
    }
    
    const data = await response.json();
    console.log(`✅ ADMIN API: Users retrieved - ${data.users.length} on page, ${data.total_users} total`);
    return data;
  },

  /**
   * Get detailed subscription information for a specific user
   */
  async getUserDetail(userId: string): Promise<AdminUserDetail> {
    console.log(`👤 ADMIN API: Getting user detail for ${userId}`);
    
    const response = await makeAuthenticatedRequest(
      `/admin/users/${userId}/subscription`,
      { method: 'GET' }
    );
    
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || `Failed to fetch user detail: ${response.status}`);
    }
    
    const data = await response.json();
    console.log(`✅ ADMIN API: User detail retrieved for ${data.email}`);
    return data;
  },

  /**
   * Manually upgrade user to Pro tier
   */
  async upgradeUser(
    userId: string, 
    targetTier: 'pro' = 'pro', 
    extendDays: number = 30,
    reason: string = 'Admin manual upgrade'
  ): Promise<AdminActionResponse> {
    console.log(`⬆️ ADMIN API: Upgrading user ${userId} to ${targetTier} for ${extendDays} days`);
    
    const response = await makeAuthenticatedRequest(
      `/admin/users/${userId}/upgrade`,
      {
        method: 'POST',
        body: JSON.stringify({
          target_tier: targetTier,
          extend_days: extendDays,
          reason: reason
        })
      }
    );
    
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || `Failed to upgrade user: ${response.status}`);
    }
    
    const data = await response.json();
    console.log(`✅ ADMIN API: User upgraded successfully`);
    return data;
  },

  /**
   * Manually downgrade user to Free tier
   */
  async downgradeUser(
    userId: string, 
    reason: string = 'Admin manual downgrade'
  ): Promise<AdminActionResponse> {
    console.log(`⬇️ ADMIN API: Downgrading user ${userId}`);
    
    const response = await makeAuthenticatedRequest(
      `/admin/users/${userId}/downgrade?reason=${encodeURIComponent(reason)}`,
      { method: 'POST' }
    );
    
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || `Failed to downgrade user: ${response.status}`);
    }
    
    const data = await response.json();
    console.log(`✅ ADMIN API: User downgraded successfully`);
    return data;
  },

  /**
   * Extend user subscription end date
   */
  async extendSubscription(
    userId: string, 
    extendDays: number,
    reason: string = 'Admin manual extension'
  ): Promise<AdminActionResponse> {
    console.log(`📅 ADMIN API: Extending user ${userId} subscription by ${extendDays} days`);
    
    const response = await makeAuthenticatedRequest(
      `/admin/users/${userId}/extend`,
      {
        method: 'POST',
        body: JSON.stringify({
          extend_days: extendDays,
          reason: reason
        })
      }
    );
    
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || `Failed to extend subscription: ${response.status}`);
    }
    
    const data = await response.json();
    console.log(`✅ ADMIN API: Subscription extended successfully`);
    return data;
  },

  /**
   * Reset user usage counters
   */
  async resetUsage(
    userId: string,
    resetMemories: boolean = false,
    resetMonthlySummaries: boolean = false,
    reason: string = 'Admin manual reset'
  ): Promise<AdminActionResponse> {
    console.log(`🔄 ADMIN API: Resetting usage for user ${userId}`);
    
    const response = await makeAuthenticatedRequest(
      `/admin/users/${userId}/reset-usage`,
      {
        method: 'POST',
        body: JSON.stringify({
          reset_memories: resetMemories,
          reset_monthly_summaries: resetMonthlySummaries,
          reason: reason
        })
      }
    );
    
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || `Failed to reset usage: ${response.status}`);
    }
    
    const data = await response.json();
    console.log(`✅ ADMIN API: Usage reset successfully`);
    return data;
  },

  /**
   * Get subscription analytics and metrics
   */
  async getAnalytics(): Promise<AdminAnalytics> {
    console.log(`📊 ADMIN API: Getting subscription analytics`);
    
    const response = await makeAuthenticatedRequest(
      `/admin/analytics`,
      { method: 'GET' }
    );
    
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || `Failed to fetch analytics: ${response.status}`);
    }
    
    const data = await response.json();
    console.log(`✅ ADMIN API: Analytics retrieved - ${data.total_users} total users, ${data.conversion_rate}% conversion`);
    return data;
  },

  /**
   * Check if current user has admin privileges
   */
  async checkAdminStatus(): Promise<boolean> {
    try {
      console.log(`🔐 ADMIN API: Checking admin status`);
      
      // Try to access analytics endpoint as a simple admin check
      const response = await makeAuthenticatedRequest(
        `/admin/analytics`,
        { method: 'GET' }
      );
      
      const isAdmin = response.ok;
      console.log(`${isAdmin ? '✅' : '❌'} ADMIN API: Admin status - ${isAdmin}`);
      return isAdmin;
    } catch (error) {
      console.log(`❌ ADMIN API: Admin check failed - ${error}`);
      return false;
    }
  }
};

export default adminApi; 