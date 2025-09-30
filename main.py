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
from datetime import datetime, timedelta
from src.downloader import Downloader
from utils import convert_to_mp3, format_mapping
from yt_dlp import YoutubeDL
from flask import Flask, request, jsonify

# ------------------ Globals ------------------
download_queue = []
paused_flags = []
queue_frames = []
CURRENT_VERSION = "1.0.0"
UPDATE_CHECK_URL = "https://swiftharrydm.harshchaudhary.com.np/version.txt"
DOWNLOAD_PAGE_URL = "https://swiftharrydm.harshchaudhary.com.np/downloads"

# License / Trial Config
LICENSE_SERVER = "http://localhost:3000"
TOKEN_FILE = os.path.join(os.path.expanduser("~"), ".swift_dm_token.json")
TRIAL_DAYS = 7

# ------------------ Modern UI Colors ------------------
COLORS = {
    "primary": "#667eea",
    "primary_dark": "#5a6fd8",
    "secondary": "#764ba2",
    "success": "#10b981",
    "warning": "#f59e0b",
    "danger": "#ef4444",
    "dark": "#1f2937",
    "light": "#f8fafc",
    "gray": "#6b7280"
}

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

def get_filename_from_url(url):
    return sanitize_filename(url.split('/')[-1])

def get_machine_id():
    return hashlib.sha256(uuid.getnode().to_bytes(6,'big')).hexdigest()

def save_local_token(data):
    with open(TOKEN_FILE, "w") as f:
        json.dump(data, f)

def load_local_token():
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, "r") as f:
            return json.load(f)
    return None

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

