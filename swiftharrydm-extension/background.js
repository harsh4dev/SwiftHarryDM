// background.js
class BackgroundManager {
    constructor() {
        this.init();
    }

    init() {
        console.log('SwiftHarryDM Extension Background Started');
        this.createContextMenu();
        this.setupMessageListener();
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
            switch (request.action) {
                case 'downloadMedia':
                    this.handleDownload(request.data, sender.tab);
                    break;
                case 'getAppStatus':
                    this.checkAppStatus(sendResponse);
                    return true;
                case 'openApp':
                    this.openSwiftHarryApp();
                    break;
            }
        });
    }

    async checkAppStatus(sendResponse) {
        try {
            const response = await fetch('http://localhost:3000/health', {
                method: 'GET',
                timeout: 3000
            });
            const data = await response.json();
            sendResponse({ status: 'connected', data });
        } catch (error) {
            sendResponse({ status: 'disconnected', error: error.message });
        }
    }

    async handleDownload(downloadData, tab) {
        try {
            // Send download request to your app
            const response = await this.sendToApp(downloadData);
            
            if (response.success) {
                this.showNotification('Download Started', `Added to SwiftHarryDM queue: ${downloadData.title}`);
            } else {
                this.showNotification('Download Failed', 'Could not connect to SwiftHarryDM');
            }
        } catch (error) {
            console.error('Download error:', error);
            this.showNotification('Error', 'Failed to start download. Make sure SwiftHarryDM is running.');
        }
    }

    async sendToApp(downloadData) {
        // This will send the download request to your Python app
        // You can use native messaging or HTTP requests
        try {
            const response = await fetch('http://localhost:3000/api/download', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(downloadData)
            });
            return await response.json();
        } catch (error) {
            // Fallback: Store in local storage and notify app
            await this.storePendingDownload(downloadData);
            return { success: true, queued: true };
        }
    }

    async storePendingDownload(downloadData) {
        const pending = await this.getPendingDownloads();
        pending.push({
            ...downloadData,
            timestamp: Date.now()
        });
        await chrome.storage.local.set({ pendingDownloads: pending });
    }

    async getPendingDownloads() {
        const result = await chrome.storage.local.get(['pendingDownloads']);
        return result.pendingDownloads || [];
    }

    openSwiftHarryApp() {
        // You can implement this to open your desktop app
        // For now, we'll just show a notification
        this.showNotification('SwiftHarryDM', 'Please make sure the SwiftHarryDM app is running on your computer.');
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