import os
import subprocess

def format_mapping(fmt):
    """Map CLI format input to yt-dlp format string"""
    mapping = {
        "best": "bestvideo[ext=mp4]+bestaudio[ext=m4a]/mp4",
        "1080": "bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/mp4",
        "720": "bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/mp4",
        "mp3": "bestaudio/best"
    }
    return mapping.get(fmt, "bestvideo+bestaudio/best")


def convert_to_mp3(input_file, output_file):
    """Convert audio/video to MP3 using ffmpeg"""
    cmd = ["ffmpeg", "-y", "-i", input_file, "-vn", "-acodec", "libmp3lame", "-q:a", "2", output_file]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    os.remove(input_file)
