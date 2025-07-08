// Content script for the auth site to access localStorage
console.log('🔐 AUTH CONTENT: Script loaded on:', window.location.href);

// Listen for messages from the extension
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === "getTokensFromLocalStorage") {
    console.log('🔍 AUTH CONTENT: Getting tokens from localStorage');
    
    const accessToken = localStorage.getItem('access_token');
    const refreshToken = localStorage.getItem('refresh_token');
    const session = localStorage.getItem('session');
    
    console.log('📋 AUTH CONTENT: Found tokens:', {
      hasAccessToken: !!accessToken,
      hasRefreshToken: !!refreshToken,
      hasSession: !!session,
      accessTokenLength: accessToken ? accessToken.length : 0,
      refreshTokenLength: refreshToken ? refreshToken.length : 0
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
    console.log('✅ AUTH CONTENT: Auth tokens found, notifying background script');
    console.log(`   ├─ Access token length: ${accessToken.length}`);
    console.log(`   └─ Refresh token length: ${refreshToken.length}`);
    
    // Notify background script that auth is complete
    // Backend will handle cookie setting via login endpoint
    chrome.runtime.sendMessage({ action: "authCompleted" }).catch(error => {
      console.log('⚠️  AUTH CONTENT: Could not notify background script:', error);
    });
    
    return true; // Auth found
  }
  return false; // No auth found
}

// Monitor localStorage changes with enhanced detection
let lastAccessToken = localStorage.getItem('access_token');
let checkInterval;

function startTokenMonitoring() {
  console.log('👀 AUTH CONTENT: Starting token monitoring');
  
  // Check immediately
  if (checkForAuthCompletion()) {
    return; // Auth already complete
  }
  
  // Monitor with interval
  checkInterval = setInterval(() => {
    const currentAccessToken = localStorage.getItem('access_token');
    
    if (currentAccessToken && currentAccessToken !== lastAccessToken) {
      console.log('🔄 AUTH CONTENT: New token detected in localStorage');
      lastAccessToken = currentAccessToken;
      
      if (checkForAuthCompletion()) {
        // Stop monitoring once auth is complete
        clearInterval(checkInterval);
        console.log('🎉 AUTH CONTENT: Auth completion detected, stopping monitoring');
      }
    }
  }, 500); // Check every 500ms for faster detection
  
  // Stop monitoring after 60 seconds to prevent indefinite running
  setTimeout(() => {
    if (checkInterval) {
      clearInterval(checkInterval);
      console.log('⏰ AUTH CONTENT: Token monitoring timeout after 60 seconds');
    }
  }, 60000);
}

// Run on page load
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', startTokenMonitoring);
} else {
  startTokenMonitoring();
}

// Also run after delays to catch auth that happens after page load
setTimeout(() => {
  if (!lastAccessToken) {
    console.log('🔍 AUTH CONTENT: Delayed check at 2 seconds');
    checkForAuthCompletion();
  }
}, 2000);

setTimeout(() => {
  if (!lastAccessToken) {
    console.log('🔍 AUTH CONTENT: Final delayed check at 5 seconds');
    checkForAuthCompletion();
  }
}, 5000);
