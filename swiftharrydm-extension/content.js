// content.js
class MediaDetector {
    constructor() {
        this.mediaElements = new Map();
        this.downloadButtons = new Set();
        this.observer = null;
        this.init();
    }

    init() {
        console.log('🎯 Initializing Media Detector...');
        this.detectMediaElements();
        this.setupMutationObserver();
        this.setupMessageListener();
    }

    detectMediaElements() {
        // Only detect prominent media elements
        const videos = document.querySelectorAll('video');
        const audios = document.querySelectorAll('audio');
        
        console.log(`🎬 Found ${videos.length} videos, ${audios.length} audios`);
        
        videos.forEach((video, index) => {
            if (this.isProminentVideo(video)) {
                this.processVideoElement(video, `video_${index}`);
            }
        });

        audios.forEach((audio, index) => {
            if (this.isProminentAudio(audio)) {
                this.processAudioElement(audio, `audio_${index}`);
            }
        });

        this.detectVideoLinks();
    }

    isProminentVideo(video) {
        // Only process videos that are likely the main content
        const rect = video.getBoundingClientRect();
        const isVisible = rect.width > 200 && rect.height > 150;
        const isMainVideo = video.duration > 10 || video.currentTime > 0;
        
        return isVisible && (isMainVideo || this.isCentered(video));
    }

    isProminentAudio(audio) {
        const rect = audio.getBoundingClientRect();
        return rect.width > 100 || this.hasControls(audio);
    }

    isCentered(element) {
        const rect = element.getBoundingClientRect();
        const viewportCenter = window.innerWidth / 2;
        const elementCenter = rect.left + (rect.width / 2);
        return Math.abs(viewportCenter - elementCenter) < 200;
    }

    hasControls(element) {
        return element.hasAttribute('controls') || element.controls;
    }

