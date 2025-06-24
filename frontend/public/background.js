// Enhanced backend URL configuration
const BASE_URL = process.env.NODE_ENV === 'production' 
  ? 'https://hippocampus-backend-vvv9.onrender.com'
  : 'http://127.0.0.1:8000';

chrome.action.onClicked.addListener((tab) => {
  chrome.scripting.insertCSS({
    target: { tabId: tab.id },
    files: ["content.css"]
  });

  chrome.scripting.executeScript({
    target: { tabId: tab.id },
    files: ["content.js"]
  });
});

// Enhanced token management
async function getStoredTokens() {
  return new Promise((resolve) => {
    chrome.storage.local.get(['access_token', 'refresh_token'], (result) => {
      resolve({
        access_token: result.access_token,
        refresh_token: result.refresh_token
      });
    });
  });
}

async function storeTokens(accessToken, refreshToken) {
  return new Promise((resolve) => {
    chrome.storage.local.set({
      access_token: accessToken,
      refresh_token: refreshToken,
      token_timestamp: Date.now()
    }, resolve);
  });
}

async function clearStoredTokens() {
  return new Promise((resolve) => {
    chrome.storage.local.remove(['access_token', 'refresh_token', 'token_timestamp'], resolve);
  });
}

// Enhanced token refresh with proper error handling
async function refreshTokenIfNeeded(originalResponse) {
  if (originalResponse.status === 401) {
    try {
      console.log('Token expired, attempting refresh...');
      
      const tokens = await getStoredTokens();
      if (!tokens.refresh_token) {
        console.log('No refresh token available');
        await clearStoredTokens();
        throw new Error('No refresh token available');
      }

      // Attempt to refresh the access token using backend endpoint
      const refreshResponse = await fetch(`${BASE_URL}/auth/refresh`, {
        method: 'POST',
        credentials: 'include',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ refresh_token: tokens.refresh_token })
      });

      if (refreshResponse.ok) {
        const tokenData = await refreshResponse.json();
        
        if (tokenData.access_token) {
          // Store new tokens
          await storeTokens(
            tokenData.access_token, 
            tokenData.refresh_token || tokens.refresh_token
          );
          
          console.log('Token refresh successful');
          return tokenData.access_token;
        }
      } else {
        console.error('Token refresh failed:', refreshResponse.status);
        await clearStoredTokens();
      }
    } catch (error) {
      console.error('Token refresh error:', error);
      await clearStoredTokens();
    }
  }
  return null;
}

