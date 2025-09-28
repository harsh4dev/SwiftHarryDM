import os
import requests
from threading import Thread

class Downloader:
    def __init__(self, url, filename, num_threads=4):
        self.url = url
        self.filename = filename
        self.num_threads = num_threads
        self._paused = False
        self.filesize = 0
        self.downloaded = 0
        self.threads = []

    def _get_file_size(self):
        r = requests.head(self.url)
        self.filesize = int(r.headers.get('Content-Length', 0))

    def _download_segment(self, start, end, idx):
        headers = {'Range': f'bytes={start}-{end}'}
        r = requests.get(self.url, headers=headers, stream=True)
        with open(f'{self.filename}.part{idx}', 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192):
                if self._paused:
                    break
                f.write(chunk)
                self.downloaded += len(chunk)

    def download(self):
        self._get_file_size()
        part_size = self.filesize // self.num_threads

        for i in range(self.num_threads):
            start = i * part_size
            end = (start + part_size - 1) if i != self.num_threads - 1 else self.filesize - 1
            t = Thread(target=self._download_segment, args=(start, end, i))
            self.threads.append(t)
            t.start()

        for t in self.threads:
            t.join()

        # Merge parts
        with open(self.filename, 'wb') as f_out:
            for i in range(self.num_threads):
                part_file = f'{self.filename}.part{i}'
                with open(part_file, 'rb') as f_in:
                    f_out.write(f_in.read())
                os.remove(part_file)

    def pause(self):
        self._paused = True

    def start(self):
        thread = Thread(target=self.download)
        thread.start()
        return thread
