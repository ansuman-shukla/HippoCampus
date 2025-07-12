/**
 * @jest-environment jsdom
 */

import { render, screen, fireEvent, waitFor, act } from '@testing-library/react';
import '@testing-library/jest-dom';
import { MemoryRouter } from 'react-router-dom';
import { vi, describe, it, expect, beforeEach } from 'vitest';

// Import components
import AdminLogin from '../page/AdminLogin';
import AdminDashboard from '../page/AdminDashboard';

// Mock dependencies
const mockNavigate = vi.fn();
const mockSignIn = vi.fn();
const mockSignOut = vi.fn();
const mockRefreshAdminStatus = vi.fn();

// Mock hooks
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    useNavigate: () => mockNavigate,
    useLocation: () => ({ state: null, pathname: '/admin/login' })
  };
});

vi.mock('../hooks/useAuth', () => ({
  useAuth: vi.fn(() => ({
    signIn: mockSignIn,
    signOut: mockSignOut,
    isAuthenticated: false,
    isLoading: false,
    error: null,
    user: null
  }))
}));

vi.mock('../hooks/useAdminAuth', () => ({
  useAdminAuth: vi.fn(() => ({
    isAdmin: false,
    isLoading: false,
    error: null,
    isAuthenticated: false,
    user: null,
    refreshAdminStatus: mockRefreshAdminStatus
  }))
}));

// Mock admin API
const mockAdminApi = {
  getUsers: vi.fn(),
  getAnalytics: vi.fn(),
  getUserDetail: vi.fn(),
  upgradeUser: vi.fn(),
  downgradeUser: vi.fn(),
  extendSubscription: vi.fn(),
  resetUsage: vi.fn(),
  checkAdminStatus: vi.fn()
};

vi.mock('../utils/adminApi', () => ({
  adminApi: mockAdminApi
}));

// Mock framer-motion
vi.mock('framer-motion', () => ({
  motion: {
    div: ({ children, ...props }: any) => <div {...props}>{children}</div>,
    form: ({ children, ...props }: any) => <form {...props}>{children}</form>,
    h1: ({ children, ...props }: any) => <h1 {...props}>{children}</h1>
  },
  AnimatePresence: ({ children }: any) => <>{children}</>
}));

// Mock assets
vi.mock('../assets/Logo.svg', () => ({
  default: 'mock-logo.svg'
}));

// Test data
const mockUser = {
  user_id: 'user123',
  email: 'test@example.com',
  full_name: 'Test User',
  subscription_tier: 'free' as const,
  subscription_status: 'active' as const,
  total_memories_saved: 50,
  monthly_summary_pages_used: 3,
  created_at: '2024-01-01T00:00:00Z',
  last_sign_in_at: '2024-01-15T00:00:00Z'
};

const mockProUser = {
  ...mockUser,
  user_id: 'prouser123',
  email: 'pro@example.com',
  subscription_tier: 'pro' as const,
  subscription_end_date: '2024-02-01T00:00:00Z'
};

const mockAnalytics = {
  total_users: 150,
  free_users: 130,
  pro_users: 20,
  active_subscriptions: 18,
  expired_subscriptions: 2,
  cancelled_subscriptions: 0,
  total_memories_saved: 5000,
  total_summary_pages_used: 800,
  average_memories_per_user: 33.3,
  conversion_rate: 13.3,
  revenue_estimate: 160
};

const mockUsersResponse = {
  users: [mockUser, mockProUser],
  total_users: 2,
  page: 1,
  page_size: 20,
  total_pages: 1
};