# ------------------ License & Trial ------------------
def start_trial(machine_id):
    try:
        print(f"🔄 Starting trial for machine: {machine_id}")
        resp = requests.post(f"{LICENSE_SERVER}/trial", json={"machine_id": machine_id}, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        print(f"📄 Trial response: {data}")
        
        if data.get("valid"):
            days_left = data.get("days_left", TRIAL_DAYS)
            trial_data = {
                "machine_id": machine_id, 
                "trial_start": datetime.now().isoformat(),
                "trial_start_server": data.get("trial_started"),
                "days_left": days_left
            }
            save_local_token(trial_data)
            license_status_var.set(f"Trial: {days_left} days left")
            messagebox.showinfo("Trial Started", f"Your trial started! {days_left} days left.")
            return True
        else:
            messagebox.showinfo("Trial Expired", "Trial expired. Enter a license key to continue.")
            return ask_for_license()
    except Exception as e:
        print(f"❌ Trial error: {e}")
        token = load_local_token()
        if token and "trial_start" in token:
            trial_start = datetime.fromisoformat(token["trial_start"])
            elapsed = (datetime.now() - trial_start).days
            if elapsed < TRIAL_DAYS:
                days_left = TRIAL_DAYS - elapsed
                license_status_var.set(f"Trial: {days_left} days left (Offline)")
                enable_download_buttons(True)
                return True
        messagebox.showerror("Error", f"Cannot start trial.\n{str(e)}")
        return False

def verify_license_online(license_key, machine_id):
    try:
        print(f"🔐 Verifying license: {license_key} for machine: {machine_id}")
        clean_license = license_key.strip().replace(" ", "").replace("-", "").upper()
        if len(clean_license) != 24:
            return False, "invalid_format"
        
        resp = requests.post(f"{LICENSE_SERVER}/verify", 
                           json={"license_key": clean_license, "machine_id": machine_id}, 
                           timeout=10)
        resp.raise_for_status()
        data = resp.json()
        print(f"📄 License verification response: {data}")
        return data.get("valid", False), data.get("type", None)
    except Exception as e:
        print(f"❌ License verification error: {e}")
        return False, "connection_error"

def ask_for_license():
    machine_id = get_machine_id()
    license_key = simpledialog.askstring("License Key", "Enter your 24-character license key:")
    if license_key:
        clean_license = license_key.strip().replace(" ", "").replace("-", "").upper()
        if len(clean_license) != 24:
            messagebox.showerror("Invalid Format", "License key must be 24 characters long.")
            return ask_for_license()
            
        valid, ltype = verify_license_online(clean_license, machine_id)
        if valid:
            license_data = {
                "machine_id": machine_id, 
                "license_key": clean_license, 
                "license_type": ltype,
                "activated_at": datetime.now().isoformat(),
                "last_verified": datetime.now().isoformat()
            }
            save_local_token(license_data)
            license_status_var.set("License: Active")
            enable_download_buttons(True)
            messagebox.showinfo("License Activated", "License activated successfully! Lifetime access granted.")
            return True
        else:
            if ltype == "connection_error":
                messagebox.showerror("Connection Error", "Cannot connect to license server. Please check your internet connection.")
            else:
                messagebox.showerror("Invalid License", "License key is invalid or already used on another machine.")
    elif license_key is None:
        return False
    return False

def check_license_status():
    try:
        token = load_local_token()
        machine_id = get_machine_id()
        
        print(f"🔍 Checking license status for machine: {machine_id}")
        print(f"📁 Token data: {token}")

        if not token:
            print("📭 No token found, starting trial...")
            return start_trial(machine_id)

        if "license_key" in token:
            print("📋 Found license in token, verifying...")
            valid, ltype = verify_license_online(token["license_key"], machine_id)
            if valid:
                token["last_verified"] = datetime.now().isoformat()
                save_local_token(token)
                license_status_var.set("License: Active")
                enable_download_buttons(True)
                return True
            else:
                if ltype == "connection_error":
                    license_status_var.set("License: Active (Offline)")
                    enable_download_buttons(True)
                    return True
                else:
                    enable_download_buttons(False)
                    return ask_for_license()

        elif "trial_start" in token:
            print("📋 Found trial in token, checking...")
            try:
                resp = requests.post(f"{LICENSE_SERVER}/trial", json={"machine_id": machine_id}, timeout=5)
                data = resp.json()
                if data.get("valid"):
                    days_left = data.get("days_left", TRIAL_DAYS)
                    license_status_var.set(f"Trial: {days_left} days left")
                    enable_download_buttons(True)
                    return True
                else:
                    enable_download_buttons(False)
                    return ask_for_license()
            except:
                trial_start = datetime.fromisoformat(token["trial_start"])
                elapsed = (datetime.now() - trial_start).days
                if elapsed < TRIAL_DAYS:
                    days_left = TRIAL_DAYS - elapsed
                    license_status_var.set(f"Trial: {days_left} days left (Offline)")
                    enable_download_buttons(True)
                    return True
                else:
                    enable_download_buttons(False)
                    return ask_for_license()

        print("📭 No valid token, starting fresh trial...")
        return start_trial(machine_id)
        
    except Exception as e:
        print(f"💥 Error in check_license_status: {e}")
        license_status_var.set("Status: Error - Check Connection")
        enable_download_buttons(True)
        return True

def check_trial_or_license():
    def run_check():
        try:
            success = check_license_status()
            if not success:
                print("🔄 Initial check failed, retrying...")
                time.sleep(2)
                check_license_status()
        except Exception as e:
            print(f"💥 License check thread error: {e}")
            license_status_var.set("Status: Check Failed")
    
    threading.Thread(target=run_check, daemon=True).start()
    return True

def enable_download_buttons(state=True):
    for btn in [btn_add, btn_instant, btn_start, btn_pause, btn_resume, btn_clear_completed]:
        btn.config(state=tk.NORMAL if state else tk.DISABLED)

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
    about_window.configure(bg=COLORS["light"])
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
    
    tk.Label(header_frame, text="Universal Media Downloader", font=("Arial", 12), 
             bg=COLORS["primary"], fg="white").pack(expand=True)
    
    # Content
    content_frame = tk.Frame(about_window, bg=COLORS["light"], padx=20, pady=20)
    content_frame.pack(fill="both", expand=True, padx=10, pady=10)
    
    info_text = f"""
Version: {CURRENT_VERSION}

SwiftHarryDM is a powerful universal downloader that supports:
• YouTube, Vimeo, Twitter, and 1000+ sites
• Multiple formats (MP4, MP3, 1080p, 720p)
• Browser extension integration
• Queue management with pause/resume
• License and trial system

Features:
✓ High-speed downloads
✓ Format conversion
✓ Browser integration
✓ Modern UI/UX
✓ Cross-platform support

Developed with ❤️ for content creators and enthusiasts.

© 2024 SwiftHarryDM. All rights reserved.
    """
    
    tk.Label(content_frame, text=info_text, font=("Arial", 10), 
             bg=COLORS["light"], justify="left", anchor="w").pack(fill="both", expand=True)
    
    # Close button
    tk.Button(about_window, text="Close", command=about_window.destroy,
              bg=COLORS["primary"], fg="white", font=("Arial", 10, "bold"),
              width=20, height=2).pack(pady=10)

# ------------------ License Windows ------------------
def show_license_info():
    try:
        with open("LICENSE.txt","r") as f:
            license_text = f.read()
        license_window = tk.Toplevel(root)
        license_window.title("License Information")
        license_window.geometry("700x500")
        
        text_frame = tk.Frame(license_window)
        text_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        scrollbar = ttk.Scrollbar(text_frame)
        scrollbar.pack(side="right", fill="y")
        
        txt = tk.Text(text_frame, wrap="word", font=("Arial",10), yscrollcommand=scrollbar.set)
        txt.pack(side="left", fill="both", expand=True)
        scrollbar.config(command=txt.yview)
        
        txt.insert(tk.END, license_text)
        txt.config(state="disabled")
    except:
        messagebox.showerror("Error", "LICENSE.txt not found!")

def show_license_window():
    license_win = tk.Toplevel(root)
    license_win.title("License Management")
    license_win.geometry("400x300")
    license_win.resizable(False, False)
    license_win.configure(bg=COLORS["light"])
    
    license_win.transient(root)
    license_win.grab_set()
    
    # Center the window
    license_win.update_idletasks()
    x = (license_win.winfo_screenwidth() // 2) - (400 // 2)
    y = (license_win.winfo_screenheight() // 2) - (300 // 2)
    license_win.geometry(f"400x300+{x}+{y}")
    
    # Header
    header_frame = tk.Frame(license_win, bg=COLORS["primary"], height=60)
    header_frame.pack(fill="x", side="top")
    header_frame.pack_propagate(False)
    
    tk.Label(header_frame, text="License Management", font=("Arial", 16, "bold"), 
             bg=COLORS["primary"], fg="white").pack(expand=True)
    
    # Current status frame
    status_frame = tk.Frame(license_win, padx=20, pady=20, bg=COLORS["light"])
    status_frame.pack(fill="x", padx=10, pady=10)
    
    tk.Label(status_frame, text="Current Status:", font=("Arial", 12, "bold"), 
             bg=COLORS["light"]).pack(anchor="w")
    current_status_label = tk.Label(status_frame, textvariable=license_status_var, 
                                   font=("Arial", 11), fg="blue", bg=COLORS["light"])
    current_status_label.pack(anchor="w", pady=(5, 0))
    
    # Separator
    ttk.Separator(license_win, orient="horizontal").pack(fill="x", padx=20, pady=5)
    
    # Actions frame
    actions_frame = tk.Frame(license_win, padx=20, pady=10, bg=COLORS["light"])
    actions_frame.pack(fill="both", expand=True, padx=10, pady=10)
    
    tk.Label(actions_frame, text="License Actions:", font=("Arial", 12, "bold"), 
             bg=COLORS["light"]).pack(anchor="w")
    
    # Buttons
    btn_enter_license = tk.Button(actions_frame, text="Enter License Key", command=ask_for_license, 
                                 bg=COLORS["primary"], fg="white", width=20, font=("Arial", 10),
                                 relief="flat", padx=10, pady=5)
    btn_enter_license.pack(pady=10)
    
    btn_check_status = tk.Button(actions_frame, text="Check License Status", 
                                command=lambda: check_trial_or_license(), 
                                bg=COLORS["success"], fg="white", width=20, font=("Arial", 10),
                                relief="flat", padx=10, pady=5)
    btn_check_status.pack(pady=5)
    
    btn_view_info = tk.Button(actions_frame, text="View License Information", 
                             command=show_license_info, 
                             bg=COLORS["secondary"], fg="white", width=20, font=("Arial", 10),
                             relief="flat", padx=10, pady=5)
    btn_view_info.pack(pady=10)
    
    # Close button
    btn_close = tk.Button(license_win, text="Close", command=license_win.destroy,
                         bg=COLORS["danger"], fg="white", width=15, font=("Arial", 10, "bold"),
                         relief="flat", padx=10, pady=5)
    btn_close.pack(pady=10)

# ------------------ Universal Downloader ------------------
class UniversalDownloader:
    def __init__(self, url, fmt="best", save_path=None, progress_hook=None, is_extension=False):
        self.url = url
        self.fmt = fmt
        self.save_path = save_path or os.path.join(os.path.expanduser("~"), "Desktop", "SwiftHarryDM Downloads")
        self.progress_hook = progress_hook
        self.is_extension = is_extension  # New flag to detect extension downloads
        os.makedirs(self.save_path, exist_ok=True)
        print(f"🔧 [DOWNLOADER] Initialized: {url} -> {fmt} -> {self.save_path} | Extension: {is_extension}")

    def download(self):
        try:
            print(f"🔧 [DOWNLOADER] Starting yt-dlp download...")
            
            # Enhanced options for better compatibility
            opts = {
                "format": format_mapping(self.fmt),
                "outtmpl": os.path.join(self.save_path, "%(title)s.%(ext)s"),
                "progress_hooks": [self.progress_hook] if self.progress_hook else [],
                "merge_output_format": "mp4",
                "ignoreerrors": True,  # Continue on download errors
                "retries": 10,  # Increase retries
                "fragment_retries": 10,
                "skip_unavailable_fragments": True,
            }
            
            # CRITICAL FIX: Force single video download ONLY for extension requests
            if self.is_extension:
                print("🔧 [DOWNLOADER] Extension download detected - forcing SINGLE VIDEO (no playlist)")
                opts.update({
                    "noplaylist": True,  # THIS IS THE KEY - don't download playlist
                    "extract_flat": False,
                })
            else:
                print("🔧 [DOWNLOADER] Manual app download - playlist downloads ALLOWED")
                # Keep default behavior (playlist downloads enabled)
                opts.update({
                    "noplaylist": False,  # Allow playlists for manual downloads
                })
            
            # Special handling for problematic sites
            if "facebook.com" in self.url:
                print("🔧 [DOWNLOADER] Facebook detected - adding special options")
                opts.update({
                    "cookiefile": None,  # Try without cookies first
                })
            
            with YoutubeDL(opts) as ydl:
                print(f"🔧 [DOWNLOADER] Extracting info for: {self.url}")
                info = ydl.extract_info(self.url, download=True)
                
                if not info:
                    raise Exception("Failed to extract video information")
                    
                filename = ydl.prepare_filename(info)
                print(f"🔧 [DOWNLOADER] Filename: {filename}")
                
                if self.fmt.lower() == "mp3":
                    print(f"🔧 [DOWNLOADER] Converting to MP3...")
                    convert_to_mp3(filename, os.path.splitext(filename)[0]+".mp3")
                    
        except Exception as e:
            print(f"❌ [DOWNLOADER] yt-dlp failed: {e}")
            
            # Enhanced fallback with better error handling
            if self.url.startswith("http"):
                print(f"🔧 [DOWNLOADER] Falling back to enhanced downloader")
                self.fallback_download()
            else:
                raise e

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
    save_path = filedialog.askdirectory(title="Select Save Location") or os.path.join(os.path.expanduser("~"), "Desktop", "SwiftHarryDM Downloads")
    os.makedirs(save_path, exist_ok=True)
    item = {"url": url, "fmt": fmt, "save_path": save_path, "status": "Pending", "progress": 0}
    download_queue.append(item)
    paused_flags.append(False)
    create_queue_item(len(download_queue)-1)
    url_entry.delete(0, tk.END)

def instant_download():
    url = url_entry.get().strip()
    fmt = format_var.get()
    if not url:
        messagebox.showerror("Error", "Please enter a URL!")
        return
    save_path = filedialog.askdirectory(title="Select Save Location") or os.path.join(os.path.expanduser("~"), "Desktop", "SwiftHarryDM Downloads")
    os.makedirs(save_path, exist_ok=True)
    item = {"url": url, "fmt": fmt, "save_path": save_path, "status": "Downloading", "progress": 0}
    download_queue.append(item)
    paused_flags.append(False)
    idx = len(download_queue)-1
    create_queue_item(idx)
    threading.Thread(target=download_worker, args=(idx,), daemon=True).start()
    url_entry.delete(0, tk.END)

def create_queue_item(idx):
    item = download_queue[idx]
    frame = tk.Frame(queue_container, bd=1, relief="solid", padx=10, pady=8, bg="white")
    frame.pack(pady=4, fill="x", padx=5)
    
    # Header with title and status
    header_frame = tk.Frame(frame, bg="white")
    header_frame.pack(fill="x")
    
    title = item.get('title', get_filename_from_url(item['url']))
    label = tk.Label(header_frame, text=title[:80] + "..." if len(title) > 80 else title, 
                    font=("Arial", 10, "bold"), anchor="w", bg="white")
    label.pack(side="left", fill="x", expand=True)
    
    status_label = tk.Label(header_frame, text=f"{item['status']}", 
                           font=("Arial", 9, "bold"), anchor="e", bg="white")
    status_label.pack(side="right")
    
    # Progress bar
    progress = ttk.Progressbar(frame, orient="horizontal", length=650, mode="determinate")
    progress['value'] = item['progress']
    progress.pack(side="top", pady=5, fill="x")
    
    # Format and actions
    footer_frame = tk.Frame(frame, bg="white")
    footer_frame.pack(fill="x")
    
    format_label = tk.Label(footer_frame, text=f"Format: {item['fmt']}", 
                           font=("Arial", 8), anchor="w", bg="white", fg=COLORS["gray"])
    format_label.pack(side="left")
    
    if item.get('source') == 'extension':
        source_label = tk.Label(footer_frame, text="🌐 Browser", 
                               font=("Arial", 8), bg="white", fg=COLORS["primary"])
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
        "Pending": "#e5e7eb", 
        "Downloading": "#d1fae5", 
        "Paused": "#fef3c7", 
        "Completed": "#dbeafe", 
        "Error": "#fee2e2"
    }
    text_color_map = {
        "Pending": "#374151",
        "Downloading": "#065f46", 
        "Paused": "#92400e", 
        "Completed": "#1e40af", 
        "Error": "#991b1b"
    }
    
    bg_color = color_map.get(item['status'], "white")
    text_color = text_color_map.get(item['status'], "#374151")
    
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

    print(f"🔧 [WORKER] Starting download worker for: {title}")
    print(f"🔧 [WORKER] URL: {url}")
    print(f"🔧 [WORKER] Format: {fmt}")
    print(f"🔧 [WORKER] Save path: {save_path}")

    def progress_hook(d):
        if d['status'] == 'downloading':
            item['progress'] = clean_percent(d.get('_percent_str','0%'))
            update_queue_item(idx)
            # Debug progress
            if item['progress'] % 20 == 0:  # Log every 20%
                print(f"📊 [WORKER] Progress: {item['progress']}% - {title}")
        elif d['status'] == 'finished':
            item['progress'] = 100
            update_queue_item(idx)
            print(f"✅ [WORKER] Download finished: {title}")

    try:
        log_text.insert(tk.END, f"🚀 Starting download: {title}\n")
        log_text.see(tk.END)
        print(f"🎯 [WORKER] Calling UniversalDownloader for: {title}")
        
        downloader = UniversalDownloader(url, fmt, save_path, progress_hook)
        downloader.download()
        item["status"] = "Completed"
        update_queue_item(idx)
        
        success_msg = f"✅ Download completed: {title}\n"
        log_text.insert(tk.END, success_msg)
        log_text.see(tk.END)
        print(f"🎉 [WORKER] Download successful: {title}")
        
    except Exception as e:
        item["status"] = "Error"
        update_queue_item(idx)
        error_msg = f"❌ Download failed: {title} - {str(e)}\n"
        log_text.insert(tk.END, error_msg)
        log_text.see(tk.END)
        print(f"💥 [WORKER] Download failed: {title} - Error: {str(e)}")
        import traceback
        traceback.print_exc()

# ------------------ Modern GUI ------------------
root = tk.Tk()
root.title(f"SwiftHarryDM v{CURRENT_VERSION} - Universal Downloader")
root.geometry("1000x800")
root.configure(bg=COLORS["light"])

# Apply modern theme
style = ttk.Style()
style.theme_use('clam')

# Configure styles
style.configure('TFrame', background=COLORS["light"])
style.configure('TLabel', background=COLORS["light"], font=('Arial', 10))
style.configure('TButton', font=('Arial', 10))
style.configure('TEntry', font=('Arial', 11))
style.configure('TCombobox', font=('Arial', 11))

# Modern Menu
menu_bar = tk.Menu(root, bg=COLORS["light"], fg=COLORS["dark"], font=('Arial', 10))

# File Menu
file_menu = tk.Menu(menu_bar, tearoff=0, bg=COLORS["light"], fg=COLORS["dark"])
file_menu.add_command(label="Clear Completed", command=clear_completed)
file_menu.add_separator()
file_menu.add_command(label="Exit", command=root.quit)
menu_bar.add_cascade(label="File", menu=file_menu)

# License Menu
license_menu = tk.Menu(menu_bar, tearoff=0, bg=COLORS["light"], fg=COLORS["dark"])
license_menu.add_command(label="License Management", command=show_license_window)
license_menu.add_command(label="View License Info", command=show_license_info)
menu_bar.add_cascade(label="License", menu=license_menu)

# Help Menu
help_menu = tk.Menu(menu_bar, tearoff=0, bg=COLORS["light"], fg=COLORS["dark"])
help_menu.add_command(label="Check for Updates", command=lambda: check_for_updates(auto=False))
help_menu.add_command(label="About SwiftHarryDM", command=show_about)
menu_bar.add_cascade(label="Help", menu=help_menu)

root.config(menu=menu_bar)

# Header Frame
header_frame = tk.Frame(root, bg=COLORS["primary"], height=80)
header_frame.pack(fill="x", side="top")
header_frame.pack_propagate(False)

# Header Content
header_content = tk.Frame(header_frame, bg=COLORS["primary"])
header_content.pack(expand=True, fill="both", padx=20)

tk.Label(header_content, text="🚀 SwiftHarryDM", font=("Arial", 24, "bold"), 
         bg=COLORS["primary"], fg="white").pack(side="left")

tk.Label(header_content, text=f"v{CURRENT_VERSION}", font=("Arial", 12), 
         bg=COLORS["primary"], fg="white").pack(side="left", padx=(10, 0))

# Status indicators
status_frame = tk.Frame(header_content, bg=COLORS["primary"])
status_frame.pack(side="right")

license_status_var = tk.StringVar(value="Checking...")
license_label = tk.Label(status_frame, textvariable=license_status_var, font=("Arial", 10, "bold"), 
                        bg=COLORS["primary"], fg="white")
license_label.pack(side="top", anchor="e")

extension_status_var = tk.StringVar(value="🔌 Extension: Connecting...")
extension_label = tk.Label(status_frame, textvariable=extension_status_var, font=("Arial", 9), 
                          bg=COLORS["primary"], fg="#d1fae5")
extension_label.pack(side="top", anchor="e")

# Main Content Frame
main_frame = tk.Frame(root, bg=COLORS["light"], padx=20, pady=20)
main_frame.pack(fill="both", expand=True)

# URL Input Section
input_frame = tk.Frame(main_frame, bg=COLORS["light"])
input_frame.pack(fill="x", pady=(0, 15))

tk.Label(input_frame, text="Enter URL:", font=("Arial", 11, "bold"), 
         bg=COLORS["light"]).pack(anchor="w", pady=(0, 5))

url_entry_frame = tk.Frame(input_frame, bg=COLORS["light"])
url_entry_frame.pack(fill="x")

url_entry = tk.Entry(url_entry_frame, width=80, font=("Arial", 11), relief="solid", bd=1)
url_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))

