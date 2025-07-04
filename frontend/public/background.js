// Configuration - will be replaced during build
const BACKEND_URL = 'https://hippocampus-puxn.onrender.com';
const API_URL = '__VITE_API_URL__';

// Helper function to notify frontend about potential authentication changes
function notifyAuthStateChange() {
  console.log('Notifying frontend about potential auth state change');
  chrome.tabs.query({}, (tabs) => {
    tabs.forEach(tab => {
      if (tab.url && tab.url.includes('chrome-extension://')) {
        chrome.tabs.sendMessage(tab.id, { action: "authStateChanged" }).catch(() => {
          // Ignore errors if extension popup is not active
        });
      }
    });
  });
}

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






chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.action === "searchAll") {
    // Make requests sequentially to avoid race conditions with token refresh
    async function fetchAllData() {
      try {
        // Fetch links first
        const linksResponse = await fetch(`${BACKEND_URL}/links/get`, {
      method: 'GET',
      credentials: 'include',
      headers: { 
        'Content-Type': 'application/json'
      }
        });
        
        if (!linksResponse.ok) {
          throw new Error(`Links fetch failed: ${linksResponse.status}`);
        }
        
        const linksData = await linksResponse.json();
        
        // Then fetch notes (token refresh will have happened in first request if needed)
        const notesResponse = await fetch(`${BACKEND_URL}/notes/`, {
      method: 'GET',
      credentials: 'include',
      headers: { 
        'Content-Type': 'application/json'
      }
        });
        
        if (!notesResponse.ok) {
          throw new Error(`Notes fetch failed: ${notesResponse.status}`);
        }
        
                const notesData = await notesResponse.json();
        
        // Notify frontend that API calls completed (might have refreshed tokens)
        notifyAuthStateChange();
        sendResponse({ success: true, links: linksData, notes: notesData });
      } catch (error) {
        console.error('SearchAll error:', error);
      sendResponse({ success: false, error: error.message });
      }
    }
    
    fetchAllData();
    return true;
  }

  



  else if (message.action === "search") {
    const requestBody = {
      query: message.query
    };

    if (message.type !== "All") {
      requestBody.filter = { type: { $eq: message.type } };
    }

    const fetchOptions = {
      method: 'POST',
      credentials: 'include',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(requestBody)
    };

    fetch(`${BACKEND_URL}/links/search`, fetchOptions)
      .then(response => {
        if (!response.ok) {
          // Handle HTTP error responses
          return response.json().then(errorData => {
            throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
          });
        }
        return response.json();
      })
      .then(data => {
        console.log("The response is:", data);
        // Notify frontend that an API call completed (might have refreshed tokens)
        notifyAuthStateChange();
        sendResponse({ success: true, data });
      })
      .catch(error => {
        console.error("Search error:", error);
        sendResponse({ success: false, error: error.message });
      });

    return true;
  }

  else if (message.action === "submit") {
    fetch(`${BACKEND_URL}/links/save`, {
      method: 'POST',
      credentials: 'include',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(message.data)
    })
      .then(response => {
        console.log("Submit response status:", response.status);
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        return response.json();
      })
      .then(data => {
        console.log("Submit success:", data);
        // Notify frontend that an API call completed (might have refreshed tokens)
        notifyAuthStateChange();
        sendResponse({ success: true, data });
      })
      .catch(error => {
        console.error("Submission error:", error);
        sendResponse({ success: false, error: error.message });
      });
    return true;
  }
  else if (message.action === "saveNotes") {
    fetch(`${BACKEND_URL}/notes/`, {
      method: 'POST',
      credentials: 'include',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(message.data)
    })
      .then(response => {
        console.log("SaveNotes response status:", response.status);
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        return response.json();
      })
      .then(data => {
        console.log("SaveNotes success:", data);
        // Notify frontend that an API call completed (might have refreshed tokens)
        notifyAuthStateChange();
        sendResponse({ success: true, data });
      })
      .catch(error => {
        console.error("SaveNotes error:", error);
        sendResponse({ success: false, error: error.message });
      });
    return true;
  }

  else if (message.action === "getQuotes") {
    fetch(`${BACKEND_URL}/quotes/`, {
      method: 'GET',
      credentials: 'include'
    })
      .then(response => response.json())
      .then(data => {
        // Notify frontend that an API call completed (might have refreshed tokens)
        notifyAuthStateChange();
        sendResponse({ success: true, data });
      })
      .catch(error => sendResponse({ success: false, error: error.message }));
    return true;
  }
  else if (message.action === "delete") {
    fetch(`${BACKEND_URL}/links/delete?doc_id_pincone=${encodeURIComponent(message.query)}`, {
      method: 'DELETE',
      credentials: 'include'
    })
      .then(response => response.json())
      .then(data => {
        // Notify frontend that an API call completed (might have refreshed tokens)
        notifyAuthStateChange();
        sendResponse({ success: true, data });
      })
      .catch(error => sendResponse({ success: false, error: error.message }));
    return true;
  }
  else if (message.action === "deleteNote") {
    fetch(`${BACKEND_URL}/notes/${encodeURIComponent(message.query)}`, {
      method: 'DELETE',
      credentials: 'include'
    })
      .then(response => response.json())
      .then(data => {
        // Notify frontend that an API call completed (might have refreshed tokens)
        notifyAuthStateChange();
        sendResponse({ success: true, data });
      })
      .catch(error => sendResponse({ success: false, error: error.message }));
    return true;
  }
  else if (message.action === "generateSummaryforContent") {
    fetch(`${BACKEND_URL}/summary/generate`, {
      method: 'POST',
      credentials: 'include',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ content: message.content })
    })
      .then(response => response.json())
      .then(data => {
        // Notify frontend that an API call completed (might have refreshed tokens)
        notifyAuthStateChange();
        sendResponse({ success: true, data });
      })
      .catch(error => sendResponse({ success: false, error: error.message }));
    return true;
  }

  else if (message.action === "authCompleted") {
    // Notify all extension windows that auth has completed
    chrome.tabs.query({}, (tabs) => {
      tabs.forEach(tab => {
        if (tab.url && tab.url.includes('chrome-extension://')) {
          chrome.tabs.sendMessage(tab.id, { action: "authStateChanged" }).catch(() => {
            // Ignore errors if extension popup is not active
          });
        }
      });
    });
    sendResponse({ success: true });
    return true;
  }

  else {
    null
  }

});

