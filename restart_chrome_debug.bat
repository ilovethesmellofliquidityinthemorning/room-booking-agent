@echo off
echo Restarting Chrome with proper debugging setup...
echo.

echo Step 1: Closing all Chrome processes...
taskkill /f /im chrome.exe >nul 2>&1
timeout /t 3 /nobreak >nul

echo Step 2: Clearing temp directories...
if exist "C:\temp\chrome_debug" rmdir /s /q "C:\temp\chrome_debug"
if not exist "C:\temp" mkdir "C:\temp"

echo Step 3: Starting Chrome with remote debugging...
echo Chrome will start with:
echo - Remote debugging on port 9222
echo - Clean user data directory
echo - No extensions or automation detection
echo.

start chrome.exe --remote-debugging-port=9222 --user-data-dir="C:\temp\chrome_debug" --disable-extensions --disable-plugins --disable-background-timer-throttling --disable-backgrounding-occluded-windows --disable-renderer-backgrounding --disable-features=TranslateUI --no-first-run --no-default-browser-check

echo Waiting for Chrome to start...
timeout /t 5 /nobreak >nul

echo Testing connection to debug port...
echo.
powershell -Command "try { Invoke-WebRequest -Uri 'http://127.0.0.1:9222/json' -TimeoutSec 5 | Out-Null; Write-Host 'SUCCESS: Chrome debug port 9222 is accessible!' -ForegroundColor Green } catch { Write-Host 'WARNING: Cannot connect to port 9222' -ForegroundColor Yellow }"

echo.
echo Chrome restarted! You can now:
echo 1. Navigate to your login page manually
echo 2. Run: python test_login.py
echo.
pause