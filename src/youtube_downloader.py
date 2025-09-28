import os
from threading import Thread
import yt_dlp

class YouTubeDownloader:
    def __init__(self, url, format_code='best', output_dir='downloads'):
        self.url = url
        self.format_code = format_code
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)
        self.ydl_opts = self._get_opts()
        self.thread = None

    def _get_opts(self):
        out_template = os.path.join(self.output_dir, '%(title)s.%(ext)s')
        opts = {
            'format': self.format_code,
            'outtmpl': out_template,
            'noplaylist': True,
            'progress_hooks': [self._progress_hook],
            'postprocessors': []
        }

        # MP3 conversion if format_code is 'mp3'
        if self.format_code.lower() == 'mp3':
            opts['format'] = 'bestaudio/best'
            opts['postprocessors'].append({
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            })
        return opts

    def _progress_hook(self, d):
        if d['status'] == 'downloading':
            total = d.get('total_bytes') or d.get('total_bytes_estimate')
            downloaded = d.get('downloaded_bytes', 0)
            if total:
                percent = downloaded / total * 100
                print(f"[{self.url}] Downloading: {percent:.2f}% ({downloaded/1024/1024:.2f}MB / {total/1024/1024:.2f}MB)", end='\r')
        elif d['status'] == 'finished':
            print(f"\n[{self.url}] Download finished, now converting...")

    def download(self):
        with yt_dlp.YoutubeDL(self.ydl_opts) as ydl:
            ydl.download([self.url])

    def start(self):
        self.thread = Thread(target=self.download)
        self.thread.start()
        return self.thread

    def join(self):
        if self.thread:
            self.thread.join()
