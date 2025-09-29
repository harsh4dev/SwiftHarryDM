import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
from src.downloader import Downloader
from src.youtube_downloader import YouTubeDownloader
from src.playlist_downloader import PlaylistDownloader
import os
import re

# ------------------ Globals ------------------
download_queue = []
paused_flags = []

# ------------------ Functions ------------------
def clean_percent(percent_str):
    #Remove ANSI escape codes from yt-dlp percent string
    ansi_escape = re.compile(r'\x1B[@-_][0-?]*[ -/]*[@-~]')
    clean_str = ansi_escape.sub('', percent_str)
    return int(float(clean_str.replace('%','').strip()))

def add_to_queue():
    url = url_entry.get().strip()
    fmt = format_var.get()
    if not url:
        messagebox.showerror("Error", "Please enter a URL!")
        return

    save_path = filedialog.askdirectory(title="Select Save Location")
    if not save_path:
        save_path = os.path.join(os.path.expanduser("~"), "Desktop")

    item = {"url": url, "fmt": fmt, "save_path": save_path, "status": "Pending", "progress": 0}
    download_queue.append(item)
    paused_flags.append(False)
    update_queue_listbox(len(download_queue)-1)

def instant_download():
    url = url_entry.get().strip()
    fmt = format_var.get()
    if not url:
        messagebox.showerror("Error", "Please enter a URL!")
        return

    save_path = filedialog.askdirectory(title="Select Save Location")
    if not save_path:
        save_path = os.path.join(os.path.expanduser("~"), "Desktop")

    # Create a temporary queue item for progress tracking
    item = {"url": url, "fmt": fmt, "save_path": save_path, "status": "Downloading", "progress": 0}
    download_queue.append(item)
    paused_flags.append(False)
    idx = len(download_queue)-1
    update_queue_listbox(idx)
    threading.Thread(target=download_worker, args=(idx,), daemon=True).start()

def update_queue_listbox(idx):
    item = download_queue[idx]
    display_text = f"{item['url']} ({item['fmt']}) [{item['status']}] {item['progress']}%"
    queue_listbox.delete(idx)
    queue_listbox.insert(idx, display_text)

def start_selected():
    selected_indices = queue_listbox.curselection()
    for idx in selected_indices:
        if download_queue[idx]["status"] == "Pending":
            download_queue[idx]["status"] = "Downloading"
            update_queue_listbox(idx)
            threading.Thread(target=download_worker, args=(idx,), daemon=True).start()

def pause_selected():
    selected_indices = queue_listbox.curselection()
    for idx in selected_indices:
        if download_queue[idx]["status"] == "Downloading":
            paused_flags[idx] = True
            download_queue[idx]["status"] = "Paused"
            update_queue_listbox(idx)

def resume_selected():
    selected_indices = queue_listbox.curselection()
    for idx in selected_indices:
        if download_queue[idx]["status"] == "Paused":
            paused_flags[idx] = False
            download_queue[idx]["status"] = "Downloading"
            update_queue_listbox(idx)
            threading.Thread(target=download_worker, args=(idx,), daemon=True).start()

def download_worker(idx):
    item = download_queue[idx]
    url, fmt, save_path = item["url"], item["fmt"], item["save_path"]

    def progress_hook(d):
        if d['status'] == 'downloading':
            try:
                item['progress'] = clean_percent(d['_percent_str'])
            except:
                item['progress'] = 0
            update_queue_listbox(idx)
        elif d['status'] == 'finished':
            item['progress'] = 100
            update_queue_listbox(idx)

    try:
        if "youtube.com" in url or "youtu.be" in url:
            ydl_opts = {"progress_hooks":[progress_hook], "outtmpl": os.path.join(save_path, "%(title)s.%(ext)s")}
            if "playlist" in url.lower():
                downloader = PlaylistDownloader(url, fmt, save_path, progress_hook=progress_hook)
            else:
                downloader = YouTubeDownloader(url, fmt, save_path, progress_hook=progress_hook)

        else:
            downloader = Downloader(url, save_path, progress_hook)

        # Start download
        downloader.download()

        item["status"] = "Completed"
        update_queue_listbox(idx)
        log_text.insert(tk.END, f"Download completed: {url}\n")
        log_text.see(tk.END)

    except Exception as e:
        item["status"] = "Error"
        update_queue_listbox(idx)
        log_text.insert(tk.END, f"Error: {e}\n")
        log_text.see(tk.END)

# ------------------ GUI Setup ------------------
root = tk.Tk()
root.title("SwiftHarryDM - Queue & Instant Download")
root.geometry("850x650")

# URL Input
tk.Label(root, text="Enter URL:").pack(pady=5)
url_entry = tk.Entry(root, width=80)
url_entry.pack(pady=5)

# Format selection
tk.Label(root, text="Select Format:").pack(pady=5)
format_var = tk.StringVar(value="best")
format_menu = ttk.Combobox(root, textvariable=format_var,
                           values=["best", "1080", "720", "mp3"], state="readonly")
format_menu.pack(pady=5)

# Buttons
btn_frame = tk.Frame(root)
btn_frame.pack(pady=10)
tk.Button(btn_frame, text="Add to Queue", command=add_to_queue, bg="blue", fg="white", width=15).grid(row=0, column=0, padx=5)
tk.Button(btn_frame, text="Instant Download", command=instant_download, bg="darkgreen", fg="white", width=15).grid(row=0, column=1, padx=5)
tk.Button(btn_frame, text="Start Selected", command=start_selected, bg="green", fg="white", width=15).grid(row=0, column=2, padx=5)
tk.Button(btn_frame, text="Pause Selected", command=pause_selected, bg="orange", fg="white", width=15).grid(row=0, column=3, padx=5)
tk.Button(btn_frame, text="Resume Selected", command=resume_selected, bg="purple", fg="white", width=15).grid(row=0, column=4, padx=5)

# Queue Listbox
tk.Label(root, text="Download Queue:").pack(pady=5)
queue_listbox = tk.Listbox(root, width=120, height=10)
queue_listbox.pack(pady=5)

# Log / Status box
tk.Label(root, text="Log:").pack(pady=5)
log_text = tk.Text(root, height=20, wrap="word")
log_text.pack(pady=5, fill=tk.BOTH, expand=True)

root.mainloop()