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
  const [quotes, setQuotes] = useState<string[]>([    
  ]);

  function checkForCookie() {
    chrome.cookies.getAll({ url: "https://extension-auth.vercel.app" }, (cookies) => {
      const accessToken = cookies.find((cookie) => cookie.name === "access_token")?.value;

      if (accessToken && location.pathname === "/") {
        Navigate("/submit");
        localStorage.setItem("access_token", accessToken);
      } else {
        setTimeout(checkForCookie, 1000);
      }
    });
  }
  useEffect(()=>{
    checkForCookie();
  },[])

  

  useEffect(() => {
    const handleAuthFlow = async () => {

      const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });

      if (!tab?.url) return;



      try {
        const accessToken = localStorage.getItem("access_token");
        console.log("Access Token: ", accessToken);

        if (accessToken) {
          await chrome.cookies.set({
            url: import.meta.env.VITE_API_URL,
            name: 'access_token',
            value: accessToken,
            path: '/',
            domain: new URL(import.meta.env.VITE_API_URL).hostname
          });

          await chrome.cookies.set({
            url: 'https://hippocampus-backend-vvv9.onrender.com',
            name: 'access_token',
            value: accessToken,
            path: '/',
            domain: 'hippocampus-backend-vvv9.onrender.com'
          });

          const cookie = await chrome.cookies.get({
            url: tab.url,
            name: 'access_token',
          });
          if(localStorage.getItem("quotes")){
            console.log("found Quotes")
            setQuotes(JSON.parse(localStorage.getItem("quotes") || "[]"));
            console.log("have set the quotes")
          }else{chrome.runtime.sendMessage(
            {
              cookies: localStorage.getItem("access_token"),
              action: "getQuotes"
            },
            (response) => {
              if (response.success) {
    
                if (response.data) {
                  const filteredQuotes = response.data.filter((quote: string) => quote.length > 0);
                  setQuotes(prev => [
                    ...new Set([...prev, ...filteredQuotes])
                    
                  ]);
                  console.log("GOT QUOTES FROM BAKCEND")
                  localStorage.setItem("quotes", JSON.stringify(filteredQuotes));
                  console.log("Quotes are set")
                }
    
              } else {
              }
            }
          );}


          if (cookie && location.pathname === "/") {
            Navigate("/submit");


          }
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