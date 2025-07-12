# 🎯 Admin Panel Demo Guide

This guide will walk you through using your new HippoCampus Admin Panel.

## 🔐 Getting Started

### 1. Admin Login
Navigate to `http://localhost:5173/#/admin/login` (or your deployment URL)

**Demo Admin Credentials:**
- Email: `admin@hippocampus.com` (or your configured admin email)
- Password: Your admin password

**Features to Test:**
- ✅ Form validation (try empty fields)
- ✅ Error handling (try wrong credentials)
- ✅ Loading states with smooth animations
- ✅ Automatic redirect to dashboard on success

### 2. Admin Dashboard Overview
After login, you'll see the main dashboard with:

#### Analytics Cards
- **Total Users**: Complete user count
- **Pro Users**: Active Pro subscribers 
- **Conversion Rate**: Free to Pro conversion percentage
- **Revenue Estimate**: Monthly revenue projection

#### User Management Table
- **Pagination**: Navigate through user pages
- **Search**: Filter users by email, name, tier, or status
- **Sorting**: Click column headers to sort data
- **User Actions**: Click "Manage" to open user details

## 🛠 Admin Operations

### User Management Actions

#### 1. View User Details
- Click "Manage" on any user in the table
- See complete user information:
  - Personal details (email, name, user ID)
  - Subscription information (tier, status, dates)
  - Usage statistics (memories saved, summary pages used)

#### 2. Upgrade User to Pro
```
1. Click "Upgrade to Pro" (for Free users)
2. Set subscription duration (default: 30 days)
3. Add reason for upgrade
4. Confirm upgrade
```

**What happens:**
- User tier changes to "pro"
- Subscription end date is set
- User gets unlimited memories + 100 summary pages/month
- Success notification appears

#### 3. Downgrade User to Free
```
1. Click "Downgrade to Free" (for Pro users)
2. Confirm downgrade
```

**What happens:**
- User tier changes to "free"
- Memory limit: 100 total
- Summary pages: 5 per month
- Subscription marked as cancelled

#### 4. Extend Subscription
```
1. Click "Extend Subscription"
2. Set extension days (default: 30)
3. Add reason for extension
4. Confirm extension
```

**What happens:**
- Current end date extended by specified days
- Works for both active and expired subscriptions
- User retains Pro benefits for extended period

#### 5. Reset Usage Counters
```
1. Click "Reset Usage"
2. Choose what to reset:
   ☐ Total Memories Saved
   ☐ Monthly Summary Pages Used
3. Add reason for reset
4. Confirm reset
```

**What happens:**
- Selected counters reset to 0
- User can start fresh with their limits
- Useful for troubleshooting or customer support

## 🎨 UI Features

### Responsive Design
- **Desktop**: Full table with all columns
- **Tablet**: Condensed view with essential info
- **Mobile**: Stacked layout with collapsible details

### Animations & Feedback
- **Smooth transitions** between states
- **Loading indicators** for all operations
- **Success/error messages** with auto-dismiss
- **Hover effects** for interactive elements

### Search & Filtering
```
Search Examples:
- "john@example.com" - Find by email
- "John Doe" - Find by name
- "pro" - Find Pro users
- "expired" - Find expired subscriptions
```

### Sorting Options
Click any column header to sort:
- **Email**: Alphabetical
- **Tier**: Free → Pro
- **Status**: Active → Expired → Cancelled
- **Memories**: Numeric (low → high)
- **Summary Pages**: Numeric (low → high)
- **Joined**: Date (old → new)

## 🧪 Testing Scenarios

### Scenario 1: Customer Support
```
Customer: "I'm a Pro user but hitting memory limits"

Admin Actions:
1. Search for user by email
2. Click "Manage" → Check current usage
3. If needed: Reset memory counter
4. Document action with reason
```

### Scenario 2: Promotional Upgrade
```
Marketing: "Give 3 months Pro to beta testers"

Admin Actions:
1. Find beta tester users
2. Upgrade to Pro for 90 days
3. Add reason: "Beta tester reward"
4. Verify upgrade in analytics
```

### Scenario 3: Subscription Issues
```
User: "My Pro subscription expired but I paid"

Admin Actions:
1. Find user → Check subscription dates
2. Extend subscription (e.g., 30 days)
3. Add reason: "Payment processing delay"
4. Confirm user regains Pro access
```

## 📊 Analytics Insights

### Monitor Key Metrics
- **User Growth**: Track total users over time
- **Conversion Rate**: Measure Free → Pro upgrades
- **Revenue Trends**: Estimate monthly income
- **Usage Patterns**: See memory and summary usage

### Data-Driven Decisions
- **Low conversion?** → Check Pro upgrade benefits
- **High memory usage?** → Consider limit adjustments
- **Support requests?** → Use admin tools for quick fixes

## 🚨 Best Practices

### Security
- ✅ Always log reason for manual actions
- ✅ Verify user identity before major changes
- ✅ Use admin privileges responsibly
- ✅ Log out when session complete

### User Experience
- ✅ Communicate changes to affected users
- ✅ Document support actions for follow-up
- ✅ Test changes work as expected
- ✅ Monitor user satisfaction after changes

### Data Management
- ✅ Regular analytics reviews
- ✅ Export data for reporting (if needed)
- ✅ Monitor subscription health
- ✅ Track admin action outcomes

## 🔧 Troubleshooting

### Common Issues

#### Can't Login
```
Check:
- Email address is correct admin email
- Password is correct
- Backend admin configuration
- Browser console for errors
```

#### Data Not Loading
```
Check:
- Network connection
- Backend API status
- User authentication
- Browser console for API errors
```

#### Actions Failing
```
Check:
- User still exists
- Valid admin permissions
- Backend service availability
- Network connectivity
```

## 🎯 Quick Actions Reference

| Action | Steps | Result |
|--------|-------|--------|
| Find User | Search → Click Manage | User details modal |
| Upgrade | Manage → Upgrade → Set days | Pro access |
| Extend | Manage → Extend → Set days | Extended subscription |
| Reset | Manage → Reset → Choose type | Cleared counters |
| View Analytics | Dashboard top cards | Key metrics |

## 🚀 Next Steps

After familiarizing yourself with the admin panel:

1. **Customize**: Modify components for your specific needs
2. **Extend**: Add new admin features as required
3. **Monitor**: Use analytics for business insights
4. **Scale**: Handle growing user base efficiently

---

**Happy Administrating!** 🎉

*Need help? Check the main README.md or review component documentation.* 