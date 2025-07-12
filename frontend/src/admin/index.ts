// Admin Panel Module - Main Export Index
// This file exports all admin functionality for clean imports

// Pages
export { default as AdminLogin } from './pages/AdminLogin';
export { default as AdminDashboard } from './pages/AdminDashboard';

// Components
export { default as AdminLayout } from './components/AdminLayout';
export { default as UserTable } from './components/UserTable';
export { default as AnalyticsCards } from './components/AnalyticsCards';
export { default as UserModal } from './components/UserModal';
export { default as ActionModals } from './components/ActionModals';

// Services
export { adminApi } from './services/adminApi';

// Hooks
export { useAdminAuth } from './hooks/useAdminAuth';

// Types
export * from './types/admin.types';

// Utils
export * from './utils/adminHelpers'; 