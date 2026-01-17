"""
Configuration settings for the Activity Tracker application.
"""

import os
from pathlib import Path

# Database settings
DATABASE_PATH = os.path.join(os.path.dirname(__file__), "activity_tracker.db")

# Chrome DevTools Protocol settings
CDP_HOST = "localhost"
CDP_PORT = 9222

# Tracker settings
POLLING_INTERVAL_SECONDS = 1  # How often to check active window
MIN_ACTIVITY_DURATION_SECONDS = 1  # Minimum duration to log an activity

# Application settings
APP_NAME = "Activity Tracker"
TRAY_ICON_COLOR = (0, 120, 212)  # Windows blue

# Chrome detection settings
CHROME_PROCESS_NAMES = ["chrome.exe", "msedge.exe"]  # Chrome and Edge use CDP
DEFAULT_CHROME_PROFILE = "Default"

# Database field values
MATCH_FIELDS = ["url", "window_title", "process_name"]
