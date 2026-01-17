"""
Main activity tracker application.
Runs in system tray, tracks active windows, and receives Chrome tab data via HTTP.
"""
import sys
import time
import threading
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
import json
from typing import Optional, Dict, Any

# Windows-specific imports
try:
    import win32gui
    import win32process
    import psutil
    import pystray
    from PIL import Image, ImageDraw
except ImportError:
    print("Error: Missing required Windows libraries.")
    print("Please install: pip install pywin32 psutil pystray pillow")
    sys.exit(1)

import config
import database


class ActivityTracker:
    """Main tracker class that monitors active windows and Chrome tabs."""
    
    def __init__(self):
        self.running = False
        self.paused = False
        self.current_activity = None
        self.activity_start_time = None
        self.chrome_data = {}  # Store latest Chrome data by window handle
        self.lock = threading.Lock()
        
        # Initialize database
        database.initialize_database()
    
    def get_active_window_info(self) -> Optional[Dict[str, Any]]:
        """Get information about the currently active window."""
        try:
            hwnd = win32gui.GetForegroundWindow()
            if hwnd == 0:
                return None
            
            window_title = win32gui.GetWindowText(hwnd)
            if not window_title:
                return None
            
            # Get process name
            _, pid = win32process.GetWindowThreadProcessId(hwnd)
            try:
                process = psutil.Process(pid)
                process_name = process.name()
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                process_name = "Unknown"
            
            return {
                'hwnd': hwnd,
                'window_title': window_title,
                'process_name': process_name,
                'url': None,
                'chrome_profile': None
            }
        except Exception as e:
            print(f"Error getting active window: {e}")
            return None
    
    def is_chrome_window(self, process_name: str) -> bool:
        """Check if process is Chrome."""
        chrome_names = ['chrome.exe', 'msedge.exe', 'brave.exe']
        return process_name.lower() in chrome_names
    
    def update_chrome_data(self, url: str, title: str, profile: str):
        """Update Chrome tab data from extension."""
        with self.lock:
            # Store with timestamp to know it's recent
            self.chrome_data = {
                'url': url,
                'title': title,
                'profile': profile,
                'timestamp': time.time()
            }
    
    def get_current_activity(self) -> Optional[Dict[str, Any]]:
        """Get current activity with Chrome data if available."""
        info = self.get_active_window_info()
        if not info:
            return None
        
        # If it's Chrome, try to get extension data
        if self.is_chrome_window(info['process_name']):
            with self.lock:
                # Only use Chrome data if it's recent (within last 5 seconds)
                if self.chrome_data and (time.time() - self.chrome_data.get('timestamp', 0)) < 5:
                    info['url'] = self.chrome_data.get('url')
                    info['chrome_profile'] = self.chrome_data.get('profile')
        
        return info
    
    def save_current_activity(self, end_time: Optional[datetime] = None):
        """Save the current activity to database."""
        if not self.current_activity or not self.activity_start_time:
            return
        
        if end_time is None:
            end_time = datetime.now()
        
        duration = int((end_time - self.activity_start_time).total_seconds())
        if duration < config.MIN_DURATION_SECONDS:
            return
        
        try:
            database.log_activity(
                timestamp=self.activity_start_time,
                duration_seconds=duration,
                process_name=self.current_activity['process_name'],
                window_title=self.current_activity['window_title'],
                url=self.current_activity.get('url'),
                chrome_profile=self.current_activity.get('chrome_profile')
            )
            print(f"Logged: {self.current_activity['process_name']} - {self.current_activity['window_title'][:50]} ({duration}s)")
        except Exception as e:
            print(f"Error saving activity: {e}")
    
    def tracking_loop(self):
        """Main tracking loop."""
        while self.running:
            if not self.paused:
                current_time = datetime.now()
                activity = self.get_current_activity()
                
                # Check if activity changed
                activity_changed = False
                if activity != self.current_activity:
                    # Consider it changed if key fields differ
                    if not self.current_activity or \
                       activity['process_name'] != self.current_activity['process_name'] or \
                       activity['window_title'] != self.current_activity['window_title'] or \
                       activity.get('url') != self.current_activity.get('url'):
                        activity_changed = True
                
                if activity_changed:
                    # Save previous activity with current time
                    self.save_current_activity(current_time)
                    
                    # Start tracking new activity
                    self.current_activity = activity
                    self.activity_start_time = current_time
            
            time.sleep(config.POLLING_INTERVAL_SECONDS)
    
    def start(self):
        """Start the tracker."""
        self.running = True
        self.paused = False
        self.tracking_thread = threading.Thread(target=self.tracking_loop, daemon=True)
        self.tracking_thread.start()
    
    def pause(self):
        """Pause tracking."""
        self.save_current_activity()
        self.paused = True
        self.current_activity = None
        self.activity_start_time = None
    
    def resume(self):
        """Resume tracking."""
        self.paused = False
    
    def stop(self):
        """Stop the tracker."""
        self.save_current_activity()
        self.running = False


