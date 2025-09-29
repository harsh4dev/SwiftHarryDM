// popup.js
document.addEventListener('DOMContentLoaded', function() {
    const statusElement = document.getElementById('status');
    const scanPageBtn = document.getElementById('scanPageBtn');
    const downloadAllBtn = document.getElementById('downloadAllBtn');
    const openAppBtn = document.getElementById('openAppBtn');
    const pendingDownloads = document.getElementById('pendingDownloads');
    const downloadsList = document.getElementById('downloadsList');

    // Check app status when popup opens
    checkAppStatus();

    // Event listeners
    scanPageBtn.addEventListener('click', scanPageForMedia);
    downloadAllBtn.addEventListener('click', downloadAllMedia);
    openAppBtn.addEventListener('click', openApp);

    // Check for pending downloads
    checkPendingDownloads();

    async function checkAppStatus() {
        try {
            const response = await chrome.runtime.sendMessage({ action: 'getAppStatus' });
            
            if (response.status === 'connected') {
                statusElement.textContent = '✅ Connected to SwiftHarryDM';
                statusElement.className = 'status connected';
            } else {
                statusElement.textContent = '❌ SwiftHarryDM not running';
                statusElement.className = 'status disconnected';
            }
        } catch (error) {
            statusElement.textContent = '❌ Cannot connect to app';
            statusElement.className = 'status disconnected';
        }
    }

    function scanPageForMedia() {
        chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
            chrome.tabs.sendMessage(tabs[0].id, { action: 'showMediaDetection' });
            window.close();
        });
    }

    function downloadAllMedia() {
        chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
            chrome.tabs.sendMessage(tabs[0].id, { action: 'downloadPageMedia' });
            window.close();
        });
    }

    function openApp() {
        chrome.runtime.sendMessage({ action: 'openApp' });
    }

    async function checkPendingDownloads() {
        const result = await chrome.storage.local.get(['pendingDownloads']);
        const pending = result.pendingDownloads || [];
        
        if (pending.length > 0) {
            pendingDownloads.classList.remove('hidden');
            downloadsList.innerHTML = pending.map(download => `
                <div class="download-item">
                    <strong>${download.title}</strong>
                    <div>Format: ${download.format}</div>
                </div>
            `).join('');
        }
    }
});