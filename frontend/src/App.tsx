import { HashRouter as Router, Routes, Route, useLocation, useNavigate } from "react-router-dom";
import { AnimatePresence, motion } from "framer-motion";
import SearchPage from "./page/SearchPage";
import Intro from "./page/IntroPage";
import SearchResponse from "./page/SearchResultPage";
import ResponsePage from "./page/ResponsePage";
import SummarizePage from "./page/SummarizePage";
import './index.css';



const pageVariants = {
  initial: { opacity: 1, y: 0 },
  animate: { opacity: 1, y: 0, transition: { duration: 0.2 } },
  exit: { opacity: 1, y: 0, transition: { duration: 0.2 } }
};

import { ReactNode, useEffect, useState } from "react";
import { useAuth } from "./hooks/useAuth";

// Extend Window interface to include our custom property
declare global {
  interface Window {
    authTransferInProgress?: boolean;
  }
}

const PageWrapper = ({ children }: { children: ReactNode }) => (
  <motion.div
    initial="initial"
    animate="animate"
    exit="exit"
    variants={pageVariants}
    className="p-0 bg-transparent min-w-[100%]"
  >
    {children}
  </motion.div>
);

const AnimatedRoutes = () => {
  const Navigate = useNavigate();
  const location = useLocation();
  const [quotes, setQuotes] = useState<string[]>([]);
  const { checkAuthStatus } = useAuth();

  // Check for external auth (from popup/extension auth flow)
  function checkForExternalAuth() {
    chrome.cookies.getAll({ url: import.meta.env.VITE_API_URL }, async (cookies) => {
      console.log('🔍 APP: Checking for external auth cookies:', cookies);
      const accessToken = cookies.find((cookie) => cookie.name === "access_token")?.value;
      const refreshToken = cookies.find((cookie) => cookie.name === "refresh_token")?.value;

      // If cookies are not found, try to get tokens from localStorage via content script or direct injection
      if (!accessToken) {
        try {
          console.log('🔍 APP: No external cookies found, checking localStorage via content script');
          // First try to find an existing tab with the auth site
          const tabs = await chrome.tabs.query({ url: "*" });
          let result = null;
          
          if (tabs.length > 0 && tabs[0].id) {
            try {
              // Try content script first
              result = await chrome.tabs.sendMessage(tabs[0].id, { action: "getTokensFromLocalStorage" });
            } catch (error) {
              console.log('   ├─ Content script not available, trying direct injection:', error);
              
              // Fallback: inject script directly
              const [injectionResult] = await chrome.scripting.executeScript({
                target: { tabId: tabs[0].id },
                func: () => {
                  return {
                    accessToken: localStorage.getItem('access_token'),
                    refreshToken: localStorage.getItem('refresh_token'),
                    session: localStorage.getItem('session')
                  };
                }
              });
              
              result = injectionResult.result;
            }
          }
          
          if (result?.accessToken) {
            console.log('✅ APP: Found tokens in localStorage, transferring to backend...');
            await setBackendCookies(result.accessToken, result.refreshToken);
            
            // Verify and navigate
            const verificationCookie = await new Promise<chrome.cookies.Cookie | null>((resolve) => {
              chrome.cookies.get({
                url: import.meta.env.VITE_BACKEND_URL,
                name: 'access_token'
              }, (cookie) => {
                resolve(cookie);
              });
            });
            
            if (verificationCookie && location.pathname === "/") {
              console.log('✅ APP: Backend cookies set successfully from localStorage, checking auth status');
              await checkAuthStatus();
              Navigate("/submit");
            }
            return;
          }
        } catch (error) {
          console.log('⚠️  APP: Could not get tokens from localStorage:', error);
        }
      }

      // Handle external auth cookies with improved coordination
      if (accessToken && location.pathname === "/") {
        try {
          console.log('🔄 APP: External auth tokens detected, starting coordinated transfer...');
          console.log(`   ├─ Access token length: ${accessToken.length}`);
          console.log(`   └─ Refresh token present: ${!!refreshToken}`);
          
          // Set a flag to prevent multiple simultaneous transfers
          if (window.authTransferInProgress) {
            console.log('⚠️  APP: Auth transfer already in progress, skipping');
            return;
          }
          window.authTransferInProgress = true;
          
          try {
            // Wait for cookies to be set before navigating
            await setBackendCookies(accessToken, refreshToken);
            
            // Double-check that cookies were properly set with retry logic
            let verificationCookie = null;
            let retryCount = 0;
            const maxRetries = 3;
            
            while (!verificationCookie && retryCount < maxRetries) {
              verificationCookie = await new Promise<chrome.cookies.Cookie | null>((resolve) => {
                chrome.cookies.get({
                  url: import.meta.env.VITE_BACKEND_URL,
                  name: 'access_token'
                }, (cookie) => {
                  resolve(cookie);
                });
              });
              
              if (!verificationCookie) {
                retryCount++;
                console.log(`⚠️  APP: Cookie verification failed, retry ${retryCount}/${maxRetries}`);
                await new Promise(resolve => setTimeout(resolve, 500 * retryCount)); // Exponential backoff
              }
            }
            
            if (verificationCookie) {
              console.log('✅ APP: Backend cookies set successfully, checking auth status to populate localStorage');
              
              // Immediately check auth status to populate localStorage with user info
              const authSuccess = await checkAuthStatus();
              
              if (authSuccess) {
                console.log('✅ APP: Auth status verified, cleaning up and navigating');
                
                // Clean up external auth cookies after successful transfer
                chrome.cookies.remove({ url: import.meta.env.VITE_API_URL, name: "access_token" });
                chrome.cookies.remove({ url: import.meta.env.VITE_API_URL, name: "refresh_token" });
                
                // Navigate to submit page
                Navigate("/submit");
              } else {
                throw new Error('Auth status check failed after cookie transfer');
              }
            } else {
              throw new Error('Cookie verification failed after retries');
            }
          } finally {
            // Always clear the transfer flag
            window.authTransferInProgress = false;
          }
        } catch (error) {
          window.authTransferInProgress = false;
          console.error('❌ APP: Failed to set backend cookies:', error);
          // Retry after a longer delay for error cases
          setTimeout(() => checkForExternalAuth(), 2000);
        }
        return; // Exit early after handling external auth
      }

      // Check if already authenticated with backend (only if no external auth was found)
      chrome.cookies.get({
        url: import.meta.env.VITE_BACKEND_URL,
        name: 'access_token',
      }, async (cookie) => {
        if (cookie && location.pathname === "/") {
          console.log('✅ APP: Backend authentication found, ensuring localStorage is populated');
          // User is authenticated, ensure localStorage is populated
          await checkAuthStatus();
          Navigate("/submit");
        } else if (!cookie && !accessToken) {
          // Check for refresh token before giving up
          chrome.cookies.get({
            url: import.meta.env.VITE_BACKEND_URL,
            name: 'refresh_token',
          }, async (refreshCookie) => {
            if (refreshCookie) {
              console.log('🔄 APP: Found refresh token, attempting to restore session');
              try {
                const authResult = await checkAuthStatus();
                if (authResult && location.pathname === "/") {
                  Navigate("/submit");
                }
              } catch (error) {
                console.log('❌ APP: Failed to restore session with refresh token:', error);
              }
            }
            // Continue checking with shorter interval only if no refresh token
            if (!refreshCookie && !window.authTransferInProgress) {
              setTimeout(() => checkForExternalAuth(), 1000);
            }
          });
        }
      });
    });
  }

  // Helper function to set backend cookies directly from external auth
  const setBackendCookies = async (accessToken: string, refreshToken?: string) => {
    try {
      const apiUrl = import.meta.env.VITE_BACKEND_URL;
      
      // Set access token cookie and wait for completion
      await new Promise<void>((resolve, reject) => {
        chrome.cookies.set({
          url: apiUrl,
          name: 'access_token',
          value: accessToken,
          path: '/',
          domain: new URL(import.meta.env.VITE_BACKEND_URL).hostname,
          secure: true,
          sameSite: 'no_restriction' as chrome.cookies.SameSiteStatus,
          expirationDate: Math.floor(Date.now() / 1000) + 3600 // 1 hour
        }, (cookie) => {
          if (chrome.runtime.lastError) {
            reject(new Error(chrome.runtime.lastError.message));
          } else if (cookie) {
            console.log('Access token cookie set successfully');
            resolve();
          } else {
            reject(new Error('Failed to set access token cookie'));
          }
        });
      });
      
      // Set refresh token cookie if available and wait for completion
      if (refreshToken) {
        await new Promise<void>((resolve, reject) => {
          chrome.cookies.set({
            url: apiUrl,
            name: 'refresh_token',
            value: refreshToken,
            path: '/',
            domain: new URL(import.meta.env.VITE_BACKEND_URL).hostname,
            secure: true,
            sameSite: 'no_restriction' as chrome.cookies.SameSiteStatus,
            expirationDate: Math.floor(Date.now() / 1000) + 604800 // 7 days
          }, (cookie) => {
            if (chrome.runtime.lastError) {
              reject(new Error(chrome.runtime.lastError.message));
            } else if (cookie) {
              console.log('Refresh token cookie set successfully');
              resolve();
            } else {
              reject(new Error('Failed to set refresh token cookie'));
            }
          });
        });
      }

      // Verify authentication with backend after cookies are set
      await checkAuthStatus();
      
      // Small delay to ensure cookies are propagated
      await new Promise(resolve => setTimeout(resolve, 100));
      
      console.log('Backend cookies set from external auth');
    } catch (error) {
      console.error('Error setting backend cookies:', error);
      throw error; // Re-throw to be caught by caller
    }
  };
  
  useEffect(() => {
    // Small delay to let extension fully initialize before auth checks
    const timeoutId = setTimeout(() => {
      checkForExternalAuth();
    }, 100);
    
    // Listen for auth state changes from background script
    const messageListener = (message: any) => {
      if (message.action === "checkAuthStatus" || message.action === "authStateChanged") {
        console.log('Received auth state change notification');
        checkForExternalAuth();
      }
    };
    
    chrome.runtime.onMessage.addListener(messageListener);
    
    return () => {
      clearTimeout(timeoutId);
      chrome.runtime.onMessage.removeListener(messageListener);
    };
  }, []);

  

  useEffect(() => {
    const handleAuthFlow = async () => {

      const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });

      if (!tab?.url) return;



      try {
        // Check if user is authenticated via backend cookies
        const cookie = await chrome.cookies.get({
          url: import.meta.env.VITE_BACKEND_URL,
          name: 'access_token',
        });

        if (cookie && location.pathname === "/") {
          // User is authenticated, ensure localStorage is populated before navigation
          await checkAuthStatus();
          Navigate("/submit");
        }

        // Load quotes from localStorage or fetch from backend
        if(localStorage.getItem("quotes")){
          console.log("found Quotes")
          setQuotes(JSON.parse(localStorage.getItem("quotes") || "[]"));
          console.log("have set the quotes")
        }else{
          const fetchQuotes = (retryCount = 0) => {
            chrome.runtime.sendMessage(
              {
                action: "getQuotes"
              },
              (response) => {
                if (response && response.success) {
                  if (response.data && Array.isArray(response.data)) {
                    const filteredQuotes = response.data.filter((quote: string) => quote.length > 0);
                    setQuotes(prev => [
                      ...new Set([...prev, ...filteredQuotes])
                    ]);
                    console.log("GOT QUOTES FROM BACKEND")
                    localStorage.setItem("quotes", JSON.stringify(filteredQuotes));
                    console.log("Quotes are set")
                  } else {
                    console.error("Response data is not an array:", response.data);
                  }
                } else {
                  console.error("Failed to get quotes:", response?.error || "No response");
                  // Retry up to 2 times with increasing delay for new users
                  if (retryCount < 2) {
                    console.log(`Retrying quotes fetch in ${(retryCount + 1) * 1000}ms...`);
                    setTimeout(() => fetchQuotes(retryCount + 1), (retryCount + 1) * 1000);
                  }
                }
              }
            );
          };
          
          fetchQuotes();
        }
      } catch (error) {
        console.error("Error handling auth flow:", error);
      }


      
      
    };

    handleAuthFlow();

    const handleCookieChange = (changeInfo: chrome.cookies.CookieChangeInfo) => {
      if (changeInfo.cookie.name === "access_token") {
      }
    };

    chrome.cookies.onChanged.addListener(handleCookieChange);
    return () => chrome.cookies.onChanged.removeListener(handleCookieChange);
  }, []);







  return (
    <AnimatePresence mode="wait">
      <Routes location={location} key={location.pathname}>
        <Route path="/" element={<PageWrapper><Intro /></PageWrapper>} />
        <Route path="/submit" element={<PageWrapper><ResponsePage /></PageWrapper>} />
        <Route path="/search" element={<PageWrapper><SearchPage Quote={quotes[Math.floor(Math.random() * quotes.length)]} /></PageWrapper>} />
        <Route path="/response" element={<PageWrapper><SearchResponse /></PageWrapper>} />
        <Route path="/summarize" element={<PageWrapper><SummarizePage /></PageWrapper>} />
      </Routes>
    </AnimatePresence>
  );
};

const App = () => {
  return (
    <Router>
      <div className="flex items-center justify-center bg-transparent">
        <AnimatedRoutes />
      </div>
    </Router>
  );
};

export default App;