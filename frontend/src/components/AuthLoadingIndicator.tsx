import { motion } from 'framer-motion';
import LoaderPillars from './LoaderPillars';

interface AuthLoadingIndicatorProps {
  message?: string;
  showDetails?: boolean;
}

const AuthLoadingIndicator = ({ 
  message = "Setting things up for you...", 
  showDetails = false 
}: AuthLoadingIndicatorProps) => {
  return (
    <motion.div 
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.3, ease: "easeOut" }}
      className="h-[500px] w-[100%] relative border border-black rounded-lg overflow-hidden"
    >
      {/* Background with colored sections */}
      <div className="absolute inset-0 flex">
        <div className="w-1/4 bg-[var(--primary-orange)]" />
        <div className="w-1/4 bg-[var(--primary-green)]" />
        <div className="w-1/4 bg-[var(--primary-yellow)]" />
        <div className="w-1/4 bg-[var(--primary-blue)]" />
      </div>

      {/* Content */}
      <div className="relative h-full w-full flex items-center justify-center">
        <div className="flex flex-col items-center text-center space-y-8">
          <p className="text-4xl nyr max-w-md">
            "{message}"
          </p>
          
          {/* Loader animation */}
          <LoaderPillars />
          
          {showDetails && (
            <motion.div 
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.5, duration: 0.3 }}
              className="text-sm text-gray-600 max-w-sm"
            >
              <p>Validating authentication...</p>
            </motion.div>
          )}
        </div>
      </div>
    </motion.div>
  );
};

export default AuthLoadingIndicator;