// Monitor cookie changes for authentication on both auth and backend domains
chrome.cookies.onChanged.addListener((changeInfo) => {
  const authDomain = API_URL !== '__VITE_API_URL__' ? new URL(API_URL).hostname : null;
  const backendDomain = new URL(BACKEND_URL).hostname;
  const cookieDomain = changeInfo.cookie.domain;
  const cookieName = changeInfo.cookie.name;
  
  // Check if this is an auth-related cookie on either domain
  const isAuthCookie = (cookieName === 'access_token' || cookieName === 'refresh_token');
  const isAuthDomain = (authDomain && cookieDomain === authDomain + '/') || cookieDomain === authDomain;
  const isBackendDomain = cookieDomain === backendDomain;
  
  if (isAuthCookie && (isAuthDomain || isBackendDomain) && !changeInfo.removed) {
    const source = isAuthDomain ? 'auth page' : 'backend';
    console.log(`🍪 Auth cookie detected from ${source}: ${cookieName}`);
    console.log(`   Domain: ${cookieDomain}`);
    
    // Notify extension about potential auth completion or token refresh
    chrome.tabs.query({}, (tabs) => {
      tabs.forEach(tab => {
        if (tab.url && tab.url.includes('chrome-extension://')) {
          chrome.tabs.sendMessage(tab.id, { action: "checkAuthStatus" }).catch(() => {
            // Ignore errors if extension popup is not active
          });
        }
      });
    });
  }
});