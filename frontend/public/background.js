// Configuration - will be replaced during build
const BACKEND_URL = 'https://hippocampus-puxn.onrender.com';
const API_URL = '__VITE_API_URL__';

// Subscription upgrade messages
const SUBSCRIPTION_MESSAGES = {
  memory_limit: {
    title: "Memory Limit Reached",
    message: "You've reached your limit of 100 saved memories on the Free plan. Upgrade to Pro for unlimited memories!",
    benefits: ["Unlimited memory saves", "Up to 100 summary pages per month", "Priority support"],
    action: "Upgrade to Pro ($8/month)"
  },
  summary_limit: {
    title: "Summary Limit Reached", 
    message: "You've used all 5 summary pages for this month on the Free plan. Upgrade to Pro for 100 pages per month!",
    benefits: ["Up to 100 summary pages monthly", "Unlimited memory saves", "Priority support"],
    action: "Upgrade to Pro ($8/month)"
  },
  generic: {
    title: "Subscription Limit Reached",
    message: "You've reached a limit on your current plan. Upgrade to Pro for expanded access!",
    benefits: ["Unlimited memory saves", "Up to 100 summary pages monthly", "Priority support"],
    action: "Upgrade to Pro ($8/month)"
  }
};

// Function to determine limit type from error response
function getSubscriptionLimitType(errorData) {
  if (!errorData || !errorData.detail) return 'generic';
  
  const detail = errorData.detail.toLowerCase();
  if (detail.includes('memory') || detail.includes('save')) {
    return 'memory_limit';
  } else if (detail.includes('summary') || detail.includes('page')) {
    return 'summary_limit';
  }
  return 'generic';
}

// Function to show upgrade notification
function showUpgradeNotification(limitType = 'generic') {
  const message = SUBSCRIPTION_MESSAGES[limitType];
  
  chrome.notifications.create({
    type: 'basic',
    iconUrl: 'HippoCampusLogo.png',
    title: message.title,
    message: message.message + "\n\n" + message.benefits.join("\n• "),
    buttons: [{title: message.action}, {title: "Maybe Later"}]
  });
  
  console.log(`💰 BACKGROUND: Subscription limit reached - ${limitType}`);
}

// Handle notification clicks for subscription upgrades
chrome.notifications.onClicked.addListener((notificationId) => {
  // Open upgrade page when notification is clicked
  const upgradeUrl = `${BACKEND_URL.replace('/api', '')}/upgrade`; // Assuming frontend has an upgrade page
  chrome.tabs.create({ url: upgradeUrl });
  chrome.notifications.clear(notificationId);
});

chrome.notifications.onButtonClicked.addListener((notificationId, buttonIndex) => {
  if (buttonIndex === 0) {
    // "Upgrade to Pro" button clicked
    const upgradeUrl = `${BACKEND_URL.replace('/api', '')}/upgrade`;
    chrome.tabs.create({ url: upgradeUrl });
  }
  // "Maybe Later" button (index 1) - just dismiss the notification
  chrome.notifications.clear(notificationId);
});

