// Content script for the auth site to access localStorage
console.log('Auth content script loaded on:', window.location.href);

// Listen for messages from the extension
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === "getTokensFromLocalStorage") {
    console.log('Content script: Getting tokens from localStorage');
    
    const accessToken = localStorage.getItem('access_token');
    const refreshToken = localStorage.getItem('refresh_token');
    const session = localStorage.getItem('session');
    
    console.log('Content script: Found tokens:', {
      hasAccessToken: !!accessToken,
      hasRefreshToken: !!refreshToken,
      hasSession: !!session
    });
    
    if (accessToken) {
      sendResponse({
        accessToken: accessToken,
        refreshToken: refreshToken,
        session: session ? JSON.parse(session) : null
      });
    } else {
      sendResponse({ accessToken: null, refreshToken: null, session: null });
    }
    
    return true; // Keep the messaging channel open for async response
  }
});

// Also check if tokens exist and try to set cookies if they're missing
function ensureTokensAreCookies() {
  const accessToken = localStorage.getItem('access_token');
  const refreshToken = localStorage.getItem('refresh_token');
  
  if (accessToken && refreshToken) {
    // Check if cookies already exist
    const cookies = document.cookie.split(';').reduce((acc, cookie) => {
      const [name, value] = cookie.trim().split('=');
      acc[name] = value;
      return acc;
    }, {});
    
    if (!cookies.access_token || !cookies.refresh_token) {
      console.log('Content script: Setting missing cookies from localStorage');
      
      // Try to get session data for expiration
      let expirationDate = new Date(Date.now() + 60 * 60 * 1000); // Default 1 hour
      const sessionData = localStorage.getItem('session');
      if (sessionData) {
        try {
          const session = JSON.parse(sessionData);
          if (session.expires_in) {
            expirationDate = new Date(Date.now() + (session.expires_in * 1000));
          }
        } catch (e) {
          console.log('Could not parse session data:', e);
        }
      }
      
      // Set cookies with proper attributes
      document.cookie = `access_token=${accessToken}; path=/; SameSite=None; Secure; expires=${expirationDate.toUTCString()}`;
      document.cookie = `refresh_token=${refreshToken}; path=/; SameSite=None; Secure; expires=${new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toUTCString()}`;
      
      console.log('Content script: Cookies set from localStorage');
      
      // Notify background script that auth is complete
      chrome.runtime.sendMessage({ action: "authCompleted" }).catch(error => {
        console.log('Could not notify background script:', error);
      });
    }
  }
}

// Monitor localStorage changes
let lastAccessToken = localStorage.getItem('access_token');
function checkForTokenChanges() {
  const currentAccessToken = localStorage.getItem('access_token');
  if (currentAccessToken && currentAccessToken !== lastAccessToken) {
    console.log('Content script: New token detected in localStorage');
    lastAccessToken = currentAccessToken;
    ensureTokensAreCookies();
  }
}

// Run on page load
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', ensureTokensAreCookies);
} else {
  ensureTokensAreCookies();
}

// Also run periodically in case auth completes after page load
setTimeout(ensureTokensAreCookies, 2000);
setTimeout(ensureTokensAreCookies, 5000);

// Monitor for changes more frequently
setInterval(checkForTokenChanges, 1000);
