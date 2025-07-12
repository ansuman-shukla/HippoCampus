import React from 'react';
import { motion } from 'framer-motion';
import Button from '../../components/Button';
import Logo from '../../assets/Logo.svg';
import type { AdminLayoutProps } from '../types/admin.types';

/**
 * Admin Layout Component
 * Provides consistent layout for all admin pages with header, navigation, and content area
 */
const AdminLayout: React.FC<AdminLayoutProps> = ({ 
  children, 
  title = 'Admin Dashboard',
  user,
  onLogout 
}) => {
  return (
    <div className="max-w-6xl bg-white rounded-lg px-8 w-full min-h-[700px] flex flex-col py-8 border border-black">
      {/* Header */}
      <motion.div 
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="flex justify-between items-center mb-6 border-b border-gray-200 pb-4"
      >
        <div className="flex items-center space-x-4">
          <img src={Logo} alt="HippoCampus Logo" className="w-10 h-10" />
          <div>
            <h1 className="text-2xl font-NanumMyeongjo text-black">{title}</h1>
            <p className="text-sm font-SansMono400 text-gray-600">
              Welcome, {user?.full_name || user?.email || 'Admin'}
            </p>
          </div>
        </div>
        
        <div className="flex items-center space-x-4">
          {/* Navigation Links */}
          <nav className="hidden md:flex items-center space-x-4">
            <a 
              href="#/admin/dashboard" 
              className="text-sm font-SansMono400 text-gray-600 hover:text-black transition-colors px-3 py-1 rounded"
            >
              Dashboard
            </a>
            <a 
              href="#/admin/analytics" 
              className="text-sm font-SansMono400 text-gray-600 hover:text-black transition-colors px-3 py-1 rounded"
            >
              Analytics
            </a>
          </nav>
          
          <Button 
            handle={onLogout} 
            text="LOGOUT" 
            textColor="--primary-white" 
            IncMinWidth="100px"
          />
        </div>
      </motion.div>

      {/* Main Content Area */}
      <motion.div 
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1 }}
        className="flex-1 flex flex-col"
      >
        {children}
      </motion.div>

      {/* Footer */}
      <motion.div 
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.3 }}
        className="mt-6 pt-4 border-t border-gray-200"
      >
        <div className="flex justify-between items-center text-xs font-SansMono400 text-gray-500">
          <span>HippoCampus Admin Panel v1.0</span>
          <span>© 2024 HippoCampus. All rights reserved.</span>
        </div>
      </motion.div>
    </div>
  );
};

export default AdminLayout; 