// content.js
class MediaDetector {
    constructor() {
        this.mediaElements = new Map();
        this.downloadButtons = new Set();
        this.init();
    }

    init() {
        this.detectMediaElements();
        this.setupMutationObserver();
        this.setupMessageListener();
        this.injectDownloadButtons();
    }

    detectMediaElements() {
        // Detect video elements
        const videos = document.querySelectorAll('video');
        videos.forEach((video, index) => {
            this.processVideoElement(video, `video_${index}`);
        });

        // Detect audio elements
        const audios = document.querySelectorAll('audio');
        audios.forEach((audio, index) => {
            this.processAudioElement(audio, `audio_${index}`);
        });

        // Detect video links
        this.detectVideoLinks();
    }

    processVideoElement(video, id) {
        const sources = this.getVideoSources(video);
        if (sources.length > 0) {
            this.mediaElements.set(id, {
                type: 'video',
                element: video,
                sources: sources,
                title: this.getMediaTitle(video) || document.title,
                thumbnail: this.getVideoThumbnail(video),
                duration: video.duration || null
            });
            this.attachDownloadButton(video, id);
        }
    }

    processAudioElement(audio, id) {
        const sources = this.getAudioSources(audio);
        if (sources.length > 0) {
            this.mediaElements.set(id, {
                type: 'audio',
                element: audio,
                sources: sources,
                title: this.getMediaTitle(audio) || document.title,
                duration: audio.duration || null
            });
            this.attachDownloadButton(audio, id);
        }
    }

    getVideoSources(video) {
        const sources = [];
        
        // Direct src attribute
        if (video.src && !video.src.startsWith('blob:')) {
            sources.push({
                url: video.src,
                quality: 'best',
                type: this.getMimeType(video.src)
            });
        }

        // Source elements
        video.querySelectorAll('source').forEach(source => {
            if (source.src && !source.src.startsWith('blob:')) {
                sources.push({
                    url: source.src,
                    quality: source.getAttribute('quality') || 'unknown',
                    type: source.type || this.getMimeType(source.src)
                });
            }
        });

        return sources;
    }

    getAudioSources(audio) {
        const sources = [];
        
        if (audio.src && !audio.src.startsWith('blob:')) {
            sources.push({
                url: audio.src,
                quality: 'best',
                type: this.getMimeType(audio.src)
            });
        }

        audio.querySelectorAll('source').forEach(source => {
            if (source.src && !source.src.startsWith('blob:')) {
                sources.push({
                    url: source.src,
                    quality: 'best',
                    type: source.type || this.getMimeType(source.src)
                });
            }
        });

        return sources;
    }

    detectVideoLinks() {
        // Detect common video hosting patterns
        const patterns = [
            /\.(mp4|webm|ogg|mov|avi|mkv|flv|wmv|m4v|3gp)(\?|$)/i,
            /youtube\.com\/watch\?v=/i,
            /youtu\.be\//i,
            /vimeo\.com\//i,
            /dailymotion\.com\//i,
            /twitch\.tv\//i
        ];

        const links = document.querySelectorAll('a[href]');
        links.forEach((link, index) => {
            const href = link.href;
            if (patterns.some(pattern => pattern.test(href))) {
                const id = `link_${index}`;
                this.mediaElements.set(id, {
                    type: 'video_link',
                    element: link,
                    url: href,
                    title: link.textContent || link.title || 'Video Link',
                    isDirectLink: true
                });
                this.attachDownloadButton(link, id);
            }
        });
    }

    getMediaTitle(mediaElement) {
        return mediaElement.getAttribute('title') || 
               mediaElement.getAttribute('alt') ||
               mediaElement.getAttribute('aria-label') ||
               document.title;
    }

    getVideoThumbnail(video) {
        // Try to get poster image or create thumbnail from video
        return video.getAttribute('poster') || 
               this.createVideoThumbnail(video);
    }

    createVideoThumbnail(video) {
        // Create a thumbnail from video frame
        const canvas = document.createElement('canvas');
        const ctx = canvas.getContext('2d');
        canvas.width = 160;
        canvas.height = 90;
        ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
        return canvas.toDataURL();
    }

    getMimeType(url) {
        const ext = url.split('.').pop().split('?')[0].toLowerCase();
        const mimeTypes = {
            'mp4': 'video/mp4',
            'webm': 'video/webm',
            'ogg': 'video/ogg',
            'mp3': 'audio/mp3',
            'wav': 'audio/wav',
            'm4a': 'audio/mp4'
        };
        return mimeTypes[ext] || 'unknown';
    }

    attachDownloadButton(element, mediaId) {
        // Check if button already exists
        if (element.swiftharryButton) return;

        const button = this.createDownloadButton();
        this.positionButton(element, button);
        
        button.addEventListener('click', (e) => {
            e.preventDefault();
            e.stopPropagation();
            this.showDownloadPopup(mediaId);
        });

        element.swiftharryButton = button;
        this.downloadButtons.add(button);
    }

    createDownloadButton() {
        const button = document.createElement('div');
        button.className = 'swiftharry-download-btn';
        button.innerHTML = `
            <svg width="16" height="16" viewBox="0 0 24 24" fill="white">
                <path d="M19 9h-4V3H9v6H5l7 7 7-7zM5 18v2h14v-2H5z"/>
            </svg>
            <span>Download</span>
        `;
        return button;
    }

