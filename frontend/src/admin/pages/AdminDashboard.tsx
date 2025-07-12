import { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { useAuth } from '../../hooks/useAuth';
import { useAdminAuth } from '../hooks/useAdminAuth';
import { adminApi } from '../services/adminApi';
import AdminLayout from '../components/AdminLayout';
import AnalyticsCards from '../components/AnalyticsCards';
import UserTable from '../components/UserTable';
import UserModal from '../components/UserModal';
import { UpgradeModal, ExtendModal, ResetUsageModal } from '../components/ActionModals';
import type { 
  AdminUser, 
  AdminAnalytics, 
  AdminUserDetail 
} from '../types/admin.types';

/**
 * Admin Dashboard Page Component
 * Main admin interface with user management and analytics
 */
const AdminDashboard = () => {
  const navigate = useNavigate();
  const { signOut } = useAuth();
  const { isAdmin, isLoading: adminLoading, error: adminError, user } = useAdminAuth();

  // State management
  const [users, setUsers] = useState<AdminUser[]>([]);
  const [analytics, setAnalytics] = useState<AdminAnalytics | null>(null);
  const [selectedUser, setSelectedUser] = useState<AdminUserDetail | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [totalUsers, setTotalUsers] = useState(0);
  const [isActionLoading, setIsActionLoading] = useState(false);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  
  // Modal states
  const [showUserDetail, setShowUserDetail] = useState(false);
  const [showUpgradeModal, setShowUpgradeModal] = useState(false);
  const [showExtendModal, setShowExtendModal] = useState(false);
  const [showResetModal, setShowResetModal] = useState(false);

  // Redirect if not admin
  useEffect(() => {
    if (!adminLoading && !isAdmin) {
      console.log('❌ ADMIN DASHBOARD: Non-admin access blocked, redirecting to login');
      navigate('/admin/login', { 
        state: { from: { pathname: '/admin/dashboard' } }
      });
    }
  }, [isAdmin, adminLoading, navigate]);

  // Load data
  const loadData = useCallback(async () => {
    if (!isAdmin) return;

    try {
      setIsLoading(true);
      setError(null);

      const [usersResponse, analyticsResponse] = await Promise.all([
        adminApi.getUsers(currentPage, 20),
        adminApi.getAnalytics()
      ]);

      setUsers(usersResponse.users);
      setTotalPages(usersResponse.total_pages);
      setTotalUsers(usersResponse.total_users);
      setAnalytics(analyticsResponse);

      console.log(`✅ ADMIN DASHBOARD: Data loaded - ${usersResponse.users.length} users, ${analyticsResponse.total_users} total`);
    } catch (error: any) {
      console.error('❌ ADMIN DASHBOARD: Failed to load data:', error);
      setError(error.message || 'Failed to load dashboard data');
    } finally {
      setIsLoading(false);
    }
  }, [isAdmin, currentPage]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  // User management handlers
  const handleUserClick = async (userId: string) => {
    try {
      setIsActionLoading(true);
      const userDetail = await adminApi.getUserDetail(userId);
      setSelectedUser(userDetail);
      setShowUserDetail(true);
    } catch (error: any) {
      setError(`Failed to load user detail: ${error.message}`);
    } finally {
      setIsActionLoading(false);
    }
  };

  const handleUpgradeUser = async (days: number, reason: string) => {
    if (!selectedUser) return;

    try {
      setIsActionLoading(true);
      await adminApi.upgradeUser(selectedUser.user_id, 'pro', days, reason);
      setSuccessMessage(`Successfully upgraded ${selectedUser.email} to Pro for ${days} days`);
      closeAllModals();
      await loadData(); // Refresh data
    } catch (error: any) {
      setError(`Failed to upgrade user: ${error.message}`);
    } finally {
      setIsActionLoading(false);
    }
  };

  const handleDowngradeUser = async () => {
    if (!selectedUser) return;

    try {
      setIsActionLoading(true);
      await adminApi.downgradeUser(selectedUser.user_id, 'Admin manual downgrade');
      setSuccessMessage(`Successfully downgraded ${selectedUser.email} to Free`);
      closeAllModals();
      await loadData(); // Refresh data
    } catch (error: any) {
      setError(`Failed to downgrade user: ${error.message}`);
    } finally {
      setIsActionLoading(false);
    }
  };

  const handleExtendSubscription = async (days: number, reason: string) => {
    if (!selectedUser) return;

    try {
      setIsActionLoading(true);
      await adminApi.extendSubscription(selectedUser.user_id, days, reason);
      setSuccessMessage(`Successfully extended ${selectedUser.email} subscription by ${days} days`);
      closeAllModals();
      await loadData(); // Refresh data
    } catch (error: any) {
      setError(`Failed to extend subscription: ${error.message}`);
    } finally {
      setIsActionLoading(false);
    }
  };

  const handleResetUsage = async (resetMemories: boolean, resetSummaries: boolean, reason: string) => {
    if (!selectedUser) return;

    try {
      setIsActionLoading(true);
      await adminApi.resetUsage(selectedUser.user_id, resetMemories, resetSummaries, reason);
      
      const resetItems = [];
      if (resetMemories) resetItems.push('memories');
      if (resetSummaries) resetItems.push('summary pages');
      
      setSuccessMessage(`Successfully reset ${resetItems.join(' and ')} for ${selectedUser.email}`);
      closeAllModals();
      await loadData(); // Refresh data
    } catch (error: any) {
      setError(`Failed to reset usage: ${error.message}`);
    } finally {
      setIsActionLoading(false);
    }
  };

  const handleLogout = async () => {
    await signOut();
    navigate('/');
  };

  const closeAllModals = () => {
    setShowUserDetail(false);
    setShowUpgradeModal(false);
    setShowExtendModal(false);
    setShowResetModal(false);
    setSelectedUser(null);
  };

  // Open specific action modals
  const openUpgradeModal = () => {
    setShowUserDetail(false);
    setShowUpgradeModal(true);
  };

  const openExtendModal = () => {
    setShowUserDetail(false);
    setShowExtendModal(true);
  };

  const openResetModal = () => {
    setShowUserDetail(false);
    setShowResetModal(true);
  };

  // Clear messages after 5 seconds
  useEffect(() => {
    if (successMessage || error) {
      const timer = setTimeout(() => {
        setSuccessMessage(null);
        setError(null);
      }, 5000);
      return () => clearTimeout(timer);
    }
  }, [successMessage, error]);

  if (adminLoading) {
    return (
      <AdminLayout title="Admin Dashboard" user={user} onLogout={handleLogout}>
        <div className="flex-1 flex justify-center items-center">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-black mx-auto mb-4"></div>
            <p className="font-SansMono400 text-gray-600">Loading admin dashboard...</p>
          </div>
        </div>
      </AdminLayout>
    );
  }

  if (!isAdmin) {
    return null; // Will redirect via useEffect
  }

  return (
    <AdminLayout title="Admin Dashboard" user={user} onLogout={handleLogout}>
      {/* Success/Error Messages */}
      <AnimatePresence>
        {(successMessage || error || adminError) && (
          <motion.div
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            className={`mb-4 p-3 rounded-lg ${
              successMessage ? 'bg-green-100 text-green-800 border border-green-200' : 'bg-red-100 text-red-800 border border-red-200'
            }`}
          >
            <p className="font-SansMono400 text-sm">
              {successMessage || error || adminError}
            </p>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Analytics Cards */}
      <AnalyticsCards analytics={analytics} isLoading={isLoading} />

      {/* Users Table */}
      <UserTable
        users={users}
        currentPage={currentPage}
        totalPages={totalPages}
        totalUsers={totalUsers}
        onPageChange={setCurrentPage}
        onUserClick={handleUserClick}
        isLoading={isLoading}
      />

      {/* User Detail Modal */}
      <UserModal
        user={selectedUser}
        isOpen={showUserDetail}
        onClose={closeAllModals}
        onUpgrade={openUpgradeModal}
        onDowngrade={handleDowngradeUser}
        onExtend={openExtendModal}
        onResetUsage={openResetModal}
        isActionLoading={isActionLoading}
      />

      {/* Action Modals */}
      <UpgradeModal
        isOpen={showUpgradeModal}
        onClose={closeAllModals}
        onConfirm={handleUpgradeUser}
        isLoading={isActionLoading}
      />

      <ExtendModal
        isOpen={showExtendModal}
        onClose={closeAllModals}
        onConfirm={handleExtendSubscription}
        isLoading={isActionLoading}
      />

      <ResetUsageModal
        isOpen={showResetModal}
        onClose={closeAllModals}
        onConfirm={handleResetUsage}
        isLoading={isActionLoading}
      />
    </AdminLayout>
  );
};

export default AdminDashboard; 