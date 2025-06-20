if (window.location.protocol === "chrome:") {
  window.location.href = chrome.runtime.getURL("error.html");
}


chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.action === "closeExtension" && message.target === "content") {
    const sidebar = document.getElementById("my-extension-sidebar");
    if (sidebar) {
      sidebar.style.animation = "slideOut 0.3s ease-in-out forwards";
      setTimeout(() => {
        sidebar.remove();
      }, 300);
    }
    sendResponse({success: true});
  }
  if (message.action === "extractPageContent") {
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
        if (response) {
          console.log("Content sent to background script");
          console.log("Summary:", response.data.summary);
          sendResponse({ content: response.data.summary });
        } else {
          console.error("Failed to send content to background script");
          sendResponse({ error: "Failed to send content to background script" });
        }
      }
    );
    return true;
  }
});
  

(() => {
  let sidebar = document.getElementById("my-extension-sidebar");

  const closeSidebar = () => {
    sidebar.style.animation = "slideOut 0.3s ease-in-out forwards";
    setTimeout(() => {
      sidebar.remove();
      document.removeEventListener("click", handleClickOutside);
    }, 300);
  };

  const handleClickOutside = (event) => {
    if (!sidebar.contains(event.target)) {
      closeSidebar();
    }
  };

  if (sidebar) {
    closeSidebar();
    return;
  }

  sidebar = document.createElement("div");
  sidebar.id = "my-extension-sidebar";
  sidebar.style.animation = "slideIn 0.3s ease-in-out forwards";

  const iframe = document.createElement("iframe");
  iframe.src = chrome.runtime.getURL("index.html");
  iframe.style.width = "100%";
  iframe.style.height = "100%";
  iframe.style.border = "none";
  

  sidebar.appendChild(iframe);
  document.body.appendChild(sidebar);

  document.addEventListener("click", handleClickOutside);
  
})();