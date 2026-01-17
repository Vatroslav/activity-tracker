// Activity Tracker Chrome Extension
// Sends active tab data to local HTTP server

const SERVER_URL = 'http://localhost:5678/chrome-data';
let lastTabId = null;
let lastUrl = null;

// Get Chrome profile name
async function getProfileName() {
  try {
    // Try to get profile user info
    const userInfo = await chrome.identity.getProfileUserInfo();
    if (userInfo.email) {
      return userInfo.email;
    }
  } catch (e) {
    // Log error to help diagnose profile issues
    console.error('Failed to get profile info:', e);
  }
  
  // Fallback: Use a generic identifier
  return 'Unknown profile';
}

// Send tab data to server
async function sendTabData(tab) {
  if (!tab || !tab.url) return;
  
  // Skip internal Chrome pages
  if (tab.url.startsWith('chrome://') || tab.url.startsWith('chrome-extension://')) {
    return;
  }
  
  const profileName = await getProfileName();
  
  const data = {
    url: tab.url,
    title: tab.title || '',
    profile: profileName
  };
  
  try {
    await fetch(SERVER_URL, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(data)
    });
  } catch (error) {
    // Silently fail if server is not running
    // Don't spam console with errors
  }
}

// Handle tab activation
chrome.tabs.onActivated.addListener(async (activeInfo) => {
  const tab = await chrome.tabs.get(activeInfo.tabId);
  lastTabId = activeInfo.tabId;
  lastUrl = tab.url;
  await sendTabData(tab);
});

// Handle tab URL updates
chrome.tabs.onUpdated.addListener(async (tabId, changeInfo, tab) => {
  // Only send if this is the active tab and URL changed
  if (changeInfo.url && tabId === lastTabId) {
    lastUrl = changeInfo.url;
    await sendTabData(tab);
  }
});

// Send initial data for current active tab
chrome.tabs.query({ active: true, currentWindow: true }, async (tabs) => {
  if (tabs[0]) {
    lastTabId = tabs[0].id;
    lastUrl = tabs[0].url;
    await sendTabData(tabs[0]);
  }
});
