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
POLLING_INTERVAL_SECONDS = 3  # How often to check active window

# Minimum duration to log (seconds)
MIN_DURATION_SECONDS = 1

# Default category for uncategorized activities
UNCATEGORIZED_CATEGORY = "Uncategorized"
