@echo off
REM Build script for Activity Tracker
REM Creates a single executable using PyInstaller

echo Building Activity Tracker...

REM Clean previous builds
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist

REM Build the executable
pyinstaller --name ActivityTracker ^
    --onefile ^
    --windowed ^
    --icon=NONE ^
    --add-data "config.py;." ^
    --add-data "database.py;." ^
    tracker.py

echo.
echo Build complete!
echo Executable is in: dist\ActivityTracker.exe
echo.

pause
