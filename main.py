import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, filedialog
import threading
import os
import re
import requests
import json
import hashlib
import uuid
from datetime import datetime, timedelta
from src.downloader import Downloader
from utils import convert_to_mp3, format_mapping
from yt_dlp import YoutubeDL

# ------------------ Globals ------------------
download_queue = []
paused_flags = []
queue_frames = []
CURRENT_VERSION = "1.0.0"
UPDATE_CHECK_URL = "https://swiftharrydm.harshchaudhary.com.np/version.txt"
DOWNLOAD_PAGE_URL = "https://swiftharrydm.harshchaudhary.com.np/downloads"

# License / Trial Config
LICENSE_SERVER = "http://localhost:3000"  # change to live URL when deploying
TOKEN_FILE = os.path.join(os.path.expanduser("~"), ".swift_dm_token.json")
TRIAL_DAYS = 7


#temporary
def check_trial_or_license():
    print("Checking trial/license...")
    token = load_local_token()
    machine_id = get_machine_id()
    now = datetime.now()
    
    if token:
        print("Token found:", token)
    else:
        print("No token found. Starting trial...")

# ------------------ Utilities ------------------
def clean_percent(percent_str):
    ansi_escape = re.compile(r'\x1B[@-_][0-?]*[ -/]*[@-~]')
    clean_str = ansi_escape.sub('', percent_str)
    try:
        return int(float(clean_str.replace('%','').strip()))
    except:
        return 0

def sanitize_filename(name):
    return re.sub(r'[<>:"/\\|?*]', '_', name)

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

