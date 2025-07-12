import { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../../hooks/useAuth';
import { adminApi } from '../services/adminApi';
import type { AdminAuthState } from '../types/admin.types';

/**
 * Admin Authentication Hook
 * Manages admin authentication state and privilege checking
 */
export const useAdminAuth = () => {
  const { isAuthenticated, user, isLoading: authLoading } = useAuth();
  const [adminState, setAdminState] = useState<AdminAuthState>({
    isAdmin: false,
    isLoading: true,
    error: null,
    isAuthenticated: false
  });

  const checkAdminStatus = useCallback(async () => {
    if (!isAuthenticated || authLoading) {
      setAdminState({
        isAdmin: false,
        isLoading: false,
        error: null,
        isAuthenticated: false
      });
      return false;
    }

    try {
      console.log('🔐 ADMIN AUTH: Checking admin privileges');
      setAdminState(prev => ({ ...prev, isLoading: true, error: null }));
      
      const isAdmin = await adminApi.checkAdminStatus();
      
      setAdminState({
        isAdmin,
        isLoading: false,
        error: null,
        isAuthenticated: true
      });
      
      console.log(`${isAdmin ? '✅' : '❌'} ADMIN AUTH: Admin status confirmed - ${isAdmin}`);
      return isAdmin;
    } catch (error: any) {
      console.error('❌ ADMIN AUTH: Admin check failed:', error);
      
      let errorMessage = 'Failed to verify admin privileges';
      if (error.message?.includes('403')) {
        errorMessage = 'Admin privileges required';
      } else if (error.message?.includes('401')) {
        errorMessage = 'Authentication required';
      }
      
      setAdminState({
        isAdmin: false,
        isLoading: false,
        error: errorMessage,
        isAuthenticated: true
      });
      
      return false;
    }
  }, [isAuthenticated, authLoading]);

  // Check admin status whenever authentication changes
  useEffect(() => {
    checkAdminStatus();
  }, [checkAdminStatus]);

  // Manually refresh admin status
  const refreshAdminStatus = useCallback(async () => {
    return await checkAdminStatus();
  }, [checkAdminStatus]);

  return {
    ...adminState,
    user,
    refreshAdminStatus
  };
}; 