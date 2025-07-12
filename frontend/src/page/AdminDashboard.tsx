import { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { useAdminAuth } from '../hooks/useAdminAuth';
import { useAuth } from '../hooks/useAuth';
import { adminApi, AdminUser, AdminAnalytics, AdminUserDetail } from '../utils/adminApi';
import Button from '../components/Button';
import LoaderPillars from '../components/LoaderPillars';
import Logo from '../assets/Logo.svg';

// Icons (you can replace with react-icons if preferred)
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

  // Form states
  const [upgradeDays, setUpgradeDays] = useState(30);
  const [upgradeReason, setUpgradeReason] = useState('');
  const [extendDays, setExtendDays] = useState(30);
  const [extendReason, setExtendReason] = useState('');
  const [resetMemories, setResetMemories] = useState(false);
  const [resetSummaries, setResetSummaries] = useState(false);
  const [resetReason, setResetReason] = useState('');

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

  // User actions
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

  const handleUpgradeUser = async () => {
    if (!selectedUser) return;

    try {
      setIsActionLoading(true);
      await adminApi.upgradeUser(selectedUser.user_id, 'pro', upgradeDays, upgradeReason);
      setSuccessMessage(`Successfully upgraded ${selectedUser.email} to Pro`);
      setShowUpgradeModal(false);
      setShowUserDetail(false);
      await loadData(); // Refresh data
    } catch (error: any) {
      setError(`Failed to upgrade user: ${error.message}`);
    } finally {
      setIsActionLoading(false);
      setUpgradeReason('');
      setUpgradeDays(30);
    }
  };

  const handleDowngradeUser = async () => {
    if (!selectedUser) return;

    try {
      setIsActionLoading(true);
      await adminApi.downgradeUser(selectedUser.user_id, 'Admin manual downgrade');
      setSuccessMessage(`Successfully downgraded ${selectedUser.email} to Free`);
      setShowUserDetail(false);
      await loadData(); // Refresh data
    } catch (error: any) {
      setError(`Failed to downgrade user: ${error.message}`);
    } finally {
      setIsActionLoading(false);
    }
  };

  const handleExtendSubscription = async () => {
    if (!selectedUser) return;

    try {
      setIsActionLoading(true);
      await adminApi.extendSubscription(selectedUser.user_id, extendDays, extendReason);
      setSuccessMessage(`Successfully extended ${selectedUser.email} subscription by ${extendDays} days`);
      setShowExtendModal(false);
      setShowUserDetail(false);
      await loadData(); // Refresh data
    } catch (error: any) {
      setError(`Failed to extend subscription: ${error.message}`);
    } finally {
      setIsActionLoading(false);
      setExtendReason('');
      setExtendDays(30);
    }
  };

  const handleResetUsage = async () => {
    if (!selectedUser) return;

    try {
      setIsActionLoading(true);
      await adminApi.resetUsage(selectedUser.user_id, resetMemories, resetSummaries, resetReason);
      setSuccessMessage(`Successfully reset usage counters for ${selectedUser.email}`);
      setShowResetModal(false);
      setShowUserDetail(false);
      await loadData(); // Refresh data
    } catch (error: any) {
      setError(`Failed to reset usage: ${error.message}`);
    } finally {
      setIsActionLoading(false);
      setResetReason('');
      setResetMemories(false);
      setResetSummaries(false);
    }
  };

  const handleLogout = async () => {
    await signOut();
    navigate('/');
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

  if (adminLoading || isLoading) {
    return (
      <div className="max-w-6xl bg-white rounded-lg px-10 w-full min-h-[600px] flex flex-col justify-center items-center py-10 border border-black">
        <LoaderPillars />
        <p className="mt-4 font-SansMono400 text-gray-600">Loading admin dashboard...</p>
      </div>
    );
  }

  if (!isAdmin) {
    return null; // Will redirect via useEffect
  }

  return (
    <div className="max-w-6xl bg-white rounded-lg px-8 w-full min-h-[700px] flex flex-col py-8 border border-black">
      {/* Header */}
      <div className="flex justify-between items-center mb-6 border-b border-gray-200 pb-4">
        <div className="flex items-center space-x-4">
          <img src={Logo} alt="HippoCampus Logo" className="w-10 h-10" />
          <div>
            <h1 className="text-2xl font-NanumMyeongjo text-black">Admin Dashboard</h1>
            <p className="text-sm font-SansMono400 text-gray-600">
              Welcome, {user?.full_name || user?.email || 'Admin'}
            </p>
          </div>
        </div>
        <Button 
          handle={handleLogout} 
          text="LOGOUT" 
          textColor="--primary-white" 
          IncMinWidth="100px"
        />
      </div>

      {/* Success/Error Messages */}
      <AnimatePresence>
        {(successMessage || error || adminError) && (
          <motion.div
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            className={`mb-4 p-3 rounded-lg ${
              successMessage ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
            }`}
          >
            <p className="font-SansMono400 text-sm">
              {successMessage || error || adminError}
            </p>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Analytics Cards */}
      {analytics && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
          <div className="bg-blue-50 rounded-lg p-4 border border-blue-200">
            <h3 className="font-SansMono400 text-sm text-blue-800 mb-1">Total Users</h3>
            <p className="text-2xl font-NanumMyeongjo text-blue-900">{analytics.total_users}</p>
          </div>
          <div className="bg-green-50 rounded-lg p-4 border border-green-200">
            <h3 className="font-SansMono400 text-sm text-green-800 mb-1">Pro Users</h3>
            <p className="text-2xl font-NanumMyeongjo text-green-900">{analytics.pro_users}</p>
          </div>
          <div className="bg-purple-50 rounded-lg p-4 border border-purple-200">
            <h3 className="font-SansMono400 text-sm text-purple-800 mb-1">Conversion Rate</h3>
            <p className="text-2xl font-NanumMyeongjo text-purple-900">{analytics.conversion_rate.toFixed(1)}%</p>
          </div>
          <div className="bg-yellow-50 rounded-lg p-4 border border-yellow-200">
            <h3 className="font-SansMono400 text-sm text-yellow-800 mb-1">Revenue Est.</h3>
            <p className="text-2xl font-NanumMyeongjo text-yellow-900">${analytics.revenue_estimate}</p>
          </div>
        </div>
      )}

      {/* Users Table */}
      <div className="flex-1 bg-gray-50 rounded-lg p-4 border border-gray-200">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-lg font-SansMono400 text-black">Users ({totalUsers})</h2>
          <div className="flex space-x-2">
            <button
              onClick={() => setCurrentPage(Math.max(1, currentPage - 1))}
              disabled={currentPage === 1}
              className="px-3 py-1 bg-black text-white rounded font-SansMono400 text-xs disabled:opacity-50"
            >
              Previous
            </button>
            <span className="px-3 py-1 font-SansMono400 text-sm">
              Page {currentPage} of {totalPages}
            </span>
            <button
              onClick={() => setCurrentPage(Math.min(totalPages, currentPage + 1))}
              disabled={currentPage === totalPages}
              className="px-3 py-1 bg-black text-white rounded font-SansMono400 text-xs disabled:opacity-50"
            >
              Next
            </button>
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full bg-white rounded-lg overflow-hidden">
            <thead className="bg-gray-100">
              <tr>
                <th className="px-4 py-3 text-left font-SansMono400 text-sm">Email</th>
                <th className="px-4 py-3 text-left font-SansMono400 text-sm">Tier</th>
                <th className="px-4 py-3 text-left font-SansMono400 text-sm">Status</th>
                <th className="px-4 py-3 text-left font-SansMono400 text-sm">Memories</th>
                <th className="px-4 py-3 text-left font-SansMono400 text-sm">Summary Pages</th>
                <th className="px-4 py-3 text-left font-SansMono400 text-sm">Actions</th>
              </tr>
            </thead>
            <tbody>
              {users.map((user) => (
                <tr key={user.user_id} className="border-b border-gray-100 hover:bg-gray-50">
                  <td className="px-4 py-3 font-SansMono400 text-sm">{user.email}</td>
                  <td className="px-4 py-3">
                    <span className={`px-2 py-1 rounded-full text-xs font-SansMono400 ${
                      user.subscription_tier === 'pro' 
                        ? 'bg-green-100 text-green-800' 
                        : 'bg-gray-100 text-gray-800'
                    }`}>
                      {user.subscription_tier.toUpperCase()}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    <span className={`px-2 py-1 rounded-full text-xs font-SansMono400 ${
                      user.subscription_status === 'active' 
                        ? 'bg-green-100 text-green-800'
                        : user.subscription_status === 'expired'
                        ? 'bg-red-100 text-red-800'
                        : 'bg-yellow-100 text-yellow-800'
                    }`}>
                      {user.subscription_status.toUpperCase()}
                    </span>
                  </td>
                  <td className="px-4 py-3 font-SansMono400 text-sm">{user.total_memories_saved}</td>
                  <td className="px-4 py-3 font-SansMono400 text-sm">{user.monthly_summary_pages_used}</td>
                  <td className="px-4 py-3">
                    <button
                      onClick={() => handleUserClick(user.user_id)}
                      className="px-3 py-1 bg-black text-white rounded font-SansMono400 text-xs hover:bg-gray-800"
                      disabled={isActionLoading}
                    >
                      Manage
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* User Detail Modal */}
      <AnimatePresence>
        {showUserDetail && selectedUser && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50"
            onClick={() => setShowUserDetail(false)}
          >
            <motion.div
              initial={{ scale: 0.9, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.9, opacity: 0 }}
              className="bg-white rounded-lg p-6 w-full max-w-md mx-4"
              onClick={(e) => e.stopPropagation()}
            >
              <h3 className="text-lg font-NanumMyeongjo mb-4">User Management</h3>
              <div className="space-y-3 mb-6">
                <p className="font-SansMono400 text-sm"><strong>Email:</strong> {selectedUser.email}</p>
                <p className="font-SansMono400 text-sm"><strong>Name:</strong> {selectedUser.full_name || 'N/A'}</p>
                <p className="font-SansMono400 text-sm"><strong>Tier:</strong> {selectedUser.subscription_tier}</p>
                <p className="font-SansMono400 text-sm"><strong>Status:</strong> {selectedUser.subscription_status}</p>
                <p className="font-SansMono400 text-sm"><strong>Memories:</strong> {selectedUser.total_memories_saved}</p>
                <p className="font-SansMono400 text-sm"><strong>Summary Pages:</strong> {selectedUser.monthly_summary_pages_used}</p>
                {selectedUser.subscription_end_date && (
                  <p className="font-SansMono400 text-sm">
                    <strong>Expires:</strong> {new Date(selectedUser.subscription_end_date).toLocaleDateString()}
                  </p>
                )}
              </div>
              
              <div className="grid grid-cols-2 gap-2">
                {selectedUser.subscription_tier === 'free' ? (
                  <button
                    onClick={() => setShowUpgradeModal(true)}
                    className="px-3 py-2 bg-green-600 text-white rounded font-SansMono400 text-xs"
                  >
                    Upgrade to Pro
                  </button>
                ) : (
                  <button
                    onClick={handleDowngradeUser}
                    className="px-3 py-2 bg-red-600 text-white rounded font-SansMono400 text-xs"
                    disabled={isActionLoading}
                  >
                    Downgrade
                  </button>
                )}
                <button
                  onClick={() => setShowExtendModal(true)}
                  className="px-3 py-2 bg-blue-600 text-white rounded font-SansMono400 text-xs"
                >
                  Extend Sub
                </button>
                <button
                  onClick={() => setShowResetModal(true)}
                  className="px-3 py-2 bg-yellow-600 text-white rounded font-SansMono400 text-xs"
                >
                  Reset Usage
                </button>
                <button
                  onClick={() => setShowUserDetail(false)}
                  className="px-3 py-2 bg-gray-600 text-white rounded font-SansMono400 text-xs"
                >
                  Close
                </button>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Upgrade Modal */}
      <AnimatePresence>
        {showUpgradeModal && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50"
            onClick={() => setShowUpgradeModal(false)}
          >
            <motion.div
              initial={{ scale: 0.9, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.9, opacity: 0 }}
              className="bg-white rounded-lg p-6 w-full max-w-md mx-4"
              onClick={(e) => e.stopPropagation()}
            >
              <h3 className="text-lg font-NanumMyeongjo mb-4">Upgrade to Pro</h3>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-SansMono400 mb-1">Days:</label>
                  <input
                    type="number"
                    value={upgradeDays}
                    onChange={(e) => setUpgradeDays(Number(e.target.value))}
                    className="w-full border border-gray-300 rounded px-3 py-2 font-SansMono400 text-sm"
                    min="1"
                    max="365"
                  />
                </div>
                <div>
                  <label className="block text-sm font-SansMono400 mb-1">Reason:</label>
                  <input
                    type="text"
                    value={upgradeReason}
                    onChange={(e) => setUpgradeReason(e.target.value)}
                    className="w-full border border-gray-300 rounded px-3 py-2 font-SansMono400 text-sm"
                    placeholder="Admin manual upgrade"
                  />
                </div>
              </div>
              <div className="flex space-x-2 mt-6">
                <button
                  onClick={handleUpgradeUser}
                  className="flex-1 px-4 py-2 bg-green-600 text-white rounded font-SansMono400 text-sm"
                  disabled={isActionLoading}
                >
                  {isActionLoading ? 'Upgrading...' : 'Upgrade'}
                </button>
                <button
                  onClick={() => setShowUpgradeModal(false)}
                  className="flex-1 px-4 py-2 bg-gray-600 text-white rounded font-SansMono400 text-sm"
                >
                  Cancel
                </button>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Extend Modal */}
      <AnimatePresence>
        {showExtendModal && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50"
            onClick={() => setShowExtendModal(false)}
          >
            <motion.div
              initial={{ scale: 0.9, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.9, opacity: 0 }}
              className="bg-white rounded-lg p-6 w-full max-w-md mx-4"
              onClick={(e) => e.stopPropagation()}
            >
              <h3 className="text-lg font-NanumMyeongjo mb-4">Extend Subscription</h3>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-SansMono400 mb-1">Extend by (days):</label>
                  <input
                    type="number"
                    value={extendDays}
                    onChange={(e) => setExtendDays(Number(e.target.value))}
                    className="w-full border border-gray-300 rounded px-3 py-2 font-SansMono400 text-sm"
                    min="1"
                    max="365"
                  />
                </div>
                <div>
                  <label className="block text-sm font-SansMono400 mb-1">Reason:</label>
                  <input
                    type="text"
                    value={extendReason}
                    onChange={(e) => setExtendReason(e.target.value)}
                    className="w-full border border-gray-300 rounded px-3 py-2 font-SansMono400 text-sm"
                    placeholder="Admin extension"
                  />
                </div>
              </div>
              <div className="flex space-x-2 mt-6">
                <button
                  onClick={handleExtendSubscription}
                  className="flex-1 px-4 py-2 bg-blue-600 text-white rounded font-SansMono400 text-sm"
                  disabled={isActionLoading}
                >
                  {isActionLoading ? 'Extending...' : 'Extend'}
                </button>
                <button
                  onClick={() => setShowExtendModal(false)}
                  className="flex-1 px-4 py-2 bg-gray-600 text-white rounded font-SansMono400 text-sm"
                >
                  Cancel
                </button>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Reset Usage Modal */}
      <AnimatePresence>
        {showResetModal && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50"
            onClick={() => setShowResetModal(false)}
          >
            <motion.div
              initial={{ scale: 0.9, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.9, opacity: 0 }}
              className="bg-white rounded-lg p-6 w-full max-w-md mx-4"
              onClick={(e) => e.stopPropagation()}
            >
              <h3 className="text-lg font-NanumMyeongjo mb-4">Reset Usage Counters</h3>
              <div className="space-y-4">
                <div className="flex items-center space-x-2">
                  <input
                    type="checkbox"
                    id="resetMemories"
                    checked={resetMemories}
                    onChange={(e) => setResetMemories(e.target.checked)}
                    className="rounded"
                  />
                  <label htmlFor="resetMemories" className="text-sm font-SansMono400">
                    Reset Memory Counter
                  </label>
                </div>
                <div className="flex items-center space-x-2">
                  <input
                    type="checkbox"
                    id="resetSummaries"
                    checked={resetSummaries}
                    onChange={(e) => setResetSummaries(e.target.checked)}
                    className="rounded"
                  />
                  <label htmlFor="resetSummaries" className="text-sm font-SansMono400">
                    Reset Monthly Summary Counter
                  </label>
                </div>
                <div>
                  <label className="block text-sm font-SansMono400 mb-1">Reason:</label>
                  <input
                    type="text"
                    value={resetReason}
                    onChange={(e) => setResetReason(e.target.value)}
                    className="w-full border border-gray-300 rounded px-3 py-2 font-SansMono400 text-sm"
                    placeholder="Admin usage reset"
                  />
                </div>
              </div>
              <div className="flex space-x-2 mt-6">
                <button
                  onClick={handleResetUsage}
                  className="flex-1 px-4 py-2 bg-yellow-600 text-white rounded font-SansMono400 text-sm"
                  disabled={isActionLoading || (!resetMemories && !resetSummaries)}
                >
                  {isActionLoading ? 'Resetting...' : 'Reset'}
                </button>
                <button
                  onClick={() => setShowResetModal(false)}
                  className="flex-1 px-4 py-2 bg-gray-600 text-white rounded font-SansMono400 text-sm"
                >
                  Cancel
                </button>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

export default AdminDashboard; 