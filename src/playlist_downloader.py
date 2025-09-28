import threading
import os
from yt_dlp import YoutubeDL
from utils import format_mapping, convert_to_mp3

class PlaylistDownloader:
    def __init__(self, playlist_url, fmt="best", save_path=None):
        self.playlist_url = playlist_url
        self.fmt = fmt.lower()
        self.save_path = save_path or os.path.join(os.path.expanduser("~"), "Desktop")
        os.makedirs(self.save_path, exist_ok=True)

        self.ydl_opts = {
            "format": format_mapping(self.fmt),
            "outtmpl": os.path.join(self.save_path, "%(playlist_index)s - %(title)s.%(ext)s"),
            "noplaylist": False,
            "merge_output_format": "mp4"
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