# Format selection
format_frame = tk.Frame(input_frame, bg=COLORS["light"])
format_frame.pack(fill="x", pady=(10, 0))

tk.Label(format_frame, text="Select Format:", font=("Arial", 11, "bold"), 
         bg=COLORS["light"]).pack(side="left")

format_var = tk.StringVar(value="best")
format_menu = ttk.Combobox(format_frame, textvariable=format_var,
                           values=["best", "1080", "720", "mp3"], state="readonly", 
                           width=15, font=("Arial", 11))
format_menu.pack(side="left", padx=(10, 0))

# Action Buttons
btn_frame = tk.Frame(main_frame, bg=COLORS["light"])
btn_frame.pack(fill="x", pady=15)

def create_modern_button(parent, text, command, color, width=15):
    return tk.Button(parent, text=text, command=command, 
                    bg=color, fg="white", width=width, font=("Arial", 10, "bold"),
                    relief="flat", padx=15, pady=8, bd=0)

btn_add = create_modern_button(btn_frame, "Add to Queue", add_to_queue, COLORS["primary"])
btn_add.grid(row=0, column=0, padx=5)

btn_instant = create_modern_button(btn_frame, "Instant Download", instant_download, COLORS["success"])
btn_instant.grid(row=0, column=1, padx=5)

