import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
import os
import re
import requests
from src.downloader import Downloader
from utils import convert_to_mp3, format_mapping
from yt_dlp import YoutubeDL

# ------------------ Globals ------------------
download_queue = []
paused_flags = []
queue_frames = []
CURRENT_VERSION = "1.0.0"
UPDATE_CHECK_URL = "https://raw.githubusercontent.com/yourusername/SwiftHarryDM/main/version.txt"

# ------------------ Utilities ------------------
def clean_percent(percent_str):
    ansi_escape = re.compile(r'\x1B[@-_][0-?]*[ -/]*[@-~]')
    clean_str = ansi_escape.sub('', percent_str)
    try:
        return int(float(clean_str.replace('%','').strip()))
    except:
        return 0

def sanitize_filename(name):
    # Remove illegal characters for Windows filenames
    return re.sub(r'[<>:"/\\|?*]', '_', name)

def get_filename_from_url(url):
    return sanitize_filename(url.split('/')[-1])

def check_for_updates():
    try:
        resp = requests.get(UPDATE_CHECK_URL, timeout=5)
        latest_version = resp.text.strip()
        if latest_version != CURRENT_VERSION:
            if messagebox.askyesno("Update Available", f"A new version {latest_version} is available. Visit download page?"):
                import webbrowser
                webbrowser.open("https://github.com/yourusername/SwiftHarryDM/releases")
    except:
        log_text.insert(tk.END, "Unable to check updates.\n")

def show_license():
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
            # fallback for direct file links
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

# ------------------ Download Worker ------------------
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
root.geometry("1000x750")

# Menu
menu_bar = tk.Menu(root)
help_menu = tk.Menu(menu_bar, tearoff=0)
help_menu.add_command(label="Check for Updates", command=check_for_updates)
help_menu.add_command(label="License", command=show_license)
menu_bar.add_cascade(label="Help", menu=help_menu)
root.config(menu=menu_bar)

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
tk.Button(btn_frame, text="Add to Queue", command=add_to_queue, bg="#0078D7", fg="white", width=18, font=("Arial",10)).grid(row=0, column=0, padx=5)
tk.Button(btn_frame, text="Instant Download", command=instant_download, bg="#107C10", fg="white", width=18, font=("Arial",10)).grid(row=0, column=1, padx=5)
tk.Button(btn_frame, text="Start Selected", command=start_selected, bg="#28A745", fg="white", width=18, font=("Arial",10)).grid(row=0, column=2, padx=5)
tk.Button(btn_frame, text="Pause Selected", command=pause_selected, bg="#FFA500", fg="white", width=18, font=("Arial",10)).grid(row=0, column=3, padx=5)
tk.Button(btn_frame, text="Resume Selected", command=resume_selected, bg="#6A0DAD", fg="white", width=18, font=("Arial",10)).grid(row=0, column=4, padx=5)

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
threading.Thread(target=check_for_updates, daemon=True).start()

root.mainloop()