    positionButton(element, button) {
        const rect = element.getBoundingClientRect();
        
        // Position button relative to the media element
        button.style.position = 'absolute';
        button.style.top = (rect.top + window.scrollY + 10) + 'px';
        button.style.left = (rect.left + window.scrollX + 10) + 'px';
        button.style.zIndex = '10000';
        
        document.body.appendChild(button);
    }

    showDownloadPopup(mediaId) {
        const media = this.mediaElements.get(mediaId);
        if (!media) return;

        // Create and show popup
        const popup = this.createDownloadPopup(media);
        document.body.appendChild(popup);

        // Close popup when clicking outside
        setTimeout(() => {
            const closeHandler = (e) => {
                if (!popup.contains(e.target)) {
                    popup.remove();
                    document.removeEventListener('click', closeHandler);
                }
            };
            document.addEventListener('click', closeHandler);
        }, 100);
    }

    createDownloadPopup(media) {
        const popup = document.createElement('div');
        popup.className = 'swiftharry-download-popup';
        
        popup.innerHTML = `
            <div class="popup-header">
                <h3>Download with SwiftHarryDM</h3>
                <button class="close-btn">&times;</button>
            </div>
            <div class="popup-content">
                <div class="media-info">
                    <strong>${media.title}</strong>
                    ${media.duration ? `<div>Duration: ${this.formatDuration(media.duration)}</div>` : ''}
                </div>
                <div class="format-selection">
                    <label>Download Format:</label>
                    <select class="format-select">
                        <option value="best">Best Quality</option>
                        <option value="1080">1080p</option>
                        <option value="720">720p</option>
                        <option value="mp3">MP3 Audio</option>
                    </select>
                </div>
                <button class="download-now-btn">Download Now</button>
                <button class="add-to-queue-btn">Add to Queue</button>
            </div>
        `;

        // Add event listeners
        popup.querySelector('.close-btn').addEventListener('click', () => popup.remove());
        popup.querySelector('.download-now-btn').addEventListener('click', () => {
            this.startDownload(media, popup.querySelector('.format-select').value, true);
            popup.remove();
        });
        popup.querySelector('.add-to-queue-btn').addEventListener('click', () => {
            this.startDownload(media, popup.querySelector('.format-select').value, false);
            popup.remove();
        });

        return popup;
    }

    startDownload(media, format, instant = false) {
        const downloadData = {
            url: media.sources?.[0]?.url || media.url,
            title: media.title,
            format: format,
            type: media.type,
            thumbnail: media.thumbnail,
            duration: media.duration,
            pageUrl: window.location.href,
            instantDownload: instant
        };

        // Send to background script
        chrome.runtime.sendMessage({
            action: 'downloadMedia',
            data: downloadData
        });
    }

    formatDuration(seconds) {
        const mins = Math.floor(seconds / 60);
        const secs = Math.floor(seconds % 60);
        return `${mins}:${secs.toString().padStart(2, '0')}`;
    }

    setupMutationObserver() {
        // Watch for new media elements added to the page
        const observer = new MutationObserver((mutations) => {
            mutations.forEach((mutation) => {
                mutation.addedNodes.forEach((node) => {
                    if (node.nodeType === 1) { // Element node
                        if (node.tagName === 'VIDEO') {
                            this.processVideoElement(node, `video_${Date.now()}`);
                        } else if (node.tagName === 'AUDIO') {
                            this.processAudioElement(node, `audio_${Date.now()}`);
                        }
                        
                        // Check for media elements within added node
                        node.querySelectorAll?.('video').forEach(video => {
                            this.processVideoElement(video, `video_${Date.now()}`);
                        });
                        node.querySelectorAll?.('audio').forEach(audio => {
                            this.processAudioElement(audio, `audio_${Date.now()}`);
                        });
                    }
                });
            });
        });

        observer.observe(document.body, {
            childList: true,
            subtree: true
        });
    }

    setupMessageListener() {
        chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
            switch (request.action) {
                case 'contextMenuDownload':
                    this.handleContextMenuDownload(request.context);
                    break;
                case 'downloadPageMedia':
                    this.downloadAllMedia();
                    break;
            }
        });
    }

    handleContextMenuDownload(context) {
        // Handle right-click context menu downloads
        if (context.mediaType === 'video' || context.mediaType === 'audio') {
            this.showMediaSelectionPopup();
        } else if (context.linkUrl) {
            this.startDownload({
                url: context.linkUrl,
                title: context.linkText || 'Linked Media',
                type: 'video_link'
            }, 'best', true);
        }
    }

    downloadAllMedia() {
        // Download all detected media on the page
        this.mediaElements.forEach((media, id) => {
            if (media.sources && media.sources.length > 0) {
                this.startDownload(media, 'best', false);
            }
        });
    }

    injectDownloadButtons() {
        // Initial injection after page load
        setTimeout(() => {
            this.detectMediaElements();
        }, 2000);
    }
}

// Initialize when page loads
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        new MediaDetector();
    });
} else {
    new MediaDetector();
}