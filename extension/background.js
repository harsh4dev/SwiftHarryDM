// Listen for video/audio file requests
chrome.webRequest.onBeforeRequest.addListener(
  (details) => {
    if (details.url.match(/\.(mp4|mkv|webm|mp3|wav|m4a)(\?|$)/i)) {
      console.log("Captured media URL:", details.url);

      // Send captured URL to local SwiftHarryDM app
      fetch("http://127.0.0.1:5001/capture", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ url: details.url })
      }).catch(err => console.error("SwiftHarryDM not running:", err));
    }
  },
  { urls: ["<all_urls>"] },
  ["blocking"]
);