    processVideoElement(video, id) {
        const sources = this.getVideoSources(video);
        if (sources.length > 0 && !this.mediaElements.has(id)) {
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
        if (sources.length > 0 && !this.mediaElements.has(id)) {
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
        return video.getAttribute('poster') || 
               this.createVideoThumbnail(video);
    }

    createVideoThumbnail(video) {
        try {
            const canvas = document.createElement('canvas');
            const ctx = canvas.getContext('2d');
            canvas.width = 160;
            canvas.height = 90;
            ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
            return canvas.toDataURL();
        } catch (e) {
            return null;
        }
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
        // Remove existing button if any
        if (element.swiftharryButton) {
            element.swiftharryButton.remove();
        }

        const button = this.createDownloadButton();
        this.positionButtonNearMedia(element, button);
        
        button.addEventListener('click', (e) => {
            e.preventDefault();
            e.stopPropagation();
            this.showDownloadPopup(mediaId);
        });

        element.swiftharryButton = button;
        this.downloadButtons.add(button);
        
        // Add hover effect to show button
        element.addEventListener('mouseenter', () => {
            button.style.opacity = '1';
            button.style.transform = 'translateY(0)';
        });
        
        element.addEventListener('mouseleave', () => {
            button.style.opacity = '0.9';
        });
    }

    createDownloadButton() {
        const button = document.createElement('div');
        button.className = 'swiftharry-download-btn';
        button.style.cssText = `
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 20px;
            padding: 8px 16px;
            font-size: 12px;
            font-weight: 600;
            cursor: pointer;
            display: flex;
            align-items: center;
            gap: 6px;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
            transition: all 0.3s ease;
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.2);
            opacity: 0.9;
            transform: translateY(-5px);
            pointer-events: auto;
            z-index: 10000;
        `;
        button.innerHTML = `
            <svg width="14" height="14" viewBox="0 0 24 24" fill="white">
                <path d="M19 9h-4V3H9v6H5l7 7 7-7zM5 18v2h14v-2H5z"/>
            </svg>
            <span>Download</span>
        `;
        return button;
    }

    positionButtonNearMedia(mediaElement, button) {
        const rect = mediaElement.getBoundingClientRect();
        
        // Position button in top-right corner of media element
        button.style.position = 'fixed';
        button.style.top = (rect.top + window.scrollY + 10) + 'px';
        button.style.left = (rect.left + window.scrollX + rect.width - 130) + 'px';
        button.style.zIndex = '10000';
        
        document.body.appendChild(button);
    }

    showDownloadPopup(mediaId) {
        const media = this.mediaElements.get(mediaId);
        if (!media) return;

        const popup = this.createDownloadPopup(media);
        document.body.appendChild(popup);

        // Close when clicking outside
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
        popup.style.cssText = `
            position: fixed;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            background: white;
            border-radius: 12px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.3);
            z-index: 100000;
            min-width: 350px;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        `;
        
        popup.innerHTML = `
            <div class="popup-header" style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 15px 20px; border-radius: 12px 12px 0 0; display: flex; justify-content: space-between; align-items: center;">
                <h3 style="margin: 0; font-size: 16px; font-weight: 600;">🚀 Download with SwiftHarryDM</h3>
                <button class="close-btn" style="background: none; border: none; color: white; font-size: 20px; cursor: pointer; padding: 0; width: 24px; height: 24px; display: flex; align-items: center; justify-content: center;">&times;</button>
            </div>
            <div class="popup-content" style="padding: 20px;">
                <div class="media-info" style="margin-bottom: 15px; padding: 10px; background: #f8f9fa; border-radius: 6px; font-size: 14px;">
                    <strong style="display: block; margin-bottom: 5px; color: #333;">${media.title}</strong>
                    ${media.duration ? `<div style="color: #666;">Duration: ${this.formatDuration(media.duration)}</div>` : ''}
                </div>
                <div class="format-selection" style="margin-bottom: 20px;">
                    <label style="display: block; margin-bottom: 8px; font-weight: 600; color: #333;">Download Format:</label>
                    <select class="format-select" style="width: 100%; padding: 10px; border: 2px solid #e9ecef; border-radius: 6px; font-size: 14px; background: white;">
                        <option value="best">Best Quality</option>
                        <option value="1080">1080p</option>
                        <option value="720">720p</option>
                        <option value="mp3">MP3 Audio</option>
                    </select>
                </div>
                <button class="download-now-btn" style="width: 100%; padding: 12px; background: linear-gradient(135deg, #10b981 0%, #059669 100%); color: white; border: none; border-radius: 6px; font-size: 14px; font-weight: 600; cursor: pointer; margin-bottom: 8px;">
                    ⬇️ Download Now
                </button>
                <button class="add-to-queue-btn" style="width: 100%; padding: 12px; background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%); color: white; border: none; border-radius: 6px; font-size: 14px; font-weight: 600; cursor: pointer;">
                    📥 Add to Queue
                </button>
            </div>
        `;

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

    async startDownload(media, format, instant = false) {
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

        console.log('📤 Starting download:', downloadData);

        try {
            const response = await chrome.runtime.sendMessage({
                action: 'downloadMedia',
                data: downloadData
            });
            
            console.log('📥 Extension response:', response);
            
            if (response && response.success) {
                this.showDownloadStartedNotification(media.title, response.queuePosition);
            } else {
                this.showErrorNotification(response?.error || 'Download failed');
            }
        } catch (error) {
            console.error('❌ Download error:', error);
            this.showErrorNotification('Failed to connect to SwiftHarryDM app');
        }
    }

    showDownloadStartedNotification(title, queuePosition) {
        const notification = document.createElement('div');
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: #10b981;
            color: white;
            padding: 15px 20px;
            border-radius: 8px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.3);
            z-index: 100001;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            max-width: 300px;
        `;
        notification.innerHTML = `
            <div style="font-weight: 600; margin-bottom: 5px;">✅ Download Started</div>
            <div style="font-size: 14px;">"${title}"</div>
            <div style="font-size: 12px; opacity: 0.9;">Queue position: ${queuePosition}</div>
        `;
        
        document.body.appendChild(notification);
        
        setTimeout(() => {
            notification.remove();
        }, 4000);
    }

    showErrorNotification(message) {
        const notification = document.createElement('div');
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: #ef4444;
            color: white;
            padding: 15px 20px;
            border-radius: 8px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.3);
            z-index: 100001;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            max-width: 300px;
        `;
        notification.innerHTML = `
            <div style="font-weight: 600; margin-bottom: 5px;">❌ Download Failed</div>
            <div style="font-size: 14px;">${message}</div>
        `;
        
        document.body.appendChild(notification);
        
        setTimeout(() => {
            notification.remove();
        }, 4000);
    }

    formatDuration(seconds) {
        if (!seconds) return 'Unknown';
        const mins = Math.floor(seconds / 60);
        const secs = Math.floor(seconds % 60);
        return `${mins}:${secs.toString().padStart(2, '0')}`;
    }

    setupMutationObserver() {
        // Watch for new media elements added to the page
        this.observer = new MutationObserver((mutations) => {
            mutations.forEach((mutation) => {
                mutation.addedNodes.forEach((node) => {
                    if (node.nodeType === 1) {
                        if (node.tagName === 'VIDEO' && this.isProminentVideo(node)) {
                            this.processVideoElement(node, `video_${Date.now()}`);
                        } else if (node.tagName === 'AUDIO' && this.isProminentAudio(node)) {
                            this.processAudioElement(node, `audio_${Date.now()}`);
                        }
                        
                        // Check for media elements within added node
                        if (node.querySelectorAll) {
                            node.querySelectorAll('video').forEach(video => {
                                if (this.isProminentVideo(video)) {
                                    this.processVideoElement(video, `video_${Date.now()}`);
                                }
                            });
                            node.querySelectorAll('audio').forEach(audio => {
                                if (this.isProminentAudio(audio)) {
                                    this.processAudioElement(audio, `audio_${Date.now()}`);
                                }
                            });
                        }
                    }
                });
            });
        });

        this.observer.observe(document.body, {
            childList: true,
            subtree: true
        });
    }

    setupMessageListener() {
        chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
            console.log('Content script received:', request);
            
            switch (request.action) {
                case 'contextMenuDownload':
                    this.handleContextMenuDownload(request.context);
                    break;
                case 'downloadPageMedia':
                    this.downloadAllMedia();
                    break;
                case 'showMediaDetection':
                    this.showDetectionResults();
                    break;
            }
        });
    }

    handleContextMenuDownload(context) {
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
        this.mediaElements.forEach((media, id) => {
            if (media.sources && media.sources.length > 0) {
                this.startDownload(media, 'best', false);
            }
        });
    }

    showDetectionResults() {
        const count = this.mediaElements.size;
        alert(`🎯 Found ${count} media elements on this page\nCheck the top-right corners of videos for download buttons!`);
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