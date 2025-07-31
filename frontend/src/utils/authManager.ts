// Global authentication state manager to prevent concurrent auth checks
let isAuthCheckInProgress = false;
let authCheckPromise: Promise<boolean> | null = null;
let lastAuthCheckTime = 0;
const AUTH_CHECK_COOLDOWN = 2000; // 2 seconds cooldown between checks

/**
 * Global authentication check coordinator
 * Ensures only one auth check happens at a time and implements cooldown
 */
export const coordinatedAuthCheck = async (
  authCheckFunction: () => Promise<boolean>,
  forceFresh = false
): Promise<boolean> => {
  const now = Date.now();
  
  // If there's already an auth check in progress, wait for it
  if (isAuthCheckInProgress && authCheckPromise) {
    console.log('🔄 AUTH MANAGER: Auth check already in progress, waiting for result...');
    try {
      return await authCheckPromise;
    } catch (error) {
      console.error('🔄 AUTH MANAGER: Waiting auth check failed:', error);
      // Reset state and continue with new check
      isAuthCheckInProgress = false;
      authCheckPromise = null;
    }
  }
  
  // Implement cooldown to prevent rapid successive checks
  if (!forceFresh && (now - lastAuthCheckTime) < AUTH_CHECK_COOLDOWN) {
    console.log('🔄 AUTH MANAGER: Auth check on cooldown, skipping...');
    return false;
  }
  
  // Start new auth check
  console.log('🔄 AUTH MANAGER: Starting coordinated auth check...');
  isAuthCheckInProgress = true;
  lastAuthCheckTime = now;
  
  authCheckPromise = (async () => {
    try {
      const result = await authCheckFunction();
      console.log(`🔄 AUTH MANAGER: Auth check completed with result: ${result}`);
      return result;
    } catch (error) {
      console.error('🔄 AUTH MANAGER: Auth check failed:', error);
      return false;
    } finally {
      isAuthCheckInProgress = false;
      authCheckPromise = null;
    }
  })();
  
  return await authCheckPromise;
};

/**
 * Reset the auth check state (useful for forced re-authentication)
 */
export const resetAuthCheckState = (): void => {
  console.log('🔄 AUTH MANAGER: Resetting auth check state...');
  isAuthCheckInProgress = false;
  authCheckPromise = null;
  lastAuthCheckTime = 0;
};

/**
 * Check if an auth check is currently in progress
 */
export const isAuthCheckActive = (): boolean => {
  return isAuthCheckInProgress;
};