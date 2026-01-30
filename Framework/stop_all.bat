@echo off
echo Stopping all MediSecure processes...

echo Killing MediSecure.exe...
taskkill /F /IM MediSecure.exe /T 2>nul

echo Killing MockDataGenerator.exe...
taskkill /F /IM MockDataGenerator.exe /T 2>nul

echo Killing Python processes (if running from source)...
taskkill /F /IM python.exe /T 2>nul

echo.
echo All processes stopped.
pause