btn_start = create_modern_button(btn_frame, "Start Selected", start_selected, COLORS["success"])
btn_start.grid(row=0, column=2, padx=5)

btn_pause = create_modern_button(btn_frame, "Pause Selected", pause_selected, COLORS["warning"])
btn_pause.grid(row=0, column=3, padx=5)

btn_resume = create_modern_button(btn_frame, "Resume Selected", resume_selected, COLORS["secondary"])
btn_resume.grid(row=0, column=4, padx=5)

btn_clear_completed = create_modern_button(btn_frame, "Clear Completed", clear_completed, COLORS["danger"])
btn_clear_completed.grid(row=0, column=5, padx=5)

# Queue Section
queue_section = tk.Frame(main_frame, bg=COLORS["light"])
queue_section.pack(fill="both", expand=True, pady=(20, 0))

queue_header = tk.Frame(queue_section, bg=COLORS["light"])
queue_header.pack(fill="x")

tk.Label(queue_header, text="Download Queue:", font=("Arial", 14, "bold"), 
         bg=COLORS["light"]).pack(side="left")

queue_count_var = tk.StringVar(value="(0 items)")
queue_count_label = tk.Label(queue_header, textvariable=queue_count_var, font=("Arial", 11), 
                            bg=COLORS["light"], fg=COLORS["gray"])
