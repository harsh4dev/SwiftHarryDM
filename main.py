import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, filedialog
import threading
import os
import re
import requests
import json
import hashlib
import uuid
import time
import subprocess
import platform
import winreg
from datetime import datetime, timedelta
from src.downloader import Downloader
from utils import get_ffmpeg_path, convert_to_mp3, manual_merge_video_audio
from utils import convert_to_mp3, format_mapping
from yt_dlp import YoutubeDL
from flask import Flask, request, jsonify
from download_window import show_download_window, close_download_window, active_download_windows


# ------------------ Globals ------------------
download_queue = []
paused_flags = []
queue_frames = []
CURRENT_VERSION = "1.0.0"
UPDATE_CHECK_URL = "https://swiftharrydm.harshchaudhary.com.np/version.txt"
DOWNLOAD_PAGE_URL = "https://swiftharrydm.harshchaudhary.com.np/downloads"

# IDM Color Theme
COLORS = {
    "primary": "#2C5F8A",        # IDM Blue
    "primary_light": "#3A7BB3",  # Lighter Blue
    "primary_dark": "#1E4A6B",   # Darker Blue
    "secondary": "#E8A735",      # Accent Orange
    "success": "#4CAF50",        # Green
    "warning": "#FF9800",        # Orange
    "danger": "#F44336",         # Red
    "dark_bg": "#2D2D2D",        # Dark Background
    "dark_surface": "#3C3C3C",   # Dark Surface
    "dark_text": "#FFFFFF",      # White Text
    "light_text": "#CCCCCC",     # Light Gray Text
    "border": "#555555",         # Border Color
    "header_bg": "#1E3A5F",      # Header Background
    "row_even": "#2D2D2D",       # Even Row
    "row_odd": "#363636",        # Odd Row
    "progress_bg": "#1E4A6B",    # Progress Background
    "progress_fg": "#4CAF50",    # Progress Foreground
}

# ------------------ IDM Style Configuration ------------------
def configure_idm_styles():
    style = ttk.Style()
    
    # Configure main styles
    style.configure("IDM.TFrame", background=COLORS["dark_bg"])
    style.configure("IDM.TLabel", background=COLORS["dark_bg"], foreground=COLORS["dark_text"])
    style.configure("IDM.TButton", 
                   background=COLORS["primary"],
                   foreground=COLORS["dark_text"],
                   borderwidth=1,
                   focuscolor=COLORS["primary_light"])
    
    # Progressbar style
    style.configure("IDM.Horizontal.TProgressbar",
                   background=COLORS["progress_fg"],
                   troughcolor=COLORS["progress_bg"],
                   borderwidth=0,
                   lightcolor=COLORS["progress_fg"],
                   darkcolor=COLORS["progress_fg"])
    
    # Treeview style (for download list)
    style.configure("IDM.Treeview",
                   background=COLORS["dark_surface"],
                   foreground=COLORS["dark_text"],
                   fieldbackground=COLORS["dark_surface"],
                   borderwidth=0,
                   rowheight=25)
    
    style.configure("IDM.Treeview.Heading",
                   background=COLORS["primary_dark"],
                   foreground=COLORS["dark_text"],
                   relief="flat",
                   borderwidth=0,
                   font=('Arial', 10, 'bold'))
    
    # Combobox style
    style.configure("IDM.TCombobox",
                   background=COLORS["dark_surface"],
                   foreground=COLORS["dark_text"],
                   fieldbackground=COLORS["dark_surface"],
                   borderwidth=1)
    
    # Scrollbar style
    style.configure("IDM.Vertical.TScrollbar",
                   background=COLORS["primary_dark"],
                   troughcolor=COLORS["dark_bg"],
                   borderwidth=0,
                   arrowsize=12)

# ------------------ Utilities ------------------
def clean_percent(percent_str):
    ansi_escape = re.compile(r'\x1B[@-_][0-?]*[ -/]*[@-~]')
    clean_str = ansi_escape.sub('', percent_str)
    try:
        return int(float(clean_str.replace('%','').strip()))
    except:
        return 0

def sanitize_filename(name):
    # More comprehensive sanitization
    name = re.sub(r'[<>:"/\\|?*]', '_', name)
    name = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', name)  # Remove control characters
    name = name.strip().strip('.')  # Remove leading/trailing spaces and dots
    name = name[:200]  # Limit length
    return name if name else "download"

def open_download_folder():
    """Open the download folder in file explorer"""
    try:
        save_path = get_default_save_path()
        if os.path.exists(save_path):
            os.startfile(save_path)  # Windows
            log_text.insert(tk.END, f"📁 Opened folder: {save_path}\n")
        else:
            messagebox.showinfo("Folder Not Found", f"Download folder doesn't exist:\n{save_path}")
    except Exception as e:
        messagebox.showerror("Error", f"Cannot open folder:\n{str(e)}")

def get_filename_from_url(url):
    return sanitize_filename(url.split('/')[-1])

def get_default_save_path():
    """Get reliable default save path with fallbacks"""
    try:
        # Try Desktop first
        desktop = os.path.join(os.path.expanduser("~"), "Desktop")
        if os.path.exists(desktop):
            save_path = os.path.join(desktop, "SwiftHarryDM Downloads")
        else:
            # Fallback to Documents
            documents = os.path.join(os.path.expanduser("~"), "Documents")
            save_path = os.path.join(documents, "SwiftHarryDM Downloads")
        
        # Ensure directory exists
        os.makedirs(save_path, exist_ok=True)
        return save_path
        
    except Exception as e:
        # Ultimate fallback - current directory
        fallback = os.path.join(os.getcwd(), "SwiftHarryDM Downloads")
        os.makedirs(fallback, exist_ok=True)
        return fallback

#--------------------Enhanced Extension Integration------------------------
app = Flask(__name__)

# Enable CORS properly
@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response

