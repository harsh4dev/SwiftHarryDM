import os
import subprocess
import sys
import tempfile
import shutil
import atexit

def format_mapping(fmt):
    """Map CLI format input to yt-dlp format selector with SABR workarounds"""
    mapping = {
        "best": "best",  # Let yt-dlp choose the best quality
        "1080": "best[height<=1080]",  # Best up to 1080p
        "720": "best[height<=720]",    # Best up to 720p  
        "480": "best[height<=480]",    # Best up to 480p
        "mp3": "bestaudio/best",       # Audio only - will be converted to MP3
        "mp4": "best[ext=mp4]",        # Prefer MP4 container
        "bestaudio": "bestaudio/best", # Best audio for MP3 fallback
        "safe": "best[height<=720][vcodec!=none][protocol!=m3u8]"  # Safe format for problematic videos
    }
    return mapping.get(fmt, "best")

# ==================== FFMPEG STANDALONE SUPPORT ====================
_ffmpeg_temp_dir = None

def cleanup_ffmpeg_temp():
    """Clean up temporary ffmpeg files on exit"""
    global _ffmpeg_temp_dir
    if _ffmpeg_temp_dir and os.path.exists(_ffmpeg_temp_dir):
        try:
            shutil.rmtree(_ffmpeg_temp_dir)
        except:
            pass

def setup_ffmpeg():
    """Extract ffmpeg from bundled exe to temp directory and return path"""
    global _ffmpeg_temp_dir
    
    if getattr(sys, 'frozen', False):
        # Running as bundled executable
        base_path = sys._MEIPASS
    else:
        # Running as script
        base_path = os.path.dirname(os.path.abspath(__file__))
    
    # Create temp directory for ffmpeg
    _ffmpeg_temp_dir = os.path.join(tempfile.gettempdir(), 'swiftharrydm_ffmpeg')
    os.makedirs(_ffmpeg_temp_dir, exist_ok=True)
    
    # Source paths in bundled app
    ffmpeg_src = os.path.join(base_path, 'ffmpeg.exe')
    ffprobe_src = os.path.join(base_path, 'ffprobe.exe')
    
    # Destination paths in temp
    ffmpeg_dest = os.path.join(_ffmpeg_temp_dir, 'ffmpeg.exe')
    ffprobe_dest = os.path.join(_ffmpeg_temp_dir, 'ffprobe.exe')
    
    # Copy ffmpeg files if they exist in bundle
    for src, dest in [(ffmpeg_src, ffmpeg_dest), (ffprobe_src, ffprobe_dest)]:
        if os.path.exists(src) and not os.path.exists(dest):
            try:
                shutil.copy2(src, dest)
                print(f"✅ Extracted {os.path.basename(src)} to temp directory")
            except Exception as e:
                print(f"❌ Failed to extract {src}: {e}")
    
    # Register cleanup function
    atexit.register(cleanup_ffmpeg_temp)
    
    return _ffmpeg_temp_dir

def get_ffmpeg_path():
    """Get ffmpeg path that works everywhere"""
    temp_dir = setup_ffmpeg()
    ffmpeg_path = os.path.join(temp_dir, 'ffmpeg.exe')
    
    if os.path.exists(ffmpeg_path):
        # Test if ffmpeg works
        try:
            result = subprocess.run([ffmpeg_path, "-version"], capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                print(f"✅ FFmpeg verified: {ffmpeg_path}")
                return ffmpeg_path
        except:
            print(f"❌ FFmpeg test failed: {ffmpeg_path}")
    
    # Fallback to system PATH
    return 'ffmpeg'

def manual_merge_video_audio(video_file, audio_file, output_file):
    """Manually merge video and audio streams using ffmpeg"""
    try:
        ffmpeg_path = get_ffmpeg_path()
        
        # If output file exists from failed merge, remove it
        if os.path.exists(output_file):
            os.remove(output_file)
            
        cmd = [
            ffmpeg_path, "-y",
            "-i", video_file,
            "-i", audio_file,
            "-c", "copy",  # Copy streams without re-encoding
            "-shortest",
            output_file
        ]
        
        print(f"🔧 [MANUAL MERGE] Merging: {video_file} + {audio_file} -> {output_file}")
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        
        # Clean up separate files after successful merge
        if os.path.exists(output_file):
            if os.path.exists(video_file):
                os.remove(video_file)
            if os.path.exists(audio_file):
                os.remove(audio_file)
            print(f"✅ [MANUAL MERGE] Merge completed and cleaned up separate files")
            return True
        return False
            
    except subprocess.CalledProcessError as e:
        print(f"❌ [MANUAL MERGE] FFmpeg merge failed: {e}")
        print(f"🔧 [MANUAL MERGE] stderr: {e.stderr}")
    except Exception as e:
        print(f"❌ [MANUAL MERGE] Merge error: {e}")
    
    return False

def convert_to_mp3(input_file, output_file):
    """Convert audio/video to MP3 using ffmpeg"""
    ffmpeg_path = get_ffmpeg_path()
    cmd = [ffmpeg_path, "-y", "-i", input_file, "-vn", "-acodec", "libmp3lame", "-q:a", "2", output_file]
    
    try:
        result = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        if os.path.exists(input_file):
            os.remove(input_file)
        print(f"✅ Successfully converted to MP3: {output_file}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ FFmpeg conversion failed: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error during conversion: {e}")
        return False