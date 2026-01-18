"""
Configuration settings for the activity tracker.
"""
import os

# HTTP server settings
HTTP_SERVER_PORT = 5678
HTTP_SERVER_HOST = "localhost"

# Database settings
DATABASE_PATH = os.path.join(os.path.dirname(__file__), "activity_tracker.db")

# Tracker settings
POLLING_INTERVAL_SECONDS = 1  # How often to check active window

# Minimum duration to log (seconds)
MIN_DURATION_SECONDS = 1

# Default category for uncategorized activities
UNCATEGORIZED_CATEGORY = "Uncategorized"

# Idle timeout settings
IDLE_TIMEOUT_MINUTES = 10
IDLE_PROMPT_TIMEOUT_MINUTES = 2

# Apps that are exceptions to idle detection (process names)
IDLE_EXCEPTION_APPS = [
    'spotify.exe',
    'vlc.exe',
]

# URLs that are exceptions to idle detection (regex patterns)
IDLE_EXCEPTION_URLS = [
    r'youtube\.com',
    r'netflix\.com',
]
