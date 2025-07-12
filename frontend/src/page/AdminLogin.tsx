import { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { motion } from 'framer-motion';
import Button from '../components/Button';
import LoaderPillars from '../components/LoaderPillars';
import { useAuth } from '../hooks/useAuth';
import { useAdminAuth } from '../hooks/useAdminAuth';
import Logo from '../assets/Logo.svg';

const AdminLogin = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { signIn, isAuthenticated, isLoading: authLoading, error: authError } = useAuth();
  const { isAdmin, isLoading: adminLoading, error: adminError, refreshAdminStatus } = useAdminAuth();

  const [formData, setFormData] = useState({
    email: '',
    password: ''
  });
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Redirect if already admin
  useEffect(() => {
    if (isAuthenticated && isAdmin && !adminLoading) {
      console.log('✅ ADMIN LOGIN: User is already authenticated admin, redirecting to dashboard');
      const redirectTo = (location.state as any)?.from?.pathname || '/admin/dashboard';
      navigate(redirectTo);
    }
  }, [isAuthenticated, isAdmin, adminLoading, navigate, location.state]);

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
    // Clear errors when user starts typing
    if (error) setError(null);
  };

  const handleSubmit = async () => {
    
    if (!formData.email || !formData.password) {
      setError('Please enter both email and password');
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      console.log('🔐 ADMIN LOGIN: Attempting admin login');
      
      // First, authenticate with regular auth system
      const authResult = await signIn(formData.email, formData.password);
      
      if (!authResult.success) {
        throw new Error(authResult.error || 'Authentication failed');
      }

      console.log('✅ ADMIN LOGIN: Authentication successful, checking admin privileges');

      // Small delay to let auth state update
      await new Promise(resolve => setTimeout(resolve, 500));

      // Check admin privileges
      const isAdminUser = await refreshAdminStatus();
      
      if (!isAdminUser) {
        console.log('❌ ADMIN LOGIN: User authenticated but lacks admin privileges');
        throw new Error('Admin privileges required. Contact system administrator.');
      }

      console.log('✅ ADMIN LOGIN: Admin login successful, redirecting to dashboard');
      const redirectTo = (location.state as any)?.from?.pathname || '/admin/dashboard';
      navigate(redirectTo);

    } catch (error: any) {
      console.error('❌ ADMIN LOGIN: Login failed:', error);
      setError(error.message || 'Login failed. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleClear = () => {
    setFormData({ email: '', password: '' });
    setError(null);
  };

  const handleBackToHome = () => {
    navigate('/');
  };

  return (
    <div className="max-w-md bg-white rounded-lg px-10 w-[420px] h-[500px] flex flex-col justify-between py-10 border border-black">
      {/* Header */}
      <div className="flex flex-col items-center mb-6">
        <img src={Logo} alt="HippoCampus Logo" className="w-12 h-12 mb-4" />
        <motion.h1
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
          className="text-2xl font-NanumMyeongjo text-center text-black mb-2"
        >
          Admin Access
        </motion.h1>
        <p className="text-sm font-SansMono400 text-gray-600 text-center">
          Administrator authentication required
        </p>
      </div>

      {/* Login Form */}
      <motion.form
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, delay: 0.2 }}
        onSubmit={(e) => {
          e.preventDefault();
          handleSubmit();
        }}
        className="space-y-5 flex-1"
      >
        <div className="space-y-4">
          <div className="space-y-1">
            <label className="block text-sm font-SansMono400">Admin Email:</label>
            <input
              type="email"
              name="email"
              autoComplete="email"
              value={formData.email}
              onChange={handleInputChange}
              className="w-full border-b border-black bg-transparent focus:outline-none pb-1 placeholder-[#151515] placeholder-opacity-25"
              placeholder="admin@hippocampus.com"
              disabled={isLoading || authLoading || adminLoading}
            />
          </div>

          <div className="space-y-1">
            <label className="block text-sm font-SansMono400">Password:</label>
            <input
              type="password"
              name="password"
              autoComplete="current-password"
              value={formData.password}
              onChange={handleInputChange}
              className="w-full border-b border-black bg-transparent focus:outline-none pb-1 placeholder-[#151515] placeholder-opacity-25"
              placeholder="Enter admin password"
              disabled={isLoading || authLoading || adminLoading}
            />
          </div>
        </div>

        {/* Error Display */}
        {(error || authError || adminError) && (
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            className="pb-0 mb-0 space-y-0"
          >
            <p className="text-red-500 font-SansMono400 text-sm text-center pb-0">
              {error || authError || adminError}
            </p>
          </motion.div>
        )}

        {/* Loading State */}
        {(isLoading || authLoading || adminLoading) && (
          <div className="flex justify-center w-full py-4">
            <LoaderPillars />
          </div>
        )}

        {/* Buttons */}
        {!(isLoading || authLoading || adminLoading) && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.4 }}
            className="flex justify-between mx-auto pt-1"
          >
            <Button 
              handle={handleClear} 
              text="CLEAR" 
              textColor="--primary-white" 
              iSdisabled={false} 
            />
            <Button 
              handle={handleSubmit} 
              text="LOGIN" 
              textColor="--primary-white" 
              IncMinWidth="129px" 
              iSdisabled={false} 
            />
          </motion.div>
        )}
      </motion.form>

      {/* Footer */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.6 }}
        className="flex justify-center"
      >
        <button
          onClick={handleBackToHome}
          className="text-xs font-SansMono400 text-gray-500 hover:text-black transition-colors"
          disabled={isLoading || authLoading || adminLoading}
        >
          ← Back to Home
        </button>
      </motion.div>
    </div>
  );
};

export default AdminLogin; 