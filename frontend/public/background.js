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
      fetch(`https://hippocampus-cyfo.onrender.com/links/get`, {
      method: 'GET',
      credentials: 'include',
      headers: { 
        'Content-Type': 'application/json'
      }
      }).then(response => response.json()),
      fetch(`https://hippocampus-cyfo.onrender.com/notes/`, {
      method: 'GET',
      credentials: 'include',
      headers: { 
        'Content-Type': 'application/json'
      }
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
      credentials: 'include',
      headers: {
        'Content-Type': 'application/json'
      }
    };

    if (message.type !== "All") {
      fetchOptions.body = JSON.stringify({ type: { $eq: message.type } });
    }

    fetch(`https://hippocampus-cyfo.onrender.com/links/search?query=${message.query}`, fetchOptions)
      .then(response => response.json())
      .then(data => {
        console.log("The response is:", data);
        sendResponse({ success: true, data });
      })
      .catch(error => sendResponse({ success: false, error: error.message }));

    return true;
  }

  else if (message.action === "submit") {
    fetch('https://hippocampus-cyfo.onrender.com/links/save', {
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
    fetch('https://hippocampus-cyfo.onrender.com/notes/', {
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
    fetch('https://hippocampus-cyfo.onrender.com/quotes/', {
      method: 'GET',
      credentials: 'include'
    })
      .then(response => response.json())
      .then(data => sendResponse({ success: true, data }))
      .catch(error => sendResponse({ success: false, error: error.message }));
    return true;
  }
  else if (message.action === "delete") {
    fetch(`https://hippocampus-cyfo.onrender.com/links/delete?doc_id_pincone=${message.query}`, {
      method: 'DELETE',
      credentials: 'include'
    })
      .then(response => response.json())
      .then(data => sendResponse({ success: true, data }))
      .catch(error => sendResponse({ success: false, error: error.message }));
    return true;
  }
  else if (message.action === "generateSummaryforContent") {
    fetch(`https://hippocampus-cyfo.onrender.com/summary/generate`, {
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

  else {
    null
  }

});