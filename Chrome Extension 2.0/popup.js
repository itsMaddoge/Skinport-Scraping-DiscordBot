document.addEventListener('DOMContentLoaded', () => {
    chrome.storage.sync.get(['tabDelay'], (result) => {
      document.getElementById('delayInput').value = result.tabDelay || 30;
    });
  
    document.getElementById('saveBtn').addEventListener('click', () => {
      const delay = parseInt(document.getElementById('delayInput').value, 10);
      chrome.storage.sync.set({ tabDelay: delay }, () => {
        alert('Delay saved!');
      });
    });
  });
  