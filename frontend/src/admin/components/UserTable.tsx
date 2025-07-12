import React, { useState } from 'react';
import { motion } from 'framer-motion';
import LoaderPillars from '../../components/LoaderPillars';
import type { UserTableProps } from '../types/admin.types';
import { getStatusBadgeStyle, getTierBadgeStyle, formatDate } from '../utils/adminHelpers';

/**
 * User Table Component
 * Displays users in a paginated table with sorting and search functionality
 */
const UserTable: React.FC<UserTableProps> = ({
  users,
  currentPage,
  totalPages,
  totalUsers,
  onPageChange,
  onUserClick,
  isLoading
}) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [sortField, setSortField] = useState('email');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('asc');

  const handleSort = (field: string) => {
    if (sortField === field) {
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
    } else {
      setSortField(field);
      setSortOrder('asc');
    }
  };

  const getSortIcon = (field: string) => {
    if (sortField !== field) return '↕️';
    return sortOrder === 'asc' ? '↑' : '↓';
  };

  const filteredUsers = users.filter(user =>
    user.email.toLowerCase().includes(searchTerm.toLowerCase()) ||
    user.full_name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    user.subscription_tier.toLowerCase().includes(searchTerm.toLowerCase()) ||
    user.subscription_status.toLowerCase().includes(searchTerm.toLowerCase())
  );

  if (isLoading) {
    return (
      <div className="flex-1 bg-gray-50 rounded-lg p-4 border border-gray-200 flex justify-center items-center min-h-[400px]">
        <LoaderPillars />
      </div>
    );
  }

  return (
    <motion.div 
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="flex-1 bg-gray-50 rounded-lg p-4 border border-gray-200"
    >
      {/* Table Header with Search and Pagination */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center mb-4 space-y-3 md:space-y-0">
        <div className="flex items-center space-x-4">
          <h2 className="text-lg font-SansMono400 text-black">
            Users ({totalUsers.toLocaleString()})
          </h2>
          
          {/* Search Input */}
          <div className="relative">
            <input
              type="text"
              placeholder="Search users..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="px-3 py-1 border border-gray-300 rounded font-SansMono400 text-sm w-48 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
            {searchTerm && (
              <button
                onClick={() => setSearchTerm('')}
                className="absolute right-2 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-gray-600"
              >
                ✕
              </button>
            )}
          </div>
        </div>

        {/* Pagination Controls */}
        <div className="flex items-center space-x-2">
          <button
            onClick={() => onPageChange(Math.max(1, currentPage - 1))}
            disabled={currentPage === 1}
            className="px-3 py-1 bg-black text-white rounded font-SansMono400 text-xs disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-800 transition-colors"
          >
            Previous
          </button>
          <span className="px-3 py-1 font-SansMono400 text-sm">
            Page {currentPage} of {totalPages}
          </span>
          <button
            onClick={() => onPageChange(Math.min(totalPages, currentPage + 1))}
            disabled={currentPage === totalPages}
            className="px-3 py-1 bg-black text-white rounded font-SansMono400 text-xs disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-800 transition-colors"
          >
            Next
          </button>
        </div>
      </div>

      {/* Results Info */}
      {searchTerm && (
        <div className="mb-3">
          <p className="text-sm font-SansMono400 text-gray-600">
            Showing {filteredUsers.length} of {users.length} users
            {filteredUsers.length !== users.length && (
              <span className="ml-2 text-blue-600">
                (filtered by "{searchTerm}")
              </span>
            )}
          </p>
        </div>
      )}

      {/* Table */}
      <div className="overflow-x-auto">
        <table className="w-full bg-white rounded-lg overflow-hidden">
          <thead className="bg-gray-100">
            <tr>
              <th 
                className="px-4 py-3 text-left font-SansMono400 text-sm cursor-pointer hover:bg-gray-200 transition-colors"
                onClick={() => handleSort('email')}
              >
                <div className="flex items-center space-x-1">
                  <span>Email</span>
                  <span className="text-xs">{getSortIcon('email')}</span>
                </div>
              </th>
              <th 
                className="px-4 py-3 text-left font-SansMono400 text-sm cursor-pointer hover:bg-gray-200 transition-colors"
                onClick={() => handleSort('subscription_tier')}
              >
                <div className="flex items-center space-x-1">
                  <span>Tier</span>
                  <span className="text-xs">{getSortIcon('subscription_tier')}</span>
                </div>
              </th>
              <th 
                className="px-4 py-3 text-left font-SansMono400 text-sm cursor-pointer hover:bg-gray-200 transition-colors"
                onClick={() => handleSort('subscription_status')}
              >
                <div className="flex items-center space-x-1">
                  <span>Status</span>
                  <span className="text-xs">{getSortIcon('subscription_status')}</span>
                </div>
              </th>
              <th 
                className="px-4 py-3 text-left font-SansMono400 text-sm cursor-pointer hover:bg-gray-200 transition-colors"
                onClick={() => handleSort('total_memories_saved')}
              >
                <div className="flex items-center space-x-1">
                  <span>Memories</span>
                  <span className="text-xs">{getSortIcon('total_memories_saved')}</span>
                </div>
              </th>
              <th 
                className="px-4 py-3 text-left font-SansMono400 text-sm cursor-pointer hover:bg-gray-200 transition-colors"
                onClick={() => handleSort('monthly_summary_pages_used')}
              >
                <div className="flex items-center space-x-1">
                  <span>Summary Pages</span>
                  <span className="text-xs">{getSortIcon('monthly_summary_pages_used')}</span>
                </div>
              </th>
              <th 
                className="px-4 py-3 text-left font-SansMono400 text-sm cursor-pointer hover:bg-gray-200 transition-colors"
                onClick={() => handleSort('created_at')}
              >
                <div className="flex items-center space-x-1">
                  <span>Joined</span>
                  <span className="text-xs">{getSortIcon('created_at')}</span>
                </div>
              </th>
              <th className="px-4 py-3 text-left font-SansMono400 text-sm">Actions</th>
            </tr>
          </thead>
          <tbody>
            {(searchTerm ? filteredUsers : users).map((user, index) => (
              <motion.tr
                key={user.user_id}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.05 }}
                className="border-b border-gray-100 hover:bg-gray-50 transition-colors"
              >
                <td className="px-4 py-3 font-SansMono400 text-sm">
                  <div>
                    <div className="font-medium">{user.email}</div>
                    {user.full_name && (
                      <div className="text-xs text-gray-500">{user.full_name}</div>
                    )}
                  </div>
                </td>
                <td className="px-4 py-3">
                  <span className={`px-2 py-1 rounded-full text-xs font-SansMono400 ${getTierBadgeStyle(user.subscription_tier)}`}>
                    {user.subscription_tier.toUpperCase()}
                  </span>
                </td>
                <td className="px-4 py-3">
                  <span className={`px-2 py-1 rounded-full text-xs font-SansMono400 ${getStatusBadgeStyle(user.subscription_status)}`}>
                    {user.subscription_status.toUpperCase()}
                  </span>
                </td>
                <td className="px-4 py-3 font-SansMono400 text-sm">
                  {user.total_memories_saved.toLocaleString()}
                </td>
                <td className="px-4 py-3 font-SansMono400 text-sm">
                  {user.monthly_summary_pages_used.toLocaleString()}
                </td>
                <td className="px-4 py-3 font-SansMono400 text-sm text-gray-600">
                  {formatDate(user.created_at)}
                </td>
                <td className="px-4 py-3">
                  <button
                    onClick={() => onUserClick(user.user_id)}
                    className="px-3 py-1 bg-black text-white rounded font-SansMono400 text-xs hover:bg-gray-800 transition-colors"
                  >
                    Manage
                  </button>
                </td>
              </motion.tr>
            ))}
          </tbody>
        </table>

        {/* Empty State */}
        {(searchTerm ? filteredUsers : users).length === 0 && (
          <div className="text-center py-12">
            <p className="text-gray-500 font-SansMono400">
              {searchTerm ? 'No users found matching your search.' : 'No users found.'}
            </p>
          </div>
        )}
      </div>
    </motion.div>
  );
};

export default UserTable; 