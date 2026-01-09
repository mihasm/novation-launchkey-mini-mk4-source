@echo off
REM Script to retrieve the latest log file from Ableton Live directory
REM Source: C:\ProgramData\Ableton\Live 12 Suite\Resources\MIDI Remote Scripts\Launchkey_MK4_patched\launchkey_mk4.log
REM Destination: Current directory (project root)

setlocal enabledelayedexpansion

REM Set source and destination paths
set "SOURCE_LOG=C:\ProgramData\Ableton\Live 12 Suite\Resources\MIDI Remote Scripts\Launchkey_MK4_patched\launchkey_mk4.log"
set "DEST_DIR=%~dp0"
set "DEST_LOG=%DEST_DIR%launchkey_mk4.log"

echo.
echo ========================================
echo Launchkey MK4 Log Retrieval Script
echo ========================================
echo.
echo Source: %SOURCE_LOG%
echo Destination: %DEST_LOG%
echo.

REM Check if source log file exists
if not exist "%SOURCE_LOG%" (
    echo ERROR: Log file not found at source location.
    echo Please make sure:
    echo   1. Ableton Live has been started at least once
    echo   2. The Launchkey_MK4_patched script has been loaded
    echo.
    pause
    exit /b 1
)

REM Copy the log file
echo Copying log file...
copy "%SOURCE_LOG%" "%DEST_LOG%" >nul 2>&1
if errorlevel 1 (
    echo ERROR: Failed to copy log file.
    echo The log file might be locked by Ableton Live.
    echo Try closing Ableton Live and run this script again.
    echo.
    pause
    exit /b 1
)

REM Get file size for confirmation
for %%A in ("%DEST_LOG%") do set "FILE_SIZE=%%~zA"
set /a FILE_SIZE_KB=%FILE_SIZE% / 1024

echo Log file copied successfully!
echo File size: %FILE_SIZE_KB% KB
echo.
echo The log file is now available at:
echo %DEST_LOG%
echo.
echo You can open it with any text editor to view the latest logs.
echo.
pause
