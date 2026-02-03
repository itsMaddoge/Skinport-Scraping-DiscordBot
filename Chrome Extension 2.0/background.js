let skinportTabs = [];
let currentTabIndex = 0;

// Function to refresh the next tab
function processNextTab() {
  if (currentTabIndex >= skinportTabs.length) {
    console.log("All Skinport tabs processed. Restarting cycle...");

    // Optional: Add a slight delay before restarting cycle (same as tabDelay for now)
    chrome.storage.sync.get(['tabDelay'], (result) => {
      const delay = (result.tabDelay !== undefined ? result.tabDelay : 30) * 1000;
      console.log(`Waiting ${delay / 1000} seconds before starting over...`);

      setTimeout(() => {
        startSequentialRefresh(); // Restart entire cycle
      }, delay);
    });

    return;
  }

  const tab = skinportTabs[currentTabIndex];
  console.log(`Refreshing Tab: ${tab.url}`);

  chrome.tabs.reload(tab.id, () => {
    chrome.scripting.executeScript({
      target: { tabId: tab.id },
      files: ["content.js"]
    }).then(() => {
      console.log(`Injected content script into ${tab.url}`);

      // Retrieve the delay from storage
      chrome.storage.sync.get(['tabDelay'], (result) => {
        const delay = (result.tabDelay !== undefined ? result.tabDelay : 30) * 1000;
        console.log(`Waiting ${delay / 1000} seconds before refreshing the next tab...`);
        setTimeout(() => {
          currentTabIndex++;
          processNextTab(); // Move to next tab
        }, delay);
      });
    }).catch(error => console.warn("Error injecting content script:", error));
  });
}

// Start the sequential refresh process
function startSequentialRefresh() {
  chrome.tabs.query({}, (tabs) => {
    skinportTabs = tabs.filter(tab => tab.url && tab.url.startsWith("https://skinport.com/market"));
    currentTabIndex = 0;

    if (skinportTabs.length === 0) {
      console.log("No Skinport tabs found. Retrying in 30 seconds...");
      setTimeout(startSequentialRefresh, 30000);
      return;
    }

    console.log(`Found ${skinportTabs.length} Skinport tabs. Starting sequential refresh...`);
    processNextTab();
  });
}

// Listen for messages from content scripts
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.html && sender.tab && sender.tab.url && sender.tab.url.startsWith("https://skinport.com/market")) {
    const tabId = sender.tab.id;
    console.log(`Received updated HTML from Tab ID: ${tabId} (${sender.tab.url}), sending to server...`);

    const dataToSend = JSON.stringify({
      tabId: tabId,
      html: message.html
    });

    fetch("http://localhost:8000/", {
      method: "POST",
      body: dataToSend,
      headers: {
        "Content-Type": "application/json",
      },
    })
    .then(response => response.text())
    .then(data => {
      console.log("Server response:", data);
      sendResponse({ status: "Success", serverResponse: data });
    })
    .catch(error => {
      console.error("Error sending HTML to server:", error);
      sendResponse({ status: "Error", error: error.message });
    });

    return true; // Keeps the message channel open for sendResponse
  } else {
    console.log("Ignored message: Either no HTML or URL doesn't match.");
    sendResponse({ status: "Ignored: No valid HTML or URL" });
  }
});

// Initialize the process
startSequentialRefresh();
