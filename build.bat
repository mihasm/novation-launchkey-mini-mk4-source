@echo off
REM Build script to copy patched Launchkey MK4 scripts to Ableton Live directory
REM Target: C:\ProgramData\Ableton\Live 12 Suite\Resources\MIDI Remote Scripts\

setlocal enabledelayedexpansion

REM Set source and target directories
set "SOURCE_DIR=%~dp0patched"
set "TARGET_DIR=C:\ProgramData\Ableton\Live 12 Suite\Resources\MIDI Remote Scripts"

REM Check if source directory exists
if not exist "%SOURCE_DIR%" (
    echo ERROR: Source directory not found: %SOURCE_DIR%
    echo Please run this script from the repository root directory.
    pause
    exit /b 1
)

REM Check if target directory exists
if not exist "%TARGET_DIR%" (
    echo ERROR: Target directory not found: %TARGET_DIR%
    echo Please make sure Ableton Live 12 Suite is installed.
    pause
    exit /b 1
)

echo.
echo ========================================
echo Launchkey MK4 Build Script
echo ========================================
echo.
echo Source: %SOURCE_DIR%
echo Target: %TARGET_DIR%
echo.

REM Remove existing folders
echo Removing existing folders...
if exist "%TARGET_DIR%\Launchkey_Mini_MK4_patched" (
    echo   Removing Launchkey_Mini_MK4_patched...
    rmdir /s /q "%TARGET_DIR%\Launchkey_Mini_MK4_patched"
    if !errorlevel! neq 0 (
        echo   WARNING: Failed to remove Launchkey_Mini_MK4_patched
    ) else (
        echo   Removed Launchkey_Mini_MK4_patched
    )
)

if exist "%TARGET_DIR%\Launchkey_MK4_patched" (
    echo   Removing Launchkey_MK4_patched...
    rmdir /s /q "%TARGET_DIR%\Launchkey_MK4_patched"
    if !errorlevel! neq 0 (
        echo   WARNING: Failed to remove Launchkey_MK4_patched
    ) else (
        echo   Removed Launchkey_MK4_patched
    )
)

echo.
echo Copying new folders (excluding __pycache__)...
echo.

REM Copy Launchkey_Mini_MK4_patched (excluding __pycache__)
if exist "%SOURCE_DIR%\Launchkey_Mini_MK4_patched" (
    echo   Copying Launchkey_Mini_MK4_patched...
    robocopy "%SOURCE_DIR%\Launchkey_Mini_MK4_patched" "%TARGET_DIR%\Launchkey_Mini_MK4_patched" /E /XD __pycache__ /NFL /NDL /NJH /NJS
    if !errorlevel! geq 8 (
        echo   ERROR: Failed to copy Launchkey_Mini_MK4_patched
        pause
        exit /b 1
    ) else (
        echo   Copied Launchkey_Mini_MK4_patched
    )
) else (
    echo   WARNING: Launchkey_Mini_MK4_patched not found in source
)

REM Copy Launchkey_MK4_patched (excluding __pycache__)
if exist "%SOURCE_DIR%\Launchkey_MK4_patched" (
    echo   Copying Launchkey_MK4_patched...
    robocopy "%SOURCE_DIR%\Launchkey_MK4_patched" "%TARGET_DIR%\Launchkey_MK4_patched" /E /XD __pycache__ /NFL /NDL /NJH /NJS
    if !errorlevel! geq 8 (
        echo   ERROR: Failed to copy Launchkey_MK4_patched
        pause
        exit /b 1
    ) else (
        echo   Copied Launchkey_MK4_patched
    )
) else (
    echo   WARNING: Launchkey_MK4_patched not found in source
)

REM Clean up any __pycache__ folders that might have been copied (safety check)
echo.
echo Cleaning up any remaining __pycache__ folders...
for /d /r "%TARGET_DIR%\Launchkey_Mini_MK4_patched" %%d in (__pycache__) do (
    if exist "%%d" (
        echo   Removing %%d
        rmdir /s /q "%%d" 2>nul
    )
)
for /d /r "%TARGET_DIR%\Launchkey_MK4_patched" %%d in (__pycache__) do (
    if exist "%%d" (
        echo   Removing %%d
        rmdir /s /q "%%d" 2>nul
    )
)

echo.
echo ========================================
echo Build completed successfully!
echo ========================================
echo.
echo You can now start Ableton Live to test the changes.
echo.
pause
