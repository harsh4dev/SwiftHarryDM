from src.downloader import Downloader
from src.youtube_downloader import YouTubeDownloader
from src.playlist_downloader import PlaylistDownloader

def main():
    while True:
        print("\nSwiftHarryDM CLI")
        print("1. Add normal file download")
        print("2. Add YouTube download")
        print("3. Add YouTube playlist download")
        print("4. Pause download")
        print("5. Exit")
        choice = input("Enter choice: ")

        if choice == "1":
            url = input("Enter file URL: ")
            d = Downloader(url)
            d.start()
        elif choice == "2":
            url = input("Enter YouTube URL: ")
            fmt = input("Enter format code (best, 1080, 720, mp3): ")
            ydl = YouTubeDownloader(url, fmt)
            ydl.start()
        elif choice == "3":
            playlist_url = input("Enter Playlist URL: ")
            fmt = input("Enter format code (best, 1080, 720, mp3): ")
            pdl = PlaylistDownloader(playlist_url, fmt)
            pdl.start()
        elif choice == "4":
            print("Pause feature coming soon...")
        elif choice == "5":
            print("Exiting...")
            break
        else:
            print("Invalid choice!")

if __name__ == "__main__":
    main()
