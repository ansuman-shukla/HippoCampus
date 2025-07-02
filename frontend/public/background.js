// Configuration - will be replaced during build
const BACKEND_URL = '__VITE_BACKEND_URL__';
const API_URL = '__VITE_API_URL__';

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
    const fetchOptions = {
      method: 'POST',
      credentials: 'include',
      headers: {
        'Content-Type': 'application/json'
      }
    };

    if (message.type !== "All") {
      fetchOptions.body = JSON.stringify({ type: { $eq: message.type } });
    }

    fetch(`${BACKEND_URL}/links/search?query=${message.query}`, fetchOptions)
      .then(response => response.json())
      .then(data => {
        console.log("The response is:", data);
        sendResponse({ success: true, data });
      })
      .catch(error => sendResponse({ success: false, error: error.message }));

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
      .then(data => sendResponse({ success: true, data }))
      .catch(error => sendResponse({ success: false, error: error.message }));
    return true;
  }
  else if (message.action === "delete") {
    fetch(`${BACKEND_URL}/links/delete?doc_id_pincone=${message.query}`, {
      method: 'DELETE',
      credentials: 'include'
    })
      .then(response => response.json())
      .then(data => sendResponse({ success: true, data }))
      .catch(error => sendResponse({ success: false, error: error.message }));
    return true;
  }
  else if (message.action === "deleteNote") {
    fetch(`${BACKEND_URL}/notes/${message.query}`, {
      method: 'DELETE',
      credentials: 'include'
    })
      .then(response => response.json())
      .then(data => sendResponse({ success: true, data }))
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
      .then(data => sendResponse({ success: true, data }))
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

// Monitor cookie changes for authentication
chrome.cookies.onChanged.addListener((changeInfo) => {
  if (changeInfo.cookie.domain === new URL(API_URL).hostname + '/' && 
      (changeInfo.cookie.name === 'access_token' || changeInfo.cookie.name === 'refresh_token') &&
      !changeInfo.removed) {
    console.log('Auth cookie detected, triggering auth check');
    
    // Notify extension about potential auth completion
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