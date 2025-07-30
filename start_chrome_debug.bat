@echo off
echo Starting Chrome with remote debugging for room booking automation...
echo.

REM Create temp directory if it doesn't exist
if not exist "C:\temp" mkdir "C:\temp"

echo Chrome will start with:
echo - Remote debugging on port 9222
echo - Separate user data directory
echo.

echo After Chrome opens:
echo 1. Navigate to your UT SharePoint dashboard
echo 2. Log in with your credentials
echo 3. Choose a test to run:
echo    - python test_session_automation.py (original test)
echo    - python test_enhanced_booking.py (enhanced test - RECOMMENDED)
echo.

start chrome.exe --remote-debugging-port=9222 --user-data-dir="C:\temp\chrome_debug"

echo Chrome started! You can now log in and run the automation test.
echo.
echo TIP: Use the enhanced test for the latest features:
echo      python test_enhanced_booking.py
echo.
pause