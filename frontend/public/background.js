// Configuration - will be replaced during build
const BACKEND_URL = 'https://hippocampus-1.onrender.com';
// const BACKEND_URL = 'http://127.0.0.1:8000';
const API_URL = '__VITE_API_URL__';

// BACKGROUND SCRIPT STARTUP LOGGING
console.log('🚀 BACKGROUND: Service worker starting up');
console.log(`   ├─ Startup time: ${new Date().toISOString()}`);
console.log(`   ├─ Extension ID: ${chrome.runtime.id}`);
console.log(`   ├─ Backend URL: ${BACKEND_URL}`);

// Check available commands at startup
chrome.commands.getAll((commands) => {
  console.log('⌨️ BACKGROUND: Available keyboard commands:');
  commands.forEach(command => {
    console.log(`   ├─ Command: ${command.name}`);
    console.log(`   │  ├─ Description: ${command.description}`);
    console.log(`   │  ├─ Shortcut: ${command.shortcut || 'Not set'}`);
    console.log(`   │  └─ Global: ${command.global || false}`);
  });
  
  if (commands.length === 0) {
    console.warn('⚠️ BACKGROUND: No keyboard commands found! Check manifest.json');
  }
});

// Test if action listener is properly set up
console.log('🔧 BACKGROUND: Setting up extension action listener');
console.log('   ├─ This should respond to Alt+M and extension icon clicks');

// Add runtime startup event listener
chrome.runtime.onStartup.addListener(() => {
  console.log('🔄 BACKGROUND: Extension runtime started');
});

chrome.runtime.onInstalled.addListener((details) => {
  console.log('📦 BACKGROUND: Extension installed/updated');
  console.log(`   ├─ Reason: ${details.reason}`);
  console.log(`   ├─ Previous version: ${details.previousVersion || 'N/A'}`);
  
  // Re-check commands after installation
  setTimeout(() => {
    chrome.commands.getAll((commands) => {
      console.log('🔍 BACKGROUND: Post-install command check:');
      commands.forEach(command => {
        console.log(`   ├─ ${command.name}: ${command.shortcut || 'Not set'}`);
      });
    });
  }, 1000);
});

// Helper function to notify frontend of authentication failures
async function notifyAuthenticationFailure(reason = 'Authentication failed') {
  console.log('🚫 BACKGROUND: Notifying frontend of authentication failure');
  try {
    // Get all extension tabs/windows
    const tabs = await chrome.tabs.query({});
    
    // Send message to all extension contexts
    for (const tab of tabs) {
      if (tab.url && tab.url.includes('chrome-extension://')) {
        try {
          await chrome.tabs.sendMessage(tab.id, { 
            action: "authenticationFailed", 
            reason: reason 
          });
          console.log(`   ├─ Notified tab ${tab.id} of auth failure`);
        } catch (error) {
          // Ignore errors if tab is not ready to receive messages
          console.log(`   ├─ Could not notify tab ${tab.id}: ${error.message}`);
        }
      }
    }
    
    console.log('✅ BACKGROUND: Authentication failure notifications sent');
  } catch (error) {
    console.error('❌ BACKGROUND: Failed to notify frontend of auth failure:', error);
  }
}

// Generic helper function for making API calls with auth failure detection
async function makeAuthenticatedRequest(url, options, actionName, maxRetries = 3) {
  let retryCount = 0;
  let lastStatusCode = null;
  
  while (retryCount < maxRetries) {
    try {
      const response = await fetch(url, {
        credentials: 'include',
        headers: {
          'Content-Type': 'application/json'
        },
        ...options
      });
      
      lastStatusCode = response.status;
      
      if (response.ok) {
        console.log(`✅ BACKGROUND: ${actionName} successful`);
        return await response.json();
      } else if (response.status === 401 && retryCount < maxRetries - 1) {
        console.log(`⚠️  BACKGROUND: ${actionName} got 401, retry ${retryCount + 1}/${maxRetries}`);
        retryCount++;
        await new Promise(resolve => setTimeout(resolve, 1000 * retryCount));
        continue;
      } else {
        throw new Error(`${actionName} failed: ${response.status}`);
      }
    } catch (error) {
      if (retryCount < maxRetries - 1) {
        console.log(`⚠️  BACKGROUND: ${actionName} error, retry ${retryCount + 1}/${maxRetries}:`, error.message);
        retryCount++;
        await new Promise(resolve => setTimeout(resolve, 1000 * retryCount));
      } else {
        // Check if all retries failed due to authentication issues
        if (lastStatusCode === 401 || error.message.includes('401')) {
          console.log(`🚫 BACKGROUND: ${actionName} failed with authentication error after all retries`);
          notifyAuthenticationFailure(`${actionName} authentication failed after ${maxRetries} retries`);
        }
        throw new Error(`${actionName} failed after ${maxRetries} retries: ${error.message}`);
      }
    }
  }
}