queue_count_label.pack(side="left", padx=(10, 0))

# Queue container with scroll
queue_container_frame = tk.Frame(queue_section, bg=COLORS["light"])
queue_container_frame.pack(fill="both", expand=True, pady=(10, 0))

queue_canvas = tk.Canvas(queue_container_frame, bg="white", highlightthickness=0)
queue_scrollbar = ttk.Scrollbar(queue_container_frame, orient="vertical", command=queue_canvas.yview)
queue_container = tk.Frame(queue_canvas, bg="white")

queue_container.bind("<Configure>", lambda e: queue_canvas.configure(scrollregion=queue_canvas.bbox("all")))
queue_canvas.create_window((0,0), window=queue_container, anchor="nw", width=queue_canvas.winfo_width())
queue_canvas.configure(yscrollcommand=queue_scrollbar.set)

queue_canvas.pack(side="left", fill="both", expand=True)
queue_scrollbar.pack(side="right", fill="y")

def update_queue_display(event):
    queue_canvas.configure(scrollregion=queue_canvas.bbox("all"))
    queue_canvas.itemconfig('all', width=queue_canvas.winfo_width())

queue_canvas.bind('<Configure>', update_queue_display)

# Log Section
log_section = tk.Frame(main_frame, bg=COLORS["light"])
log_section.pack(fill="x", pady=(20, 0))

