import threading
import requests
import os

class Downloader:
    def __init__(self, url, dest_folder=None):
        self.url = url
        self.dest_folder = dest_folder or os.getcwd()
        self.filename = os.path.join(self.dest_folder, self.url.split("/")[-1])

    def download(self):
        print(f"Downloading {self.url} ...")
        response = requests.get(self.url, stream=True)
        total = int(response.headers.get("content-length", 0))
        with open(self.filename, "wb") as f:
            for data in response.iter_content(chunk_size=1024*1024):
                f.write(data)
        print(f"Download finished: {self.filename}")

    def start(self):
        t = threading.Thread(target=self.download)
        t.start()