describe('AdminLogin Component', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should render admin login form correctly', () => {
    render(
      <MemoryRouter>
        <AdminLogin />
      </MemoryRouter>
    );

    expect(screen.getByText('Admin Access')).toBeInTheDocument();
    expect(screen.getByPlaceholderText('admin@hippocampus.com')).toBeInTheDocument();
    expect(screen.getByPlaceholderText('Enter admin password')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /login/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /clear/i })).toBeInTheDocument();
  });

  it('should handle form input changes', async () => {
    render(
      <MemoryRouter>
        <AdminLogin />
      </MemoryRouter>
    );

    const emailInput = screen.getByPlaceholderText('admin@hippocampus.com');
    const passwordInput = screen.getByPlaceholderText('Enter admin password');

    await act(async () => {
      fireEvent.change(emailInput, { target: { value: 'admin@test.com' } });
      fireEvent.change(passwordInput, { target: { value: 'password123' } });
    });

    expect(emailInput).toHaveValue('admin@test.com');
    expect(passwordInput).toHaveValue('password123');
  });

  it('should show validation error for empty fields', async () => {
    render(
      <MemoryRouter>
        <AdminLogin />
      </MemoryRouter>
    );

    const loginButton = screen.getByRole('button', { name: /login/i });

    await act(async () => {
      fireEvent.click(loginButton);
    });

    await waitFor(() => {
      expect(screen.getByText('Please enter both email and password')).toBeInTheDocument();
    });
  });

  it('should handle successful admin login', async () => {
    mockSignIn.mockResolvedValue({ success: true });
    mockRefreshAdminStatus.mockResolvedValue(true);

    render(
      <MemoryRouter>
        <AdminLogin />
      </MemoryRouter>
    );

    const emailInput = screen.getByPlaceholderText('admin@hippocampus.com');
    const passwordInput = screen.getByPlaceholderText('Enter admin password');
    const loginButton = screen.getByRole('button', { name: /login/i });

    await act(async () => {
      fireEvent.change(emailInput, { target: { value: 'admin@test.com' } });
      fireEvent.change(passwordInput, { target: { value: 'password123' } });
      fireEvent.click(loginButton);
    });

    await waitFor(() => {
      expect(mockSignIn).toHaveBeenCalledWith('admin@test.com', 'password123');
      expect(mockRefreshAdminStatus).toHaveBeenCalled();
      expect(mockNavigate).toHaveBeenCalledWith('/admin/dashboard');
    });
  });

  it('should handle login failure with non-admin user', async () => {
    mockSignIn.mockResolvedValue({ success: true });
    mockRefreshAdminStatus.mockResolvedValue(false);

    render(
      <MemoryRouter>
        <AdminLogin />
      </MemoryRouter>
    );

    const emailInput = screen.getByPlaceholderText('admin@hippocampus.com');
    const passwordInput = screen.getByPlaceholderText('Enter admin password');
    const loginButton = screen.getByRole('button', { name: /login/i });

    await act(async () => {
      fireEvent.change(emailInput, { target: { value: 'user@test.com' } });
      fireEvent.change(passwordInput, { target: { value: 'password123' } });
      fireEvent.click(loginButton);
    });

    await waitFor(() => {
      expect(screen.getByText('Admin privileges required. Contact system administrator.')).toBeInTheDocument();
    });
  });

  it('should clear form when clear button is clicked', async () => {
    render(
      <MemoryRouter>
        <AdminLogin />
      </MemoryRouter>
    );

    const emailInput = screen.getByPlaceholderText('admin@hippocampus.com');
    const passwordInput = screen.getByPlaceholderText('Enter admin password');
    const clearButton = screen.getByRole('button', { name: /clear/i });

    await act(async () => {
      fireEvent.change(emailInput, { target: { value: 'admin@test.com' } });
      fireEvent.change(passwordInput, { target: { value: 'password123' } });
      fireEvent.click(clearButton);
    });

    expect(emailInput).toHaveValue('');
    expect(passwordInput).toHaveValue('');
  });
});

