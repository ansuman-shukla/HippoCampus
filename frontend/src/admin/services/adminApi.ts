import { makeAuthenticatedRequest } from '../../utils/authUtils';
import type {
  AdminUserListResponse,
  AdminUserDetail,
  AdminAnalytics,
  AdminActionResponse
} from '../types/admin.types';

/**
 * Admin API Service
 * Comprehensive service for all admin panel operations
 */
export class AdminApiService {
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
  }

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
  }

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
  }

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
  }

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
  }

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
  }

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
  }

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
}

// Export singleton instance
export const adminApi = new AdminApiService();
export default adminApi; 