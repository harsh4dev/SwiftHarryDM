// background.js
class BackgroundManager {
    constructor() {
        this.init();
    }

    init() {
        console.log('SwiftHarryDM Extension Background Started');
        this.createContextMenu();
        this.setupMessageListener();
        this.checkAppConnection();
    }

    createContextMenu() {
        chrome.contextMenus.create({
            id: "download-with-swiftharry",
            title: "Download with SwiftHarryDM",
            contexts: ["video", "audio", "link"]
        });

        chrome.contextMenus.create({
            id: "download-page-media",
            title: "Download all media from page",
            contexts: ["page"]
        });
    }

    setupMessageListener() {
        chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
            console.log('📨 Message received:', request);
            
            if (request.action === 'downloadMedia') {
                this.handleDownload(request.data)
                    .then(sendResponse);
                return true;
            }
            
            if (request.action === 'checkAppStatus') {
                this.checkAppConnection()
                    .then(() => sendResponse({ status: 'checked' }));
                return true;
            }
        });
    }

    async checkAppConnection() {
        try {
            const response = await fetch('http://127.0.0.1:5001/health', {
                method: 'GET'
            });
            console.log('✅ App connection status:', response.status);
            return { connected: true, status: response.status };
        } catch (error) {
            console.log('❌ App not running:', error.message);
            return { connected: false, error: error.message };
        }
    }

    async handleDownload(downloadData) {
        try {
            console.log('📤 Sending download to app:', downloadData);
            
            const response = await fetch('http://127.0.0.1:5001/api/download', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(downloadData)
            });
            
            const result = await response.json();
            console.log('📥 App response:', result);
            
            if (result.success) {
                this.showNotification('Download Started', `Added to SwiftHarryDM: ${downloadData.title}`);
                return { success: true, queuePosition: result.queue_position };
            } else {
                this.showNotification('Download Failed', result.error || 'Unknown error');
                return { success: false, error: result.error };
            }
        } catch (error) {
            console.error('Download error:', error);
            this.showNotification('Connection Failed', 'Make sure SwiftHarryDM app is running');
            return { success: false, error: error.message };
        }
    }

    showNotification(title, message) {
        chrome.notifications.create({
            type: 'basic',
            iconUrl: 'icons/icon128.png',
            title: title,
            message: message
        });
    }
}

// Initialize background manager
const backgroundManager = new BackgroundManager();

// Context menu click handler
chrome.contextMenus.onClicked.addListener((info, tab) => {
    if (info.menuItemId === "download-with-swiftharry") {
        chrome.tabs.sendMessage(tab.id, {
            action: "contextMenuDownload",
            context: info
        });
    } else if (info.menuItemId === "download-page-media") {
        chrome.tabs.sendMessage(tab.id, {
            action: "downloadPageMedia"
        });
    }
});