describe('AdminDashboard Component', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    
    // Mock successful admin state
    const { useAdminAuth } = require('../hooks/useAdminAuth');
    useAdminAuth.mockReturnValue({
      isAdmin: true,
      isLoading: false,
      error: null,
      isAuthenticated: true,
      user: { email: 'admin@test.com', full_name: 'Admin User' },
      refreshAdminStatus: mockRefreshAdminStatus
    });

    // Mock API responses
    mockAdminApi.getUsers.mockResolvedValue(mockUsersResponse);
    mockAdminApi.getAnalytics.mockResolvedValue(mockAnalytics);
    mockAdminApi.getUserDetail.mockResolvedValue({
      ...mockUser,
      monthly_summary_reset_date: '2024-02-01T00:00:00Z',
      days_remaining: 15,
      is_expired: false
    });
  });

  it('should render admin dashboard with analytics and user list', async () => {
    render(
      <MemoryRouter>
        <AdminDashboard />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('Admin Dashboard')).toBeInTheDocument();
      expect(screen.getByText('Welcome, Admin User')).toBeInTheDocument();
      
      // Analytics cards
      expect(screen.getByText('150')).toBeInTheDocument(); // Total users
      expect(screen.getByText('20')).toBeInTheDocument(); // Pro users
      expect(screen.getByText('13.3%')).toBeInTheDocument(); // Conversion rate
      expect(screen.getByText('$160')).toBeInTheDocument(); // Revenue
      
      // User table
      expect(screen.getByText('test@example.com')).toBeInTheDocument();
      expect(screen.getByText('pro@example.com')).toBeInTheDocument();
    });
  });

  it('should redirect non-admin users to login', () => {
    const { useAdminAuth } = require('../hooks/useAdminAuth');
    useAdminAuth.mockReturnValue({
      isAdmin: false,
      isLoading: false,
      error: null,
      isAuthenticated: true,
      user: null,
      refreshAdminStatus: mockRefreshAdminStatus
    });

    render(
      <MemoryRouter>
        <AdminDashboard />
      </MemoryRouter>
    );

    expect(mockNavigate).toHaveBeenCalledWith('/admin/login', {
      state: { from: { pathname: '/admin/dashboard' } }
    });
  });

  it('should open user detail modal when manage button is clicked', async () => {
    render(
      <MemoryRouter>
        <AdminDashboard />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('test@example.com')).toBeInTheDocument();
    });

    const manageButtons = screen.getAllByText('Manage');
    
    await act(async () => {
      fireEvent.click(manageButtons[0]);
    });

    await waitFor(() => {
      expect(mockAdminApi.getUserDetail).toHaveBeenCalledWith('user123');
      expect(screen.getByText('User Management')).toBeInTheDocument();
      expect(screen.getByText('Email: test@example.com')).toBeInTheDocument();
    });
  });

  it('should handle user upgrade flow', async () => {
    mockAdminApi.upgradeUser.mockResolvedValue({
      success: true,
      message: 'User upgraded successfully',
      user_id: 'user123',
      action: 'upgrade'
    });

    render(
      <MemoryRouter>
        <AdminDashboard />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('test@example.com')).toBeInTheDocument();
    });

    // Open user detail modal
    const manageButtons = screen.getAllByText('Manage');
    await act(async () => {
      fireEvent.click(manageButtons[0]);
    });

    await waitFor(() => {
      expect(screen.getByText('User Management')).toBeInTheDocument();
    });

    // Click upgrade button
    const upgradeButton = screen.getByText('Upgrade to Pro');
    await act(async () => {
      fireEvent.click(upgradeButton);
    });

    await waitFor(() => {
      expect(screen.getByText('Upgrade to Pro')).toBeInTheDocument();
    });

    // Fill upgrade form
    const daysInput = screen.getByDisplayValue('30');
    const reasonInput = screen.getByPlaceholderText('Admin manual upgrade');
    
    await act(async () => {
      fireEvent.change(daysInput, { target: { value: '60' } });
      fireEvent.change(reasonInput, { target: { value: 'Test upgrade' } });
    });

    // Submit upgrade
    const submitButton = screen.getByRole('button', { name: /upgrade/i });
    await act(async () => {
      fireEvent.click(submitButton);
    });

    await waitFor(() => {
      expect(mockAdminApi.upgradeUser).toHaveBeenCalledWith(
        'user123',
        'pro',
        60,
        'Test upgrade'
      );
    });
  });

  it('should handle user downgrade', async () => {
    mockAdminApi.downgradeUser.mockResolvedValue({
      success: true,
      message: 'User downgraded successfully',
      user_id: 'prouser123',
      action: 'downgrade'
    });

    // Mock pro user detail
    mockAdminApi.getUserDetail.mockResolvedValue({
      ...mockProUser,
      monthly_summary_reset_date: '2024-02-01T00:00:00Z',
      days_remaining: 15,
      is_expired: false
    });

    render(
      <MemoryRouter>
        <AdminDashboard />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('pro@example.com')).toBeInTheDocument();
    });

    // Open user detail modal for pro user
    const manageButtons = screen.getAllByText('Manage');
    await act(async () => {
      fireEvent.click(manageButtons[1]);
    });

    await waitFor(() => {
      expect(screen.getByText('User Management')).toBeInTheDocument();
    });

    // Click downgrade button
    const downgradeButton = screen.getByText('Downgrade');
    await act(async () => {
      fireEvent.click(downgradeButton);
    });

    await waitFor(() => {
      expect(mockAdminApi.downgradeUser).toHaveBeenCalledWith(
        'prouser123',
        'Admin manual downgrade'
      );
    });
  });

  it('should handle pagination', async () => {
    // Mock multi-page response
    const multiPageResponse = {
      ...mockUsersResponse,
      total_users: 50,
      total_pages: 3,
      page: 1
    };
    mockAdminApi.getUsers.mockResolvedValue(multiPageResponse);

    render(
      <MemoryRouter>
        <AdminDashboard />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('Page 1 of 3')).toBeInTheDocument();
    });

    const nextButton = screen.getByText('Next');
    expect(nextButton).toBeEnabled();

    await act(async () => {
      fireEvent.click(nextButton);
    });

    await waitFor(() => {
      expect(mockAdminApi.getUsers).toHaveBeenCalledWith(2, 20);
    });
  });

  it('should handle extend subscription flow', async () => {
    mockAdminApi.extendSubscription.mockResolvedValue({
      success: true,
      message: 'Subscription extended',
      user_id: 'user123',
      action: 'extend'
    });

    render(
      <MemoryRouter>
        <AdminDashboard />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('test@example.com')).toBeInTheDocument();
    });

    // Open user detail modal
    const manageButtons = screen.getAllByText('Manage');
    await act(async () => {
      fireEvent.click(manageButtons[0]);
    });

    await waitFor(() => {
      expect(screen.getByText('User Management')).toBeInTheDocument();
    });

    // Click extend subscription button
    const extendButton = screen.getByText('Extend Sub');
    await act(async () => {
      fireEvent.click(extendButton);
    });

    await waitFor(() => {
      expect(screen.getByText('Extend Subscription')).toBeInTheDocument();
    });

    // Fill extend form and submit
    const submitButton = screen.getByRole('button', { name: /extend/i });
    await act(async () => {
      fireEvent.click(submitButton);
    });

    await waitFor(() => {
      expect(mockAdminApi.extendSubscription).toHaveBeenCalledWith(
        'user123',
        30,
        ''
      );
    });
  });

  it('should handle reset usage flow', async () => {
    mockAdminApi.resetUsage.mockResolvedValue({
      success: true,
      message: 'Usage reset',
      user_id: 'user123',
      action: 'reset-usage'
    });

    render(
      <MemoryRouter>
        <AdminDashboard />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('test@example.com')).toBeInTheDocument();
    });

    // Open user detail modal
    const manageButtons = screen.getAllByText('Manage');
    await act(async () => {
      fireEvent.click(manageButtons[0]);
    });

    await waitFor(() => {
      expect(screen.getByText('User Management')).toBeInTheDocument();
    });

    // Click reset usage button
    const resetButton = screen.getByText('Reset Usage');
    await act(async () => {
      fireEvent.click(resetButton);
    });

    await waitFor(() => {
      expect(screen.getByText('Reset Usage Counters')).toBeInTheDocument();
    });

    // Select checkboxes
    const memoryCheckbox = screen.getByLabelText('Reset Memory Counter');
    const summaryCheckbox = screen.getByLabelText('Reset Monthly Summary Counter');
    
    await act(async () => {
      fireEvent.click(memoryCheckbox);
      fireEvent.click(summaryCheckbox);
    });

    // Submit reset
    const submitButton = screen.getByRole('button', { name: /reset/i });
    await act(async () => {
      fireEvent.click(submitButton);
    });

    await waitFor(() => {
      expect(mockAdminApi.resetUsage).toHaveBeenCalledWith(
        'user123',
        true,
        true,
        ''
      );
    });
  });

  it('should handle logout', async () => {
    render(
      <MemoryRouter>
        <AdminDashboard />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('Admin Dashboard')).toBeInTheDocument();
    });

    const logoutButton = screen.getByText('LOGOUT');
    await act(async () => {
      fireEvent.click(logoutButton);
    });

    expect(mockSignOut).toHaveBeenCalled();
    expect(mockNavigate).toHaveBeenCalledWith('/');
  });

  it('should display error messages correctly', async () => {
    mockAdminApi.getUsers.mockRejectedValue(new Error('API Error'));

    render(
      <MemoryRouter>
        <AdminDashboard />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('API Error')).toBeInTheDocument();
    });
  });

  it('should display loading state', () => {
    const { useAdminAuth } = require('../hooks/useAdminAuth');
    useAdminAuth.mockReturnValue({
      isAdmin: true,
      isLoading: true,
      error: null,
      isAuthenticated: true,
      user: null,
      refreshAdminStatus: mockRefreshAdminStatus
    });

    render(
      <MemoryRouter>
        <AdminDashboard />
      </MemoryRouter>
    );

    expect(screen.getByText('Loading admin dashboard...')).toBeInTheDocument();
  });
});

