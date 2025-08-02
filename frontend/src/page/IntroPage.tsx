import Button from "../components/Button";
import Logo from '../assets/Logo.svg'
import AuthLoadingIndicator from '../components/AuthLoadingIndicator';
import '../index.css'
import { useNavigate } from 'react-router-dom';
import {motion} from 'framer-motion';
import { useAuth } from '../hooks/useAuth';
import { useState } from 'react';

const Intro = () => {
    const Navigate = useNavigate();
    const { checkAuthStatus } = useAuth();
    const [isCheckingAuth, setIsCheckingAuth] = useState(false);

    // Helper function to validate authentication with backend
    const validateAuthenticationWithBackend = async (): Promise<boolean> => {
        try {
            console.log('🔍 INTRO: Validating authentication with backend...');
            const authResult = await checkAuthStatus();
            console.log(`📊 INTRO: Auth validation result: ${authResult}`);
            return authResult;
        } catch (error) {
            console.error('❌ INTRO: Auth validation failed:', error);
            return false;
        }
    };

    const handleAuth = async () => {
        console.log('🚀 STEP 300: User clicked Get Started - initiating authentication flow');
        console.log('   ├─ Function: IntroPage.handleAuth()');
        console.log('   ├─ Current page: Intro/Landing page');
        console.log('   └─ Purpose: Start comprehensive authentication check and setup');
        
        console.log('🔄 STEP 301: Setting authentication check state');
        setIsCheckingAuth(true);
        
        try {
            console.log('🔍 STEP 302: Checking for ongoing auth transfer from App.tsx');
            // Check if auth transfer is already in progress from App.tsx
            if (window.authTransferInProgress) {
                console.log('⚠️  STEP 303: Auth transfer already in progress, waiting for completion...');
                console.log('   ├─ Transfer in progress: App.tsx is handling external auth');
                console.log('   ├─ Max wait time: 10 seconds');
                console.log('   └─ Polling every 500ms');
                
                // Wait for the transfer to complete (with timeout)
                let waitCount = 0;
                const maxWait = 20; // 10 seconds maximum wait
                
                while (window.authTransferInProgress && waitCount < maxWait) {
                    await new Promise(resolve => setTimeout(resolve, 500));
                    waitCount++;
                    console.log(`   ├─ Waiting... ${waitCount * 500}ms elapsed`);
                }
                
                if (window.authTransferInProgress) {
                    console.log('⚠️  STEP 304A: Auth transfer timeout - proceeding with manual check');
                    console.log('   └─ App.tsx transfer may be stuck, taking over');
                } else {
                    console.log('✅ STEP 304B: Auth transfer completed successfully');
                    console.log('   └─ App.tsx finished external auth processing');
                }
            } else {
                console.log('ℹ️  STEP 303: No ongoing auth transfer detected');
                console.log('   └─ Proceeding with standard auth check');
            }

            // First check if we already have backend tokens and validate them
            const backendCookie = await new Promise<chrome.cookies.Cookie | null>((resolve) => {
                chrome.cookies.get({
                    url: import.meta.env.VITE_BACKEND_URL,
                    name: 'access_token',
                }, (cookie) => {
                    resolve(cookie);
                });
            });

            if (backendCookie) {
                console.log('🔍 INTRO: Backend cookies found in handleAuth, validating authentication...');
                const isValidAuth = await validateAuthenticationWithBackend();
                
                if (isValidAuth) {
                    console.log('✅ INTRO: Authentication validated in handleAuth, navigating to submit');
                    Navigate("/submit");
                    return;
                } else {
                    console.log('❌ INTRO: Authentication validation failed in handleAuth, continuing with external auth check');
                }
            }

            // Check for external auth cookies with improved logic
            const externalCookie = await new Promise<chrome.cookies.Cookie | null>((resolve) => {
                chrome.cookies.get({
                    url: import.meta.env.VITE_API_URL,
                    name: 'access_token',
                }, (cookie) => {
                    resolve(cookie);
                });
            });

            if (externalCookie) {
                console.log('🔄 INTRO: External auth found, triggering coordinated transfer...');
                
                // Set flag to coordinate with App.tsx
                window.authTransferInProgress = true;
                
                try {
                    // Get refresh token as well
                    const externalRefreshCookie = await new Promise<chrome.cookies.Cookie | null>((resolve) => {
                        chrome.cookies.get({
                            url: import.meta.env.VITE_API_URL,
                            name: 'refresh_token',
                        }, (cookie) => {
                            resolve(cookie);
                        });
                    });

                    // Transfer cookies to backend with retry logic
                    let transferSuccess = false;
                    let retryCount = 0;
                    const maxRetries = 3;

                    while (!transferSuccess && retryCount < maxRetries) {
                        try {
                            // Set backend cookies
                            const apiUrl = import.meta.env.VITE_BACKEND_URL;
                            const isSecure = apiUrl.startsWith('https://');
                            
                            await new Promise<void>((resolve, reject) => {
                                chrome.cookies.set({
                                    url: apiUrl,
                                    name: 'access_token',
                                    value: externalCookie.value,
                                    path: '/',
                                    domain: new URL(apiUrl).hostname,
                                    secure: isSecure,
                                    sameSite: 'no_restriction' as chrome.cookies.SameSiteStatus,
                                    expirationDate: Math.floor(Date.now() / 1000) + 3600 // 1 hour
                                }, (cookie) => {
                                    if (chrome.runtime.lastError) {
                                        reject(new Error(chrome.runtime.lastError.message));
                                    } else if (cookie) {
                                        resolve();
                                    } else {
                                        reject(new Error('Failed to set access token cookie'));
                                    }
                                });
                            });

                            if (externalRefreshCookie) {
                                await new Promise<void>((resolve, reject) => {
                                    chrome.cookies.set({
                                        url: apiUrl,
                                        name: 'refresh_token',
                                        value: externalRefreshCookie.value,
                                        path: '/',
                                        domain: new URL(apiUrl).hostname,
                                        secure: isSecure,
                                        sameSite: 'no_restriction' as chrome.cookies.SameSiteStatus,
                                        expirationDate: Math.floor(Date.now() / 1000) + 604800 // 7 days
                                    }, (cookie) => {
                                        if (chrome.runtime.lastError) {
                                            reject(new Error(chrome.runtime.lastError.message));
                                        } else if (cookie) {
                                            resolve();
                                        } else {
                                            reject(new Error('Failed to set refresh token cookie'));
                                        }
                                    });
                                });
                            }

                            // Add delay to ensure cookies are properly set
                            await new Promise(resolve => setTimeout(resolve, 500));
                            
                            // Verify the transfer worked with retry logic
                            let authResult = false;
                            let authRetryCount = 0;
                            const maxAuthRetries = 3;
                            
                            while (!authResult && authRetryCount < maxAuthRetries) {
                                try {
                                    authResult = await checkAuthStatus();
                                    if (authResult) {
                                        transferSuccess = true;
                                        console.log('✅ INTRO: Cookie transfer successful, cleaning up external cookies');
                                        
                                        // Clean up external cookies
                                        chrome.cookies.remove({ url: import.meta.env.VITE_API_URL, name: "access_token" });
                                        chrome.cookies.remove({ url: import.meta.env.VITE_API_URL, name: "refresh_token" });
                                        
                                        Navigate("/submit");
                                        return;
                                    } else {
                                        authRetryCount++;
                                        console.log(`⚠️  INTRO: Auth status check failed, retry ${authRetryCount}/${maxAuthRetries}`);
                                        if (authRetryCount < maxAuthRetries) {
                                            await new Promise(resolve => setTimeout(resolve, 1000 * authRetryCount));
                                        }
                                    }
                                } catch (error) {
                                    authRetryCount++;
                                    console.log(`⚠️  INTRO: Auth status check error, retry ${authRetryCount}/${maxAuthRetries}:`, error);
                                    if (authRetryCount < maxAuthRetries) {
                                        await new Promise(resolve => setTimeout(resolve, 1000 * authRetryCount));
                                    }
                                }
                            }
                            
                            if (!authResult) {
                                console.warn('⚠️  INTRO: Auth status check failed after all retries, but proceeding anyway');
                                // Proceed anyway since cookies are set
                                transferSuccess = true;
                                chrome.cookies.remove({ url: import.meta.env.VITE_API_URL, name: "access_token" });
                                chrome.cookies.remove({ url: import.meta.env.VITE_API_URL, name: "refresh_token" });
                                Navigate("/submit");
                                return;
                            }
                        } catch (error) {
                            retryCount++;
                            console.log(`⚠️  INTRO: Cookie transfer attempt ${retryCount}/${maxRetries} failed:`, error);
                            if (retryCount < maxRetries) {
                                await new Promise(resolve => setTimeout(resolve, 1000 * retryCount));
                            }
                        }
                    }

                    if (!transferSuccess) {
                        throw new Error('Cookie transfer failed after all retries');
                    }
                } finally {
                    window.authTransferInProgress = false;
                }
            }

            // Check for refresh token that might be usable
            const refreshCookie = await new Promise<chrome.cookies.Cookie | null>((resolve) => {
                chrome.cookies.get({
                    url: import.meta.env.VITE_BACKEND_URL,
                    name: 'refresh_token',
                }, (cookie) => {
                    resolve(cookie);
                });
            });

            if (refreshCookie) {
                console.log('🔄 INTRO: Refresh token found, attempting session restoration');
                try {
                    const authResult = await checkAuthStatus();
                    if (authResult) {
                        Navigate("/submit");
                        return;
                    }
                } catch (error) {
                    console.log('❌ INTRO: Session restoration failed:', error);
                }
            }

            // No authentication found - open auth window
            console.log('🔐 INTRO: No authentication found, opening auth window');
            const authUrl = `https://extension-auth.vercel.app/`;
            
            const authWindow = window.open(
                authUrl,
                'authWindow',
                'width=500,height=600,scrollbars=yes,resizable=yes'
            );

            if (authWindow) {
                console.log('🪟 INTRO: Auth window opened, monitoring for completion');
                
                // Monitor for auth completion
                const checkAuthCompletion = setInterval(async () => {
                    if (authWindow.closed) {
                        clearInterval(checkAuthCompletion);
                        console.log('🪟 INTRO: Auth window closed, starting auth completion check');
                        
                        // Give a short delay for cookies to be set
                        setTimeout(async () => {
                            // Trigger the external auth check
                            const externalCheck = await new Promise<chrome.cookies.Cookie | null>((resolve) => {
                                chrome.cookies.get({
                                    url: import.meta.env.VITE_API_URL,
                                    name: 'access_token',
                                }, (cookie) => {
                                    resolve(cookie);
                                });
                            });

                            if (externalCheck) {
                                console.log('✅ INTRO: Auth completion detected, re-running handleAuth');
                                // Recursively call handleAuth to process the new cookies
                                await handleAuth();
                            } else {
                                console.log('ℹ️  INTRO: No auth cookies found after window close');
                                setIsCheckingAuth(false);
                            }
                        }, 1000);
                    }
                }, 1000);
            } else {
                console.log('❌ INTRO: Failed to open auth window');
                setIsCheckingAuth(false);
            }
        } catch (error) {
            console.error('💥 INTRO: Error in handleAuth:', error);
            setIsCheckingAuth(false);
        }
    };

    // Show loading state while checking authentication
    if (isCheckingAuth) {
        return (
            <AuthLoadingIndicator 
                message="Setting things up for you..." 
                showDetails={true}
            />
        );
    }

  return (
    <motion.div 
    initial={{ opacity: 0 }}
    animate={{ opacity: 1 }}
    transition={{ duration: 1.5, ease: "ease" }}
    
    className="h-[500px] w-[100%] relative border border-black rounded-lg overflow-hidden">
      
      <div className="absolute inset-0 flex">
        <div className="w-1/4 bg-[var(--primary-orange)]" />
        <div className="w-1/4 bg-[var(--primary-green)]" />
        <div className="w-1/4 bg-[var(--primary-yellow)]" />
        <div className="w-1/4 bg-[var(--primary-blue)]" />
      </div>

      {/* Content */}
      <div className="relative h-[500px] w-[419px]  flex my-auto justify-center rounded-lg">
        <div className="flex flex-col items-center text-center space-y-8 p-8">

          <div className="flex items-center mb-16">
           <img src={Logo} alt="" className="pl-6"/>
          </div>
          
          <p className="text-4xl nyr max-w-md">
            "Every bookmark is a doorway to a new journey"
          </p>
          
          {/* Button */}
          <Button handle={handleAuth} text="GET STARTED" textColor="--primary-white"/>
        </div>
      </div>
    </motion.div>
  );
};


export default Intro;