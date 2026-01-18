"""
Main activity tracker application.
Runs in system tray, tracks active windows, and receives Chrome tab data via HTTP.
"""
import sys
import time
import threading
import ctypes
import re
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


class LASTINPUTINFO(ctypes.Structure):
    """Windows structure for GetLastInputInfo."""
    _fields_ = [
        ('cbSize', ctypes.c_uint),
        ('dwTime', ctypes.c_uint),
    ]


def get_idle_seconds():
    """Get the number of seconds since last user input."""
    lii = LASTINPUTINFO()
    lii.cbSize = ctypes.sizeof(LASTINPUTINFO)
    ctypes.windll.user32.GetLastInputInfo(ctypes.byref(lii))
    millis = ctypes.windll.kernel32.GetTickCount() - lii.dwTime
    return millis / 1000.0


class ActivityTracker:
    """Main tracker class that monitors active windows and Chrome tabs."""
    
    def __init__(self):
        self.running = False
        self.paused = False
        self.current_activity = None
        self.activity_start_time = None
        self.chrome_data = {}  # Store latest Chrome data by window handle
        self.lock = threading.Lock()
        
        # Idle detection state
        self.idle_start_time = None
        self.idle_prompt_shown = False
        self.idle_prompt_start_time = None
        
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
    
    def is_exception_app(self, process_name: str) -> bool:
        """Check if the process is on the idle exception list."""
        if not process_name:
            return False
        process_lower = process_name.lower()
        return any(app.lower() == process_lower for app in config.IDLE_EXCEPTION_APPS)
    
    def is_exception_url(self, url: Optional[str]) -> bool:
        """Check if the URL matches any idle exception pattern."""
        if not url:
            return False
        for pattern in config.IDLE_EXCEPTION_URLS:
            if re.search(pattern, url, re.IGNORECASE):
                return True
        return False
    
    def is_idle_exception(self, activity: Optional[Dict[str, Any]]) -> bool:
        """Check if current activity is an exception to idle detection."""
        if not activity:
            return False
        
        # Check if process is on exception list
        if self.is_exception_app(activity.get('process_name', '')):
            return True
        
        # Check if URL matches exception pattern
        if self.is_exception_url(activity.get('url')):
            return True
        
        return False
    
    def show_idle_prompt(self) -> bool:
        """Show Windows prompt asking if user is still present.
        
        Returns True if user clicked YES, False if user clicked NO or closed dialog.
        This is a blocking call.
        """
        MB_YESNO = 0x4
        MB_ICONQUESTION = 0x20
        MB_TOPMOST = 0x40000
        IDYES = 6
        
        result = ctypes.windll.user32.MessageBoxW(
            0,
            "You appear to be idle. Are you still here?",
            "Activity Tracker - Idle Detection",
            MB_YESNO | MB_ICONQUESTION | MB_TOPMOST
        )
        
        return result == IDYES
    
    def handle_idle_prompt_thread(self):
        """Handle idle prompt in a separate thread."""
        response = self.show_idle_prompt()
        
        with self.lock:
            self.idle_prompt_shown = False
            
            if response:
                # User clicked YES - reset idle state and continue tracking
                print("User responded to idle prompt: continuing tracking")
                self.idle_start_time = None
                self.idle_prompt_start_time = None
            else:
                # User clicked NO or closed dialog - treat as no response
                print("User dismissed idle prompt")
    
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
                    if self.current_activity is None or activity is None or \
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
                    
                    # Reset idle state when activity changes
                    self.idle_start_time = None
                    self.idle_prompt_start_time = None
                
                # Check idle status
                idle_seconds = get_idle_seconds()
                idle_minutes = idle_seconds / 60.0
                
                # Track when user became idle
                if idle_minutes >= config.IDLE_TIMEOUT_MINUTES:
                    if self.idle_start_time is None:
                        # User just became idle
                        self.idle_start_time = current_time
                        print(f"User idle detected ({idle_minutes:.1f} minutes)")
                    
                    # Check if we should show prompt
                    if not self.idle_prompt_shown and self.idle_prompt_start_time is None:
                        # Check if current activity is an exception
                        if self.is_idle_exception(self.current_activity):
                            print(f"Idle exception detected: {self.current_activity.get('process_name', 'Unknown')} - continuing tracking")
                        else:
                            # Save current activity before showing prompt
                            self.save_current_activity(current_time)
                            
                            # Show prompt in a separate thread (non-blocking)
                            self.idle_prompt_shown = True
                            self.idle_prompt_start_time = current_time
                            prompt_thread = threading.Thread(target=self.handle_idle_prompt_thread, daemon=True)
                            prompt_thread.start()
                            print("Showing idle prompt...")
                    
                    # Check if prompt timeout expired
                    elif self.idle_prompt_start_time is not None and not self.idle_prompt_shown:
                        # Prompt was shown and dismissed, check timeout
                        prompt_elapsed = (current_time - self.idle_prompt_start_time).total_seconds() / 60.0
                        if prompt_elapsed >= config.IDLE_PROMPT_TIMEOUT_MINUTES:
                            # No response within timeout - delete recent activity
                            print(f"Idle prompt timeout - deleting last {config.IDLE_TIMEOUT_MINUTES} minutes of activity")
                            deleted = database.delete_recent_activity(config.IDLE_TIMEOUT_MINUTES)
                            print(f"Deleted {deleted} activity records")
                            
                            # Reset tracking state
                            self.current_activity = None
                            self.activity_start_time = None
                            self.idle_start_time = None
                            self.idle_prompt_start_time = None
                else:
                    # User is active - reset idle state
                    if self.idle_start_time is not None:
                        print("User is active again")
                        self.idle_start_time = None
                        self.idle_prompt_start_time = None
            
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
        # Reset idle state when pausing
        self.idle_start_time = None
        self.idle_prompt_shown = False
        self.idle_prompt_start_time = None
    
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
    
    def send_cors_headers(self):
        """Send CORS headers to allow requests from Chrome extension.
        
        Note: Using '*' for Access-Control-Allow-Origin is acceptable here because
        the server only listens on localhost and is not exposed to the internet.
        Chrome extensions require CORS headers for fetch requests to HTTP servers.
        """
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
    
    def do_OPTIONS(self):
        """Handle OPTIONS preflight request for CORS."""
        self.send_response(200)
        self.send_cors_headers()
        self.end_headers()
    
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
                self.send_cors_headers()
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'status': 'ok'}).encode())
            except Exception as e:
                print(f"Error handling Chrome data: {e}")
                self.send_response(500)
                self.send_cors_headers()
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'status': 'error', 'message': 'Internal server error'}).encode())
        else:
            self.send_response(404)
            self.send_cors_headers()
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'status': 'error', 'message': 'Not found'}).encode())
    
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