describe('Admin Route Protection', () => {
  it('should block non-admin users from accessing dashboard', () => {
    const { useAdminAuth } = require('../hooks/useAdminAuth');
    useAdminAuth.mockReturnValue({
      isAdmin: false,
      isLoading: false,
      error: 'Admin privileges required',
      isAuthenticated: true,
      user: { email: 'user@test.com' },
      refreshAdminStatus: mockRefreshAdminStatus
    });

    render(
      <MemoryRouter>
        <AdminDashboard />
      </MemoryRouter>
    );

    expect(mockNavigate).toHaveBeenCalledWith('/admin/login', {
      state: { from: { pathname: '/admin/dashboard' } }
    });
  });

  it('should redirect already authenticated admin from login to dashboard', () => {
    const { useAdminAuth } = require('../hooks/useAdminAuth');
    useAdminAuth.mockReturnValue({
      isAdmin: true,
      isLoading: false,
      error: null,
      isAuthenticated: true,
      user: { email: 'admin@test.com' },
      refreshAdminStatus: mockRefreshAdminStatus
    });

    const { useAuth } = require('../hooks/useAuth');
    useAuth.mockReturnValue({
      signIn: mockSignIn,
      signOut: mockSignOut,
      isAuthenticated: true,
      isLoading: false,
      error: null,
      user: { email: 'admin@test.com' }
    });

    render(
      <MemoryRouter>
        <AdminLogin />
      </MemoryRouter>
    );

    expect(mockNavigate).toHaveBeenCalledWith('/admin/dashboard');
  });
}); 