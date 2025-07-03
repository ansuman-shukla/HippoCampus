import Button from "../components/Button";
import Logo from '../assets/Logo.svg'
import '../index.css'
import { useNavigate } from 'react-router-dom';
import {motion} from 'framer-motion';
import { useAuth } from '../hooks/useAuth';
import { useEffect, useState } from 'react';

const Intro = () => {
    const Navigate = useNavigate();
    const { checkAuthStatus } = useAuth();
    const [isCheckingAuth, setIsCheckingAuth] = useState(true);

    // Check if user is already authenticated on component mount
    useEffect(() => {
        const checkExistingAuth = async () => {
            try {
                // Check backend cookies first
                const backendCookie = await new Promise<chrome.cookies.Cookie | null>((resolve) => {
                    chrome.cookies.get({
                        url: import.meta.env.VITE_BACKEND_URL,
                        name: 'access_token',
                    }, (cookie) => {
                        resolve(cookie);
                    });
                });

                if (backendCookie) {
                    console.log('User already authenticated, navigating to submit page');
                    Navigate("/submit");
                    return;
                }

                // Check for external auth cookies
                const externalCookie = await new Promise<chrome.cookies.Cookie | null>((resolve) => {
                    chrome.cookies.get({
                        url: import.meta.env.VITE_API_URL,
                        name: 'access_token',
                    }, (cookie) => {
                        resolve(cookie);
                    });
                });

                if (externalCookie) {
                    console.log('External auth detected, checking auth status');
                    await checkAuthStatus();
                    Navigate("/submit");
                    return;
                }

                // Check if we have a refresh token that could be used
                const refreshCookie = await new Promise<chrome.cookies.Cookie | null>((resolve) => {
                    chrome.cookies.get({
                        url: import.meta.env.VITE_BACKEND_URL,
                        name: 'refresh_token',
                    }, (cookie) => {
                        resolve(cookie);
                    });
                });

                if (refreshCookie) {
                    console.log('Refresh token found, checking auth status');
                    const authResult = await checkAuthStatus();
                    if (authResult) {
                        Navigate("/submit");
                        return;
                    }
                }

                console.log('No authentication found, showing intro page');
            } catch (error) {
                console.error('Error checking existing auth:', error);
            } finally {
                setIsCheckingAuth(false);
            }
        };

        checkExistingAuth();
    }, [Navigate, checkAuthStatus]);

    const handleAuth = async () => {
        console.log('Get Started clicked, checking authentication...');
        setIsCheckingAuth(true);
        
        try {
            // First check if we already have backend tokens
            const backendCookie = await new Promise<chrome.cookies.Cookie | null>((resolve) => {
                chrome.cookies.get({
                    url: import.meta.env.VITE_BACKEND_URL,
                    name: 'access_token',
                }, (cookie) => {
                    resolve(cookie);
                });
            });

            if (backendCookie) {
                console.log('Backend auth found, navigating to submit');
                Navigate("/submit");
                return;
            }

            // Check for external auth cookies
            const externalCookie = await new Promise<chrome.cookies.Cookie | null>((resolve) => {
                chrome.cookies.get({
                    url: import.meta.env.VITE_API_URL,
                    name: 'access_token',
                }, (cookie) => {
                    resolve(cookie);
                });
            });

            if (externalCookie) {
                console.log('External auth found, navigating to submit');
                Navigate("/submit");
                return;
            }

            // Check for refresh token
            const refreshCookie = await new Promise<chrome.cookies.Cookie | null>((resolve) => {
                chrome.cookies.get({
                    url: import.meta.env.VITE_BACKEND_URL,
                    name: 'refresh_token',
                }, (cookie) => {
                    resolve(cookie);
                });
            });

            if (refreshCookie) {
                console.log('Refresh token found, attempting auth status check');
                const authResult = await checkAuthStatus();
                if (authResult) {
                    Navigate("/submit");
                    return;
                }
            }

            // No existing auth, open login page
            console.log('No authentication found, opening login page');
            window.open(import.meta.env.VITE_API_URL);
        } catch (error) {
            console.error('Error in handleAuth:', error);
            // Fallback to opening login page
            window.open(import.meta.env.VITE_API_URL);
        } finally {
            setIsCheckingAuth(false);
        }
    };

    // Show loading state while checking authentication
    if (isCheckingAuth) {
        return (
            <motion.div 
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ duration: 1.5, ease: "ease" }}
                className="h-[500px] w-[100%] relative border border-black rounded-lg overflow-hidden flex items-center justify-center"
            >
                <div className="text-center">
                    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900 mx-auto mb-4"></div>
                    <p className="text-lg">Checking authentication...</p>
                </div>
            </motion.div>
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