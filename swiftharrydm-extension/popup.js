// popup.js - FIXED CONNECTION VERSION
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

    // Add to popup.js
    document.getElementById('forceRescanBtn').addEventListener('click', function() {
        chrome.tabs.query({active: true, currentWindow: true}, function(tabs) {
        chrome.tabs.sendMessage(tabs[0].id, {action: "forceRescan"});
    });
    window.close();
    });

    async function checkAppStatus() {
        try {
            console.log('🔄 Checking app connection from popup...');
            
            // Test direct connection first
            const directTest = await testDirectConnection();
            if (directTest.connected) {
                statusElement.textContent = '✅ Connected to SwiftHarryDM';
                statusElement.className = 'status connected';
                console.log('✅ Direct connection successful');
                return;
            }

            // If direct fails, try through background script
            console.log('🔄 Trying background script connection...');
            const response = await chrome.runtime.sendMessage({ 
                action: 'checkAppStatus' 
            });
            
            console.log('📨 Background response:', response);
            
            if (response && response.connected) {
                statusElement.textContent = `✅ Connected on port ${response.port}`;
                statusElement.className = 'status connected';
            } else {
                statusElement.textContent = '❌ SwiftHarryDM not running';
                statusElement.className = 'status disconnected';
                
                // Show help message
                showHelpMessage();
            }
        } catch (error) {
            console.error('❌ Popup connection error:', error);
            statusElement.textContent = '❌ Cannot connect to app';
            statusElement.className = 'status disconnected';
            showHelpMessage();
        }
    }

    async function testDirectConnection() {
        try {
            // Try both possible ports
            const ports = [5001, 5002];
            
            for (const port of ports) {
                try {
                    const response = await fetch(`http://127.0.0.1:${port}/health`, {
                        method: 'GET',
                        // Note: We can't set timeout in popup due to CORS, but we'll catch the error
                    });
                    
                    if (response.status === 200) {
                        const data = await response.json();
                        console.log(`✅ Direct connection to port ${port}:`, data);
                        return { connected: true, port: port, data: data };
                    }
                } catch (error) {
                    console.log(`❌ Port ${port} failed:`, error.message);
                    continue;
                }
            }
            
            return { connected: false };
        } catch (error) {
            console.error('Direct connection test failed:', error);
            return { connected: false };
        }
    }

    function showHelpMessage() {
        // Create help message if it doesn't exist
        if (!document.getElementById('helpMessage')) {
            const helpMessage = document.createElement('div');
            helpMessage.id = 'helpMessage';
            helpMessage.style.cssText = `
                background: rgba(255,255,255,0.1);
                padding: 10px;
                border-radius: 6px;
                margin-top: 10px;
                font-size: 12px;
            `;
            helpMessage.innerHTML = `
                <strong>💡 Troubleshooting:</strong><br>
                1. Make sure SwiftHarryDM app is running<br>
                2. Check if your firewall is blocking the connection<br>
                3. Try restarting the app
            `;
            statusElement.parentNode.insertBefore(helpMessage, statusElement.nextSibling);
        }
    }

    function scanPageForMedia() {
        chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
            if (tabs[0]) {
                chrome.tabs.sendMessage(tabs[0].id, { action: 'showMediaDetection' });
            }
            window.close();
        });
    }

    function downloadAllMedia() {
        chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
            if (tabs[0]) {
                chrome.tabs.sendMessage(tabs[0].id, { action: 'downloadPageMedia' });
            statusElement.textContent = '⬇️ Downloading all media...';
                statusElement.className = 'status connected';
            }
            window.close();
        });
    }

    function openApp() {
        // Create a notification to guide user
        chrome.notifications.create({
            type: 'basic',
            iconUrl: 'icons/icon128.png',
            title: 'SwiftHarryDM',
            message: 'Please make sure the SwiftHarryDM desktop app is running.'
        });
        
        // Try to focus the app window if possible
        chrome.runtime.sendMessage({ action: 'openApp' });
    }

    // Check for pending downloads
    checkPendingDownloads();

    async function checkPendingDownloads() {
        try {
            const response = await fetch('http://127.0.0.1:5001/api/queue');
            const data = await response.json();
            
            if (data.total > 0) {
                pendingDownloads.classList.remove('hidden');
                downloadsList.innerHTML = data.queue.map(item => `
                    <div class="download-item">
                        <strong>${item.title}</strong>
                        <div>Status: ${item.status} | Progress: ${item.progress}%</div>
                    </div>
                `).join('');
            }
        } catch (error) {
            // Silently fail - queue might not be accessible
            console.log('Queue not accessible:', error.message);
        }
    }

    // Add click handlers for troubleshooting
    statusElement.addEventListener('click', () => {
        checkAppStatus();
    });

    // Auto-refresh status every 3 seconds while popup is open
    const refreshInterval = setInterval(checkAppStatus, 3000);
    
    // Clear interval when popup closes
    window.addEventListener('unload', () => {
        clearInterval(refreshInterval);
    });
});