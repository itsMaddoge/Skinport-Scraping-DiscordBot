(function executeContentScript() {
  // Skip iframes
  if (window.top !== window.self) {
    console.log('Injected into iframe, skipping:', window.location.href);
    return;
  }

  // Avoid double execution
  if (window.hasAlreadySentHTML) {
    console.log('Already sent HTML, skipping:', window.location.href);
    return;
  }
  window.hasAlreadySentHTML = true;
  console.log('Running content script on:', window.location.href);

  let SEND_DELAY_MS = 1000;

  function sendHTMLOnce() {
    console.log(`Waiting ${SEND_DELAY_MS}ms before sending HTML...`);
    setTimeout(() => {
      const fullHTML = document.documentElement.outerHTML;
      console.log('Sending HTML...');
      chrome.runtime.sendMessage({ html: fullHTML }, response => {
        console.log('Message sent, response:', response);
      });
    }, SEND_DELAY_MS);
  }

  chrome.storage.sync.get(['sendDelay'], result => {
    if (result.sendDelay !== undefined) {
      SEND_DELAY_MS = parseInt(result.sendDelay, 10);
    }

    if (document.readyState === 'complete') {
      sendHTMLOnce();
    } else {
      window.addEventListener('load', sendHTMLOnce);
    }
  });
})();
