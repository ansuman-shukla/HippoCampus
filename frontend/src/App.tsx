import { HashRouter as Router, Routes, Route, useLocation, useNavigate } from "react-router-dom";
import { AnimatePresence, motion } from "framer-motion";
import SearchPage from "./page/SearchPage";
import Intro from "./page/IntroPage";
import SearchResponse from "./page/SearchResultPage";
import ResponsePage from "./page/ResponsePage";
import SummarizePage from "./page/SummarizePage";
import { supabase, tokenManager, authUtils } from "./supabaseClient";
import './index.css';

const pageVariants = {
  initial: { opacity: 1, y: 0 },
  animate: { opacity: 1, y: 0, transition: { duration: 0.2 } },
  exit: { opacity: 1, y: 0, transition: { duration: 0.2 } }
};

import { ReactNode, useEffect, useState } from "react";

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
  const [isAuthenticating, setIsAuthenticating] = useState(true);
  const [authError, setAuthError] = useState<string | null>(null);

  // Enhanced authentication check
  useEffect(() => {
    const initializeAuth = async () => {
      try {
        setIsAuthenticating(true);
        setAuthError(null);

        console.log('Initializing authentication...');

        // First, check for existing Supabase session
        const { data: { session }, error } = await supabase.auth.getSession();
        
        if (error) {
          console.error('Supabase session error:', error);
        }
        
        if (session) {
          console.log("Found existing Supabase session");
          await tokenManager.setTokens(session.access_token, session.refresh_token);
          
          // Verify with backend
          const isBackendAuth = await tokenManager.ensureAuthenticated();
          if (isBackendAuth) {
            console.log('Backend authentication verified');
            if (location.pathname === "/") {
              Navigate("/submit");
            }
            return;
          }
        }

        // Check for cookies from auth domain
        try {
          chrome.cookies.getAll({ url: "https://extension-auth.vercel.app" }, async (cookies) => {
            const accessToken = cookies.find((cookie) => cookie.name === "access_token")?.value;
            const refreshToken = cookies.find((cookie) => cookie.name === "refresh_token")?.value;

            if (accessToken && refreshToken) {
              console.log("Found tokens in cookies from auth domain");
              await tokenManager.setTokens(accessToken, refreshToken);
              
              // Verify with backend
              const isBackendAuth = await tokenManager.ensureAuthenticated();
              if (isBackendAuth && location.pathname === "/") {
                Navigate("/submit");
              }
            }
          });
        } catch (error) {
          console.error('Error checking auth domain cookies:', error);
        }

        // Check Chrome storage as fallback
        chrome.storage.local.get(['access_token', 'refresh_token'], async (result) => {
          if (result.access_token && result.refresh_token) {
            console.log("Found tokens in Chrome storage");
            await tokenManager.setTokens(result.access_token, result.refresh_token);
            
            // Verify with backend
            const isBackendAuth = await tokenManager.ensureAuthenticated();
            if (isBackendAuth && location.pathname === "/") {
              Navigate("/submit");
            }
          }
        });

      } catch (error) {
        console.error("Error during auth initialization:", error);
        setAuthError('Authentication initialization failed');
      } finally {
        setIsAuthenticating(false);
      }
    };

    initializeAuth();
  }, []);

  // Handle auth flow and quotes loading
  useEffect(() => {
    const handleAuthenticatedFlow = async () => {
      try {
        const isAuthenticated = await tokenManager.ensureAuthenticated();
        if (!isAuthenticated) {
          console.log('User not authenticated, staying on intro page');
          return;
        }

        console.log('User authenticated, loading app data...');

        // Load quotes if not already cached
        if (localStorage.getItem("quotes")) {
          console.log("Using cached quotes");
          setQuotes(JSON.parse(localStorage.getItem("quotes") || "[]"));
        } else {
          // Load quotes using the message passing system
          chrome.runtime.sendMessage(
            { action: "getQuotes" },
            (response) => {
              if (response?.success && response.data) {
                const filteredQuotes = response.data.filter((quote: string) => quote.length > 0);
                setQuotes(prev => [
                  ...new Set([...prev, ...filteredQuotes])
                ]);
                localStorage.setItem("quotes", JSON.stringify(filteredQuotes));
                console.log("Quotes loaded from backend");
              } else {
                console.warn('Failed to load quotes:', response?.error);
              }
            }
          );
        }

        // Navigate to submit page if on homepage
        if (location.pathname === "/") {
          Navigate("/submit");
        }
      } catch (error) {
        console.error("Error in authenticated flow:", error);
        setAuthError('Failed to load application data');
      }
    };

    if (!isAuthenticating) {
      handleAuthenticatedFlow();
    }
  }, [location.pathname, Navigate, isAuthenticating]);

  // Enhanced auth state listener
  useEffect(() => {
    console.log('Setting up auth state listener...');
    
    const { data: { subscription } } = supabase.auth.onAuthStateChange(async (event, session) => {
      console.log('Supabase auth event:', event, session?.user?.id);
      
      try {
        if (event === 'SIGNED_IN' && session) {
          console.log('User signed in via Supabase');
          await tokenManager.setTokens(session.access_token, session.refresh_token);
          
          // Verify backend auth
          const isBackendAuth = await tokenManager.ensureAuthenticated();
          if (isBackendAuth && location.pathname === "/") {
            Navigate("/submit");
          }
        } else if (event === 'SIGNED_OUT') {
          console.log('User signed out via Supabase');
          await authUtils.signOut();
          Navigate("/");
        } else if (event === 'TOKEN_REFRESHED' && session) {
          console.log('Supabase token refreshed');
          await tokenManager.setTokens(session.access_token, session.refresh_token);
        }
      } catch (error) {
        console.error('Error handling auth state change:', error);
        setAuthError('Authentication error occurred');
      }
    });

    // Listen for custom auth events from API client
    const handleAuthLogout = () => {
      console.log('Received auth logout event');
      Navigate("/");
    };

    window.addEventListener('auth:logout', handleAuthLogout);

    return () => {
      subscription.unsubscribe();
      window.removeEventListener('auth:logout', handleAuthLogout);
    };
  }, [location.pathname, Navigate]);

  // Show loading or error states
  if (isAuthenticating) {
    return (
      <PageWrapper>
        <div className="flex items-center justify-center min-h-screen">
          <div className="text-center">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500 mx-auto"></div>
            <p className="mt-2 text-sm text-gray-600">Initializing...</p>
          </div>
        </div>
      </PageWrapper>
    );
  }

  if (authError) {
    return (
      <PageWrapper>
        <div className="flex items-center justify-center min-h-screen">
          <div className="text-center">
            <p className="text-red-500 mb-2">{authError}</p>
            <button 
              onClick={() => {
                setAuthError(null);
                window.location.reload();
              }}
              className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
            >
              Retry
            </button>
          </div>
        </div>
      </PageWrapper>
    );
  }







  return (
    <AnimatePresence mode="wait">
      <Routes location={location} key={location.pathname}>
        <Route path="/" element={<PageWrapper><Intro /></PageWrapper>} />
        <Route path="/submit" element={<PageWrapper><ResponsePage /></PageWrapper>} />
        <Route path="/search" element={<PageWrapper><SearchPage Quote={quotes[Math.floor(Math.random() * quotes.length)] || "Keep learning, keep growing!"} /></PageWrapper>} />
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