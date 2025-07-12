import type { AdminUser, SubscriptionTier, SubscriptionStatus } from '../types/admin.types';

/**
 * Admin Utility Functions
 * Helper functions for admin panel operations
 */

/**
 * Format subscription status with appropriate styling
 */
export const getStatusBadgeStyle = (status: SubscriptionStatus): string => {
  switch (status) {
    case 'active':
      return 'bg-green-100 text-green-800';
    case 'expired':
      return 'bg-red-100 text-red-800';
    case 'cancelled':
      return 'bg-yellow-100 text-yellow-800';
    default:
      return 'bg-gray-100 text-gray-800';
  }
};

/**
 * Format subscription tier with appropriate styling
 */
export const getTierBadgeStyle = (tier: SubscriptionTier): string => {
  switch (tier) {
    case 'pro':
      return 'bg-green-100 text-green-800';
    case 'free':
      return 'bg-gray-100 text-gray-800';
    default:
      return 'bg-gray-100 text-gray-800';
  }
};

/**
 * Calculate days remaining for subscription
 */
export const calculateDaysRemaining = (endDate?: string): number | null => {
  if (!endDate) return null;
  
  const end = new Date(endDate);
  const now = new Date();
  const diffTime = end.getTime() - now.getTime();
  const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
  
  return diffDays;
};

/**
 * Format currency for revenue display
 */
export const formatCurrency = (amount: number): string => {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 0,
    maximumFractionDigits: 0
  }).format(amount);
};

/**
 * Format percentage for conversion rates
 */
export const formatPercentage = (value: number, decimals: number = 1): string => {
  return `${value.toFixed(decimals)}%`;
};

/**
 * Format date for display
 */
export const formatDate = (dateString?: string): string => {
  if (!dateString) return 'N/A';
  
  return new Date(dateString).toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric'
  });
};

/**
 * Format datetime for display
 */
export const formatDateTime = (dateString?: string): string => {
  if (!dateString) return 'N/A';
  
  return new Date(dateString).toLocaleString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  });
};

/**
 * Get user display name
 */
export const getUserDisplayName = (user: AdminUser): string => {
  return user.full_name || user.email.split('@')[0] || 'User';
};

/**
 * Check if user subscription is expired
 */
export const isSubscriptionExpired = (user: AdminUser): boolean => {
  if (!user.subscription_end_date || user.subscription_tier === 'free') {
    return false;
  }
  
  return new Date(user.subscription_end_date) < new Date();
};

/**
 * Get subscription status color for charts
 */
export const getSubscriptionStatusColor = (status: SubscriptionStatus): string => {
  switch (status) {
    case 'active':
      return '#10B981'; // green-500
    case 'expired':
      return '#EF4444'; // red-500
    case 'cancelled':
      return '#F59E0B'; // yellow-500
    default:
      return '#6B7280'; // gray-500
  }
};

/**
 * Sort users by different criteria
 */
export const sortUsers = (users: AdminUser[], sortBy: string, sortOrder: 'asc' | 'desc' = 'asc'): AdminUser[] => {
  return [...users].sort((a, b) => {
    let valueA: any;
    let valueB: any;
    
    switch (sortBy) {
      case 'email':
        valueA = a.email.toLowerCase();
        valueB = b.email.toLowerCase();
        break;
      case 'tier':
        valueA = a.subscription_tier;
        valueB = b.subscription_tier;
        break;
      case 'status':
        valueA = a.subscription_status;
        valueB = b.subscription_status;
        break;
      case 'memories':
        valueA = a.total_memories_saved;
        valueB = b.total_memories_saved;
        break;
      case 'summaries':
        valueA = a.monthly_summary_pages_used;
        valueB = b.monthly_summary_pages_used;
        break;
      case 'created':
        valueA = new Date(a.created_at || 0);
        valueB = new Date(b.created_at || 0);
        break;
      default:
        return 0;
    }
    
    if (valueA < valueB) return sortOrder === 'asc' ? -1 : 1;
    if (valueA > valueB) return sortOrder === 'asc' ? 1 : -1;
    return 0;
  });
};

/**
 * Filter users by search term
 */
export const filterUsers = (users: AdminUser[], searchTerm: string): AdminUser[] => {
  if (!searchTerm.trim()) return users;
  
  const term = searchTerm.toLowerCase();
  return users.filter(user => 
    user.email.toLowerCase().includes(term) ||
    user.full_name?.toLowerCase().includes(term) ||
    user.subscription_tier.toLowerCase().includes(term) ||
    user.subscription_status.toLowerCase().includes(term)
  );
};

/**
 * Generate random color for charts
 */
export const generateChartColors = (count: number): string[] => {
  const colors = [
    '#3B82F6', // blue-500
    '#10B981', // green-500
    '#F59E0B', // yellow-500
    '#EF4444', // red-500
    '#8B5CF6', // purple-500
    '#F97316', // orange-500
    '#06B6D4', // cyan-500
    '#84CC16', // lime-500
  ];
  
  const result = [];
  for (let i = 0; i < count; i++) {
    result.push(colors[i % colors.length]);
  }
  return result;
}; 