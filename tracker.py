"""
Activity Tracker - System tray application for tracking active windows and Chrome tabs.
"""

import sys
import time
import threading
import re
from datetime import datetime
from typing import Optional, Dict, Any
import win32gui
import win32process
import psutil
import pystray
from PIL import Image, ImageDraw
from pychrome import Browser
import config
import database


class ActivityTracker:
    """Main activity tracking class."""
    
    def __init__(self):
        self.running = False
        self.paused = False
        self.current_activity = None
        self.activity_start_time = None
        self.tray_icon = None
        self.tracking_thread = None
        
        # Initialize database
        database.initialize_database()
        
        # Load category rules once at startup
        self.category_rules = database.get_all_category_rules()
    
    def get_active_window_info(self) -> Dict[str, Any]:
        """Get information about the currently active window."""
        try:
            hwnd = win32gui.GetForegroundWindow()
            window_title = win32gui.GetWindowText(hwnd)
            
            # Get process information
            _, pid = win32process.GetWindowThreadProcessId(hwnd)
            process = psutil.Process(pid)
            process_name = process.name()
            
            return {
                'process_name': process_name,
                'window_title': window_title,
                'pid': pid
            }
        except Exception as e:
            print(f"Error getting active window info: {e}")
            return None
    
    def get_chrome_tab_info(self) -> Optional[Dict[str, str]]:
        """Get information about the current Chrome tab using CDP."""
        try:
            browser = Browser(url=f"http://{config.CDP_HOST}:{config.CDP_PORT}")
            
            # Get all tabs
            tabs = browser.list_tab()
            
            if not tabs:
                return None
            
            # Find the active tab (the one that's visible)
            for tab in tabs:
                # Connect to the tab
                try:
                    tab_obj = browser.get_tab(tab['id'])
                    tab_obj.start()
                    
                    # Get the page information
                    url = tab.get('url', '')
                    title = tab.get('title', '')
                    
                    # Try to extract profile from the webSocketDebuggerUrl
                    # Format is usually: ws://localhost:9222/devtools/page/...
                    # The profile info might be in the URL or we need another approach
                    profile_name = self._extract_chrome_profile(tab)
                    
                    tab_obj.stop()
                    
                    # Return the first tab we find (this is a simplified approach)
                    # In a more complex implementation, we'd track which tab is actually focused
                    return {
                        'url': url,
                        'title': title,
                        'profile': profile_name
                    }
                except Exception as e:
                    continue
            
            return None
        except Exception as e:
            # Chrome might not be running with CDP enabled
            return None
    
    def _extract_chrome_profile(self, tab_info: Dict[str, Any]) -> Optional[str]:
        """Extract Chrome profile name from tab information."""
        # This is a simplified approach - Chrome's CDP doesn't directly expose profile names
        # In practice, you might need to parse the user data directory or use other heuristics
        try:
            # Try to get profile from the description or URL
            description = tab_info.get('description', '')
            # You could parse the user-data-dir from Chrome's command line
            # For now, return a placeholder or None
            return "Default"  # Simplified - would need more sophisticated detection
        except:
            return None
    
    def match_category(self, activity: Dict[str, Any]) -> Optional[int]:
        """Match an activity to a category based on rules."""
        for rule in self.category_rules:
            pattern = rule['pattern']
            match_field = rule['match_field']
            
            try:
                # Get the field to match against
                field_value = None
                if match_field == 'url' and activity.get('url'):
                    field_value = activity['url']
                elif match_field == 'window_title':
                    field_value = activity['window_title']
                elif match_field == 'process_name':
                    field_value = activity['process_name']
                
                if field_value and re.search(pattern, field_value, re.IGNORECASE):
                    return rule['category_id']
            except re.error:
                # Invalid regex pattern, skip this rule
                continue
        
        return None
    
    def save_current_activity(self):
        """Save the current activity to the database."""
        if not self.current_activity or not self.activity_start_time:
            return
        
        # Calculate duration
        duration = int(time.time() - self.activity_start_time)
        
        if duration < config.MIN_ACTIVITY_DURATION_SECONDS:
            return
        
        # Match category
        category_id = self.match_category(self.current_activity)
        
        # Save to database
        timestamp = datetime.fromtimestamp(self.activity_start_time).isoformat()
        database.add_activity_log(
            timestamp=timestamp,
            duration_seconds=duration,
            process_name=self.current_activity['process_name'],
            window_title=self.current_activity['window_title'],
            url=self.current_activity.get('url'),
            chrome_profile=self.current_activity.get('chrome_profile'),
            category_id=category_id
        )
    
    def track_activity(self):
        """Main tracking loop."""
        while self.running:
            if self.paused:
                time.sleep(config.POLLING_INTERVAL_SECONDS)
                continue
            
            # Get current window info
            window_info = self.get_active_window_info()
            
            if not window_info:
                time.sleep(config.POLLING_INTERVAL_SECONDS)
                continue
            
            # Check if it's Chrome and get tab info
            activity = {
                'process_name': window_info['process_name'],
                'window_title': window_info['window_title'],
                'url': None,
                'chrome_profile': None
            }
            
            if 'chrome.exe' in window_info['process_name'].lower():
                chrome_info = self.get_chrome_tab_info()
                if chrome_info:
                    activity['url'] = chrome_info['url']
                    activity['chrome_profile'] = chrome_info['profile']
            
            # Check if activity has changed
            activity_changed = (
                not self.current_activity or
                activity['process_name'] != self.current_activity['process_name'] or
                activity['window_title'] != self.current_activity['window_title'] or
                activity.get('url') != self.current_activity.get('url')
            )
            
            if activity_changed:
                # Save previous activity
                self.save_current_activity()
                
                # Start tracking new activity
                self.current_activity = activity
                self.activity_start_time = time.time()
            
            time.sleep(config.POLLING_INTERVAL_SECONDS)
    
    def start_tracking(self):
        """Start the tracking thread."""
        if not self.running:
            self.running = True
            self.tracking_thread = threading.Thread(target=self.track_activity, daemon=True)
            self.tracking_thread.start()
    
    def stop_tracking(self):
        """Stop the tracking thread."""
        if self.running:
            self.running = False
            # Save the current activity before stopping
            self.save_current_activity()
            if self.tracking_thread:
                self.tracking_thread.join(timeout=2)
    
    def toggle_pause(self):
        """Toggle pause/resume tracking."""
        if self.paused:
            self.paused = False
            # Resume tracking with current activity
            self.activity_start_time = time.time()
        else:
            # Save current activity before pausing
            self.save_current_activity()
            self.paused = True
            self.current_activity = None
            self.activity_start_time = None
    
    def create_tray_icon(self) -> Image.Image:
        """Create a simple tray icon."""
        # Create a simple colored circle as icon
        size = 64
        image = Image.new('RGB', (size, size), color='white')
        draw = ImageDraw.Draw(image)
        draw.ellipse([8, 8, size-8, size-8], fill=config.TRAY_ICON_COLOR)
        return image
    
    def on_quit(self, icon, item):
        """Handle quit action from tray menu."""
        self.stop_tracking()
        icon.stop()
    
    def on_pause_resume(self, icon, item):
        """Handle pause/resume action from tray menu."""
        self.toggle_pause()
        # Update menu
        icon.menu = self.create_menu()
    
    def on_show_status(self, icon, item):
        """Show current tracking status."""
        if self.paused:
            status = "Status: Paused"
        elif self.current_activity:
            status = f"Tracking: {self.current_activity['process_name']} - {self.current_activity['window_title'][:50]}"
        else:
            status = "Status: Running"
        
        print(status)
        # In a real implementation, you might want to show a notification or popup
        # For now, we just print to console
    
    def create_menu(self):
        """Create the tray icon menu."""
        pause_resume_text = "Resume" if self.paused else "Pause"
        return pystray.Menu(
            pystray.MenuItem("Show Status", self.on_show_status),
            pystray.MenuItem(pause_resume_text, self.on_pause_resume),
            pystray.MenuItem("Exit", self.on_quit)
        )
    
    def run(self):
        """Run the application."""
        # Start tracking
        self.start_tracking()
        
        # Create and run tray icon
        icon = pystray.Icon(
            config.APP_NAME,
            self.create_tray_icon(),
            config.APP_NAME,
            self.create_menu()
        )
        
        self.tray_icon = icon
        icon.run()


def main():
    """Main entry point."""
    tracker = ActivityTracker()
    tracker.run()


if __name__ == "__main__":
    main()
