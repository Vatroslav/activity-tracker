@echo off
REM Build script for Activity Tracker

echo Building Activity Tracker...

REM Install dependencies if needed
pip install -r requirements.txt

REM Build the tracker executable
pyinstaller --name=ActivityTracker ^
    --onefile ^
    --windowed ^
    --icon=NONE ^
    --add-data "config.py;." ^
    --hidden-import=win32timezone ^
    tracker.py

REM Build the reporter executable
pyinstaller --name=ActivityReporter ^
    --onefile ^
    --console ^
    --add-data "config.py;." ^
    reporter.py

echo.
echo Build complete!
echo Executables can be found in the dist/ folder:
echo - ActivityTracker.exe (system tray app)
echo - ActivityReporter.exe (CLI reporting tool)
echo.
echo Note: Copy the database file (activity_tracker.db) to the same folder as the executables
echo if you want to use them outside the development environment.

pause