@app.route("/health", methods=["GET", "OPTIONS"])
def health_check():
    if request.method == 'OPTIONS':
        return jsonify({"status": "ok"})
    return jsonify({
        "status": "running", 
        "app": "SwiftHarryDM",
        "version": CURRENT_VERSION,
        "timestamp": datetime.now().isoformat()
    })

@app.route("/api/download", methods=["POST", "OPTIONS"])
def handle_download():
    if request.method == 'OPTIONS':
        return jsonify({"status": "ok"})
    
    try:
        data = request.get_json()
        print(f"📥 [EXTENSION] Download request received")
        print(f"   URL: {data.get('url', 'N/A')}")
        print(f"   Title: {data.get('title', 'N/A')}")
        print(f"   Format: {data.get('format', 'N/A')}")
        
        url = data.get("url")
        title = data.get("title", "Unknown Title")
        format_type = data.get("format", "best")
        page_url = data.get("pageUrl", "")
        
        if not url:
            return jsonify({"success": False, "error": "No URL provided"}), 400
        
        # Sanitize title for filename
        title = sanitize_filename(title)
        
        # Default save path
        save_path = os.path.join(os.path.expanduser("~"), "Desktop", "SwiftHarryDM Downloads")
        os.makedirs(save_path, exist_ok=True)
        
        # Create download item - AUTO START ALL EXTENSION DOWNLOADS
        item = {
            "url": url, 
            "fmt": format_type, 
            "save_path": save_path, 
            "status": "Downloading",  # Changed from "Pending" to "Downloading"
            "progress": 0,
            "title": title,
            "source": "extension",
            "page_url": page_url,
            "added_at": datetime.now().isoformat()
        }
        
        # Add to queue
        download_queue.append(item)
        paused_flags.append(False)
        queue_position = len(download_queue)
        
        # Update GUI in main thread - FIXED with proper lambda
        root.after(0, lambda idx=len(download_queue)-1: add_extension_download_to_gui(idx))
        
        # AUTO START DOWNLOAD for all extension requests
        root.after(100, lambda idx=len(download_queue)-1: start_extension_download(idx))
        
        log_text.insert(tk.END, f"✅ [EXTENSION] Added and started: {title}\n")
        log_text.see(tk.END)
        
        return jsonify({
            "success": True, 
            "message": "Download added to queue and started",
            "queue_position": queue_position,
            "title": title,
            "format": format_type
        })
        
    except Exception as e:
        error_msg = f"❌ [EXTENSION] Error: {str(e)}"
        print(error_msg)
        log_text.insert(tk.END, f"{error_msg}\n")
        log_text.see(tk.END)
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/queue", methods=["GET", "OPTIONS"])
def get_queue_status():
    if request.method == 'OPTIONS':
        return jsonify({"status": "ok"})
    
    queue_info = []
    for idx, item in enumerate(download_queue):
        queue_info.append({
            "position": idx + 1,
            "title": item.get("title", get_filename_from_url(item["url"])),
            "status": item["status"],
            "progress": item["progress"],
            "format": item["fmt"]
        })
    
    return jsonify({
        "total": len(download_queue),
        "active": len([item for item in download_queue if item["status"] == "Downloading"]),
        "queue": queue_info
    })

def add_extension_download_to_gui(idx):
    """Add extension download to GUI queue"""
    if idx < len(download_queue):
        create_queue_item(idx)
        # Auto-scroll to show new item
        queue_canvas.yview_moveto(1.0)
        # Update queue count
        update_queue_count()
        
        # Log the addition
        item = download_queue[idx]
        log_text.insert(tk.END, f"📥 [EXTENSION] Added to queue: {item['title']} ({item['fmt']})\n")
        log_text.see(tk.END)
        
        print(f"✅ [EXTENSION] Added to GUI: {item['title']} at index {idx}")

def start_extension_download(idx):
    """Start download for extension-added items"""
    if idx < len(download_queue) and download_queue[idx]["status"] == "Downloading":
        print(f"🚀 [EXTENSION] Starting download for index {idx}: {download_queue[idx]['title']}")
        # Update the GUI first
        update_queue_item(idx)
        # Then start the download worker
        threading.Thread(target=download_worker, args=(idx,), daemon=True).start()

def run_flask():
    """Run Flask server for browser extension"""
    try:
        print("🚀 Starting Flask server for browser extension on port 5001...")
        # Disable Flask logging for cleaner output
        import logging
        log = logging.getLogger('werkzeug')
        log.setLevel(logging.ERROR)
        
        # Use these settings for better compatibility
        app.run(
            host='127.0.0.1', 
            port=5001, 
            debug=False, 
            threaded=True, 
            use_reloader=False
        )
    except Exception as e:
        print(f"❌ Flask server error on port 5001: {e}")
        # Try alternative port
        try:
            print("🔄 Trying port 5002...")
            app.run(
                host='127.0.0.1', 
                port=5002, 
                debug=False, 
                threaded=True, 
                use_reloader=False
            )
        except Exception as e2:
            print(f"❌ Failed to start Flask server: {e2}")

# Start Flask in background when app launches
threading.Thread(target=run_flask, daemon=True).start()

# ------------------ Update Checker ------------------
def check_for_updates(auto=False):
    try:
        resp = requests.get(UPDATE_CHECK_URL, timeout=5)
        latest_version = resp.text.strip()
        if latest_version != CURRENT_VERSION:
            if auto:
                log_text.insert(tk.END, f"Update available: {latest_version}\n")
                log_text.see(tk.END)
            else:
                if messagebox.askyesno("Update Available", f"New version {latest_version} available. Download?"):
                    import webbrowser
                    webbrowser.open(DOWNLOAD_PAGE_URL)
        elif not auto:
            messagebox.showinfo("No Update", "You are running the latest version.")
    except Exception as e:
        if not auto:
            messagebox.showwarning("Update Check Failed", f"Unable to check updates.\nError: {e}")
        log_text.insert(tk.END, f"Update check failed: {e}\n")
        log_text.see(tk.END)

