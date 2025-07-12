# HippoCampus Admin Panel

A comprehensive admin panel for managing users, subscriptions, and analytics in the HippoCampus application.

## 📁 Folder Structure

```
src/admin/
├── index.ts                     # Main module exports
├── README.md                    # This documentation file
├── components/                  # Reusable admin components
│   ├── AdminLayout.tsx         # Main layout with header/footer
│   ├── AnalyticsCards.tsx      # Analytics metrics cards
│   ├── UserTable.tsx           # User management table
│   ├── UserModal.tsx           # User detail modal
│   └── ActionModals.tsx        # Upgrade/extend/reset modals
├── hooks/                      # Admin-specific hooks
│   └── useAdminAuth.ts         # Admin authentication hook
├── pages/                      # Admin page components
│   ├── AdminLogin.tsx          # Admin login page
│   └── AdminDashboard.tsx      # Main admin dashboard
├── services/                   # Admin API services
│   └── adminApi.ts             # Admin API client
├── types/                      # TypeScript definitions
│   └── admin.types.ts          # Admin-related interfaces
└── utils/                      # Admin utility functions
    └── adminHelpers.ts         # Helper functions
```

## 🚀 Quick Start

### Using the Admin Panel

1. **Import admin components:**
   ```tsx
   import { AdminLogin, AdminDashboard } from '../admin';
   ```

2. **Setup routes in your router:**
   ```tsx
   <Route path="/admin/login" element={<AdminLogin />} />
   <Route path="/admin/dashboard" element={<AdminDashboard />} />
   ```

3. **Admin authentication:**
   ```tsx
   import { useAdminAuth } from '../admin';
   
   const { isAdmin, isLoading, error } = useAdminAuth();
   ```

## 🔧 Components

### AdminLayout
Provides consistent layout for all admin pages with header, navigation, and footer.

**Props:**
- `children`: React.ReactNode
- `title?`: string (default: "Admin Dashboard")
- `user?`: User object
- `onLogout`: () => void

### AnalyticsCards
Displays key subscription and user metrics in card format.

**Props:**
- `analytics`: AdminAnalytics | null
- `isLoading?`: boolean

### UserTable
Comprehensive user table with pagination, sorting, and search functionality.

**Props:**
- `users`: AdminUser[]
- `currentPage`: number
- `totalPages`: number
- `totalUsers`: number
- `onPageChange`: (page: number) => void
- `onUserClick`: (userId: string) => void
- `isLoading?`: boolean

### UserModal
Detailed user information modal with management actions.

**Props:**
- `user`: AdminUserDetail | null
- `isOpen`: boolean
- `onClose`: () => void
- `onUpgrade`: () => void
- `onDowngrade`: () => void
- `onExtend`: () => void
- `onResetUsage`: () => void
- `isActionLoading?`: boolean

### ActionModals
Collection of action modals for specific user operations:
- `UpgradeModal`: Upgrade user to Pro tier
- `ExtendModal`: Extend subscription duration
- `ResetUsageModal`: Reset usage counters

## 🔌 Services

### AdminApiService
Comprehensive service for all admin panel operations:

```tsx
import { adminApi } from '../admin';

// Get users with pagination
const users = await adminApi.getUsers(page, pageSize);

// Get user details
const userDetail = await adminApi.getUserDetail(userId);

// User management actions
await adminApi.upgradeUser(userId, 'pro', 30, 'reason');
await adminApi.downgradeUser(userId, 'reason');
await adminApi.extendSubscription(userId, 30, 'reason');
await adminApi.resetUsage(userId, true, false, 'reason');

// Analytics
const analytics = await adminApi.getAnalytics();

// Admin status check
const isAdmin = await adminApi.checkAdminStatus();
```

## 🎯 Hooks

### useAdminAuth
Manages admin authentication state and privilege checking:

