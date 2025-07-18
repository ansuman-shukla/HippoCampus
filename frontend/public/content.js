// Handle multiple script execution
if (window.hippoCampusContentScriptLoaded) {
  console.log("HippoCampus content script already loaded, executing toggle only");
  
  // Use global state to check current status
  const state = window.hippoCampusExtensionState || { isOpen: false, isInitializing: false };
  
  // Prevent multiple simultaneous operations
  if (state.isInitializing) {
    console.log("Extension operation already in progress, ignoring toggle");
  } else {
    // Handle toggle for already loaded script
    const existingSidebar = document.getElementById("my-extension-sidebar");
    console.log(`Debug: existingSidebar=${!!existingSidebar}, state.isOpen=${state.isOpen}`);
    
    if (existingSidebar && state.isOpen) {
      // Close existing sidebar
      console.log("Closing existing sidebar via global function");
      if (window.hippoCampusCloseSidebar) {
        window.hippoCampusCloseSidebar(existingSidebar);
      } else {
        console.log("Global close function not available, using fallback");
        state.isOpen = false;
        existingSidebar.style.animation = "slideOut 0.3s ease-in-out forwards";
        setTimeout(() => {
          if (existingSidebar.parentNode) {
            existingSidebar.remove();
          }
          document.removeEventListener("click", window.hippoCampusHandleClickOutside);
        }, 300);
      }
    } else if (!existingSidebar && !state.isOpen) {
      // Create new sidebar
      console.log("Creating new sidebar via global function");
      if (window.hippoCampusCreateSidebar) {
        window.hippoCampusCreateSidebar();
      } else {
        console.log("Global create function not available");
      }
    } else {
      console.log(`No action taken: existingSidebar=${!!existingSidebar}, state.isOpen=${state.isOpen}`);
    }
  }
} else {
  window.hippoCampusContentScriptLoaded = true;

if (window.location.protocol === "chrome:") {
  window.location.href = chrome.runtime.getURL("error.html");
}

// Flag to prevent duplicate summary generation requests
let isGeneratingSummary = false;

// Global state tracking
let extensionState = window.hippoCampusExtensionState || {
  isOpen: false,
  isInitializing: false
};

// Make state globally available
window.hippoCampusExtensionState = extensionState;

// Sync state with DOM on script load
const existingSidebarOnLoad = document.getElementById("my-extension-sidebar");
if (existingSidebarOnLoad && !extensionState.isOpen) {
  console.log("Found existing sidebar, syncing state");
  extensionState.isOpen = true;
}

chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.action === "closeExtension" && message.target === "content") {
    const sidebar = document.getElementById("my-extension-sidebar");
    if (sidebar) {
      sidebar.style.animation = "slideOut 0.3s ease-in-out forwards";
      setTimeout(() => {
        sidebar.remove();
        // Clean up click listener
        document.removeEventListener("click", window.hippoCampusHandleClickOutside || handleClickOutside);
      }, 300);
    }
    sendResponse({success: true});
  }
  
  if (message.action === "focusSearch") {
    // Alt+X handler: ensure extension is open and focus on search
    let sidebar = document.getElementById("my-extension-sidebar");
    
    if (!sidebar || !extensionState.isOpen) {
      // If sidebar doesn't exist, create it first
      sidebar = createSidebar();
      if (!sidebar) {
        console.log("Failed to create sidebar for focus search");
        sendResponse({success: false, error: "Failed to create sidebar"});
        return;
      }
    }
    
    // Send message to iframe to focus on search input
    if (sidebar) {
      const iframe = sidebar.querySelector('iframe');
      if (iframe) {
        // Wait for iframe to load before sending message
        setTimeout(() => {
          try {
            iframe.contentWindow.postMessage({ action: "focusSearch" }, "*");
            console.log("Focus search message sent to iframe");
          } catch (error) {
            console.error("Failed to send focus message to iframe:", error);
          }
        }, 200); // Increased delay to ensure iframe is loaded
      }
    }
    
    sendResponse({success: true});
  }
  if (message.action === "extractPageContent") {
    // Prevent duplicate summary generation
    if (isGeneratingSummary) {
      console.log("Summary generation already in progress, ignoring duplicate request");
      sendResponse({ error: "Summary generation already in progress" });
      return;
    }
    
    isGeneratingSummary = true;
    
    const elements = Array.from(document.querySelectorAll('div, p, a'));
    const seen = new Set();
    let lines = elements
      .filter(el => !el.querySelector('div, p, a'))
      .filter(el => {
        const style = window.getComputedStyle(el);
        return (
          el.offsetParent !== null &&
          style.display !== "none" &&
          style.visibility !== "hidden"
        );
      })
      .map(el => el.textContent?.replace(/\s+/g, ' ').trim() || '')
      .filter(text => text.length > 2 && !seen.has(text) && seen.add(text)); 

    let content = lines.join('\n').replace(/\n{2,}/g, '\n');
    chrome.runtime.sendMessage(
      { action: "generateSummaryforContent", content: content, cookies: localStorage.getItem("access_token") },
      (response) => {
        // Reset the flag when request completes
        isGeneratingSummary = false;
        
        if (response && response.success) {
          console.log("Content sent to background script");
          console.log("Summary:", response.data.summary);
          sendResponse({ content: response.data.summary });
        } else {
          console.error("Failed to send content to background script");
          const errorMessage = response?.error || "Failed to send content to background script";
          sendResponse({ error: errorMessage });
        }
      }
    );
    return true;
  }
});
  

