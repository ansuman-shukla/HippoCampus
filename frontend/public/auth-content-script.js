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

// Check if tokens exist and notify background script for auth completion
function checkForAuthCompletion() {
  const accessToken = localStorage.getItem('access_token');
  const refreshToken = localStorage.getItem('refresh_token');
  
  if (accessToken && refreshToken) {
    console.log('Content script: Auth tokens found, notifying background script');
    
    // Notify background script that auth is complete
    // Backend will handle cookie setting via login endpoint
    chrome.runtime.sendMessage({ action: "authCompleted" }).catch(error => {
      console.log('Could not notify background script:', error);
    });
  }
}

// Monitor localStorage changes
let lastAccessToken = localStorage.getItem('access_token');
function checkForTokenChanges() {
  const currentAccessToken = localStorage.getItem('access_token');
  if (currentAccessToken && currentAccessToken !== lastAccessToken) {
    console.log('Content script: New token detected in localStorage');
    lastAccessToken = currentAccessToken;
    checkForAuthCompletion();
  }
}

// Run on page load
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', checkForAuthCompletion);
} else {
  checkForAuthCompletion();
}

// Also run periodically in case auth completes after page load
setTimeout(checkForAuthCompletion, 2000);
setTimeout(checkForAuthCompletion, 5000);

// Monitor for changes more frequently
setInterval(checkForTokenChanges, 1000);
