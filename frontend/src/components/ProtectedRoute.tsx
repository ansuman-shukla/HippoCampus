import { Navigate, useLocation } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import LoaderPillars from './LoaderPillars';
import { ReactNode, useEffect, useState } from 'react';

interface ProtectedRouteProps {
  children: ReactNode;
}

const ProtectedRoute = ({ children }: ProtectedRouteProps) => {
  const { isAuthenticated, isLoading } = useAuth();
  const location = useLocation();
  const [fallbackAuth, setFallbackAuth] = useState<boolean | null>(null);
  const [fallbackLoading, setFallbackLoading] = useState(false);
  
  console.log('🐛 PROTECTED_ROUTE: Component render with state:', {
    isAuthenticated,
    isLoading,
    fallbackAuth,
    fallbackLoading,
    location: location.pathname,
    timestamp: new Date().toISOString()
  });

  // Fallback authentication check using direct cookie inspection
  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      console.log('🔍 PROTECTED_ROUTE: Auth hook shows not authenticated, checking fallback methods');
      setFallbackLoading(true);
      
      // Check for backend cookies as a fallback
      if (typeof window !== 'undefined' && window.chrome && window.chrome.cookies) {
        chrome.cookies.get({
          url: import.meta.env.VITE_BACKEND_URL,
          name: 'access_token'
        }, (cookie) => {
          if (cookie && cookie.value) {
            console.log('✅ PROTECTED_ROUTE: Found valid backend cookie via fallback');
            setFallbackAuth(true);
          } else {
            console.log('❌ PROTECTED_ROUTE: No valid backend cookie found');
            setFallbackAuth(false);
          }
          setFallbackLoading(false);
        });
      } else {
        // Non-extension environment - check document cookies
        const hasAccessToken = document.cookie.includes('access_token');
        console.log(`📋 PROTECTED_ROUTE: Document cookie check: ${hasAccessToken}`);
        setFallbackAuth(hasAccessToken);
        setFallbackLoading(false);
      }
    } else if (isAuthenticated) {
      setFallbackAuth(true);
      setFallbackLoading(false);
    }
  }, [isAuthenticated, isLoading]);

  // Show loading while auth hook is loading OR fallback is loading
  if (isLoading || fallbackLoading) {
    return (
      <div className="h-[500px] w-[420px] flex items-center justify-center">
        <LoaderPillars />
      </div>
    );
  }

  // Use auth hook result OR fallback authentication result
  const finalAuthStatus = isAuthenticated || fallbackAuth;

  if (!finalAuthStatus) {
    console.log('🚫 PROTECTED_ROUTE: Not authenticated, redirecting to intro');
    return <Navigate to="/" state={{ from: location }} replace />;
  }

  if (fallbackAuth && !isAuthenticated) {
    console.log('✅ PROTECTED_ROUTE: Using fallback authentication, rendering children');
  }

  // If authenticated (either via hook or fallback), render the requested component
  return <>{children}</>;
};

export default ProtectedRoute;