// Multi-domain cookie cleanup function
async function clearAllAuthCookies() {
  console.log('🧹 BACKGROUND: Starting comprehensive cookie cleanup across all domains');
  
  // All domains where auth cookies might exist
  const domains = [
    'https://hippocampus-puxn.onrender.com',
    'https://extension-auth.vercel.app',
    'http://127.0.0.1:8000',
    BACKEND_URL
  ];
  
  // All possible auth cookie names
  const authCookieNames = [
    'access_token',
    'refresh_token',
    'user_id',
    'user_name',
    'user_picture'
  ];
  
  for (const domain of domains) {
    console.log(`   ├─ Clearing cookies from domain: ${domain}`);
    for (const cookieName of authCookieNames) {
      try {
        await chrome.cookies.remove({
          url: domain,
          name: cookieName
        });
        console.log(`   │  ✓ Cleared ${cookieName} from ${domain}`);
      } catch (error) {
        console.warn(`   │  ⚠️  Failed to clear ${cookieName} from ${domain}:`, error);
      }
    }
  }
  
  console.log('✅ BACKGROUND: Multi-domain cookie cleanup completed');
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
        console.log('🔍 BACKGROUND: Starting searchAll request');
        
        // Fetch links first with retry logic
        let linksResponse;
        let retryCount = 0;
        const maxRetries = 3;
        
        while (retryCount < maxRetries) {
          try {
            linksResponse = await fetch(`${BACKEND_URL}/links/get`, {
              method: 'GET',
              credentials: 'include',
              headers: { 
                'Content-Type': 'application/json'
              }
            });
            
            if (linksResponse.ok) {
              console.log('✅ BACKGROUND: Links fetch successful');
              break; // Success, exit retry loop
            } else if (linksResponse.status === 401 && retryCount < maxRetries - 1) {
              console.log(`⚠️  BACKGROUND: Links fetch got 401, retry ${retryCount + 1}/${maxRetries}`);
              retryCount++;
              await new Promise(resolve => setTimeout(resolve, 1000 * retryCount)); // Exponential backoff
              continue;
            } else {
              throw new Error(`Links fetch failed: ${linksResponse.status}`);
            }
          } catch (error) {
            if (retryCount < maxRetries - 1) {
              console.log(`⚠️  BACKGROUND: Links fetch error, retry ${retryCount + 1}/${maxRetries}:`, error.message);
              retryCount++;
              await new Promise(resolve => setTimeout(resolve, 1000 * retryCount));
            } else {
              throw error;
            }
          }
        }
        
        if (!linksResponse || !linksResponse.ok) {
          throw new Error(`Links fetch failed after ${maxRetries} retries`);
        }
        
        const linksData = await linksResponse.json();
        console.log('📦 BACKGROUND: Links data received');
        
        // Then fetch notes (reset retry count)
        let notesResponse;
        retryCount = 0;
        
        while (retryCount < maxRetries) {
          try {
            notesResponse = await fetch(`${BACKEND_URL}/notes/`, {
              method: 'GET',
              credentials: 'include',
              headers: { 
                'Content-Type': 'application/json'
              }
            });
            
            if (notesResponse.ok) {
              console.log('✅ BACKGROUND: Notes fetch successful');
              break; // Success, exit retry loop
            } else if (notesResponse.status === 401 && retryCount < maxRetries - 1) {
              console.log(`⚠️  BACKGROUND: Notes fetch got 401, retry ${retryCount + 1}/${maxRetries}`);
              retryCount++;
              await new Promise(resolve => setTimeout(resolve, 1000 * retryCount));
              continue;
            } else {
              throw new Error(`Notes fetch failed: ${notesResponse.status}`);
            }
          } catch (error) {
            if (retryCount < maxRetries - 1) {
              console.log(`⚠️  BACKGROUND: Notes fetch error, retry ${retryCount + 1}/${maxRetries}:`, error.message);
              retryCount++;
              await new Promise(resolve => setTimeout(resolve, 1000 * retryCount));
            } else {
              throw error;
            }
          }
        }
        
        if (!notesResponse || !notesResponse.ok) {
          throw new Error(`Notes fetch failed after ${maxRetries} retries`);
        }
        
        const notesData = await notesResponse.json();
        console.log('📦 BACKGROUND: Notes data received');
        
        console.log('✅ BACKGROUND: SearchAll completed successfully');
        sendResponse({ success: true, links: linksData, notes: notesData });
      } catch (error) {
        console.error('❌ BACKGROUND: SearchAll error:', error);
        sendResponse({ success: false, error: error.message });
      }
    }
    
    fetchAllData();
    return true;
  }

  else if (message.action === "search") {
    async function performSearch() {
      try {
        console.log('🔍 BACKGROUND: Starting search request');
        
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

        let response;
        let retryCount = 0;
        const maxRetries = 3;
        
        while (retryCount < maxRetries) {
          try {
            response = await fetch(`${BACKEND_URL}/links/search`, fetchOptions);
            
            if (response.ok) {
              console.log('✅ BACKGROUND: Search successful');
              break; // Success, exit retry loop
            } else if (response.status === 401 && retryCount < maxRetries - 1) {
              console.log(`⚠️  BACKGROUND: Search got 401, retry ${retryCount + 1}/${maxRetries}`);
              retryCount++;
              await new Promise(resolve => setTimeout(resolve, 1000 * retryCount));
              continue;
            } else {
              // Handle HTTP error responses
              const errorData = await response.json().catch(() => ({ detail: `HTTP error! status: ${response.status}` }));
              throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
            }
          } catch (error) {
            if (retryCount < maxRetries - 1) {
              console.log(`⚠️  BACKGROUND: Search error, retry ${retryCount + 1}/${maxRetries}:`, error.message);
              retryCount++;
              await new Promise(resolve => setTimeout(resolve, 1000 * retryCount));
            } else {
              throw error;
            }
          }
        }
        
        if (!response || !response.ok) {
          throw new Error(`Search failed after ${maxRetries} retries`);
        }
        
        const data = await response.json();
        console.log("✅ BACKGROUND: Search response received:", data);
        sendResponse({ success: true, data });
      } catch (error) {
        console.error("❌ BACKGROUND: Search error:", error);
        sendResponse({ success: false, error: error.message });
      }
    }
    
    performSearch();
    return true;
  }

  else if (message.action === "submit") {
    async function performSubmit() {
      try {
        console.log('📤 BACKGROUND: Starting submit request');
        
        let response;
        let retryCount = 0;
        const maxRetries = 3;
        
        while (retryCount < maxRetries) {
          try {
            response = await fetch(`${BACKEND_URL}/links/save`, {
              method: 'POST',
              credentials: 'include',
              headers: {
                'Content-Type': 'application/json'
              },
              body: JSON.stringify(message.data)
            });
            
            console.log(`📤 BACKGROUND: Submit response status: ${response.status}`);
            
            if (response.ok) {
              console.log('✅ BACKGROUND: Submit successful');
              break; // Success, exit retry loop
            } else if (response.status === 401 && retryCount < maxRetries - 1) {
              console.log(`⚠️  BACKGROUND: Submit got 401, retry ${retryCount + 1}/${maxRetries}`);
              retryCount++;
              await new Promise(resolve => setTimeout(resolve, 1000 * retryCount));
              continue;
            } else if (response.status === 402) {
              // Payment Required - subscription limit reached
              console.log('💰 BACKGROUND: Submit blocked - subscription limit reached');
              const errorData = await response.json().catch(() => ({ detail: 'Memory limit reached' }));
              const limitType = getSubscriptionLimitType(errorData);
              showUpgradeNotification(limitType);
              throw new Error(errorData.detail || 'Subscription limit reached. Please upgrade to continue.');
            } else {
              throw new Error(`HTTP error! status: ${response.status}`);
            }
          } catch (error) {
            if (retryCount < maxRetries - 1) {
              console.log(`⚠️  BACKGROUND: Submit error, retry ${retryCount + 1}/${maxRetries}:`, error.message);
              retryCount++;
              await new Promise(resolve => setTimeout(resolve, 1000 * retryCount));
            } else {
              throw error;
            }
          }
        }
        
        if (!response || !response.ok) {
          throw new Error(`Submit failed after ${maxRetries} retries`);
        }
        
        const data = await response.json();
        console.log("✅ BACKGROUND: Submit success:", data);
        sendResponse({ success: true, data });
      } catch (error) {
        console.error("❌ BACKGROUND: Submission error:", error);
        sendResponse({ success: false, error: error.message });
      }
    }
    
    performSubmit();
    return true;
  }
  else if (message.action === "saveNotes") {
    async function performSaveNotes() {
      try {
        console.log('📝 BACKGROUND: Starting saveNotes request');
        
        let response;
        let retryCount = 0;
        const maxRetries = 3;
        
        while (retryCount < maxRetries) {
          try {
            response = await fetch(`${BACKEND_URL}/notes/`, {
              method: 'POST',
              credentials: 'include',
              headers: {
                'Content-Type': 'application/json'
              },
              body: JSON.stringify(message.data)
            });
            
            console.log(`📝 BACKGROUND: SaveNotes response status: ${response.status}`);
            
            if (response.ok) {
              console.log('✅ BACKGROUND: SaveNotes successful');
              break; // Success, exit retry loop
            } else if (response.status === 401 && retryCount < maxRetries - 1) {
              console.log(`⚠️  BACKGROUND: SaveNotes got 401, retry ${retryCount + 1}/${maxRetries}`);
              retryCount++;
              await new Promise(resolve => setTimeout(resolve, 1000 * retryCount));
              continue;
            } else if (response.status === 402) {
              // Payment Required - subscription limit reached
              console.log('💰 BACKGROUND: SaveNotes blocked - subscription limit reached');
              const errorData = await response.json().catch(() => ({ detail: 'Notes limit reached' }));
              const limitType = getSubscriptionLimitType(errorData);
              showUpgradeNotification(limitType);
              throw new Error(errorData.detail || 'Subscription limit reached. Please upgrade to continue.');
            } else {
              throw new Error(`HTTP error! status: ${response.status}`);
            }
          } catch (error) {
            if (retryCount < maxRetries - 1) {
              console.log(`⚠️  BACKGROUND: SaveNotes error, retry ${retryCount + 1}/${maxRetries}:`, error.message);
              retryCount++;
              await new Promise(resolve => setTimeout(resolve, 1000 * retryCount));
            } else {
              throw error;
            }
          }
        }
        
        if (!response || !response.ok) {
          throw new Error(`SaveNotes failed after ${maxRetries} retries`);
        }
        
        const data = await response.json();
        console.log("✅ BACKGROUND: SaveNotes success:", data);
        sendResponse({ success: true, data });
      } catch (error) {
        console.error("❌ BACKGROUND: SaveNotes error:", error);
        sendResponse({ success: false, error: error.message });
      }
    }
    
    performSaveNotes();
    return true;
  }

  else if (message.action === "getQuotes") {
    async function performGetQuotes() {
      try {
        console.log('💬 BACKGROUND: Starting getQuotes request');
        
        let response;
        let retryCount = 0;
        const maxRetries = 3;
        
        while (retryCount < maxRetries) {
          try {
            response = await fetch(`${BACKEND_URL}/quotes/`, {
              method: 'GET',
              credentials: 'include'
            });
            
            if (response.ok) {
              console.log('✅ BACKGROUND: GetQuotes successful');
              break; // Success, exit retry loop
            } else if (response.status === 401 && retryCount < maxRetries - 1) {
              console.log(`⚠️  BACKGROUND: GetQuotes got 401, retry ${retryCount + 1}/${maxRetries}`);
              retryCount++;
              await new Promise(resolve => setTimeout(resolve, 1000 * retryCount));
              continue;
            } else {
              throw new Error(`HTTP error! status: ${response.status}`);
            }
          } catch (error) {
            if (retryCount < maxRetries - 1) {
              console.log(`⚠️  BACKGROUND: GetQuotes error, retry ${retryCount + 1}/${maxRetries}:`, error.message);
              retryCount++;
              await new Promise(resolve => setTimeout(resolve, 1000 * retryCount));
            } else {
              throw error;
            }
          }
        }
        
        if (!response || !response.ok) {
          throw new Error(`GetQuotes failed after ${maxRetries} retries`);
        }
        
        const data = await response.json();
        console.log('✅ BACKGROUND: GetQuotes response received');
        sendResponse({ success: true, data });
      } catch (error) {
        console.error('❌ BACKGROUND: GetQuotes error:', error);
        sendResponse({ success: false, error: error.message });
      }
    }
    
    performGetQuotes();
    return true;
  }
  
  else if (message.action === "delete") {
    async function performDelete() {
      try {
        console.log('🗑️ BACKGROUND: Starting delete request');
        
        let response;
        let retryCount = 0;
        const maxRetries = 3;
        
        while (retryCount < maxRetries) {
          try {
            response = await fetch(`${BACKEND_URL}/links/delete?doc_id_pincone=${encodeURIComponent(message.query)}`, {
              method: 'DELETE',
              credentials: 'include'
            });
            
            if (response.ok) {
              console.log('✅ BACKGROUND: Delete successful');
              break; // Success, exit retry loop
            } else if (response.status === 401 && retryCount < maxRetries - 1) {
              console.log(`⚠️  BACKGROUND: Delete got 401, retry ${retryCount + 1}/${maxRetries}`);
              retryCount++;
              await new Promise(resolve => setTimeout(resolve, 1000 * retryCount));
              continue;
            } else {
              throw new Error(`HTTP error! status: ${response.status}`);
            }
          } catch (error) {
            if (retryCount < maxRetries - 1) {
              console.log(`⚠️  BACKGROUND: Delete error, retry ${retryCount + 1}/${maxRetries}:`, error.message);
              retryCount++;
              await new Promise(resolve => setTimeout(resolve, 1000 * retryCount));
            } else {
              throw error;
            }
          }
        }
        
        if (!response || !response.ok) {
          throw new Error(`Delete failed after ${maxRetries} retries`);
        }
        
        const data = await response.json();
        console.log('✅ BACKGROUND: Delete response received');
        sendResponse({ success: true, data });
      } catch (error) {
        console.error('❌ BACKGROUND: Delete error:', error);
        sendResponse({ success: false, error: error.message });
      }
    }
    
    performDelete();
    return true;
  }
  
  else if (message.action === "deleteNote") {
    async function performDeleteNote() {
      try {
        console.log('🗑️ BACKGROUND: Starting deleteNote request');
        
        let response;
        let retryCount = 0;
        const maxRetries = 3;
        
        while (retryCount < maxRetries) {
          try {
            response = await fetch(`${BACKEND_URL}/notes/${encodeURIComponent(message.query)}`, {
              method: 'DELETE',
              credentials: 'include'
            });
            
            if (response.ok) {
              console.log('✅ BACKGROUND: DeleteNote successful');
              break; // Success, exit retry loop
            } else if (response.status === 401 && retryCount < maxRetries - 1) {
              console.log(`⚠️  BACKGROUND: DeleteNote got 401, retry ${retryCount + 1}/${maxRetries}`);
              retryCount++;
              await new Promise(resolve => setTimeout(resolve, 1000 * retryCount));
              continue;
            } else {
              throw new Error(`HTTP error! status: ${response.status}`);
            }
          } catch (error) {
            if (retryCount < maxRetries - 1) {
              console.log(`⚠️  BACKGROUND: DeleteNote error, retry ${retryCount + 1}/${maxRetries}:`, error.message);
              retryCount++;
              await new Promise(resolve => setTimeout(resolve, 1000 * retryCount));
            } else {
              throw error;
            }
          }
        }
        
        if (!response || !response.ok) {
          throw new Error(`DeleteNote failed after ${maxRetries} retries`);
        }
        
        const data = await response.json();
        console.log('✅ BACKGROUND: DeleteNote response received');
        sendResponse({ success: true, data });
      } catch (error) {
        console.error('❌ BACKGROUND: DeleteNote error:', error);
        sendResponse({ success: false, error: error.message });
      }
    }
    
    performDeleteNote();
    return true;
  }
  
  else if (message.action === "generateSummaryforContent") {
    async function performGenerateSummary() {
      try {
        console.log('📄 BACKGROUND: Starting generateSummary request');
        
        let response;
        let retryCount = 0;
        const maxRetries = 3;
        
        while (retryCount < maxRetries) {
          try {
            response = await fetch(`${BACKEND_URL}/summary/generate`, {
              method: 'POST',
              credentials: 'include',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({ content: message.content })
            });
            
            if (response.ok) {
              console.log('✅ BACKGROUND: GenerateSummary successful');
              break; // Success, exit retry loop
            } else if (response.status === 401 && retryCount < maxRetries - 1) {
              console.log(`⚠️  BACKGROUND: GenerateSummary got 401, retry ${retryCount + 1}/${maxRetries}`);
              retryCount++;
              await new Promise(resolve => setTimeout(resolve, 1000 * retryCount));
              continue;
            } else if (response.status === 402) {
              // Payment Required - subscription limit reached
              console.log('💰 BACKGROUND: GenerateSummary blocked - subscription limit reached');
              const errorData = await response.json().catch(() => ({ detail: 'Summary limit reached' }));
              const limitType = getSubscriptionLimitType(errorData);
              showUpgradeNotification(limitType);
              throw new Error(errorData.detail || 'Summary limit reached. Please upgrade to continue.');
            } else {
              throw new Error(`HTTP error! status: ${response.status}`);
            }
          } catch (error) {
            if (retryCount < maxRetries - 1) {
              console.log(`⚠️  BACKGROUND: GenerateSummary error, retry ${retryCount + 1}/${maxRetries}:`, error.message);
              retryCount++;
              await new Promise(resolve => setTimeout(resolve, 1000 * retryCount));
            } else {
              throw error;
            }
          }
        }
        
        if (!response || !response.ok) {
          throw new Error(`GenerateSummary failed after ${maxRetries} retries`);
        }
        
        const data = await response.json();
        console.log('✅ BACKGROUND: GenerateSummary response received');
        sendResponse({ success: true, data });
      } catch (error) {
        console.error('❌ BACKGROUND: GenerateSummary error:', error);
        sendResponse({ success: false, error: error.message });
      }
    }
    
    performGenerateSummary();
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

  else if (message.action === "clearAllCookies") {
    // Handle request to clear all auth cookies
    clearAllAuthCookies()
      .then(() => {
        sendResponse({ success: true, message: "All auth cookies cleared" });
      })
      .catch((error) => {
        console.error('Background cookie cleanup failed:', error);
        sendResponse({ success: false, error: error.message });
      });
    return true;
  }

  else {
    null
  }

});

// Enhanced cookie monitoring for authentication across all domains
chrome.cookies.onChanged.addListener((changeInfo) => {
  // Monitor the correct backend domain instead of API_URL
  const backendDomain = new URL(BACKEND_URL).hostname;
  
  if (changeInfo.cookie.domain === backendDomain &&
      (changeInfo.cookie.name === 'access_token' || changeInfo.cookie.name === 'refresh_token')) {
    
    if (!changeInfo.removed) {
      console.log(`🔑 BACKGROUND: Auth cookie detected on ${backendDomain}:`, changeInfo.cookie.name);
      console.log('   ├─ Triggering auth check across extension');
      
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
    } else {
      console.log(`🚫 BACKGROUND: Auth cookie removed from ${backendDomain}:`, changeInfo.cookie.name);
      console.log('   ├─ This may indicate logout or session expiration');
    }
  }
});