// Enhanced fetch with comprehensive auth handling
async function fetchWithAuth(url, options = {}) {
  const tokens = await getStoredTokens();
  
  // Prepare headers with authentication
  const headers = {
    'Content-Type': 'application/json',
    ...options.headers
  };

  if (tokens.access_token) {
    headers['Authorization'] = `Bearer ${tokens.access_token}`;
  }

  const fetchOptions = {
    ...options,
    headers,
    credentials: 'include' // Include cookies for backend auth
  };

  try {
    let response = await fetch(url, fetchOptions);
    
    // If unauthorized, try to refresh token
    if (response.status === 401 && tokens.access_token) {
      console.log('Received 401, attempting token refresh...');
      
      const newAccessToken = await refreshTokenIfNeeded(response);
      
      if (newAccessToken) {
        // Retry with new token
        fetchOptions.headers['Authorization'] = `Bearer ${newAccessToken}`;
        response = await fetch(url, fetchOptions);
        
        if (response.status === 401) {
          console.log('Still unauthorized after refresh, clearing tokens');
          await clearStoredTokens();
          throw new Error('Authentication failed after token refresh');
        }
      } else {
        console.log('Token refresh failed, clearing stored tokens');
        await clearStoredTokens();
        throw new Error('Authentication failed - no valid tokens');
      }
    }
    
    return response;
  } catch (error) {
    console.error('Fetch with auth failed:', error);
    throw error;
  }
}
// Enhanced message listener with better error handling
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  console.log('Received message:', message.action);

  // Search all data sources
  if (message.action === "searchAll") {
    Promise.all([
      fetchWithAuth(`${BASE_URL}/links/get`),
      fetchWithAuth(`${BASE_URL}/notes`)
    ])
    .then(async ([linksResponse, notesResponse]) => {
      const linksData = linksResponse.ok ? await linksResponse.json() : [];
      const notesData = notesResponse.ok ? await notesResponse.json() : [];
      sendResponse({ success: true, links: linksData, notes: notesData });
    })
    .catch(error => {
      console.error('Search all failed:', error);
      sendResponse({ success: false, error: error.message });
    });
    return true;
  }

  // Search with query
  else if (message.action === "search") {
    const fetchOptions = {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      }
    };

    if (message.type !== "All") {
      fetchOptions.body = JSON.stringify({ type: { $eq: message.type } });
    }

    fetchWithAuth(`${BASE_URL}/links/search?query=${encodeURIComponent(message.query)}`, fetchOptions)
      .then(async (response) => {
        if (response.ok) {
          const data = await response.json();
          console.log("Search response:", data);
          sendResponse({ success: true, data });
        } else {
          const errorData = await response.json().catch(() => ({ detail: 'Search failed' }));
          sendResponse({ success: false, error: errorData.detail || 'Search failed' });
        }
      })
      .catch(error => {
        console.error('Search failed:', error);
        sendResponse({ success: false, error: error.message });
      });
    return true;
  }

  // Submit/save data
  else if (message.action === "submit") {
    fetchWithAuth(`${BASE_URL}/links/save`, {
      method: 'POST',
      body: JSON.stringify(message.data)
    })
      .then(async (response) => {
        if (response.ok) {
          const data = await response.json();
          sendResponse({ success: true, data });
        } else {
          const errorData = await response.json().catch(() => ({ detail: 'Save failed' }));
          sendResponse({ success: false, error: errorData.detail || 'Save failed' });
        }
      })
      .catch(error => {
        console.error("Submit error:", error);
        sendResponse({ success: false, error: error.message });
      });
    return true;
  }

  // Save notes
  else if (message.action === "saveNotes") {
    fetchWithAuth(`${BASE_URL}/notes`, {
      method: 'POST',
      body: JSON.stringify(message.data)
    })
      .then(async (response) => {
        if (response.ok) {
          const data = await response.json();
          sendResponse({ success: true, data });
        } else {
          const errorData = await response.json().catch(() => ({ detail: 'Save notes failed' }));
          sendResponse({ success: false, error: errorData.detail || 'Save notes failed' });
        }
      })
      .catch(error => {
        console.error("Save notes error:", error);
        sendResponse({ success: false, error: error.message });
      });
    return true;
  }

  // Get quotes
  else if (message.action === "getQuotes") {
    fetchWithAuth(`${BASE_URL}/quotes`)
      .then(async (response) => {
        if (response.ok) {
          const data = await response.json();
          sendResponse({ success: true, data });
        } else {
          const errorData = await response.json().catch(() => ({ detail: 'Get quotes failed' }));
          sendResponse({ success: false, error: errorData.detail || 'Get quotes failed' });
        }
      })
      .catch(error => {
        console.error("Get quotes error:", error);
        sendResponse({ success: false, error: error.message });
      });
    return true;
  }

  // Delete item
  else if (message.action === "delete") {
    fetchWithAuth(`${BASE_URL}/links/delete?doc_id_pincone=${encodeURIComponent(message.query)}`, {
      method: 'DELETE'
    })
      .then(async (response) => {
        if (response.ok) {
          const data = await response.json();
          sendResponse({ success: true, data });
        } else {
          const errorData = await response.json().catch(() => ({ detail: 'Delete failed' }));
          sendResponse({ success: false, error: errorData.detail || 'Delete failed' });
        }
      })
      .catch(error => {
        console.error("Delete error:", error);
        sendResponse({ success: false, error: error.message });
      });
    return true;
  }

  // Generate summary
  else if (message.action === "generateSummaryforContent") {
    fetchWithAuth(`${BASE_URL}/summary/generate`, {
      method: 'POST',
      body: JSON.stringify({ content: message.content })
    })
      .then(async (response) => {
        if (response.ok) {
          const data = await response.json();
          sendResponse({ success: true, data });
        } else {
          const errorData = await response.json().catch(() => ({ detail: 'Summary generation failed' }));
          sendResponse({ success: false, error: errorData.detail || 'Summary generation failed' });
        }
      })
      .catch(error => {
        console.error("Generate summary error:", error);
        sendResponse({ success: false, error: error.message });
      });
    return true;
  }

  // Health check
  else if (message.action === "healthCheck") {
    fetch(`${BASE_URL}/health`)
      .then(async (response) => {
        if (response.ok) {
          const data = await response.json();
          sendResponse({ success: true, data });
        } else {
          sendResponse({ success: false, error: 'Health check failed' });
        }
      })
      .catch(error => {
        console.error("Health check error:", error);
        sendResponse({ success: false, error: error.message });
      });
    return true;
  }

  // Auth status check
  else if (message.action === "checkAuthStatus") {
    fetchWithAuth(`${BASE_URL}/auth/status`)
      .then(async (response) => {
        if (response.ok) {
          const data = await response.json();
          sendResponse({ success: true, data });
        } else {
          sendResponse({ success: false, error: 'Auth status check failed' });
        }
      })
      .catch(error => {
        console.error("Auth status check error:", error);
        sendResponse({ success: false, error: error.message });
      });
    return true;
  }

  // Unknown action
  else {
    console.warn('Unknown action:', message.action);
    sendResponse({ success: false, error: 'Unknown action' });
  }
});