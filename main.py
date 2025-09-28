import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
from urllib.parse import urlparse, parse_qs
from src.downloader import Downloader
from src.youtube_downloader import YouTubeDownloader
from src.playlist_downloader import PlaylistDownloader
import os

# ------------------ Helper Functions ------------------
def is_playlist(url):
    """Detect if the URL is a playlist"""
    parsed = urlparse(url)
    query = parse_qs(parsed.query)
    if "list" in query:
        return True
    if "/playlist" in parsed.path:
        return True
    return False

# ------------------ Functions ------------------
def start_download():
    url = url_entry.get().strip()
    fmt = format_var.get()

    if not url:
        messagebox.showerror("Error", "Please enter a URL!")
        return

    # Ask user for save location
    save_path = filedialog.askdirectory(title="Select Save Location")
    if not save_path:
        save_path = os.path.join(os.path.expanduser("~"), "Desktop")  # default Desktop

    log_text.insert(tk.END, f"Starting download: {url} ({fmt})...\n")
    log_text.see(tk.END)

    def run():
        try:
            if "youtube.com" in url or "youtu.be" in url:
                if is_playlist(url):
                    downloader = PlaylistDownloader(url, fmt, save_path)
                    downloader.download()
                else:
                    downloader = YouTubeDownloader(url, fmt, save_path)
                    downloader.download()
            else:
                downloader = Downloader(url, save_path)
                downloader.start()

            log_text.insert(tk.END, f"Download completed: {url}\n")
            log_text.see(tk.END)

        except Exception as e:
            log_text.insert(tk.END, f"Error: {e}\n")
            log_text.see(tk.END)

    threading.Thread(target=run, daemon=True).start()

# ------------------ GUI Setup ------------------
root = tk.Tk()
root.title("SwiftHarryDM")
root.geometry("700x500")

# URL Input
tk.Label(root, text="Enter URL:").pack(pady=5)
url_entry = tk.Entry(root, width=80)
url_entry.pack(pady=5)

# Format selection
tk.Label(root, text="Select Format:").pack(pady=5)
format_var = tk.StringVar(value="best")
format_menu = ttk.Combobox(
    root, textvariable=format_var,
    values=["best", "1080", "720", "mp3"], state="readonly"
)
format_menu.pack(pady=5)

# Download button
download_btn = tk.Button(
    root, text="Download", command=start_download,
    bg="green", fg="white", width=25
)
download_btn.pack(pady=10)

# Log / Status box
log_text = tk.Text(root, height=20, wrap="word")
log_text.pack(pady=10, fill=tk.BOTH, expand=True)

root.mainloop()