```tsx
import { useAdminAuth } from '../admin';

const {
  isAdmin,
  isLoading,
  error,
  isAuthenticated,
  user,
  refreshAdminStatus
} = useAdminAuth();
```

## 🛠 Utility Functions

### Badge Styling
```tsx
import { getStatusBadgeStyle, getTierBadgeStyle } from '../admin';

const statusStyle = getStatusBadgeStyle('active');
const tierStyle = getTierBadgeStyle('pro');
```

### Date & Currency Formatting
```tsx
import { formatDate, formatCurrency, formatPercentage } from '../admin';

const date = formatDate('2024-01-01');
const currency = formatCurrency(100);
const percentage = formatPercentage(85.5);
```

### User Operations
```tsx
import { getUserDisplayName, calculateDaysRemaining } from '../admin';

const displayName = getUserDisplayName(user);
const daysLeft = calculateDaysRemaining(user.subscription_end_date);
```

## 📊 Types

### Core Types
```tsx
interface AdminUser {
  user_id: string;
  email: string;
  full_name?: string;
  subscription_tier: 'free' | 'pro';
  subscription_status: 'active' | 'expired' | 'cancelled';
  total_memories_saved: number;
  monthly_summary_pages_used: number;
  // ... more fields
}

interface AdminAnalytics {
  total_users: number;
  free_users: number;
  pro_users: number;
  conversion_rate: number;
  revenue_estimate: number;
  // ... more fields
}
```

## 🔐 Security

### Admin Authentication
- Admin status is verified via backend API call
- Routes are protected with admin privilege checks
- Automatic redirects for non-admin users

### API Security
- All API calls use authenticated requests
- Proper error handling for 401/403 responses
- Admin privilege validation on backend

## 🎨 Styling

The admin panel uses:
- **Tailwind CSS** for utility-first styling
- **Framer Motion** for smooth animations
- **Consistent design system** with the main app
- **Responsive design** for mobile and desktop

### Color Scheme
- **Success**: Green tones (upgrades, active status)
- **Warning**: Yellow tones (expiration, resets)
- **Error**: Red tones (expired, failures)
- **Info**: Blue tones (extensions, general info)

## 🧪 Testing

### Component Testing
```tsx
import { render, screen } from '@testing-library/react';
import { AdminDashboard } from '../admin';

test('renders admin dashboard', () => {
  render(<AdminDashboard />);
  expect(screen.getByText('Admin Dashboard')).toBeInTheDocument();
});
```

### API Testing
```tsx
import { adminApi } from '../admin';

test('gets users successfully', async () => {
  const users = await adminApi.getUsers(1, 10);
  expect(users.users).toHaveLength(10);
});
```

## 📈 Performance

### Optimizations
- **Pagination** for large user lists
- **Search filtering** on client-side
- **Lazy loading** of modals
- **Efficient state management**
- **Memoized components** where appropriate

### Caching
- Analytics data cached for 5 minutes
- User list cached per page
- Admin status cached during session

## 🚀 Deployment

### Environment Variables
Make sure these are set for admin functionality:
```env
VITE_API_URL=https://your-backend-api.com
VITE_BACKEND_URL=https://your-backend-api.com
```

### Admin User Setup
1. Configure admin email in backend environment
2. Ensure proper authentication flow
3. Test admin privilege verification

## 🔄 Development

### Adding New Features
1. Add types to `types/admin.types.ts`
2. Implement API methods in `services/adminApi.ts`
3. Create components in `components/`
4. Add utility functions to `utils/adminHelpers.ts`
5. Export from main `index.ts`

### Best Practices
- Use TypeScript for all new code
- Follow existing naming conventions
- Add proper error handling
- Include loading states
- Write comprehensive documentation

## 📞 Support

For questions or issues with the admin panel:
1. Check this documentation first
2. Review existing code patterns
3. Test with sample data
4. Check browser console for errors

---

**Version**: 1.0  
**Last Updated**: December 2024  
**Maintainer**: HippoCampus Development Team 