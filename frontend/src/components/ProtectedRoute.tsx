import { Navigate, useLocation } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import LoaderPillars from './LoaderPillars';
import { ReactNode } from 'react';

interface ProtectedRouteProps {
  children: ReactNode;
}

const ProtectedRoute = ({ children }: ProtectedRouteProps) => {
  const { isAuthenticated, isLoading } = useAuth();
  const location = useLocation();
  
  console.log('🐛 PROTECTED_ROUTE: Component render with state:', {
    isAuthenticated,
    isLoading,
    location: location.pathname,
    timestamp: new Date().toISOString()
  });

  // Show loading while auth hook is loading
  if (isLoading) {
    return (
      <div className="h-[500px] w-[420px] flex items-center justify-center">
        <LoaderPillars />
      </div>
    );
  }

  if (!isAuthenticated) {
    console.log('🚫 PROTECTED_ROUTE: Not authenticated, redirecting to intro');
    return <Navigate to="/" state={{ from: location }} replace />;
  }

  return <>{children}</>;
};

export default ProtectedRoute;