// Multi-domain cookie cleanup function
async function clearAllAuthCookies() {
  console.log('🧹 BACKGROUND: Starting comprehensive cookie cleanup across all domains');
  
  // All domains where auth cookies might exist
  const domains = [
    'https://hippocampus-1.onrender.com',
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

// Test that action listener is registered
console.log('📋 BACKGROUND: Registering chrome.action.onClicked listener...');

// STEP 1: Alt+M Extension Action Handler
// This fires when the user clicks the extension icon OR presses Alt+M
chrome.action.onClicked.addListener((tab) => {
  console.log('🔥 BACKGROUND STEP 1: Extension action triggered (Alt+M or icon click)');
  console.log(`   ├─ Tab ID: ${tab.id}`);
  console.log(`   ├─ Tab URL: ${tab.url}`);
  console.log(`   ├─ Current time: ${new Date().toISOString()}`);
  console.log('   ├─ This confirms the action listener is working!');
  
  console.log('🎨 BACKGROUND STEP 2: Injecting CSS styles into target tab');
  chrome.scripting.insertCSS({
    target: { tabId: tab.id },
    files: ["content.css"]
  }).then(() => {
    console.log('✅ BACKGROUND STEP 2: CSS injection completed successfully');
  }).catch((error) => {
    console.error('❌ BACKGROUND STEP 2: CSS injection failed:', error);
  });

  console.log('📜 BACKGROUND STEP 3: Executing content script in target tab');
  chrome.scripting.executeScript({
    target: { tabId: tab.id },
    files: ["content.js"]
  }).then(() => {
    console.log('✅ BACKGROUND STEP 3: Content script execution completed successfully');
    console.log('   ├─ The content script should now toggle the sidebar');
    console.log('   ├─ Check the tab console for content script logs');
  }).catch((error) => {
    console.error('❌ BACKGROUND STEP 3: Content script execution failed:', error);
  });
});

console.log('✅ BACKGROUND: chrome.action.onClicked listener registered successfully');

// MANUAL TEST: Add a context menu item to test if background script is working
chrome.runtime.onInstalled.addListener(() => {
  chrome.contextMenus.create({
    id: "test-background-script",
    title: "🧪 Test Background Script (Alt+M)",
    contexts: ["page"]
  });
});

// Handle context menu clicks (this tests if background script is responsive)
chrome.contextMenus.onClicked.addListener((info, tab) => {
  if (info.menuItemId === "test-background-script") {
    console.log('🧪 BACKGROUND: Manual test triggered via context menu');
    console.log('   ├─ This confirms the background script is active and responsive');
    console.log('   ├─ Now manually executing the same logic as Alt+M shortcut');
    
    // Manually execute the same CSS injection and script execution as Alt+M
    console.log('🎨 BACKGROUND TEST: Injecting CSS styles into target tab');
    chrome.scripting.insertCSS({
      target: { tabId: tab.id },
      files: ["content.css"]
    }).then(() => {
      console.log('✅ BACKGROUND TEST: CSS injection completed successfully');
    }).catch((error) => {
      console.error('❌ BACKGROUND TEST: CSS injection failed:', error);
    });

    console.log('📜 BACKGROUND TEST: Executing content script in target tab');
    chrome.scripting.executeScript({
      target: { tabId: tab.id },
      files: ["content.js"]
    }).then(() => {
      console.log('✅ BACKGROUND TEST: Content script execution completed successfully');
    }).catch((error) => {
      console.error('❌ BACKGROUND TEST: Content script execution failed:', error);
    });
  }
});

// KEYBOARD SHORTCUT COMMAND HANDLER
chrome.commands.onCommand.addListener((command, tab) => {
  console.log('⌨️ BACKGROUND: Keyboard shortcut command received');
  console.log(`   ├─ Command: ${command}`);
  console.log(`   ├─ Tab ID: ${tab.id}`);
  console.log(`   ├─ Tab URL: ${tab.url}`);
  console.log(`   ├─ Current time: ${new Date().toISOString()}`);
  
  if (command === "quick_search") {
    console.log('🔍 BACKGROUND: Processing Alt+X (quick_search) command');
    
    // Alt+X: Open extension and focus on search
    console.log('🎨 BACKGROUND: Injecting CSS for Alt+X command');
    chrome.scripting.insertCSS({
      target: { tabId: tab.id },
      files: ["content.css"]
    }).then(() => {
      console.log('✅ BACKGROUND: CSS injection completed for Alt+X');
    }).catch((error) => {
      console.error('❌ BACKGROUND: CSS injection failed for Alt+X:', error);
    });

    console.log('📜 BACKGROUND: Executing content script for Alt+X command');
    chrome.scripting.executeScript({
      target: { tabId: tab.id },
      files: ["content.js"]
    }, () => {
      console.log('✅ BACKGROUND: Content script executed for Alt+X');
      console.log('⏱️ BACKGROUND: Setting up focus search message with 500ms delay');
      
      // Send message to focus on search after extension is loaded
      setTimeout(() => {
        console.log('📤 BACKGROUND: Sending focusSearch message to content script');
        chrome.tabs.sendMessage(tab.id, { 
          action: "focusSearch" 
        }).then(() => {
          console.log('✅ BACKGROUND: FocusSearch message sent successfully');
        }).catch((error) => {
          console.log("⚠️ BACKGROUND: Failed to send focusSearch message:", error);
          console.log('🔄 BACKGROUND: Trying alternative approach for already loaded scripts');
          
          // Try alternative approach for already loaded scripts
          chrome.scripting.executeScript({
            target: { tabId: tab.id },
            func: () => {
              console.log('🔄 CONTENT: Alternative focus approach executing');
              if (window.hippoCampusCreateSidebar) {
                console.log('✅ CONTENT: Found hippoCampusCreateSidebar function');
                const sidebar = window.hippoCampusCreateSidebar();
                if (sidebar) {
                  console.log('✅ CONTENT: Sidebar created successfully');
                  const iframe = sidebar.querySelector('iframe');
                  if (iframe) {
                    console.log('✅ CONTENT: Found iframe, sending focus message');
                    setTimeout(() => {
                      try {
                        iframe.contentWindow.postMessage({ action: "focusSearch" }, "*");
                        console.log('✅ CONTENT: Focus message sent to iframe');
                      } catch (err) {
                        console.error("❌ CONTENT: Failed to send focus message to iframe:", err);
                      }
                    }, 200);
                  } else {
                    console.warn('⚠️ CONTENT: No iframe found in sidebar');
                  }
                } else {
                  console.warn('⚠️ CONTENT: Failed to create sidebar');
                }
              } else {
                console.warn('⚠️ CONTENT: hippoCampusCreateSidebar function not available');
              }
            }
          });
        });
      }, 500);
    });
  } else {
    console.log(`⚠️ BACKGROUND: Unknown command received: ${command}`);
    console.log('   ├─ Expected commands: "quick_search" (Alt+X)');
    console.log('   ├─ Note: Alt+M should trigger chrome.action.onClicked, not commands');
  }
});






chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.action === "searchAll") {
    // Make requests sequentially to avoid race conditions with token refresh
    async function fetchAllData() {
      try {
        console.log('🔍 BACKGROUND: Starting searchAll request');
        
        // Make both API calls in parallel using the new helper function
        console.log('🚀 BACKGROUND: Starting parallel fetch for links and notes');
        const [linksData, notesData] = await Promise.all([
          makeAuthenticatedRequest(`${BACKEND_URL}/links/get`, { method: 'GET' }, 'Links fetch'),
          makeAuthenticatedRequest(`${BACKEND_URL}/notes/`, { method: 'GET' }, 'Notes fetch')
        ]);
        
        console.log('📦 BACKGROUND: Links data received');
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

        const data = await makeAuthenticatedRequest(
          `${BACKEND_URL}/links/search`,
          {
            method: 'POST',
            body: JSON.stringify(requestBody)
          },
          'Search'
        );
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
        
        const data = await makeAuthenticatedRequest(
          `${BACKEND_URL}/links/save`,
          {
            method: 'POST',
            body: JSON.stringify(message.data)
          },
          'Submit'
        );
        
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
        
        const data = await makeAuthenticatedRequest(
          `${BACKEND_URL}/quotes/`,
          { method: 'GET' },
          'GetQuotes'
        );
        
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
            } else if (response.status === 429) {
              // Rate limit exceeded - don't retry
              console.log('🚫 BACKGROUND: Genuine rate limit exceeded (HTTP 429)');
              console.log('   ├─ This is a legitimate rate limit from the backend API');
              throw new Error('RATE_LIMIT_EXCEEDED');
            } else if (response.status === 401 && retryCount < maxRetries - 1) {
              console.log(`⚠️  BACKGROUND: GenerateSummary got 401, retry ${retryCount + 1}/${maxRetries}`);
              retryCount++;
              await new Promise(resolve => setTimeout(resolve, 1000 * retryCount));
              continue;
            } else {
              throw new Error(`HTTP error! status: ${response.status}`);
            }
          } catch (error) {
            // Don't retry rate limit errors
            if (error.message === 'RATE_LIMIT_EXCEEDED') {
              throw error;
            }
            
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
        
        // Log specifically if this is a rate limit vs other error
        if (error.message === 'RATE_LIMIT_EXCEEDED') {
          console.log('📊 BACKGROUND: Confirmed rate limit error being sent to content script');
        } else {
          console.log('📊 BACKGROUND: Non-rate-limit error being sent to content script:', error.message);
        }
        
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