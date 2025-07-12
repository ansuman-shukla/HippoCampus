import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import type { UserModalProps } from '../types/admin.types';
import { 
  formatDate, 
  getUserDisplayName, 
  getTierBadgeStyle, 
  getStatusBadgeStyle,
  calculateDaysRemaining 
} from '../utils/adminHelpers';

/**
 * User Detail Modal Component
 * Displays detailed user information and management actions
 */
const UserModal: React.FC<UserModalProps> = ({
  user,
  isOpen,
  onClose,
  onUpgrade,
  onDowngrade,
  onExtend,
  onResetUsage,
  isActionLoading
}) => {
  if (!user) return null;

  const daysRemaining = calculateDaysRemaining(user.subscription_end_date);
  const isExpired = user.subscription_status === 'expired' || (daysRemaining !== null && daysRemaining <= 0);

  return (
    <AnimatePresence>
      {isOpen && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50"
          onClick={onClose}
        >
          <motion.div
            initial={{ scale: 0.9, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            exit={{ scale: 0.9, opacity: 0 }}
            className="bg-white rounded-lg p-6 w-full max-w-lg mx-4 max-h-[90vh] overflow-y-auto"
            onClick={(e) => e.stopPropagation()}
          >
            {/* Header */}
            <div className="flex justify-between items-start mb-6">
              <div>
                <h3 className="text-xl font-NanumMyeongjo text-black mb-1">
                  User Management
                </h3>
                <p className="text-sm font-SansMono400 text-gray-600">
                  {getUserDisplayName(user)}
                </p>
              </div>
              <button
                onClick={onClose}
                className="text-gray-400 hover:text-gray-600 text-xl"
              >
                ✕
              </button>
            </div>

            {/* User Information */}
            <div className="bg-gray-50 rounded-lg p-4 mb-6">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-3">
                  <div>
                    <label className="block text-xs font-SansMono400 text-gray-500 uppercase tracking-wide">
                      Email
                    </label>
                    <p className="font-SansMono400 text-sm text-black">{user.email}</p>
                  </div>
                  
                  <div>
                    <label className="block text-xs font-SansMono400 text-gray-500 uppercase tracking-wide">
                      Full Name
                    </label>
                    <p className="font-SansMono400 text-sm text-black">{user.full_name || 'N/A'}</p>
                  </div>

                  <div>
                    <label className="block text-xs font-SansMono400 text-gray-500 uppercase tracking-wide">
                      User ID
                    </label>
                    <p className="font-SansMono400 text-xs text-gray-700 font-mono">{user.user_id}</p>
                  </div>
                </div>

                <div className="space-y-3">
                  <div>
                    <label className="block text-xs font-SansMono400 text-gray-500 uppercase tracking-wide">
                      Subscription Tier
                    </label>
                    <span className={`inline-block px-2 py-1 rounded-full text-xs font-SansMono400 ${getTierBadgeStyle(user.subscription_tier)}`}>
                      {user.subscription_tier.toUpperCase()}
                    </span>
                  </div>

                  <div>
                    <label className="block text-xs font-SansMono400 text-gray-500 uppercase tracking-wide">
                      Status
                    </label>
                    <span className={`inline-block px-2 py-1 rounded-full text-xs font-SansMono400 ${getStatusBadgeStyle(user.subscription_status)}`}>
                      {user.subscription_status.toUpperCase()}
                    </span>
                  </div>

                  <div>
                    <label className="block text-xs font-SansMono400 text-gray-500 uppercase tracking-wide">
                      Member Since
                    </label>
                    <p className="font-SansMono400 text-sm text-black">{formatDate(user.created_at)}</p>
                  </div>
                </div>
              </div>
            </div>

            {/* Subscription Details */}
            <div className="bg-blue-50 rounded-lg p-4 mb-6 border border-blue-200">
              <h4 className="font-SansMono400 text-sm text-blue-800 mb-3">Subscription Details</h4>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <div>
                    <label className="block text-xs font-SansMono400 text-blue-600 uppercase tracking-wide">
                      Start Date
                    </label>
                    <p className="font-SansMono400 text-sm text-blue-900">
                      {formatDate(user.subscription_start_date)}
                    </p>
                  </div>
                  
                  <div>
                    <label className="block text-xs font-SansMono400 text-blue-600 uppercase tracking-wide">
                      End Date
                    </label>
                    <p className="font-SansMono400 text-sm text-blue-900">
                      {formatDate(user.subscription_end_date)}
                    </p>
                  </div>
                </div>

                <div className="space-y-2">
                  {daysRemaining !== null && (
                    <div>
                      <label className="block text-xs font-SansMono400 text-blue-600 uppercase tracking-wide">
                        Days Remaining
                      </label>
                      <p className={`font-SansMono400 text-sm ${isExpired ? 'text-red-600' : 'text-blue-900'}`}>
                        {isExpired ? 'Expired' : `${daysRemaining} days`}
                      </p>
                    </div>
                  )}
                  
                  <div>
                    <label className="block text-xs font-SansMono400 text-blue-600 uppercase tracking-wide">
                      Last Reset
                    </label>
                    <p className="font-SansMono400 text-sm text-blue-900">
                      {formatDate(user.monthly_summary_reset_date)}
                    </p>
                  </div>
                </div>
              </div>
            </div>

            {/* Usage Statistics */}
            <div className="bg-green-50 rounded-lg p-4 mb-6 border border-green-200">
              <h4 className="font-SansMono400 text-sm text-green-800 mb-3">Usage Statistics</h4>
              <div className="grid grid-cols-2 gap-4">
                <div className="text-center">
                  <div className="text-2xl font-NanumMyeongjo text-green-900">
                    {user.total_memories_saved.toLocaleString()}
                  </div>
                  <div className="text-xs font-SansMono400 text-green-700">
                    Total Memories
                  </div>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-NanumMyeongjo text-green-900">
                    {user.monthly_summary_pages_used.toLocaleString()}
                  </div>
                  <div className="text-xs font-SansMono400 text-green-700">
                    Monthly Summary Pages
                  </div>
                </div>
              </div>
            </div>

            {/* Action Buttons */}
            <div className="space-y-3">
              <div className="grid grid-cols-2 gap-3">
                {user.subscription_tier === 'free' ? (
                  <button
                    onClick={onUpgrade}
                    disabled={isActionLoading}
                    className="px-4 py-2 bg-green-600 text-white rounded font-SansMono400 text-sm hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                  >
                    {isActionLoading ? 'Processing...' : 'Upgrade to Pro'}
                  </button>
                ) : (
                  <button
                    onClick={onDowngrade}
                    disabled={isActionLoading}
                    className="px-4 py-2 bg-red-600 text-white rounded font-SansMono400 text-sm hover:bg-red-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                  >
                    {isActionLoading ? 'Processing...' : 'Downgrade to Free'}
                  </button>
                )}

                <button
                  onClick={onExtend}
                  disabled={isActionLoading}
                  className="px-4 py-2 bg-blue-600 text-white rounded font-SansMono400 text-sm hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                  {isActionLoading ? 'Processing...' : 'Extend Subscription'}
                </button>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <button
                  onClick={onResetUsage}
                  disabled={isActionLoading}
                  className="px-4 py-2 bg-yellow-600 text-white rounded font-SansMono400 text-sm hover:bg-yellow-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                  {isActionLoading ? 'Processing...' : 'Reset Usage'}
                </button>

                <button
                  onClick={onClose}
                  className="px-4 py-2 bg-gray-600 text-white rounded font-SansMono400 text-sm hover:bg-gray-700 transition-colors"
                >
                  Close
                </button>
              </div>
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
};

export default UserModal; 