// Global click handler for closing sidebar when clicking outside
const handleClickOutside = (event) => {
  const sidebar = document.getElementById("my-extension-sidebar");
  if (sidebar && !sidebar.contains(event.target)) {
    closeSidebar(sidebar);
  }
};

// Make globally available
window.hippoCampusHandleClickOutside = handleClickOutside;

// Function to close sidebar with animation
const closeSidebar = (sidebarElement) => {
  if (sidebarElement) {
    console.log("Closing existing sidebar");
    extensionState.isOpen = false;
    sidebarElement.style.animation = "slideOut 0.3s ease-in-out forwards";
    setTimeout(() => {
      if (sidebarElement.parentNode) {
        sidebarElement.remove();
      }
      // Remove click listener when sidebar is closed
      document.removeEventListener("click", window.hippoCampusHandleClickOutside || handleClickOutside);
      extensionState.isInitializing = false;
    }, 300);
  }
};

// Make function globally available
window.hippoCampusCloseSidebar = closeSidebar;

// Function to create sidebar
const createSidebar = () => {
  // Prevent multiple sidebar creation
  if (extensionState.isInitializing) {
    console.log("Sidebar creation already in progress, ignoring");
    return null;
  }
  
  // Check if sidebar already exists
  const existingSidebar = document.getElementById("my-extension-sidebar");
  if (existingSidebar) {
    console.log("Sidebar already exists, not creating new one");
    return existingSidebar;
  }
  
  console.log("Creating new sidebar");
  extensionState.isInitializing = true;
  
  const sidebar = document.createElement("div");
  sidebar.id = "my-extension-sidebar";
  sidebar.style.animation = "slideIn 0.3s ease-in-out forwards";

  const iframe = document.createElement("iframe");
  iframe.src = chrome.runtime.getURL("index.html");
  iframe.style.width = "100%";
  iframe.style.height = "100%";
  iframe.style.border = "none";
  
  sidebar.appendChild(iframe);
  document.body.appendChild(sidebar);

  // Update state
  extensionState.isOpen = true;
  extensionState.isInitializing = false;

  // Add click outside listener with small delay to avoid immediate closing
  setTimeout(() => {
    document.addEventListener("click", window.hippoCampusHandleClickOutside || handleClickOutside);
  }, 100);
  
  return sidebar;
};

// Make function globally available
window.hippoCampusCreateSidebar = createSidebar;

// Main toggle function (called when Alt+M is pressed)
(() => {
  // Prevent multiple simultaneous operations
  if (extensionState.isInitializing) {
    console.log("Extension operation already in progress, ignoring toggle");
    return;
  }

  // Check if sidebar already exists
  let existingSidebar = document.getElementById("my-extension-sidebar");

  // If sidebar exists, close it (toggle off)
  if (existingSidebar && extensionState.isOpen) {
    closeSidebar(existingSidebar);
    return;
  }

  // If no sidebar exists, create it (toggle on)
  if (!existingSidebar && !extensionState.isOpen) {
    createSidebar();
  }
})();

} // Close the else block for script loading check