# SwiftHarryDM
*Open-Source Advanced Download Manager for Windows*

---

## Project Overview
**SwiftHarryDM** is a Windows-only, open-source download manager designed to provide a fast, reliable, and intelligent downloading experience. Inspired by IDM, SwiftHarryDM combines simplicity, speed, and advanced features for users who want complete control over their downloads.

💡 *Note*: SwiftHarryDM is now fully open-source under the **MIT License**, allowing anyone to freely use, modify, and distribute the software.

---

## Core Features

1. **Intelligent Dynamic File Segmentation**  
   - Automatically splits files into multiple segments to accelerate download speed.  
   - Optimizes segment size based on network conditions for maximum efficiency.

2. **Resume Capability**  
   - Pause and resume downloads anytime without losing progress.  
   - Supports interrupted downloads due to network failure or system shutdown.

3. **Clean UI/UX**  
   - Windows-style interface for intuitive navigation.  
   - Download lists, progress bars, and detailed info displayed cleanly.

4. **Browser Integration**  
   - Seamless integration with Chrome and Firefox.  
   - Auto-capture downloadable links from clipboard or browser.

5. **Download Any File Types from Any Sites**  
   - Supports all common file formats (documents, videos, images, software).  
   - Handles direct downloads from most websites.

6. **Batch Downloads**  
   - Queue multiple downloads at once.  
   - Option to prioritize certain downloads or pause/resume selectively.

7. **YouTube Download at Any Format**  
   - Download videos in 720p, 1080p, 2K, 4K, or audio (MP3) formats.  
   - Extract audio/video separately or combine.

8. **Accelerate Download Speed**  
   - Uses multi-threading and intelligent segmentation for faster downloads.  
   - Optimizes bandwidth usage dynamically.

9. **Auto-Updater**  
   - Automatically checks for updates.  
   - Downloads and installs the latest version seamlessly.  
   - Ensures users always have the newest features and bug fixes.

---

## Tech Stack

- **Backend / Core**: Python (requests, aiohttp, pycurl)  
- **GUI**: PyQt (Windows-native look)  
- **Browser Integration**: Chrome/Firefox Extensions (JavaScript)  
- **Video Download Support**: youtube-dl / yt-dlp Python library  
- **Auto-Updater**: Python + GitHub Releases / custom server

---

## Roadmap / Milestones

### Phase 1 – MVP (Python CLI + Core Engine)
- Basic downloader with pause/resume  
- Multi-threaded downloads  
- Batch downloads  
- Simple progress display

### Phase 2 – GUI Version (PyQt)
- Windows-style UI/UX  
- Download list management  
- File categorization

### Phase 3 – Advanced Features
- Browser integration & auto-capture links  
- YouTube downloader (all formats)  
- Advanced download speed optimization  
- **Auto-Updater**

### Phase 4 – Optional C++ Version (Future)
- Ultra-fast core engine  
- Low-level system integration (Windows hooks)  
- Lightweight standalone executable

---

## License

This project is licensed under the **MIT License** – see the [LICENSE](LICENSE) file for details.  

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)]  

- Anyone is free to **use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies** of SwiftHarryDM.  
- The software is provided “**as is**”, without warranty of any kind.
