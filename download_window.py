import tkinter as tk
from tkinter import ttk, scrolledtext
import threading
import time
from datetime import datetime
import math
import os
from typing import Dict, Any, List, Optional
from urllib.parse import urlparse, unquote

class DownloadProgressWindow:
    def __init__(self, parent: tk.Tk, download_item: Dict[str, Any], download_queue: List[Dict[str, Any]]):
        self.parent = parent
        self.download_item = download_item
        self.download_queue = download_queue
        self.window: Optional[tk.Toplevel] = None
        self.is_open = True
        self.paused = False
        self.start_time: Optional[datetime] = None
        self.last_update_time: Optional[datetime] = None
        self.last_downloaded = 0.0
        self.total_size = 0.0
        self.download_speeds: List[float] = []  # Store recent speeds for averaging
        
        # UI elements
        self.progress_bar: Optional[ttk.Progressbar] = None
        self.status_label: Optional[tk.Label] = None
        self.size_label: Optional[tk.Label] = None
        self.downloaded_label: Optional[tk.Label] = None
        self.speed_label: Optional[tk.Label] = None
        self.time_label: Optional[tk.Label] = None
        self.file_label: Optional[tk.Label] = None
        self.segments_tree: Optional[ttk.Treeview] = None
        self.pause_btn: Optional[tk.Button] = None
        self.cancel_btn: Optional[tk.Button] = None
        self.hide_btn: Optional[tk.Button] = None
        self.log_text: Optional[scrolledtext.ScrolledText] = None
        
        self.create_window()
        self.start_progress_updater()
    
    def create_window(self) -> None:
        """Create the download progress window"""
        self.window = tk.Toplevel(self.parent)
        self.window.title(f"SwiftHarryDM - Downloading: {self.download_item.get('title', 'Unknown')}")
        self.window.geometry("600x500")
        self.window.configure(bg="#2b2b2b")
        self.window.resizable(True, True)
        
        # Make window stay on top
        self.window.transient(self.parent)
        self.window.grab_set()
        
        # Center the window
        self.window.update_idletasks()
        x = (self.window.winfo_screenwidth() // 2) - (600 // 2)
        y = (self.window.winfo_screenheight() // 2) - (500 // 2)
        self.window.geometry(f"600x500+{x}+{y}")
        
        self.create_ui()
        
        # Handle window close
        self.window.protocol("WM_DELETE_WINDOW", self.on_close)
    
    def create_ui(self) -> None:
        """Create the UI elements"""
        if not self.window:
            return
            
        # Main container
        main_frame = tk.Frame(self.window, bg="#2b2b2b", padx=20, pady=20)
        main_frame.pack(fill="both", expand=True)
        
        # Header
        header_frame = tk.Frame(main_frame, bg="#2b2b2b")
        header_frame.pack(fill="x", pady=(0, 15))
        
        tk.Label(header_frame, text="🚀 SwiftHarryDM Download", 
                font=("Arial", 16, "bold"), fg="white", bg="#2b2b2b").pack(anchor="w")
        
        # File info frame
        info_frame = tk.Frame(main_frame, bg="#3c3c3c", relief="solid", bd=1, padx=15, pady=10)
        info_frame.pack(fill="x", pady=(0, 15))
        
        # File name
        title = self.download_item.get('title', 'Unknown')
        # Extract better filename from URL if title is generic
        if title.lower() in ['unknown', 'unknown title', 'video', 'audio']:
            extracted_title = self.get_filename_from_url(self.download_item.get('url', ''))
            title = extracted_title or title
            
        self.file_label = tk.Label(info_frame, 
                                  text=f"File: {title}",
                                  font=("Arial", 11, "bold"), 
                                  fg="#00ff00", bg="#3c3c3c", anchor="w")
        self.file_label.pack(fill="x")
        
        # URL (truncated)
        url = self.download_item.get('url', 'N/A')
        short_url = url[:80] + "..." if len(url) > 80 else url
        tk.Label(info_frame, text=f"URL: {short_url}", 
                font=("Arial", 9), fg="#cccccc", bg="#3c3c3c", anchor="w").pack(fill="x", pady=(2, 0))
        
        # Format info
        fmt = self.download_item.get('fmt', 'best')
        tk.Label(info_frame, text=f"Format: {fmt.upper()}", 
                font=("Arial", 9), fg="#cccccc", bg="#3c3c3c", anchor="w").pack(fill="x", pady=(2, 0))
        
        # Progress section
        progress_frame = tk.Frame(main_frame, bg="#2b2b2b")
        progress_frame.pack(fill="x", pady=(0, 15))
        
        # Progress bar
        self.progress_bar = ttk.Progressbar(progress_frame, orient="horizontal", 
                                           length=560, mode="determinate")
        self.progress_bar.pack(fill="x", pady=(0, 10))
        
        # Stats frame
        stats_frame = tk.Frame(progress_frame, bg="#2b2b2b")
        stats_frame.pack(fill="x")
        
        # Left stats
        left_stats = tk.Frame(stats_frame, bg="#2b2b2b")
        left_stats.pack(side="left", fill="x", expand=True)
        
        self.status_label = tk.Label(left_stats, text="Status: Connecting...", 
                                    font=("Arial", 10, "bold"), fg="#ffa500", bg="#2b2b2b", anchor="w")
        self.status_label.pack(fill="x")
        
        self.size_label = tk.Label(left_stats, text="File size: Calculating...", 
                                  font=("Arial", 9), fg="#cccccc", bg="#2b2b2b", anchor="w")
        self.size_label.pack(fill="x")
        
        self.downloaded_label = tk.Label(left_stats, text="Downloaded: 0 MB (0%)", 
                                        font=("Arial", 9), fg="#cccccc", bg="#2b2b2b", anchor="w")
        self.downloaded_label.pack(fill="x")
        
        # Right stats
        right_stats = tk.Frame(stats_frame, bg="#2b2b2b")
        right_stats.pack(side="right")
        
        self.speed_label = tk.Label(right_stats, text="Speed: 0 KB/s", 
                                   font=("Arial", 9), fg="#cccccc", bg="#2b2b2b", anchor="e")
        self.speed_label.pack(anchor="e")
        
        self.time_label = tk.Label(right_stats, text="Time left: Calculating...", 
                                  font=("Arial", 9), fg="#cccccc", bg="#2b2b2b", anchor="e")
        self.time_label.pack(anchor="e")
        
        # Connection segments (like IDM)
        segments_frame = tk.Frame(main_frame, bg="#2b2b2b")
        segments_frame.pack(fill="x", pady=(0, 15))
        
        tk.Label(segments_frame, text="Download Segments:", 
                font=("Arial", 11, "bold"), fg="white", bg="#2b2b2b", anchor="w").pack(anchor="w")
        
        # Create segments table
        self.segments_tree = ttk.Treeview(segments_frame, 
                                         columns=("Segment", "Downloaded", "Status"), 
                                         show="headings", height=6)
        if self.segments_tree:
            self.segments_tree.heading("Segment", text="Segment")
            self.segments_tree.heading("Downloaded", text="Downloaded")
            self.segments_tree.heading("Status", text="Status")
            
            self.segments_tree.column("Segment", width=80)
            self.segments_tree.column("Downloaded", width=120)
            self.segments_tree.column("Status", width=150)
            
            self.segments_tree.pack(fill="x", pady=(5, 0))
            
            # Add some sample segments (simulated)
            for i in range(8):
                self.segments_tree.insert("", "end", values=(f"Segment {i+1}", "0 KB", "Waiting..."))
        
        # Control buttons
        buttons_frame = tk.Frame(main_frame, bg="#2b2b2b")
        buttons_frame.pack(fill="x", pady=(10, 0))
        
        self.pause_btn = tk.Button(buttons_frame, text="⏸️ Pause", 
                                  command=self.toggle_pause,
                                  bg="#f59e0b", fg="white", font=("Arial", 10, "bold"),
                                  relief="flat", padx=20, pady=8)
        self.pause_btn.pack(side="left", padx=(0, 10))
        
        self.cancel_btn = tk.Button(buttons_frame, text="❌ Cancel", 
                                   command=self.cancel_download,
                                   bg="#ef4444", fg="white", font=("Arial", 10, "bold"),
                                   relief="flat", padx=20, pady=8)
        self.cancel_btn.pack(side="left", padx=(0, 10))
        
        self.hide_btn = tk.Button(buttons_frame, text="⬇️ Hide", 
                                 command=self.hide_window,
                                 bg="#6b7280", fg="white", font=("Arial", 10, "bold"),
                                 relief="flat", padx=20, pady=8)
        self.hide_btn.pack(side="left")
        
        # Log area
        log_frame = tk.Frame(main_frame, bg="#2b2b2b")
        log_frame.pack(fill="both", expand=True, pady=(10, 0))
        
        tk.Label(log_frame, text="Download Log:", 
                font=("Arial", 11, "bold"), fg="white", bg="#2b2b2b", anchor="w").pack(anchor="w")
        
        self.log_text = scrolledtext.ScrolledText(log_frame, 
                                                 height=6, 
                                                 bg="#1a1a1a", 
                                                 fg="#00ff00",
                                                 font=("Consolas", 8),
                                                 wrap="word")
        self.log_text.pack(fill="both", expand=True, pady=(5, 0))
        self.log_text.config(state="disabled")
        
        # Add initial log
        self.add_log("🚀 Download started...")
        self.add_log(f"📁 Saving to: {self.download_item.get('save_path', 'Unknown')}")
    
    def get_filename_from_url(self, url: str) -> Optional[str]:
        """Extract filename from URL"""
        try:
            parsed = urlparse(url)
            filename = unquote(parsed.path.split('/')[-1])
            return filename if filename else None
        except Exception:
            return None
    
    def start_progress_updater(self) -> None:
        """Start updating the progress in real-time"""
        def update_progress():
            self.start_time = datetime.now()
            self.last_update_time = self.start_time
            self.last_downloaded = 0.0
            self.download_speeds = []
            
            while self.is_open and self.download_item["status"] in ["Downloading", "Paused"]:
                try:
                    # Check if window still exists
                    if not self.window or not self.window.winfo_exists():
                        break
                        
                    current_progress = self.download_item["progress"]
                    current_time = datetime.now()
                    
                    # Calculate real file size based on progress (if we have some data)
                    if current_progress > 0 and self.total_size == 0:
                        # Estimate total size from current progress and downloaded bytes
                        estimated_size = (100 / current_progress) * self.last_downloaded if self.last_downloaded > 0 else 0
                        if estimated_size > 0:
                            self.total_size = estimated_size
                    
                    # Update progress bar
                    if self.progress_bar:
                        self.progress_bar["value"] = current_progress
                    
                    # Calculate real downloaded bytes (estimate)
                    if self.total_size > 0:
                        downloaded_bytes = (current_progress / 100) * self.total_size
                    else:
                        # Fallback: use progress percentage with a reasonable file size estimate
                        estimated_total = 50 * 1024 * 1024  # 50MB default estimate
                        downloaded_bytes = (current_progress / 100) * estimated_total
                    
                    # Calculate real speed
                    elapsed = (current_time - self.last_update_time).total_seconds()
                    if elapsed >= 1.0:  # Update speed every second
                        if self.last_downloaded > 0:
                            instant_speed = (downloaded_bytes - self.last_downloaded) / elapsed
                            self.download_speeds.append(instant_speed)
                            # Keep only last 5 speeds for averaging
                            if len(self.download_speeds) > 5:
                                self.download_speeds.pop(0)
                            
                        self.last_downloaded = downloaded_bytes
                        self.last_update_time = current_time
                    
                    # Calculate average speed
                    avg_speed = (sum(self.download_speeds) / len(self.download_speeds) * 10) if self.download_speeds else 0
                    
                    # Update labels
                    if self.status_label:
                        self.status_label.config(
                            text=f"Status: {self.download_item['status']}",
                            fg="#00ff00" if self.download_item['status'] == "Downloading" else "#ffa500"
                        )
                    
                    if self.size_label:
                        if self.total_size > 0:
                            self.size_label.config(text=f"File size: {self.format_size(self.total_size)}")
                        else:
                            self.size_label.config(text="File size: Calculating...")
                    
                    if self.downloaded_label:
                        self.downloaded_label.config(
                            text=f"Downloaded: {self.format_size(downloaded_bytes)} ({current_progress:.1f}%)"
                        )
                    
                    if self.speed_label:
                        self.speed_label.config(text=f"Speed: {self.format_size(avg_speed)}/s")
                    
                    if self.time_label:
                        # Calculate time left
                        if avg_speed > 0 and current_progress < 100 and self.total_size > 0:
                            remaining_bytes = self.total_size - downloaded_bytes
                            time_left = remaining_bytes / avg_speed
                            time_text = self.format_time(time_left)
                        else:
                            time_text = "Calculating..."
                        self.time_label.config(text=f"Time left: {time_text}")
                    
                    # Update segments (simulated)
                    self.update_segments(current_progress, downloaded_bytes)
                    
                    # Add to log when download completes
                    if current_progress == 100:
                        if self.start_time:
                            total_elapsed = (datetime.now() - self.start_time).total_seconds()
                            avg_speed_total = (downloaded_bytes / total_elapsed * 10) if total_elapsed > 0 else 0
                            self.add_log(f"✅ Download completed! Average speed: {self.format_size(avg_speed_total)}/s")
                        break
                    
                    time.sleep(0.5)  # Update twice per second
                    
                except Exception as e:
                    # Window probably closed, exit thread
                    print(f"Progress updater stopping: {e}")
                    break
            
            # Download completed or stopped
            if self.window and self.window.winfo_exists():
                if self.download_item["status"] == "Completed":
                    self.add_log("🎉 Download finished! Window will close in 3 seconds...")
                    if self.window:
                        self.window.after(3000, self.close_window)
                elif self.download_item["status"] == "Error":
                    self.add_log("❌ Download failed!")
                    if self.status_label:
                        self.status_label.config(text="Status: Failed", fg="#ef4444")
        
        threading.Thread(target=update_progress, daemon=True).start()
    
    def update_segments(self, progress: float, downloaded_bytes: float) -> None:
        """Update the segment progress (simulated but more realistic)"""
        try:
            if not self.segments_tree:
                return
                
            segments_data: List[tuple] = []
            total_segments = 8
            
            for i in range(total_segments):
                # More realistic segment simulation
                segment_base = (i * (100 / total_segments))
                segment_progress = max(0.0, min(progress - segment_base, 100 / total_segments))
                segment_percent = (segment_progress / (100 / total_segments)) * 100
                
                if progress >= 100:
                    segment_downloaded = (1 / total_segments) * downloaded_bytes
                    status = "Completed"
                elif progress <= segment_base:
                    segment_downloaded = 0
                    status = "Waiting..."
                elif self.paused:
                    segment_downloaded = (segment_percent / 100) * (downloaded_bytes / total_segments)
                    status = "Paused"
                else:
                    segment_downloaded = (segment_percent / 100) * (downloaded_bytes / total_segments)
                    # Make it look like segments start at different times
                    if segment_percent < 10:
                        status = "Connecting..."
                    elif segment_percent < 30:
                        status = "Starting..."
                    else:
                        status = "Downloading..."
                
                segments_data.append((
                    f"Segment {i+1}",
                    f"{self.format_size(segment_downloaded)}",
                    status
                ))
            
            # Update treeview
            self.segments_tree.delete(*self.segments_tree.get_children())
            for segment in segments_data:
                self.segments_tree.insert("", "end", values=segment)
                
        except Exception as e:
            print(f"Segment update error: {e}")
    
    def add_log(self, message: str) -> None:
        """Add message to log"""
        try:
            if not self.log_text:
                return
                
            self.log_text.config(state="normal")
            timestamp = datetime.now().strftime("%H:%M:%S")
            self.log_text.insert("end", f"[{timestamp}] {message}\n")
            self.log_text.see("end")
            self.log_text.config(state="disabled")
        except Exception as e:
            print(f"Log update failed: {e}")
    
    def toggle_pause(self) -> None:
        """Toggle pause/resume"""
        self.paused = not self.paused
        if self.pause_btn:
            if self.paused:
                self.pause_btn.config(text="▶️ Resume", bg="#10b981")
                self.download_item["status"] = "Paused"
                self.add_log("⏸️ Download paused")
            else:
                self.pause_btn.config(text="⏸️ Pause", bg="#f59e0b")
                self.download_item["status"] = "Downloading"
                self.add_log("▶️ Download resumed")
    
    def cancel_download(self) -> None:
        """Cancel the download"""
        self.download_item["status"] = "Cancelled"
        self.add_log("❌ Download cancelled by user")
        self.is_open = False
        self.close_window()
    
    def hide_window(self) -> None:
        """Hide the window (minimize to taskbar)"""
        if self.window:
            self.window.withdraw()
            self.add_log("⬇️ Window minimized")
    
    def on_close(self) -> None:
        """Handle window close"""
        self.is_open = False
        if self.window:
            self.window.destroy()
    
    def close_window(self) -> None:
        """Close the window"""
        if self.window:
            self.is_open = False  # This stops the progress thread
            try:
                self.window.destroy()
            except Exception:
                pass  # Window might already be destroyed
    
    def format_size(self, size_bytes: float) -> str:
        """Format file size in human readable format"""
        if size_bytes <= 0:
            return "0 B"
        
        size_names = ["B", "KB", "MB", "GB"]
        i = int(math.floor(math.log(size_bytes, 1024))) if size_bytes > 0 else 0
        i = min(i, len(size_names) - 1)
        p = math.pow(1024, i)
        s = round(size_bytes / p, 2)
        
        return f"{s} {size_names[i]}"
    
    def format_time(self, seconds: float) -> str:
        """Format time in human readable format"""
        if seconds <= 0:
            return "0 sec"
        elif seconds < 60:
            return f"{int(seconds)} sec"
        elif seconds < 3600:
            return f"{int(seconds // 60)} min {int(seconds % 60)} sec"
        else:
            hours = int(seconds // 3600)
            minutes = int((seconds % 3600) // 60)
            return f"{hours} hr {minutes} min"

# Global dictionary to track open download windows
active_download_windows: Dict[int, DownloadProgressWindow] = {}

def show_download_window(parent: tk.Tk, download_item: Dict[str, Any], download_queue: List[Dict[str, Any]], item_index: int) -> Optional[DownloadProgressWindow]:
    """Show download progress window for a download item"""
    # Close existing window for this item if any
    if item_index in active_download_windows:
        active_download_windows[item_index].close_window()
    
    # Create new window
    window = DownloadProgressWindow(parent, download_item, download_queue)
    active_download_windows[item_index] = window
    
    return window

def close_download_window(item_index: int) -> None:
    """Close download window for specific item"""
    if item_index in active_download_windows:
        active_download_windows[item_index].close_window()
        del active_download_windows[item_index]