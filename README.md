# Activity Tracker

A Windows application that tracks active windows and Chrome tabs for time tracking purposes. The app runs in the Windows system tray and logs activity to a SQLite database.

## Features

- **Track Active Windows**: Monitor which application/window is currently in focus
- **Track Chrome Tabs**: Capture URL, title, and profile name from Chrome
- **Calculate Duration**: Automatically track how long each window/tab was in focus
- **Categorize Activities**: Match activities to categories based on regex rules
- **System Tray Integration**: Runs quietly in the background with tray icon controls
- **Reporting Tools**: Generate reports by category, application, Chrome profile, or time period

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  Chrome Extension (minimal, unpacked)                       │
│  - Listens for tab activation/update events                │
│  - Sends data to localhost HTTP server                     │
│  - Includes Chrome profile name in the payload             │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼ HTTP POST localhost:5678
┌─────────────────────────────────────────────────────────────┐
│  Python Tracker (system tray)                               │
│  - Runs local HTTP server to receive extension data        │
│  - Tracks active window (Windows API)                      │
│  - Combines window + extension data                        │
│  - Saves everything to SQLite                              │
└─────────────────────────────────────────────────────────────┘
```

## Installation

### 1. Install Python Dependencies

```bash
pip install -r requirements.txt
```

Required packages:
- `pywin32` - Windows API access
- `psutil` - Process information
- `pystray` - System tray icon
- `Pillow` - Image processing for tray icon
- `pyinstaller` - For building executable (optional)

### 2. Install Chrome Extension

The tracker works with Chrome windows even without the extension, but for tab-level tracking, you need to install the extension:

1. Open Chrome and navigate to `chrome://extensions/`
2. Enable "Developer mode" (toggle in top-right corner)
3. Click "Load unpacked"
4. Select the `extension` folder from this repository
5. The extension will appear with no UI - it runs in the background

**Installing on Multiple Profiles:**
- Repeat the above steps for each Chrome profile where you want tab tracking
- For profiles without the extension, the tracker will still log the Chrome window but `url` and `chrome_profile` will be NULL

### 3. Initialize Database

The database will be automatically created when you first run the tracker. The schema includes:

- `category` - Activity categories (e.g., "Work", "Entertainment")
- `category_rule` - Regex patterns to auto-categorize activities
- `activity_log` - Logged activities with timestamps and durations

## Usage

### Running the Tracker

```bash
python tracker.py
```

The tracker will:
- Start a system tray icon (blue clock icon)
- Begin monitoring active windows every second
- Listen for Chrome extension data on `localhost:5678`
- Save activities to `activity_tracker.db`

**Tray Icon Controls:**
- **Left-click**: Show current status
- **Right-click menu**:
  - Status - Display current activity
  - Pause - Pause tracking
  - Resume - Resume tracking
  - Exit - Stop tracker and save data

### Generating Reports

Use `reporter.py` to analyze your tracked activities:

```bash
# Today's summary
python reporter.py --period today

# Yesterday's report
python reporter.py --period yesterday

# Last week
python reporter.py --period week

# Last 30 days
python reporter.py --period month

# All time
python reporter.py --period all

# Custom date range
python reporter.py --start 2024-01-01 --end 2024-01-31

# Specific reports
python reporter.py --category      # Time by category
python reporter.py --app           # Time by application
python reporter.py --profile       # Time by Chrome profile
python reporter.py --daily         # Daily summary

# Export to CSV
python reporter.py --export activities.csv --period week

# Limit number of applications shown
python reporter.py --app --limit 10
```

**Default behavior**: If no specific report is requested, shows category, application, and daily summaries.

### Managing Categories

Categories help organize your activities. Use the provided example script to set up common categories:

```bash
# Quick setup with example categories (Work, Entertainment, Communication, Learning)
python setup_categories.py
```

This creates 4 categories with 13 rules for common applications and websites.

You can also add categories and rules programmatically:

```python
import database

# Initialize database
database.initialize_database()

# Add a category
work_id = database.add_category("Work", "#4CAF50", "Work-related activities")
entertainment_id = database.add_category("Entertainment", "#FF5722", "Fun stuff")

# Add category rules (higher priority wins when multiple match)
# Match by URL
database.add_category_rule(r"github\.com", "url", work_id, priority=10)
database.add_category_rule(r"stackoverflow\.com", "url", work_id, priority=10)

# Match by process name
database.add_category_rule(r"code\.exe", "process_name", work_id, priority=5)
database.add_category_rule(r"slack\.exe", "process_name", work_id, priority=5)

# Match by window title
database.add_category_rule(r"YouTube", "window_title", entertainment_id, priority=10)
database.add_category_rule(r"Netflix", "window_title", entertainment_id, priority=10)
```

**Rule Matching:**
- Rules are regex patterns (case-insensitive)
- Matched against `url`, `window_title`, or `process_name`
- Higher `priority` wins when multiple rules match
- Activities without a matching rule are marked as "Uncategorized"

### Chrome Profiles Without Extension