# ------------------ License & Trial ------------------
def start_trial(machine_id):
    try:
        print(f"Starting trial for machine: {machine_id}")
        resp = requests.post(f"{LICENSE_SERVER}/trial", json={"machine_id": machine_id}, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        print(f"Trial response: {data}")
        
        if data.get("valid"):
            days_left = data.get("days_left", TRIAL_DAYS)
            save_local_token({"machine_id": machine_id, "trial_start": datetime.now().isoformat()})
            license_status_var.set(f"Trial: {days_left} days left")
            messagebox.showinfo("Trial Started", f"Your trial started! {days_left} days left.")
            return True
        else:
            messagebox.showinfo("Trial Expired", "Trial expired. Enter a license key to continue.")
            return ask_for_license()
    except Exception as e:
        print(f"Trial error: {e}")
        messagebox.showerror("Error", f"Cannot start trial.\n{str(e)}")
        return False

def verify_license_online(license_key, machine_id):
    try:
        print(f"Verifying license: {license_key} for machine: {machine_id}")
        # Clean the license key (remove spaces and normalize)
        clean_license = license_key.strip().replace(" ", "").replace("-", "")
        
        resp = requests.post(f"{LICENSE_SERVER}/verify", 
                           json={"license_key": clean_license, "machine_id": machine_id}, 
                           timeout=10)
        resp.raise_for_status()
        data = resp.json()
        print(f"License verification response: {data}")
        return data.get("valid", False), data.get("type", None)
    except Exception as e:
        print(f"License verification error: {e}")
        messagebox.showerror("Error", f"Cannot verify license.\n{str(e)}")
        return False, None

def ask_for_license():
    machine_id = get_machine_id()
    license_key = simpledialog.askstring("License Key", "Enter your 24-character license key:")
    if license_key:
        # Clean the input
        clean_license = license_key.strip().replace(" ", "").upper()
        if len(clean_license) != 24:
            messagebox.showerror("Invalid Format", "License key must be 24 characters long.")
            return ask_for_license()
            
        valid, ltype = verify_license_online(clean_license, machine_id)
        if valid:
            save_local_token({
                "machine_id": machine_id, 
                "license_key": clean_license, 
                "license_type": ltype,
                "activated_at": datetime.now().isoformat()
            })
            license_status_var.set("License: Active")
            enable_download_buttons(True)
            messagebox.showinfo("License Activated", "License activated successfully! Lifetime access granted.")
            return True
    elif license_key is None:  # User clicked cancel
        return False
    messagebox.showerror("Invalid License", "License key is invalid or already used.")
    return False

def check_trial_or_license():
    try:
        token = load_local_token()
        machine_id = get_machine_id()
        now = datetime.now()

        print(f"Checking license/trial for machine: {machine_id}")
        print(f"Token data: {token}")

        if token:
            # License exists
            if "license_key" in token:
                print("Found existing license, verifying...")
                valid, _ = verify_license_online(token["license_key"], machine_id)
                if valid:
                    license_status_var.set("License: Active")
                    enable_download_buttons(True)
                    return True
                else:
                    enable_download_buttons(False)
                    return ask_for_license()
            # Trial exists
            elif "trial_start" in token:
                print("Found existing trial, checking...")
                trial_start = datetime.fromisoformat(token["trial_start"])
                elapsed = (now - trial_start).days
                if elapsed < TRIAL_DAYS:
                    license_status_var.set(f"Trial: {TRIAL_DAYS - elapsed} days left")
                    enable_download_buttons(True)
                    return True
                else:
                    enable_download_buttons(False)
                    # Check with server to be sure
                    return start_trial(machine_id)
        else:
            print("No token found, starting trial...")
            return start_trial(machine_id)
            
    except Exception as e:
        print(f"Error in check_trial_or_license: {e}")
        # Fallback: enable buttons and show error status
        license_status_var.set("Status: Error - Check Connection")
        enable_download_buttons(True)  # Enable anyway for better UX
        return True

def enable_download_buttons(state=True):
    for btn in [btn_add, btn_instant, btn_start, btn_pause, btn_resume]:
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

# ------------------ License Display ------------------
def show_license_info():
    try:
        with open("LICENSE.txt","r") as f:
            license_text = f.read()
        license_window = tk.Toplevel(root)
        license_window.title("License Information")
        txt = tk.Text(license_window, wrap="word", font=("Arial",10), width=100, height=30)
        txt.pack(padx=5, pady=5, fill="both", expand=True)
        txt.insert(tk.END, license_text)
    except:
        messagebox.showerror("Error", "LICENSE.txt not found!")

def show_license_window():
    """Show license management window"""
    license_win = tk.Toplevel(root)
    license_win.title("License Management")
    license_win.geometry("400x300")
    license_win.resizable(False, False)
    
    # Center the window
    license_win.transient(root)
    license_win.grab_set()
    
    # Current status frame
    status_frame = tk.Frame(license_win, padx=10, pady=10)
    status_frame.pack(fill="x", padx=10, pady=10)
    
    tk.Label(status_frame, text="Current Status:", font=("Arial", 12, "bold")).pack(anchor="w")
    current_status_label = tk.Label(status_frame, textvariable=license_status_var, font=("Arial", 11), fg="blue")
    current_status_label.pack(anchor="w", pady=(5, 0))
    
    # Separator
    ttk.Separator(license_win, orient="horizontal").pack(fill="x", padx=10, pady=5)
    
    # Actions frame
    actions_frame = tk.Frame(license_win, padx=10, pady=10)
    actions_frame.pack(fill="both", expand=True, padx=10, pady=10)
    
    tk.Label(actions_frame, text="License Actions:", font=("Arial", 12, "bold")).pack(anchor="w")
    
    # Buttons
    btn_enter_license = tk.Button(actions_frame, text="Enter License Key", command=ask_for_license, 
                                 bg="#0078D7", fg="white", width=20, font=("Arial", 10))
    btn_enter_license.pack(pady=10)
    
    btn_check_status = tk.Button(actions_frame, text="Check License Status", 
                                command=lambda: check_trial_or_license(), 
                                bg="#28A745", fg="white", width=20, font=("Arial", 10))
    btn_check_status.pack(pady=5)
    
    btn_view_info = tk.Button(actions_frame, text="View License Information", 
                             command=show_license_info, 
                             bg="#6A0DAD", fg="white", width=20, font=("Arial", 10))
    btn_view_info.pack(pady=10)
    
    # Close button
    btn_close = tk.Button(license_win, text="Close", command=license_win.destroy,
                         bg="#DC3545", fg="white", width=15, font=("Arial", 10))
    btn_close.pack(pady=10)

# ------------------ Universal Downloader ------------------
class UniversalDownloader:
    def __init__(self, url, fmt="best", save_path=None, progress_hook=None):
        self.url = url
        self.fmt = fmt
        self.save_path = save_path or os.path.join(os.path.expanduser("~"), "Desktop")
        os.makedirs(self.save_path, exist_ok=True)
        self.progress_hook = progress_hook

    def download(self):
        try:
            opts = {
                "format": format_mapping(self.fmt),
                "outtmpl": os.path.join(self.save_path, "%(title)s.%(ext)s"),
                "progress_hooks": [self.progress_hook] if self.progress_hook else [],
                "merge_output_format": "mp4",
                "noplaylist": False
            }
            with YoutubeDL(opts) as ydl:
                info = ydl.extract_info(self.url, download=True)
                filename = ydl.prepare_filename(info)
                if self.fmt.lower() == "mp3":
                    convert_to_mp3(filename, os.path.splitext(filename)[0]+".mp3")
        except Exception as e:
            if self.url.startswith("http"):
                Downloader(self.url, self.save_path).download()
            else:
                raise e

# ------------------ Queue Functions ------------------
def add_to_queue():
    url = url_entry.get().strip()
    fmt = format_var.get()
    if not url:
        messagebox.showerror("Error", "Please enter a URL!")
        return
    save_path = filedialog.askdirectory(title="Select Save Location") or os.path.join(os.path.expanduser("~"), "Desktop")
    item = {"url": url, "fmt": fmt, "save_path": save_path, "status": "Pending", "progress": 0}
    download_queue.append(item)
    paused_flags.append(False)
    create_queue_item(len(download_queue)-1)

def instant_download():
    url = url_entry.get().strip()
    fmt = format_var.get()
    if not url:
        messagebox.showerror("Error", "Please enter a URL!")
        return
    save_path = filedialog.askdirectory(title="Select Save Location") or os.path.join(os.path.expanduser("~"), "Desktop")
    item = {"url": url, "fmt": fmt, "save_path": save_path, "status": "Downloading", "progress": 0}
    download_queue.append(item)
    paused_flags.append(False)
    idx = len(download_queue)-1
    create_queue_item(idx)
    threading.Thread(target=download_worker, args=(idx,), daemon=True).start()

def create_queue_item(idx):
    item = download_queue[idx]
    frame = tk.Frame(queue_container, bd=2, relief="groove", padx=5, pady=5)
    label = tk.Label(frame, text=get_filename_from_url(item['url']), font=("Arial", 10, "bold"), anchor="w")
    label.pack(side="top", anchor="w", fill="x")
    status_label = tk.Label(frame, text=f"{item['status']}", font=("Arial", 9), anchor="w")
    status_label.pack(side="top", anchor="w", fill="x")
    progress = ttk.Progressbar(frame, orient="horizontal", length=650, mode="determinate")
    progress['value'] = item['progress']
    progress.pack(side="top", pady=3, fill="x")
    frame.pack(pady=4, fill="x")
    queue_frames.append({"frame": frame, "label": label, "status_label": status_label, "progress": progress})
    update_queue_item_color(idx)

def update_queue_item(idx):
    item = download_queue[idx]
    frame_data = queue_frames[idx]
    frame_data['label'].config(text=get_filename_from_url(item['url']))
    frame_data['status_label'].config(text=f"{item['status']}")
    frame_data['progress']['value'] = item['progress']
    update_queue_item_color(idx)

def update_queue_item_color(idx):
    item = download_queue[idx]
    frame_data = queue_frames[idx]
    color_map = {"Pending":"lightgrey","Downloading":"lightgreen","Paused":"orange","Completed":"lightblue","Error":"red"}
    frame_data['frame'].config(bg=color_map.get(item['status'], "white"))
    frame_data['label'].config(bg=color_map.get(item['status'], "white"))
    frame_data['status_label'].config(bg=color_map.get(item['status'], "white"))

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

def download_worker(idx):
    item = download_queue[idx]
    url, fmt, save_path = item["url"], item["fmt"], item["save_path"]

    def progress_hook(d):
        if d['status'] == 'downloading':
            item['progress'] = clean_percent(d.get('_percent_str','0%'))
            update_queue_item(idx)
        elif d['status'] == 'finished':
            item['progress'] = 100
            update_queue_item(idx)

    try:
        downloader = UniversalDownloader(url, fmt, save_path, progress_hook)
        downloader.download()
        item["status"] = "Completed"
        update_queue_item(idx)
        log_text.insert(tk.END, f"Download completed: {get_filename_from_url(url)}\n")
        log_text.see(tk.END)
    except Exception as e:
        item["status"] = "Error"
        update_queue_item(idx)
        log_text.insert(tk.END, f"Error: {e}\n")
        log_text.see(tk.END)

# ------------------ GUI ------------------
root = tk.Tk()
root.title("SwiftHarryDM - Universal Downloader")
root.geometry("1000x800")

# Menu
menu_bar = tk.Menu(root)

# License Menu
license_menu = tk.Menu(menu_bar, tearoff=0)
license_menu.add_command(label="License Management", command=show_license_window)
license_menu.add_command(label="View License Info", command=show_license_info)
menu_bar.add_cascade(label="License", menu=license_menu)

# Help Menu
help_menu = tk.Menu(menu_bar, tearoff=0)
help_menu.add_command(label="Check for Updates", command=lambda: check_for_updates(auto=False))
menu_bar.add_cascade(label="Help", menu=help_menu)

root.config(menu=menu_bar)

# License status (minimal display in main window)
license_status_var = tk.StringVar(value="Checking...")
status_frame = tk.Frame(root)
status_frame.pack(pady=5)
tk.Label(status_frame, text="Status:", font=("Arial", 11)).pack(side="left", padx=5)
tk.Label(status_frame, textvariable=license_status_var, font=("Arial", 11, "bold"), fg="blue").pack(side="left", padx=5)

# URL input
tk.Label(root, text="Enter URL:", font=("Arial", 11)).pack(pady=5)
url_entry = tk.Entry(root, width=100, font=("Arial", 11))
url_entry.pack(pady=5)

# Format selection
tk.Label(root, text="Select Format:", font=("Arial", 11)).pack(pady=5)
format_var = tk.StringVar(value="best")
format_menu = ttk.Combobox(root, textvariable=format_var,
                           values=["best", "1080", "720", "mp3"], state="readonly", font=("Arial", 11))
format_menu.pack(pady=5)

# Buttons
btn_frame = tk.Frame(root)
btn_frame.pack(pady=10)
btn_add = tk.Button(btn_frame, text="Add to Queue", command=add_to_queue, bg="#0078D7", fg="white", width=18, font=("Arial",10))
btn_add.grid(row=0, column=0, padx=5)
btn_instant = tk.Button(btn_frame, text="Instant Download", command=instant_download, bg="#107C10", fg="white", width=18, font=("Arial",10))
btn_instant.grid(row=0, column=1, padx=5)
btn_start = tk.Button(btn_frame, text="Start Selected", command=start_selected, bg="#28A745", fg="white", width=18, font=("Arial",10))
btn_start.grid(row=0, column=2, padx=5)
btn_pause = tk.Button(btn_frame, text="Pause Selected", command=pause_selected, bg="#FFA500", fg="white", width=18, font=("Arial",10))
btn_pause.grid(row=0, column=3, padx=5)
btn_resume = tk.Button(btn_frame, text="Resume Selected", command=resume_selected, bg="#6A0DAD", fg="white", width=18, font=("Arial",10))
btn_resume.grid(row=0, column=4, padx=5)

# Queue container
tk.Label(root, text="Download Queue:", font=("Arial", 11, "bold")).pack(pady=5)
queue_canvas = tk.Canvas(root)
queue_scrollbar = ttk.Scrollbar(root, orient="vertical", command=queue_canvas.yview)
queue_container = tk.Frame(queue_canvas)
queue_container.bind("<Configure>", lambda e: queue_canvas.configure(scrollregion=queue_canvas.bbox("all")))
queue_canvas.create_window((0,0), window=queue_container, anchor="nw")
queue_canvas.configure(yscrollcommand=queue_scrollbar.set, height=250)
queue_canvas.pack(side="left", fill="both", expand=True)
queue_scrollbar.pack(side="right", fill="y")

# Log box
tk.Label(root, text="Log:", font=("Arial", 11, "bold")).pack(pady=5)
log_text = tk.Text(root, height=25, wrap="word", font=("Arial",10))
log_text.pack(pady=5, fill="both", expand=True)

# Auto-update check at start
auto_update_check()

# Check trial/license at startup
#if not check_trial_or_license():
  #  root.destroy()
   # exit()

root.mainloop()