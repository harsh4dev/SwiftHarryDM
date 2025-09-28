import requests
from threading import Thread

class Downloader:
    def __init__(self, url, filename):
        self.url = url
        self.filename = filename
        self._paused = False

    def download(self):
        with requests.get(self.url, stream=True) as r:
            r.raise_for_status()
            with open(self.filename, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    if self._paused:
                        break
                    f.write(chunk)

    def pause(self):
        self._paused = True

    def start(self):
        thread = Thread(target=self.download)
        thread.start()
        return thread
