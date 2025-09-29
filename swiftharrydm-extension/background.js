// background.js - FIXED CONNECTION VERSION
class BackgroundManager {
    constructor() {
        this.appPort = 5001; // Default port
        this.init();
    }

    init() {
        console.log('SwiftHarryDM Extension Background Started');
        this.createContextMenu();
        this.setupMessageListener();
        this.findAppPort(); // Try to find which port the app is using
    }

    async findAppPort() {
        // Try both possible ports
        const ports = [5001, 5002];
        for (const port of ports) {
            const connected = await this.testPort(port);
            if (connected) {
                this.appPort = port;
                console.log(`✅ App found on port ${port}`);
                break;
            }
        }
    }

    async testPort(port) {
        try {
            const response = await fetch(`http://127.0.0.1:${port}/health`, {
                method: 'GET',
                timeout: 2000
            });
            return response.status === 200;
        } catch (error) {
            return false;
        }
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
        // Add this to the setupMessageListener function in background.js
        chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
            console.log('📨 Message received:', request);
    
            if (request.action === 'downloadMedia') {
            this.handleDownload(request.data)
            .then(sendResponse);
                return true;
            }
    
            if (request.action === 'checkAppStatus') {
                this.checkAppConnection()
                .then((result) => sendResponse(result));
            return true;
            }
    
        // ADD THIS NEW HANDLER:
        if (request.action === 'openApp') {
            this.showNotification('SwiftHarryDM', 'The app should be running on your desktop. If not, please launch it manually.');
            sendResponse({ success: true });
            return true;
            }
        });
    }

    async checkAppConnection() {
        try {
            const response = await fetch(`http://127.0.0.1:${this.appPort}/health`);
            if (response.status === 200) {
                return { connected: true, port: this.appPort };
            }
        } catch (error) {
            // Try to find the correct port again
            await this.findAppPort();
        }
        
        return { connected: false, error: 'App not running' };
    }

    async handleDownload(downloadData) {
        try {
            console.log('📤 Sending download to app on port:', this.appPort);
            
            const response = await fetch(`http://127.0.0.1:${this.appPort}/api/download`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(downloadData)
            });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const result = await response.json();
            console.log('📥 App response:', result);
            
            if (result.success) {
                this.showNotification('Download Started', `Added to SwiftHarryDM: ${downloadData.title}`);
                return { 
                    success: true, 
                    queuePosition: result.queue_position,
                    message: result.message 
                };
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