def auto_update_check():
    threading.Thread(target=check_for_updates, kwargs={"auto": True}, daemon=True).start()

# ------------------ About Window ------------------
def show_about():
    about_window = tk.Toplevel(root)
    about_window.title("About SwiftHarryDM")
    about_window.geometry("500x400")
    about_window.resizable(False, False)
    about_window.configure(bg=COLORS["dark_bg"])
    about_window.transient(root)
    about_window.grab_set()
    
    # Center the window
    about_window.update_idletasks()
    x = (about_window.winfo_screenwidth() // 2) - (500 // 2)
    y = (about_window.winfo_screenheight() // 2) - (400 // 2)
    about_window.geometry(f"500x400+{x}+{y}")
    
    # Header
    header_frame = tk.Frame(about_window, bg=COLORS["primary"], height=100)
    header_frame.pack(fill="x", side="top")
    header_frame.pack_propagate(False)
    
    tk.Label(header_frame, text="🚀 SwiftHarryDM", font=("Arial", 24, "bold"), 
             bg=COLORS["primary"], fg="white").pack(expand=True)
    
    tk.Label(header_frame, text="Professional Download Manager", font=("Arial", 12), 
             bg=COLORS["primary"], fg="white").pack(expand=True)
    
    # Content
    content_frame = tk.Frame(about_window, bg=COLORS["dark_bg"], padx=20, pady=20)
    content_frame.pack(fill="both", expand=True, padx=10, pady=10)
    
    info_text = f"""
Version: {CURRENT_VERSION}

SwiftHarryDM is a powerful universal downloader that supports:
• YouTube, Vimeo, Twitter, and 1000+ sites
• Multiple formats (MP4, MP3, 1080p, 720p)
• Browser extension integration
• Queue management with pause/resume

Features:
✓ High-speed downloads
✓ Format conversion
✓ Browser integration
✓ Professional UI/UX
✓ Windows support

Developed with ❤️ by Harsh Chaudhary.

© 2024 SwiftHarryDM. All rights reserved.
    """
    
    tk.Label(content_frame, text=info_text, font=("Arial", 10), 
             bg=COLORS["dark_bg"], fg=COLORS["dark_text"], justify="left", anchor="w").pack(fill="both", expand=True)
    
    # Close button
    tk.Button(about_window, text="Close", command=about_window.destroy,
              bg=COLORS["primary"], fg="white", font=("Arial", 10, "bold"),
              width=20, height=2).pack(pady=10)

# ------------------ Universal Downloader ------------------
class UniversalDownloader:
    def __init__(self, url, fmt="best", save_path=None, progress_hook=None, is_extension=False):
        self.url = url
        self.fmt = fmt
        self.save_path = save_path or get_default_save_path()
        self.progress_hook = progress_hook
        self.is_extension = is_extension
        
        # Ensure save directory exists and is writable
        try:
            os.makedirs(self.save_path, exist_ok=True)
            # Test write permission
            test_file = os.path.join(self.save_path, "write_test.tmp")
            with open(test_file, 'w') as f:
                f.write("test")
            os.remove(test_file)
            print(f"✅ [DOWNLOADER] Save path is writable: {self.save_path}")
        except Exception as e:
            print(f"❌ [DOWNLOADER] Cannot write to {self.save_path}: {e}")
            # Fallback to current directory
            self.save_path = os.getcwd()
            print(f"🔄 [DOWNLOADER] Using fallback path: {self.save_path}")
        
        print(f"🔧 [DOWNLOADER] Initialized: {url} -> {fmt} -> {self.save_path}")

    def download(self):
        try:
            print(f"🔧 [DOWNLOADER] Starting download: {self.url}")
            print(f"🔧 [DOWNLOADER] Requested format: {self.fmt}")
            
            # Get ffmpeg path for potential merging/conversion
            ffmpeg_path = get_ffmpeg_path()
            ffmpeg_dir = os.path.dirname(ffmpeg_path)
            
            # Get the format selector
            format_selector = format_mapping(self.fmt)
            print(f"🔧 [DOWNLOADER] yt-dlp format selector: {format_selector}")

            # Smart filename template to avoid duplicates and show format info
            # yt-dlp options - let yt-dlp handle format selection natively
            opts = {
                "progress_hooks": [self.progress_hook] if self.progress_hook else [],
                "ignoreerrors": True,
                "retries": 10,
                "fragment_retries": 10,
                "skip_unavailable_fragments": True,
                "noplaylist": True,
                
                # Use the format selector - yt-dlp will choose best available
                "format": format_selector,
            }

            # Configure postprocessors and merging based on format
            if self.fmt.lower() == "mp3":
                # FORCE MP3 conversion with postprocessor and FORCE .mp3 extension
                opts.update({
                    "postprocessors": [{
                        'key': 'FFmpegExtractAudio',
                        'preferredcodec': 'mp3',
                        'preferredquality': '192',
                    }],
                    # CRITICAL: Force .mp3 extension in the output template
                    "outtmpl": os.path.join(self.save_path, "%(title)s.mp3"),
                    "ffmpeg_location": ffmpeg_dir,
                })
                print(f"🔧 [DOWNLOADER] MP3 conversion enabled with forced .mp3 extension")
            else:
                # For video formats, use smart filename templates
                if self.fmt == "best":
                    filename_template = "%(title)s [%(format_note)s].%(ext)s"  # Show actual quality
                else:
                    # For specific formats like 1080, 720, include the requested format
                    filename_template = f"%(title)s [{self.fmt}p].%(ext)s"
                
                opts.update({
                    "outtmpl": os.path.join(self.save_path, filename_template),
                    "merge_output_format": "mp4",
                    "ffmpeg_location": ffmpeg_dir,
                })
                print(f"🔧 [DOWNLOADER] Video download with template: {filename_template}")
            
            # Only add postprocessors for MP3 (conversion)
            # Configure postprocessors and merging based on format
            if self.fmt.lower() == "mp3":
                # FORCE MP3 conversion with postprocessor
                opts["postprocessors"] = [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }]
                # Force the output extension to be mp3
                opts["outtmpl"] = os.path.join(self.save_path, "%(title)s.%(ext)s")
                opts["ffmpeg_location"] = ffmpeg_dir
                print(f"🔧 [DOWNLOADER] MP3 conversion enabled")
            else:
                # For video formats, let yt-dlp merge automatically if needed
                opts["merge_output_format"] = "mp4"
                opts["ffmpeg_location"] = ffmpeg_dir

            print(f"🔧 [DOWNLOADER] Download options ready")
            
            with YoutubeDL(opts) as ydl:
                print(f"🔧 [DOWNLOADER] Extracting info for: {self.url}")
                info = ydl.extract_info(self.url, download=True)
                
                if not info:
                    raise Exception("Failed to extract video information")
                    
                filename = ydl.prepare_filename(info)
                final_path = os.path.abspath(filename)
                print(f"✅ [DOWNLOADER] Download completed: {final_path}")
                
                # Handle post-download scenarios
                
                # Scenario 1: MP3 conversion was handled by yt-dlp
                # Handle MP3 conversion
                if self.fmt.lower() == "mp3":
                    if final_path.endswith('.mp3'):
                        print(f"✅ [DOWNLOADER] MP3 download completed: {final_path}")
                    else:
                        # This shouldn't happen with forced extension, but as fallback
                        print(f"⚠️ [DOWNLOADER] File is not MP3, renaming: {final_path}")
                        mp3_path = os.path.splitext(final_path)[0] + ".mp3"
                        os.rename(final_path, mp3_path)
                        final_path = mp3_path
                        print(f"✅ [DOWNLOADER] Renamed to MP3: {final_path}")
                    
                # Scenario 2: We got separate files (yt-dlp merge failed)
                elif not final_path.endswith('.mp3'):
                    base_name = os.path.splitext(final_path)[0]
                    
                    # Check for common separate file patterns
                    separate_files_found = False
                    for video_ext in ['.webm', '.mp4', '.mkv', '.flv']:
                        for audio_ext in ['.m4a', '.webm', '.opus', '.mp3']:
                            video_file = base_name + video_ext
                            audio_file = base_name + audio_ext
                            
                            if (os.path.exists(video_file) and 
                                os.path.exists(audio_file) and 
                                video_file != audio_file):
                                
                                print(f"🔧 [DOWNLOADER] Found separate files: {video_file} + {audio_file}")
                                print(f"🔧 [DOWNLOADER] Manual merge required...")
                                
                                if manual_merge_video_audio(video_file, audio_file, final_path):
                                    print(f"✅ [DOWNLOADER] Manual merge successful!")
                                    separate_files_found = True
                                    break
                        if separate_files_found:
                            break
                
                # Verify final file
                if os.path.exists(final_path):
                    file_size = os.path.getsize(final_path)
                    print(f"✅ [DOWNLOADER] Final file verified: {final_path} ({file_size} bytes)")
                else:
                    print(f"⚠️ [DOWNLOADER] Final file not found: {final_path}")
                        
                return final_path
                
        except Exception as e:
            print(f"❌ [DOWNLOADER] Download failed: {e}")
            import traceback
            traceback.print_exc()
            raise e

    def merge_video_audio(self, video_file, audio_file, output_file):
        """Manually merge video and audio streams using ffmpeg"""
        try:
            ffmpeg_path = get_ffmpeg_path()
            
            # If output file exists from failed merge, remove it
            if os.path.exists(output_file):
                os.remove(output_file)
                
            cmd = [
                ffmpeg_path, "-y",
                "-i", video_file,
                "-i", audio_file,
                "-c", "copy",  # Copy streams without re-encoding
                "-shortest",
                output_file
            ]
            
            print(f"🔧 [MERGER] Merging: {video_file} + {audio_file} -> {output_file}")
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            
            # Clean up separate files after successful merge
            if os.path.exists(output_file):
                if os.path.exists(video_file):
                    os.remove(video_file)
                if os.path.exists(audio_file):
                    os.remove(audio_file)
                print(f"✅ [MERGER] Merge completed and cleaned up separate files")
                return output_file
                
        except subprocess.CalledProcessError as e:
            print(f"❌ [MERGER] FFmpeg merge failed: {e}")
            print(f"🔧 [MERGER] stderr: {e.stderr}")
        except Exception as e:
            print(f"❌ [MERGER] Merge error: {e}")
        
        return None

    def fallback_download(self):
        """Enhanced fallback downloader with better filename handling"""
        try:
            import urllib.parse
            from pathlib import Path
            
            # Create a safe filename from URL
            parsed_url = urllib.parse.urlparse(self.url)
            if "facebook.com" in self.url:
                # Extract video ID from Facebook URL
                video_id = None
                if "v=" in self.url:
                    video_id = self.url.split("v=")[-1].split("&")[0]
                elif "video/" in self.url:
                    video_id = self.url.split("video/")[-1].split("/")[0]
                
                if video_id and video_id.isdigit():
                    filename = f"facebook_video_{video_id}.mp4"
                else:
                    filename = "facebook_video.mp4"
            else:
                # Generic filename from URL
                path = Path(parsed_url.path)
                if path.name and path.suffix:
                    filename = path.name
                else:
                    filename = "downloaded_video.mp4"
            
            # Sanitize filename
            filename = sanitize_filename(filename)
            filepath = os.path.join(self.save_path, filename)
            
            print(f"🔧 [FALLBACK] Downloading to: {filepath}")
            
            # Use requests with stream for basic download
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            response = requests.get(self.url, headers=headers, stream=True, timeout=30)
            response.raise_for_status()
            
            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0
            
            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        
                        # Update progress if hook exists
                        if self.progress_hook and total_size > 0:
                            percent = (downloaded / total_size) * 100
                            # Simulate progress update
                            fake_info = {
                                'status': 'downloading',
                                '_percent_str': f'{percent:.1f}%',
                                'total_bytes': total_size,
                                'downloaded_bytes': downloaded
                            }
                            self.progress_hook(fake_info)
            
            print(f"✅ [FALLBACK] Download completed: {filepath}")
            return filepath
            
        except Exception as fallback_error:
            print(f"❌ [FALLBACK] Fallback download also failed: {fallback_error}")
            raise fallback_error

# ------------------ Queue Functions ------------------
def add_to_queue():
    url = url_entry.get().strip()
    fmt = format_var.get()
    if not url:
        messagebox.showerror("Error", "Please enter a URL!")
        return
    
    # Use reliable save path
    save_path = filedialog.askdirectory(title="Select Save Location") or get_default_save_path()
    
    # Double-check directory creation
    try:
        os.makedirs(save_path, exist_ok=True)
        # Test if we can write to the directory
        test_file = os.path.join(save_path, "test_write.tmp")
        with open(test_file, 'w') as f:
            f.write("test")
        os.remove(test_file)
    except Exception as e:
        messagebox.showerror("Error", f"Cannot write to directory:\n{save_path}\nError: {e}")
        return
    
    item = {"url": url, "fmt": fmt, "save_path": save_path, "status": "Pending", "progress": 0}
    download_queue.append(item)
    paused_flags.append(False)
    create_queue_item(len(download_queue)-1)
    url_entry.delete(0, tk.END)
    
    # Log the save path for debugging
    log_text.insert(tk.END, f"📁 Save location: {save_path}\n")
    log_text.see(tk.END)

def instant_download():
    url = url_entry.get().strip()
    fmt = format_var.get()
    if not url:
        messagebox.showerror("Error", "Please enter a URL!")
        return
    
    # Use reliable save path
    save_path = filedialog.askdirectory(title="Select Save Location") or get_default_save_path()
    
    # Double-check directory creation
    try:
        os.makedirs(save_path, exist_ok=True)
    except Exception as e:
        messagebox.showerror("Error", f"Cannot create directory:\n{save_path}\nError: {e}")
        return
    
    item = {"url": url, "fmt": fmt, "save_path": save_path, "status": "Downloading", "progress": 0}
    download_queue.append(item)
    paused_flags.append(False)
    idx = len(download_queue)-1
    create_queue_item(idx)
    
    # Log the save path
    log_text.insert(tk.END, f"📁 Instant download to: {save_path}\n")
    log_text.see(tk.END)
    
    threading.Thread(target=download_worker, args=(idx,), daemon=True).start()
    url_entry.delete(0, tk.END)

def create_queue_item(idx):
    item = download_queue[idx]
    frame = tk.Frame(queue_container, bd=1, relief="solid", padx=10, pady=8, bg=COLORS["dark_surface"])
    frame.pack(pady=4, fill="x", padx=5)
    
    # Header with title and status
    header_frame = tk.Frame(frame, bg=COLORS["dark_surface"])
    header_frame.pack(fill="x")
    
    title = item.get('title', get_filename_from_url(item['url']))
    label = tk.Label(header_frame, text=title[:80] + "..." if len(title) > 80 else title, 
                    font=("Arial", 10, "bold"), anchor="w", bg=COLORS["dark_surface"], fg=COLORS["dark_text"])
    label.pack(side="left", fill="x", expand=True)
    
    status_label = tk.Label(header_frame, text=f"{item['status']}", 
                           font=("Arial", 9, "bold"), anchor="e", bg=COLORS["dark_surface"], fg=COLORS["dark_text"])
    status_label.pack(side="right")
    
    # Progress bar
    progress = ttk.Progressbar(frame, orient="horizontal", length=650, mode="determinate", style="IDM.Horizontal.TProgressbar")
    progress['value'] = item['progress']
    progress.pack(side="top", pady=5, fill="x")
    
    # Format and actions
    footer_frame = tk.Frame(frame, bg=COLORS["dark_surface"])
    footer_frame.pack(fill="x")
    
    format_label = tk.Label(footer_frame, text=f"Format: {item['fmt']}", 
                           font=("Arial", 8), anchor="w", bg=COLORS["dark_surface"], fg=COLORS["light_text"])
    format_label.pack(side="left")
    
    if item.get('source') == 'extension':
        source_label = tk.Label(footer_frame, text="🌐 Browser", 
                               font=("Arial", 8), bg=COLORS["dark_surface"], fg=COLORS["primary"])
        source_label.pack(side="left", padx=(10, 0))
    
    queue_frames.append({"frame": frame, "label": label, "status_label": status_label, 
                        "progress": progress, "format_label": format_label})
    update_queue_item_color(idx)

def update_queue_item(idx):
    if idx >= len(download_queue) or idx >= len(queue_frames):
        return
        
    item = download_queue[idx]
    frame_data = queue_frames[idx]
    
    title = item.get('title', get_filename_from_url(item['url']))
    frame_data['label'].config(text=title[:80] + "..." if len(title) > 80 else title)
    frame_data['status_label'].config(text=f"{item['status']}")
    frame_data['progress']['value'] = item['progress']
    frame_data['format_label'].config(text=f"Format: {item['fmt']}")
    update_queue_item_color(idx)

def update_queue_item_color(idx):
    item = download_queue[idx]
    frame_data = queue_frames[idx]
    color_map = {
        "Pending": COLORS["dark_surface"], 
        "Downloading": "#1e3a5f", 
        "Paused": "#5d4037", 
        "Completed": "#2e7d32", 
        "Error": "#c62828"
    }
    text_color_map = {
        "Pending": COLORS["dark_text"],
        "Downloading": "#4fc3f7", 
        "Paused": "#ffb74d", 
        "Completed": "#81c784", 
        "Error": "#ef5350"
    }
    
    bg_color = color_map.get(item['status'], COLORS["dark_surface"])
    text_color = text_color_map.get(item['status'], COLORS["dark_text"])
    
    frame_data['frame'].config(bg=bg_color)
    frame_data['label'].config(bg=bg_color, fg=text_color)
    frame_data['status_label'].config(bg=bg_color, fg=text_color)
    frame_data['format_label'].config(bg=bg_color, fg=text_color)

def start_selected():
    for idx, item in enumerate(download_queue):
        if item["status"] == "Pending":
            item["status"] = "Downloading"
            update_queue_item(idx)
            threading.Thread(target=download_worker, args=(idx,), daemon=True).start()

def pause_selected():
    for idx, item in enumerate(download_queue):
        if item["status"] == "Downloading":
            paused_flags[idx] = True
            item["status"] = "Paused"
            update_queue_item(idx)

def resume_selected():
    for idx, item in enumerate(download_queue):
        if item["status"] == "Paused":
            paused_flags[idx] = False
            item["status"] = "Downloading"
            update_queue_item(idx)
            threading.Thread(target=download_worker, args=(idx,), daemon=True).start()

def clear_completed():
    global download_queue, paused_flags, queue_frames
    
    completed_indices = [i for i, item in enumerate(download_queue) if item["status"] == "Completed"]
    
    # Remove from the end to avoid index issues
    for i in sorted(completed_indices, reverse=True):
        if i < len(queue_frames):
            queue_frames[i]['frame'].destroy()
    
    # Rebuild the lists
    download_queue = [item for i, item in enumerate(download_queue) if i not in completed_indices]
    paused_flags = [flag for i, flag in enumerate(paused_flags) if i not in completed_indices]
    queue_frames = []
    
    # Recreate all queue items
    for i in range(len(download_queue)):
        create_queue_item(i)

def download_worker(idx):
    if idx >= len(download_queue):
        print(f"❌ [WORKER] Index {idx} out of range!")
        return
        
    item = download_queue[idx]
    url, fmt, save_path = item["url"], item["fmt"], item["save_path"]
    title = item.get("title", get_filename_from_url(url))
    
    # Check if this is from extension
    is_extension = item.get('source') == 'extension'

    print(f"🔧 [WORKER] Starting download worker for: {title}")
    print(f"🔧 [WORKER] URL: {url}")
    print(f"🔧 [WORKER] Format: {fmt}")
    print(f"🔧 [WORKER] Save path: {save_path}")
    print(f"🔧 [WORKER] From extension: {is_extension}")

    # Show download progress window
    root.after(0, lambda: show_download_window(root, item, download_queue, idx))

    # Store file size information
    total_size = 0
    downloaded_size = 0

    def progress_hook(d):
        nonlocal total_size, downloaded_size
        
        if d['status'] == 'downloading':
            # Get actual file size information from yt-dlp
            if 'total_bytes' in d and d['total_bytes']:
                total_size = d['total_bytes']
                item['total_size'] = total_size  # Store in item for download window
            
            if 'downloaded_bytes' in d and d['downloaded_bytes']:
                downloaded_size = d['downloaded_bytes']
                item['downloaded_size'] = downloaded_size
            
            # Calculate progress percentage
            if total_size > 0:
                progress_percent = (downloaded_size / total_size) * 100
            else:
                progress_percent = clean_percent(d.get('_percent_str','0%'))
            
            item['progress'] = progress_percent
            update_queue_item(idx)
            
            # Debug progress
            if progress_percent % 20 == 0:  # Log every 20%
                print(f"📊 [WORKER] Progress: {progress_percent:.1f}% - {title}")
                
        elif d['status'] == 'finished':
            item['progress'] = 100
            item['total_size'] = total_size  # Ensure final size is stored
            update_queue_item(idx)
            print(f"✅ [WORKER] Download finished: {title}")

    try:
        log_text.insert(tk.END, f"🚀 Starting download: {title}\n")
        log_text.insert(tk.END, f"📁 Save location: {save_path}\n")
        log_text.see(tk.END)
        print(f"🎯 [WORKER] Calling UniversalDownloader for: {title}")
        
        # Pass the extension flag to downloader
        downloader = UniversalDownloader(url, fmt, save_path, progress_hook, is_extension)
        downloader.download()
        item["status"] = "Completed"
        update_queue_item(idx)
        
        success_msg = f"✅ Download completed: {title}\n"
        log_text.insert(tk.END, success_msg)
        log_text.see(tk.END)
        print(f"🎉 [WORKER] Download successful: {title}")
        
        # Close download window after completion
        root.after(100, lambda: close_download_window(idx))
        
    except Exception as e:
        item["status"] = "Error"
        update_queue_item(idx)
        error_msg = f"❌ Download failed: {title} - {str(e)}\n"
        log_text.insert(tk.END, error_msg)
        log_text.see(tk.END)
        print(f"💥 [WORKER] Download failed: {title} - Error: {str(e)}")
        import traceback
        traceback.print_exc()
        
        # Close download window on error
        root.after(100, lambda: close_download_window(idx))

# ------------------ Professional IDM GUI ------------------
root = tk.Tk()
root.title(f"SwiftHarryDM v{CURRENT_VERSION} - Professional Download Manager")
root.geometry("1200x700")
root.configure(bg=COLORS["dark_bg"])
root.minsize(1000, 600)

# Configure IDM styles
configure_idm_styles()

# Center window on screen
root.update_idletasks()
width = 1200
height = 700
x = (root.winfo_screenwidth() // 2) - (width // 2)
y = (root.winfo_screenheight() // 2) - (height // 2)
root.geometry(f"{width}x{height}+{x}+{y}")

# ------------------ Modern IDM Menu Bar ------------------
menu_bar = tk.Menu(root, bg=COLORS["dark_bg"], fg=COLORS["dark_text"], 
                  activebackground=COLORS["primary"], activeforeground=COLORS["dark_text"],
                  relief="flat", bd=0, font=('Arial', 10))

# File Menu
file_menu = tk.Menu(menu_bar, tearoff=0, bg=COLORS["dark_surface"], fg=COLORS["dark_text"],
                   activebackground=COLORS["primary"], activeforeground=COLORS["dark_text"])
file_menu.add_command(label="Add Download", command=add_to_queue, accelerator="Ctrl+N")
file_menu.add_command(label="Instant Download", command=instant_download, accelerator="Ctrl+I")
file_menu.add_separator()
file_menu.add_command(label="Import List...")
file_menu.add_command(label="Export List...")
file_menu.add_separator()
file_menu.add_command(label="Exit", command=root.quit, accelerator="Alt+F4")
menu_bar.add_cascade(label="File", menu=file_menu)

# Download Menu
download_menu = tk.Menu(menu_bar, tearoff=0, bg=COLORS["dark_surface"], fg=COLORS["dark_text"],
                       activebackground=COLORS["primary"], activeforeground=COLORS["dark_text"])
download_menu.add_command(label="Start Selected", command=start_selected, accelerator="F5")
download_menu.add_command(label="Pause Selected", command=pause_selected, accelerator="F6")
download_menu.add_command(label="Resume Selected", command=resume_selected, accelerator="F7")
download_menu.add_separator()
download_menu.add_command(label="Schedule Downloads...")
download_menu.add_command(label="Category...")
menu_bar.add_cascade(label="Download", menu=download_menu)

# View Menu
view_menu = tk.Menu(menu_bar, tearoff=0, bg=COLORS["dark_surface"], fg=COLORS["dark_text"],
                   activebackground=COLORS["primary"], activeforeground=COLORS["dark_text"])
view_menu.add_checkbutton(label="Toolbar")
view_menu.add_checkbutton(label="Status Bar")
view_menu.add_separator()
view_menu.add_command(label="Language")
view_menu.add_command(label="Skin")
menu_bar.add_cascade(label="View", menu=view_menu)

# Help Menu
help_menu = tk.Menu(menu_bar, tearoff=0, bg=COLORS["dark_surface"], fg=COLORS["dark_text"],
                   activebackground=COLORS["primary"], activeforeground=COLORS["dark_text"])
help_menu.add_command(label="Documentation")
help_menu.add_command(label="Check for Updates", command=lambda: check_for_updates(auto=False))
help_menu.add_separator()
help_menu.add_command(label="About SwiftHarryDM", command=show_about)
menu_bar.add_cascade(label="Help", menu=help_menu)

root.config(menu=menu_bar)

# ------------------ Header Frame ------------------
header_frame = tk.Frame(root, bg=COLORS["header_bg"], height=80)
header_frame.pack(fill="x", side="top")
header_frame.pack_propagate(False)

# Header Content
header_content = tk.Frame(header_frame, bg=COLORS["header_bg"])
header_content.pack(expand=True, fill="both", padx=20)

# Logo and title
title_frame = tk.Frame(header_content, bg=COLORS["header_bg"])
title_frame.pack(side="left")

# Logo placeholder
logo_label = tk.Label(title_frame, text="🚀", font=("Arial", 24), 
                     bg=COLORS["header_bg"], fg="white")
logo_label.pack(side="left", padx=(0, 10))

title_label = tk.Label(title_frame, text="SwiftHarryDM", font=("Arial", 20, "bold"), 
                      bg=COLORS["header_bg"], fg="white")
title_label.pack(side="left")

version_label = tk.Label(title_frame, text=f"v{CURRENT_VERSION}", font=("Arial", 10), 
                        bg=COLORS["header_bg"], fg="#CCCCCC")
version_label.pack(side="left", padx=(5, 0))

# Status indicators
status_frame = tk.Frame(header_content, bg=COLORS["header_bg"])
status_frame.pack(side="right")

extension_status_var = tk.StringVar(value="🔌 Extension: Connecting...")
extension_label = tk.Label(status_frame, textvariable=extension_status_var, 
                          font=("Arial", 9), bg=COLORS["header_bg"], fg="#CCCCCC")
extension_label.pack(side="top", anchor="e")

# ------------------ Main Content Frame ------------------
main_frame = ttk.Frame(root, style="IDM.TFrame")
main_frame.pack(fill="both", expand=True, padx=10, pady=10)

# ------------------ Quick Download Panel ------------------
download_panel = ttk.Frame(main_frame, style="IDM.TFrame")
download_panel.pack(fill="x", pady=(0, 15))

# URL input
url_frame = ttk.Frame(download_panel, style="IDM.TFrame")
url_frame.pack(fill="x", pady=5)

tk.Label(url_frame, text="URL:", font=("Arial", 10, "bold"), 
        bg=COLORS["dark_bg"], fg=COLORS["dark_text"]).pack(side="left", padx=(0, 10))

url_entry = tk.Entry(url_frame, width=70, font=("Arial", 11), 
                    bg=COLORS["dark_surface"], fg=COLORS["dark_text"],
                    insertbackground=COLORS["dark_text"],
                    relief="solid", bd=1)
url_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))

# Format selection
format_frame = ttk.Frame(download_panel, style="IDM.TFrame")
format_frame.pack(fill="x", pady=5)

tk.Label(format_frame, text="Format:", font=("Arial", 10, "bold"), 
        bg=COLORS["dark_bg"], fg=COLORS["dark_text"]).pack(side="left", padx=(0, 10))

format_var = tk.StringVar(value="best")
format_combo = ttk.Combobox(format_frame, textvariable=format_var,
                           values=["best", "1080", "720", "480", "mp3", "mp4"], 
                           state="readonly", width=15, style="IDM.TCombobox")
format_combo.pack(side="left", padx=(0, 20))

# Action buttons
button_frame = ttk.Frame(download_panel, style="IDM.TFrame")
button_frame.pack(fill="x", pady=10)

def create_idm_button(parent, text, command, color, width=15):
    return tk.Button(parent, text=text, command=command,
                    bg=color, fg="white", width=width, font=("Arial", 9, "bold"),
                    relief="flat", padx=15, pady=6, bd=0,
                    activebackground=color, activeforeground="white")

btn_add = create_idm_button(button_frame, "Add to Queue", add_to_queue, COLORS["primary"])
btn_add.pack(side="left", padx=5)

btn_instant = create_idm_button(button_frame, "Instant Download", instant_download, COLORS["success"])
btn_instant.pack(side="left", padx=5)

btn_start = create_idm_button(button_frame, "Start All", start_selected, COLORS["primary_light"])
btn_start.pack(side="left", padx=5)

btn_pause = create_idm_button(button_frame, "Pause All", pause_selected, COLORS["warning"])
btn_pause.pack(side="left", padx=5)

btn_resume = create_idm_button(button_frame, "Resume All", resume_selected, COLORS["secondary"])
btn_resume.pack(side="left", padx=5)

btn_clear_completed = create_idm_button(button_frame, "Clear Completed", clear_completed, COLORS["danger"])
btn_clear_completed.pack(side="left", padx=5)

btn_open_folder = create_idm_button(button_frame, "Open Download Folder", open_download_folder, COLORS["primary_light"])
btn_open_folder.pack(side="left", padx=5)

# ------------------ Download Queue Section ------------------
queue_section = ttk.Frame(main_frame, style="IDM.TFrame")
queue_section.pack(fill="both", expand=True, pady=(10, 0))

# Section header
header_frame = ttk.Frame(queue_section, style="IDM.TFrame")
header_frame.pack(fill="x", pady=(0, 10))

tk.Label(header_frame, text="Download Queue", font=("Arial", 14, "bold"), 
        bg=COLORS["dark_bg"], fg=COLORS["dark_text"]).pack(side="left")

queue_count_var = tk.StringVar(value="Downloads: 0")
queue_count_label = tk.Label(header_frame, textvariable=queue_count_var, font=("Arial", 11), 
                            bg=COLORS["dark_bg"], fg=COLORS["light_text"])
queue_count_label.pack(side="left", padx=(10, 0))

# Queue container with scroll
queue_container_frame = ttk.Frame(queue_section, style="IDM.TFrame")
queue_container_frame.pack(fill="both", expand=True, pady=(5, 0))

queue_canvas = tk.Canvas(queue_container_frame, bg=COLORS["dark_bg"], highlightthickness=0)
queue_scrollbar = ttk.Scrollbar(queue_container_frame, orient="vertical", command=queue_canvas.yview, style="IDM.Vertical.TScrollbar")
queue_container = tk.Frame(queue_canvas, bg=COLORS["dark_bg"])

queue_container.bind("<Configure>", lambda e: queue_canvas.configure(scrollregion=queue_canvas.bbox("all")))
queue_canvas.create_window((0,0), window=queue_container, anchor="nw", width=queue_canvas.winfo_width())
queue_canvas.configure(yscrollcommand=queue_scrollbar.set)

queue_canvas.pack(side="left", fill="both", expand=True)
queue_scrollbar.pack(side="right", fill="y")

def update_queue_display(event):
    queue_canvas.configure(scrollregion=queue_canvas.bbox("all"))
    queue_canvas.itemconfig('all', width=queue_canvas.winfo_width())

queue_canvas.bind('<Configure>', update_queue_display)

# ------------------ Log Section ------------------
log_section = ttk.Frame(main_frame, style="IDM.TFrame")
log_section.pack(fill="x", pady=(15, 0))

tk.Label(log_section, text="Activity Log:", font=("Arial", 12, "bold"), 
        bg=COLORS["dark_bg"], fg=COLORS["dark_text"]).pack(anchor="w")

log_frame = ttk.Frame(log_section, style="IDM.TFrame")
log_frame.pack(fill="x", pady=(5, 0))

log_text = tk.Text(log_frame, height=6, wrap="word", font=("Consolas", 9), 
                  relief="solid", bd=1, bg="#1e1e1e", fg="#00ff00",
                  insertbackground="#00ff00")
log_text.pack(side="left", fill="both", expand=True)

log_scrollbar = ttk.Scrollbar(log_frame, orient="vertical", command=log_text.yview, style="IDM.Vertical.TScrollbar")
log_text.configure(yscrollcommand=log_scrollbar.set)
log_scrollbar.pack(side="right", fill="y")

# ------------------ Status Bar ------------------
status_bar = tk.Frame(root, bg=COLORS["primary_dark"], height=25)
status_bar.pack(fill="x", side="bottom")
status_bar.pack_propagate(False)

# Left side - general status
left_status = tk.Label(status_bar, text="Ready", font=("Arial", 9), 
                      bg=COLORS["primary_dark"], fg="white")
left_status.pack(side="left", padx=10)

# Right side - transfer info
right_status = tk.Label(status_bar, text="Total: 0 | Active: 0 | Speed: 0 KB/s", 
                       font=("Arial", 9), bg=COLORS["primary_dark"], fg="white")
right_status.pack(side="right", padx=10)

# ------------------ Startup Functions ------------------
def update_queue_count():
    total = len(download_queue)
    active = len([item for item in download_queue if item["status"] == "Downloading"])
    queue_count_var.set(f"Downloads: {total} (Active: {active})")
    root.after(1000, update_queue_count)

def check_extension_connection():
    try:
        response = requests.get("http://127.0.0.1:5001/health", timeout=2)
        if response.status_code == 200:
            extension_status_var.set("🔌 Extension: Connected ✓")
        else:
            extension_status_var.set("🔌 Extension: Port busy")
    except:
        extension_status_var.set("🔌 Extension: Not connected")
    
    # Check again after 5 seconds
    root.after(5000, check_extension_connection)

# ------------------ Initialize App ------------------
auto_update_check()
root.after(3000, check_extension_connection)
root.after(1000, update_queue_count)

# Start the main loop
root.mainloop()