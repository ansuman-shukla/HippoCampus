// Admin Panel Type Definitions
// Comprehensive TypeScript interfaces for admin functionality

// Core User Types
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

export interface AdminUserDetail extends AdminUser {
  monthly_summary_reset_date?: string;
  days_remaining?: number;
  is_expired: boolean;
}

// API Response Types
export interface AdminUserListResponse {
  users: AdminUser[];
  total_users: number;
  page: number;
  page_size: number;
  total_pages: number;
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

// Component Props Types
export interface UserTableProps {
  users: AdminUser[];
  currentPage: number;
  totalPages: number;
  totalUsers: number;
  onPageChange: (page: number) => void;
  onUserClick: (userId: string) => void;
  isLoading?: boolean;
}

export interface AnalyticsCardsProps {
  analytics: AdminAnalytics | null;
  isLoading?: boolean;
}

export interface UserModalProps {
  user: AdminUserDetail | null;
  isOpen: boolean;
  onClose: () => void;
  onUpgrade: () => void;
  onDowngrade: () => void;
  onExtend: () => void;
  onResetUsage: () => void;
  isActionLoading?: boolean;
}

// Action Modal Types
export interface UpgradeModalProps {
  isOpen: boolean;
  onClose: () => void;
  onConfirm: (days: number, reason: string) => void;
  isLoading?: boolean;
}

export interface ExtendModalProps {
  isOpen: boolean;
  onClose: () => void;
  onConfirm: (days: number, reason: string) => void;
  isLoading?: boolean;
}

export interface ResetUsageModalProps {
  isOpen: boolean;
  onClose: () => void;
  onConfirm: (resetMemories: boolean, resetSummaries: boolean, reason: string) => void;
  isLoading?: boolean;
}

// Authentication Types
export interface AdminAuthState {
  isAdmin: boolean;
  isLoading: boolean;
  error: string | null;
  isAuthenticated: boolean;
}

export interface AdminLoginFormData {
  email: string;
  password: string;
}

// Layout Types
export interface AdminLayoutProps {
  children: React.ReactNode;
  title?: string;
  user?: any;
  onLogout: () => void;
}

// Utility Types
export type SubscriptionTier = 'free' | 'pro';
export type SubscriptionStatus = 'active' | 'expired' | 'cancelled';
export type AdminAction = 'upgrade' | 'downgrade' | 'extend' | 'reset'; 