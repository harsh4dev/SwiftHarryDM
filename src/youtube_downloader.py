import threading
import os
from yt_dlp import YoutubeDL
from utils import format_mapping, convert_to_mp3

download_folder = os.path.join(os.path.expanduser("~"), "Downloads")
os.makedirs(download_folder, exist_ok=True)

class YouTubeDownloader:
    def __init__(self, url, fmt="best"):
        self.url = url
        self.fmt = fmt.lower()
        self.ydl_opts = {
            "format": format_mapping(self.fmt),
            "outtmpl": os.path.join(download_folder, "%(title)s.%(ext)s"),
            "noplaylist": True
        }

    def download(self):
        print(f"YouTube download started for {self.url}")
        with YoutubeDL(self.ydl_opts) as ydl:
            info_dict = ydl.extract_info(self.url, download=True)
            filename = ydl.prepare_filename(info_dict)

            if self.fmt == "mp3":
                mp3_file = os.path.splitext(filename)[0] + ".mp3"
                convert_to_mp3(filename, mp3_file)
                print(f"MP3 saved as: {mp3_file}")
            else:
                print(f"Video saved as: {filename}")

    def start(self):
        t = threading.Thread(target=self.download)
        t.start()
