from yt_dlp import YoutubeDL
from threading import Thread
import subprocess
import os

class YouTubeDownloader:
    def __init__(self, url, output_path='./'):
        self.url = url
        self.output_path = output_path

    def download(self, format_code='best'):
        temp_path = os.path.join(self.output_path, '%(title)s.%(ext)s')
        ydl_opts = {
            'outtmpl': temp_path,
            'format': 'bestaudio/best' if format_code == 'mp3' else format_code
        }

        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(self.url, download=True)
            filename = ydl.prepare_filename(info)

        if format_code == 'mp3':
            mp3_file = os.path.splitext(filename)[0] + '.mp3'
            subprocess.run(['ffmpeg', '-y', '-i', filename, mp3_file])
            os.remove(filename)

    def start(self, format_code='best'):
        thread = Thread(target=self.download, args=(format_code,))
        thread.start()
        return thread
