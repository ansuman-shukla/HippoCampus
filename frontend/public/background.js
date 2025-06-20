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
    Promise.all([
      fetch(`https://hippocampus-backend-vvv9.onrender.com/links/get`, {
      method: 'GET',
      headers: { 
        'Content-Type': 'application/json',
        'access_token': message.cookies
      }
      }).then(response => response.json()),
      fetch(`https://hippocampus-backend-vvv9.onrender.com/notes`, {
      method: 'GET',
      headers: { 
        'Content-Type': 'application/json',
        'access_token': message.cookies }
      }).then(response => response.json())
    ])
    .then(([linksData, notesData]) => {
      sendResponse({ success: true, links: linksData, notes: notesData });
    })
    .catch(error => {
      sendResponse({ success: false, error: error.message });
    });
    return true;
  }

  



  else if (message.action === "search") {
    const fetchOptions = {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'access_token': message.cookies
      }
    };

    if (message.type !== "All") {
      fetchOptions.body = JSON.stringify({ type: { $eq: message.type } });
    }

    fetch(`https://hippocampus-backend-vvv9.onrender.com/links/search?query=${message.query}`, fetchOptions)
      .then(response => response.json())
      .then(data => {
        console.log("The response is:", data);
        sendResponse({ success: true, data });
      })
      .catch(error => sendResponse({ success: false, error: error.message }));

    return true;
  }

  else if (message.action === "submit") {
    fetch('https://hippocampus-backend-vvv9.onrender.com/links/save', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'access_token': message.cookies,

      },
      body: JSON.stringify(message.data)
    })
      .then(response => response.json())
      .then(data => {
        sendResponse({ success: true, data });
      })
      .catch(error => {
        console.error("Submission error:", error);
        sendResponse({ success: false, error: error.message });
      });
    return true;
  }
  else if (message.action === "saveNotes") {
    fetch('https://hippocampus-backend-vvv9.onrender.com/notes', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'access_token': message.cookies,
      },
      body: JSON.stringify(message.data)
    })
      .then(response => response.json())
      .then(data => {
        sendResponse({ success: true, data });
      })
      .catch(error => {
        console.error("Submission error:", error);
        sendResponse({ success: false, error: error.message });
      });
    return true;
  }

  else if (message.action === "getQuotes") {
    fetch('https://hippocampus-backend-vvv9.onrender.com/quotes', {
      method: 'GET',
      headers: { 'access_token': message.cookies }
    })
      .then(response => response.json())
      .then(data => sendResponse({ success: true, data }))
      .catch(error => sendResponse({ success: false, error: error.message }));
    return true;
  }
  else if (message.action === "delete") {
    fetch(`https://hippocampus-backend-vvv9.onrender.com/links/delete?doc_id_pincone=${message.query}`, {
      method: 'DELETE',
      headers: { 'access_token': message.cookies }
    })
      .then(response => response.json())
      .then(data => sendResponse({ success: true, data }))
      .catch(error => sendResponse({ success: false, error: error.message }));
    return true;
  }
  else if (message.action === "generateSummaryforContent") {
    fetch(`https://hippocampus-backend-vvv9.onrender.com/summary/generate`, {
      method: 'POST',
      headers: { 'access_token': message.cookies },
      body: JSON.stringify({ content: message.content })
    })
      .then(response => response.json())
      .then(data => sendResponse({ success: true, data }))
      .catch(error => sendResponse({ success: false, error: error.message }));
    return true;
  }

  else {
    null
  }

});