class ChromeDataHandler(BaseHTTPRequestHandler):
    """HTTP request handler for Chrome extension data."""
    
    tracker = None  # Will be set by setup_handler
    
    def do_POST(self):
        """Handle POST request from Chrome extension."""
        if self.path == '/chrome-data':
            try:
                content_length = int(self.headers['Content-Length'])
                post_data = self.rfile.read(content_length)
                data = json.loads(post_data.decode('utf-8'))
                
                # Update tracker with Chrome data
                if self.tracker:
                    url = data.get('url', '')
                    title = data.get('title', '')
                    profile = data.get('profile', '')
                    self.tracker.update_chrome_data(url, title, profile)
                
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'status': 'ok'}).encode())
            except Exception as e:
                print(f"Error handling Chrome data: {e}")
                self.send_response(500)
                self.end_headers()
        else:
            self.send_response(404)
            self.end_headers()
    
    def log_message(self, format, *args):
        """Suppress default HTTP logging."""
        pass


def setup_handler(tracker):
    """Setup HTTP handler with tracker reference."""
    ChromeDataHandler.tracker = tracker
    return ChromeDataHandler


def create_tray_icon():
    """Create a simple tray icon."""
    # Create a simple icon image
    width = 64
    height = 64
    image = Image.new('RGB', (width, height), 'white')
    draw = ImageDraw.Draw(image)
    
    # Draw a simple clock icon
    draw.ellipse([8, 8, 56, 56], fill='blue', outline='darkblue')
    draw.line([32, 32, 32, 16], fill='white', width=3)
    draw.line([32, 32, 42, 32], fill='white', width=3)
    
    return image


def run_tray_app(tracker: ActivityTracker, server: HTTPServer):
    """Run the system tray application."""
    
    def on_quit(icon, item):
        """Handle quit action."""
        print("Stopping tracker...")
        tracker.stop()
        server.shutdown()
        icon.stop()
    
    def on_pause(icon, item):
        """Handle pause action."""
        tracker.pause()
        print("Tracker paused")
    
    def on_resume(icon, item):
        """Handle resume action."""
        tracker.resume()
        print("Tracker resumed")
    
    def on_status(icon, item):
        """Show status."""
        status = "Paused" if tracker.paused else "Running"
        print(f"Status: {status}")
        if tracker.current_activity:
            print(f"Current: {tracker.current_activity['process_name']} - {tracker.current_activity['window_title'][:50]}")
    
    # Create menu
    menu = pystray.Menu(
        pystray.MenuItem("Status", on_status, default=True),
        pystray.MenuItem("Pause", on_pause),
        pystray.MenuItem("Resume", on_resume),
        pystray.MenuItem("Exit", on_quit)
    )
    
    # Create icon
    icon = pystray.Icon("activity_tracker", create_tray_icon(), "Activity Tracker", menu)
    
    print("Activity Tracker started in system tray")
    print(f"HTTP server listening on {config.HTTP_SERVER_HOST}:{config.HTTP_SERVER_PORT}")
    print("Right-click the tray icon for options")
    
    icon.run()


def main():
    """Main entry point."""
    # Create tracker
    tracker = ActivityTracker()
    
    # Start HTTP server for Chrome extension
    handler = setup_handler(tracker)
    server = HTTPServer((config.HTTP_SERVER_HOST, config.HTTP_SERVER_PORT), handler)
    server_thread = threading.Thread(target=server.serve_forever, daemon=True)
    server_thread.start()
    
    # Start tracking
    tracker.start()
    
    # Run tray application
    try:
        run_tray_app(tracker, server)
    except KeyboardInterrupt:
        print("\nShutting down...")
        tracker.stop()
        server.shutdown()


if __name__ == "__main__":
    main()
