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
    chrome.cookies.getAll({ url: "https://extension-auth.vercel.app" }, async (cookies) => {
      const accessToken = cookies.find((cookie) => cookie.name === "access_token")?.value;
      const refreshToken = cookies.find((cookie) => cookie.name === "refresh_token")?.value;

      if (accessToken && location.pathname === "/") {
        try {
          console.log('External auth tokens detected, transferring to backend...');
          // Wait for cookies to be set before navigating
          await setBackendCookies(accessToken, refreshToken);
          
          // Double-check that cookies were properly set
          const verificationCookie = await new Promise<chrome.cookies.Cookie | null>((resolve) => {
            chrome.cookies.get({
              url: 'https://hippocampus-cyfo.onrender.com',
              name: 'access_token'
            }, (cookie) => {
              resolve(cookie);
            });
          });
          
          if (verificationCookie) {
            console.log('Backend cookies set successfully, navigating to submit');
            Navigate("/submit");
          } else {
            throw new Error('Cookie verification failed');
          }
        } catch (error) {
          console.error('Failed to set backend cookies:', error);
          // Retry after a short delay
          setTimeout(() => checkForExternalAuth(), 2000);
        }
      } else {
        setTimeout(checkForExternalAuth, 1000);
      }
    });
  }

  // Helper function to set backend cookies directly from external auth
  const setBackendCookies = async (accessToken: string, refreshToken?: string) => {
    try {
      const apiUrl = 'https://hippocampus-cyfo.onrender.com';
      
      // Set access token cookie and wait for completion
      await new Promise<void>((resolve, reject) => {
        chrome.cookies.set({
          url: apiUrl,
          name: 'access_token',
          value: accessToken,
          path: '/',
          domain: 'hippocampus-cyfo.onrender.com',
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
            domain: 'hippocampus-cyfo.onrender.com',
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
    checkForExternalAuth();
  }, []);

  

  useEffect(() => {
    const handleAuthFlow = async () => {

      const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });

      if (!tab?.url) return;



      try {
        // Check if user is authenticated via backend cookies
        const cookie = await chrome.cookies.get({
          url: 'https://hippocampus-cyfo.onrender.com',
          name: 'access_token',
        });

        if (cookie && location.pathname === "/") {
          Navigate("/submit");
        }

        // Load quotes from localStorage or fetch from backend
        if(localStorage.getItem("quotes")){
          console.log("found Quotes")
          setQuotes(JSON.parse(localStorage.getItem("quotes") || "[]"));
          console.log("have set the quotes")
        }else{
          chrome.runtime.sendMessage(
            {
              action: "getQuotes"
            },
            (response) => {
              if (response.success) {
                if (response.data) {
                  const filteredQuotes = response.data.filter((quote: string) => quote.length > 0);
                  setQuotes(prev => [
                    ...new Set([...prev, ...filteredQuotes])
                  ]);
                  console.log("GOT QUOTES FROM BACKEND")
                  localStorage.setItem("quotes", JSON.stringify(filteredQuotes));
                  console.log("Quotes are set")
                }
              } else {
              }
            }
          );
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