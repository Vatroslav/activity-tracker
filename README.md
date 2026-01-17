# Activity Tracker

A Windows application that tracks active windows and Chrome tabs for time tracking purposes. The app runs in the system tray and logs all activity to a SQLite database, with support for categorizing activities based on configurable rules.

## Features

- **Active Window Tracking** - Monitors which application/window is currently in focus
- **Chrome Tab Tracking** - Uses Chrome DevTools Protocol (CDP) to track:
  - Current tab URL
  - Tab title
  - Chrome profile name
- **Duration Calculation** - Automatically tracks how long each window/tab was in focus
- **Activity Categorization** - Match activities to categories based on regex rules
- **System Tray Application** - Runs quietly in the background
- **Reporting Tools** - CLI tool for generating various activity reports

## Installation

### Prerequisites

- Python 3.7 or higher
- Windows OS
- Google Chrome (for Chrome tracking features)

### Setup

1. Clone the repository:
```bash
git clone https://github.com/Vatroslav/activity-tracker.git
cd activity-tracker
```

2. Install Python dependencies:
```bash
pip install -r requirements.txt
```

3. Initialize the database (automatic on first run):
```bash
python tracker.py
```

## Chrome Setup

To enable Chrome tab tracking, you need to start Chrome with remote debugging enabled:

1. Close all Chrome instances
2. Start Chrome with the `--remote-debugging-port=9222` flag:

```bash
chrome.exe --remote-debugging-port=9222
```

**For easier use**, create a shortcut or AutoHotkey (AHK) script:

### AHK Script Example
```ahk
Run, chrome.exe --remote-debugging-port=9222
```

### Windows Shortcut
1. Right-click Chrome shortcut → Properties
2. In "Target" field, append: `--remote-debugging-port=9222`
3. Example: `"C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222`

## Usage

### Running the Tracker

Start the activity tracker:
```bash
python tracker.py
```

The application will:
- Start tracking immediately
- Run in the system tray (look for the blue circle icon)
- Check active window every second
- Save activity data to `activity_tracker.db`

### Tray Icon Features

- **Show Status** - Display current tracking status
- **Pause/Resume** - Temporarily pause or resume tracking
- **Exit** - Stop tracking and close the application

### Managing Categories

Categories help organize your activities. You can add categories and rules programmatically or via a Python script.

#### Example: Adding Categories via Python

```python
import database

# Initialize database
database.initialize_database()

# Add categories
work_id = database.add_category("Work", "#0078D4", "Work-related activities")
social_id = database.add_category("Social Media", "#FF6B6B", "Social media sites")
dev_id = database.add_category("Development", "#4CAF50", "Software development")

# Add category rules
# Match GitHub URLs
database.add_category_rule(r"github\.com", "url", dev_id, priority=10)

# Match VS Code
database.add_category_rule(r"Visual Studio Code", "window_title", dev_id, priority=10)

# Match social media URLs
database.add_category_rule(r"(facebook|twitter|instagram)\.com", "url", social_id, priority=5)

# Match Chrome browser by process
database.add_category_rule(r"chrome\.exe", "process_name", work_id, priority=1)

print("Categories and rules added successfully!")
```

#### Rule Priority

When multiple rules match an activity, the rule with the **highest priority** wins. Use priority to create specific overrides:

- Low priority (0-5): General rules (e.g., "all Chrome tabs are work")
- Medium priority (6-15): Domain-specific rules (e.g., "github.com is development")
- High priority (16+): Very specific rules (e.g., "specific project URLs")

### Generating Reports

Use the `reporter.py` CLI tool to generate activity reports:

#### Daily Summary by Category
```bash
python reporter.py category -p today
```

#### Weekly Summary by Process
```bash
python reporter.py process -p week
```

#### Chrome Profile Summary
```bash
python reporter.py chrome -p month
```

#### List Recent Activities
```bash
python reporter.py list -l 50
```

#### Custom Date Range
```bash
python reporter.py category -s "2024-01-01" -e "2024-01-31"
```

#### Export to CSV
```bash
python reporter.py category -p week -f csv > report.csv
```

### Available Report Types

1. **category** - Time spent by category
2. **process** - Time spent by application/process
3. **chrome** - Time spent by Chrome profile
4. **list** - List recent activities with details

### Report Options

- `-p, --period` - Time period: today, yesterday, week, month, all
- `-s, --start-date` - Custom start date (ISO format)
- `-e, --end-date` - Custom end date (ISO format)
- `-f, --format` - Output format: table or csv
- `-l, --limit` - Limit number of results (default: 20)

## Building Executables

To create standalone `.exe` files:

```bash
build.bat
```

This will create:
- `dist/ActivityTracker.exe` - System tray tracker (no console window)
- `dist/ActivityReporter.exe` - CLI reporting tool

The executables can be distributed and run without Python installed.

## Database Schema

The application uses SQLite with three main tables:

### category
Stores activity categories with optional colors and descriptions.

### category_rule
Defines regex patterns to match activities to categories. Rules have priorities to handle overlapping patterns.

### activity_log
Records all tracked activities with timestamps, durations, and associated metadata.

## Configuration

Edit `config.py` to customize settings:

```python
# Database location
DATABASE_PATH = "activity_tracker.db"

# Chrome DevTools Protocol settings
CDP_HOST = "localhost"
CDP_PORT = 9222

# Tracking settings
POLLING_INTERVAL_SECONDS = 1
MIN_ACTIVITY_DURATION_SECONDS = 1
```

## Troubleshooting

### Chrome tab tracking not working

- Ensure Chrome is running with `--remote-debugging-port=9222`
- Check if port 9222 is already in use by another application
- Try accessing `http://localhost:9222` in a browser - you should see Chrome's DevTools endpoint

### Tracker not detecting active windows

- Run as Administrator if certain windows aren't detected
- Some protected windows (UAC prompts, etc.) cannot be tracked

### Database locked errors

- Only run one instance of the tracker at a time
- Close the tracker before running database maintenance scripts

## File Structure

```
activity-tracker/
├── tracker.py           # Main tracker (tray app)
├── reporter.py          # Ad-hoc reports (CLI)
├── config.py            # Settings (port, paths, etc.)
├── database.py          # DB schema and operations
├── requirements.txt     # Python dependencies
├── build.bat            # Script for creating .exe
├── README.md            # This file
└── activity_tracker.db  # SQLite database (created on first run)
```

## Privacy & Data

- All data is stored locally in `activity_tracker.db`
- No data is sent to external servers
- The database contains window titles, URLs, and process names
- Keep your database file secure as it contains your activity history

## License

See LICENSE file for details.

## Contributing

Contributions are welcome! Please feel free to submit issues or pull requests.

## Acknowledgments

- Uses [pystray](https://github.com/moses-palmer/pystray) for system tray functionality
- Uses [pychrome](https://github.com/fate0/pychrome) for Chrome DevTools Protocol
- Uses [pywin32](https://github.com/mhammond/pywin32) for Windows API access