The tracker handles Chrome profiles without the extension gracefully:

- `process_name` and `window_title` are still logged (from Windows API)
- `url` = NULL
- `chrome_profile` = NULL
- `category_id` = NULL (unless matched by process_name or window_title rules)

Example: If you have 4 Chrome profiles but only install the extension on 3:
- 3 profiles: Full tracking with URL, title, and profile name
- 1 profile: Basic tracking (just process and window title)

## Building Executable

To create a standalone `.exe` file:

```bash
build.bat
```

The executable will be created in the `dist` folder as `ActivityTracker.exe`.

**Notes:**
- The `.exe` is portable but still needs the `extension` folder nearby for the Chrome extension
- The database file will be created in the same directory as the `.exe`

## Database Schema

### category table
```sql
CREATE TABLE category (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    color TEXT,                    -- Hex color code (e.g., #4CAF50)
    description TEXT
);
```

### category_rule table
```sql
CREATE TABLE category_rule (
    id INTEGER PRIMARY KEY,
    pattern TEXT NOT NULL,         -- Regex pattern
    match_field TEXT NOT NULL,     -- 'url', 'window_title', or 'process_name'
    category_id INTEGER NOT NULL,
    priority INTEGER DEFAULT 0     -- Higher priority wins
);
```

### activity_log table
```sql
CREATE TABLE activity_log (
    id INTEGER PRIMARY KEY,
    timestamp TEXT NOT NULL,       -- ISO8601 format
    duration_seconds INTEGER NOT NULL,
    process_name TEXT NOT NULL,
    window_title TEXT NOT NULL,
    url TEXT,                      -- NULL if not Chrome or no extension
    chrome_profile TEXT,           -- NULL if not Chrome or no extension
    category_id INTEGER            -- NULL = uncategorized
);
```

## Configuration

Edit `config.py` to customize:

```python
# HTTP server settings
HTTP_SERVER_PORT = 5678           # Port for Chrome extension
HTTP_SERVER_HOST = "localhost"

# Database settings
DATABASE_PATH = "activity_tracker.db"

# Tracker settings
POLLING_INTERVAL_SECONDS = 1      # How often to check active window
MIN_DURATION_SECONDS = 1          # Minimum duration to log
```

## File Structure

```
activity-tracker/
├── tracker.py              # Main tracker (tray app with HTTP server)
├── reporter.py             # Ad-hoc reports (CLI)
├── config.py               # Settings (port, paths, etc.)
├── database.py             # DB schema and operations
├── setup_categories.py     # Example script to create categories
├── requirements.txt        # Python dependencies
├── build.bat               # Script for creating .exe
├── README.md               # This file
└── extension/              # Chrome extension folder
    ├── manifest.json       # Extension manifest
    └── background.js       # Service worker that tracks tabs
```

## How It Works

### Tracking Logic

1. **Every second**, the tracker checks the active window using Windows API
2. If the window **changes** (different process, title, or URL):
   - Save the previous activity with its duration to the database
   - Start tracking the new activity
3. For **Chrome windows**:
   - Use the latest data received from the extension (if available)
   - If no extension data received in the last 5 seconds, `url` and `chrome_profile` are NULL
4. When **categorizing**:
   - Match the activity against category rules (regex patterns)
   - Higher priority rules win when multiple match
   - If no match, `category_id` is NULL (Uncategorized)

### Chrome Extension

The extension is minimal (~60 lines) and runs as a service worker:

- Listens for `chrome.tabs.onActivated` (tab switch)
- Listens for `chrome.tabs.onUpdated` (URL change)
- Gets profile info using `chrome.identity.getProfileUserInfo()`
- Sends HTTP POST to `localhost:5678/chrome-data` with JSON:
  ```json
  {
    "url": "https://github.com/...",
    "title": "Repository Name",
    "profile": "user@example.com"
  }
  ```
- Silently fails if the tracker is not running

## Troubleshooting

**Tracker won't start:**
- Make sure all dependencies are installed: `pip install -r requirements.txt`
- Check if port 5678 is already in use

**Chrome tabs not tracked:**
- Verify the extension is installed and enabled in `chrome://extensions/`
- Check that the tracker is running (tray icon visible)
- Look for errors in Chrome's extension console (click "service worker" link)

**Categories not working:**
- Check your category rules with: `SELECT * FROM category_rule;`
- Make sure regex patterns are correct (test at regex101.com)
- Remember: Higher priority wins when multiple rules match

**Activities not saved:**
- Check that `activity_tracker.db` is created in the same folder
- Look for error messages in the console where you started `tracker.py`
- Ensure activities last at least `MIN_DURATION_SECONDS` (default: 1 second)

## Privacy & Security

- **All data stays local** - Nothing is sent to external servers
- Database is stored as `activity_tracker.db` in the application directory
- Chrome extension only sends data to `localhost:5678`
- The tracker only runs when manually started

## License

See LICENSE file for details.

## Contributing

Contributions are welcome! Please feel free to submit issues or pull requests.
