import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import type { 
  UpgradeModalProps, 
  ExtendModalProps, 
  ResetUsageModalProps 
} from '../types/admin.types';

/**
 * Upgrade Modal Component
 * Handles user upgrade to Pro tier with customizable parameters
 */
export const UpgradeModal: React.FC<UpgradeModalProps> = ({
  isOpen,
  onClose,
  onConfirm,
  isLoading
}) => {
  const [days, setDays] = useState(30);
  const [reason, setReason] = useState('Admin manual upgrade');

  const handleConfirm = () => {
    onConfirm(days, reason);
  };

  const handleClose = () => {
    setDays(30);
    setReason('Admin manual upgrade');
    onClose();
  };

  return (
    <AnimatePresence>
      {isOpen && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50"
          onClick={handleClose}
        >
          <motion.div
            initial={{ scale: 0.9, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            exit={{ scale: 0.9, opacity: 0 }}
            className="bg-white rounded-lg p-6 w-full max-w-md mx-4"
            onClick={(e) => e.stopPropagation()}
          >
            <h3 className="text-lg font-NanumMyeongjo mb-4">Upgrade User to Pro</h3>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-SansMono400 mb-2">
                  Subscription Duration (days):
                </label>
                <input
                  type="number"
                  value={days}
                  onChange={(e) => setDays(Number(e.target.value))}
                  className="w-full border border-gray-300 rounded px-3 py-2 font-SansMono400 text-sm focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-transparent"
                  min="1"
                  max="365"
                  disabled={isLoading}
                />
                <p className="text-xs text-gray-500 mt-1">
                  Pro subscription will be active for {days} days
                </p>
              </div>
              
              <div>
                <label className="block text-sm font-SansMono400 mb-2">
                  Reason for Upgrade:
                </label>
                <input
                  type="text"
                  value={reason}
                  onChange={(e) => setReason(e.target.value)}
                  className="w-full border border-gray-300 rounded px-3 py-2 font-SansMono400 text-sm focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-transparent"
                  placeholder="Enter reason for manual upgrade"
                  disabled={isLoading}
                />
              </div>

              <div className="bg-green-50 rounded-lg p-3 border border-green-200">
                <h4 className="font-SansMono400 text-sm text-green-800 mb-2">Pro Benefits:</h4>
                <ul className="text-xs font-SansMono400 text-green-700 space-y-1">
                  <li>• Unlimited memory saves</li>
                  <li>• Up to 100 summary pages per month</li>
                  <li>• Priority support</li>
                </ul>
              </div>
            </div>
            
            <div className="flex space-x-3 mt-6">
              <button
                onClick={handleConfirm}
                disabled={isLoading || !reason.trim()}
                className="flex-1 px-4 py-2 bg-green-600 text-white rounded font-SansMono400 text-sm hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                {isLoading ? 'Upgrading...' : 'Upgrade User'}
              </button>
              <button
                onClick={handleClose}
                disabled={isLoading}
                className="flex-1 px-4 py-2 bg-gray-600 text-white rounded font-SansMono400 text-sm hover:bg-gray-700 disabled:opacity-50 transition-colors"
              >
                Cancel
              </button>
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
};

/**
 * Extend Subscription Modal Component
 * Handles extending user subscription end date
 */
export const ExtendModal: React.FC<ExtendModalProps> = ({
  isOpen,
  onClose,
  onConfirm,
  isLoading
}) => {
  const [days, setDays] = useState(30);
  const [reason, setReason] = useState('Admin manual extension');

  const handleConfirm = () => {
    onConfirm(days, reason);
  };

  const handleClose = () => {
    setDays(30);
    setReason('Admin manual extension');
    onClose();
  };

  return (
    <AnimatePresence>
      {isOpen && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50"
          onClick={handleClose}
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
                <label className="block text-sm font-SansMono400 mb-2">
                  Extend by (days):
                </label>
                <input
                  type="number"
                  value={days}
                  onChange={(e) => setDays(Number(e.target.value))}
                  className="w-full border border-gray-300 rounded px-3 py-2 font-SansMono400 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  min="1"
                  max="365"
                  disabled={isLoading}
                />
                <p className="text-xs text-gray-500 mt-1">
                  Subscription will be extended by {days} days from current end date
                </p>
              </div>
              
              <div>
                <label className="block text-sm font-SansMono400 mb-2">
                  Reason for Extension:
                </label>
                <input
                  type="text"
                  value={reason}
                  onChange={(e) => setReason(e.target.value)}
                  className="w-full border border-gray-300 rounded px-3 py-2 font-SansMono400 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="Enter reason for extension"
                  disabled={isLoading}
                />
              </div>

              <div className="bg-blue-50 rounded-lg p-3 border border-blue-200">
                <p className="text-xs font-SansMono400 text-blue-700">
                  <strong>Note:</strong> Extension will add {days} days to the current subscription end date, 
                  regardless of whether it has expired or not.
                </p>
              </div>
            </div>
            
            <div className="flex space-x-3 mt-6">
              <button
                onClick={handleConfirm}
                disabled={isLoading || !reason.trim()}
                className="flex-1 px-4 py-2 bg-blue-600 text-white rounded font-SansMono400 text-sm hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                {isLoading ? 'Extending...' : 'Extend Subscription'}
              </button>
              <button
                onClick={handleClose}
                disabled={isLoading}
                className="flex-1 px-4 py-2 bg-gray-600 text-white rounded font-SansMono400 text-sm hover:bg-gray-700 disabled:opacity-50 transition-colors"
              >
                Cancel
              </button>
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
};

/**
 * Reset Usage Modal Component
 * Handles resetting user usage counters
 */
export const ResetUsageModal: React.FC<ResetUsageModalProps> = ({
  isOpen,
  onClose,
  onConfirm,
  isLoading
}) => {
  const [resetMemories, setResetMemories] = useState(false);
  const [resetSummaries, setResetSummaries] = useState(false);
  const [reason, setReason] = useState('Admin manual reset');

  const handleConfirm = () => {
    onConfirm(resetMemories, resetSummaries, reason);
  };

  const handleClose = () => {
    setResetMemories(false);
    setResetSummaries(false);
    setReason('Admin manual reset');
    onClose();
  };

  const canConfirm = (resetMemories || resetSummaries) && reason.trim();

  return (
    <AnimatePresence>
      {isOpen && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50"
          onClick={handleClose}
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
              <div className="space-y-3">
                <p className="text-sm font-SansMono400 text-gray-700 mb-3">
                  Select which usage counters to reset:
                </p>
                
                <label className="flex items-center space-x-3">
                  <input
                    type="checkbox"
                    checked={resetMemories}
                    onChange={(e) => setResetMemories(e.target.checked)}
                    className="w-4 h-4 text-yellow-600 bg-gray-100 border-gray-300 rounded focus:ring-yellow-500"
                    disabled={isLoading}
                  />
                  <span className="font-SansMono400 text-sm">
                    Reset Total Memories Saved to 0
                  </span>
                </label>
                
                <label className="flex items-center space-x-3">
                  <input
                    type="checkbox"
                    checked={resetSummaries}
                    onChange={(e) => setResetSummaries(e.target.checked)}
                    className="w-4 h-4 text-yellow-600 bg-gray-100 border-gray-300 rounded focus:ring-yellow-500"
                    disabled={isLoading}
                  />
                  <span className="font-SansMono400 text-sm">
                    Reset Monthly Summary Pages to 0
                  </span>
                </label>
              </div>
              
              <div>
                <label className="block text-sm font-SansMono400 mb-2">
                  Reason for Reset:
                </label>
                <input
                  type="text"
                  value={reason}
                  onChange={(e) => setReason(e.target.value)}
                  className="w-full border border-gray-300 rounded px-3 py-2 font-SansMono400 text-sm focus:outline-none focus:ring-2 focus:ring-yellow-500 focus:border-transparent"
                  placeholder="Enter reason for usage reset"
                  disabled={isLoading}
                />
              </div>

              <div className="bg-yellow-50 rounded-lg p-3 border border-yellow-200">
                <div className="flex items-start space-x-2">
                  <span className="text-yellow-600 text-sm">⚠️</span>
                  <div>
                    <p className="text-xs font-SansMono400 text-yellow-800 font-medium mb-1">
                      Warning: This action cannot be undone
                    </p>
                    <p className="text-xs font-SansMono400 text-yellow-700">
                      Reset counters will permanently set the selected usage statistics to zero.
                    </p>
                  </div>
                </div>
              </div>
            </div>
            
            <div className="flex space-x-3 mt-6">
              <button
                onClick={handleConfirm}
                disabled={isLoading || !canConfirm}
                className="flex-1 px-4 py-2 bg-yellow-600 text-white rounded font-SansMono400 text-sm hover:bg-yellow-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                {isLoading ? 'Resetting...' : 'Reset Usage'}
              </button>
              <button
                onClick={handleClose}
                disabled={isLoading}
                className="flex-1 px-4 py-2 bg-gray-600 text-white rounded font-SansMono400 text-sm hover:bg-gray-700 disabled:opacity-50 transition-colors"
              >
                Cancel
              </button>
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
};

// Default export object containing all modals
const ActionModals = {
  UpgradeModal,
  ExtendModal,
  ResetUsageModal
};

export default ActionModals; 