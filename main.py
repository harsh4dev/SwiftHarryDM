import os
from src.downloader import Downloader
from src.youtube_downloader import YouTubeDownloader

def main():
    normal_downloads = []
    youtube_downloads = []

    while True:
        print("\nSwiftHarryDM CLI – Phase 2")
        print("1. Add normal file download")
        print("2. Add YouTube download")
        print("3. Pause a download")
        print("4. Exit")

        choice = input("Enter choice: ").strip()

        if choice == '1':
            url = input("Enter file URL: ").strip()
            filename = input("Enter filename (with extension): ").strip()
            d = Downloader(url, filename)
            t = d.start()
            normal_downloads.append((d, t))
            print(f"Normal download started for {filename}")

        elif choice == '2':
            url = input("Enter YouTube URL: ").strip()
            format_code = input("Enter format (best, 720, mp3): ").strip()
            ytd = YouTubeDownloader(url, format_code)
            t = ytd.start()
            youtube_downloads.append((ytd, t))
            print(f"YouTube download started for {url}")

        elif choice == '3':
            print("1. Pause normal downloads")
            print("2. Pause YouTube downloads")
            pause_choice = input("Enter choice: ").strip()
            if pause_choice == '1':
                for d, _ in normal_downloads:
                    d.pause()
                print("All normal downloads paused.")
            elif pause_choice == '2':
                print("YouTube downloads cannot be paused in Phase 2 CLI (yt-dlp limitation).")

        elif choice == '4':
            print("Exiting...")
            break

        else:
            print("Invalid choice. Try again.")

    # Wait for ongoing downloads to finish
    for d, t in normal_downloads:
        t.join()
    for ytd, t in youtube_downloads:
        t.join()

if __name__ == "__main__":
    main()
