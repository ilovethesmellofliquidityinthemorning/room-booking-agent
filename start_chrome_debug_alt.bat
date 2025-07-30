@echo off
echo Starting Chrome with remote debugging on alternative port...
echo.

REM Create temp directory if it doesn't exist
if not exist "C:\temp" mkdir "C:\temp"

echo Chrome will start with:
echo - Remote debugging on port 9223
echo - Separate user data directory
echo.

start chrome.exe --remote-debugging-port=9223 --user-data-dir="C:\temp\chrome_debug_alt"

echo Chrome started on port 9223! You can now log in and run:
echo python test_login_alt.py
echo.
pause