import threading
import os
from yt_dlp import YoutubeDL
from utils import format_mapping, convert_to_mp3

download_folder = os.path.join(os.path.expanduser("~"), "Desktop")
os.makedirs(download_folder, exist_ok=True)

class PlaylistDownloader:
    def __init__(self, playlist_url, fmt="best"):
        self.playlist_url = playlist_url
        self.fmt = fmt.lower()
        self.ydl_opts = {
            "format": format_mapping(self.fmt),
            "outtmpl": os.path.join(download_folder, "%(playlist_index)s - %(title)s.%(ext)s"),
            "noplaylist": False
        }

    def download(self):
        print(f"Downloading playlist: {self.playlist_url}")
        with YoutubeDL(self.ydl_opts) as ydl:
            info_dict = ydl.extract_info(self.playlist_url, download=True)
            entries = info_dict.get("entries", [])
            for entry in entries:
                filename = ydl.prepare_filename(entry)
                if self.fmt == "mp3":
                    mp3_file = os.path.splitext(filename)[0] + ".mp3"
                    convert_to_mp3(filename, mp3_file)
                    print(f"MP3 saved as: {mp3_file}")
                else:
                    print(f"Video saved as: {filename}")

    def start(self):
        t = threading.Thread(target=self.download)
        t.start()