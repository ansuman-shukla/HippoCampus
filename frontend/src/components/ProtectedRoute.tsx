import { Navigate, useLocation } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import LoaderPillars from './LoaderPillars';
import { ReactNode } from 'react';

interface ProtectedRouteProps {
  children: ReactNode;
}

const ProtectedRoute = ({ children }: ProtectedRouteProps) => {
  const { isAuthenticated, isLoading } = useAuth();
  const location = useLocation();

  if (isLoading) {
    // Show a loading indicator while checking auth status
    return (
      <div className="h-[500px] w-[420px] flex items-center justify-center">
        <LoaderPillars />
      </div>
    );
  }

  if (!isAuthenticated) {
    // If not authenticated, redirect to the intro page
    return <Navigate to="/" state={{ from: location }} replace />;
  }

  // If authenticated, render the requested component
  return <>{children}</>;
};

export default ProtectedRoute;

