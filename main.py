from src.downloader import Downloader
from src.youtube_downloader import YouTubeDownloader

downloads = []

def main():
    while True:
        print("\nSwiftHarryDM CLI")
        print("1. Add normal file download")
        print("2. Add YouTube download")
        print("3. Pause download")
        print("4. Exit")
        choice = input("Enter choice: ")

        if choice == '1':
            url = input("Enter file URL: ")
            filename = input("Enter filename to save as: ")
            d = Downloader(url, filename)
            t = d.start()
            downloads.append((d, t))

        elif choice == '2':
            url = input("Enter YouTube URL: ")
            format_code = input("Enter format code (best, mp3, 720): ")
            yd = YouTubeDownloader(url)
            t = yd.start(format_code)
            downloads.append((yd, t))

        elif choice == '3':
            for i, (d, t) in enumerate(downloads):
                if hasattr(d, 'pause'):
                    d.pause()
                    print(f"Paused download {i+1}")

        elif choice == '4':
            for d, t in downloads:
                if hasattr(d, 'pause'):
                    d.pause()
            print("Exiting...")
            break

if __name__ == "__main__":
    main()