tk.Label(log_section, text="Activity Log:", font=("Arial", 14, "bold"), 
         bg=COLORS["light"]).pack(anchor="w")

log_frame = tk.Frame(log_section, bg=COLORS["light"])
log_frame.pack(fill="x", pady=(10, 0))

log_text = tk.Text(log_frame, height=8, wrap="word", font=("Consolas", 9), 
                  relief="solid", bd=1, bg="#1e1e1e", fg="#00ff00")
log_text.pack(side="left", fill="both", expand=True)

log_scrollbar = ttk.Scrollbar(log_frame, orient="vertical", command=log_text.yview)
log_text.configure(yscrollcommand=log_scrollbar.set)
log_scrollbar.pack(side="right", fill="y")

# Footer
footer_frame = tk.Frame(root, bg=COLORS["dark"], height=30)
footer_frame.pack(fill="x", side="bottom")
footer_frame.pack_propagate(False)

footer_label = tk.Label(footer_frame, text="🚀 SwiftHarryDM - Universal Downloader | © 2024 All rights reserved", 
                       font=("Arial", 9), bg=COLORS["dark"], fg="white")
footer_label.pack(expand=True)

# ------------------ Startup Functions ------------------
def update_queue_count():
    total = len(download_queue)
    active = len([item for item in download_queue if item["status"] == "Downloading"])
    queue_count_var.set(f"({total} items, {active} active)")
    root.after(1000, update_queue_count)

def check_extension_connection():
    try:
        response = requests.get("http://127.0.0.1:5001/health", timeout=2)
        if response.status_code == 200:
            extension_status_var.set("🔌 Extension: Connected ✓")
            extension_label.config(fg="#10b981")  # Green
        else:
            extension_status_var.set("🔌 Extension: Port busy")
            extension_label.config(fg="#f59e0b")  # Orange
    except:
        extension_status_var.set("🔌 Extension: Not connected")
        extension_label.config(fg="#ef4444")  # Red
    
    # Check again after 5 seconds
    root.after(5000, check_extension_connection)

# ------------------ Initialize App ------------------
auto_update_check()
root.after(3000, check_extension_connection)
root.after(1000, update_queue_count)

# Check trial/license at startup
if not check_trial_or_license():
    root.destroy()
    exit()

# Start the main loop
root.mainloop()