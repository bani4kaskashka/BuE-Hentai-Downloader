@echo off
setlocal enabledelayedexpansion
cd /d "%~dp0"

echo ===================================
echo   BuE-Hentai Downloader
echo ===================================
echo.

if not exist ".venv\Scripts\activate.bat" (
    echo [*] Creating virtual environment...
    python -m venv .venv
    if errorlevel 1 (
        echo [!] Failed to create venv. Make sure Python is installed.
        pause
        exit /b 1
    )
)

call .venv\Scripts\activate.bat

echo [*] Checking dependencies...
pip install -q -r requirements.txt
if errorlevel 1 (
    echo [!] Failed to install dependencies.
    pause
    exit /b 1
)
echo.

:: Login
set USE_LOGIN=n
set /p USE_LOGIN="Log in with your account? (y/n): "

set COOKIES_ARG=
set HIRES_ARG=

if /i "!USE_LOGIN!"=="y" (
    echo.
    echo  How to get your cookie string:
    echo  1. Open e-hentai.org in your browser and log in
    echo  2. Press F12 to open DevTools, go to the Console tab
    echo  3. Type:  document.cookie  and press Enter
    echo  4. Copy the full output and paste it below
    echo.
    set /p COOKIE_STR="  Paste cookie string: "
    set COOKIES_ARG=--cookies "!COOKIE_STR!"
    echo.
    set USE_HIRES=n
    set /p USE_HIRES="  Download original resolution? (y/n): "
    if /i "!USE_HIRES!"=="y" set HIRES_ARG=--hires
)

:: Single or batch
echo.
set BATCH_MODE=n
set /p BATCH_MODE="Download from a URL list file? (y/n): "

set URL_ARG=
set BATCH_ARG=

if /i "!BATCH_MODE!"=="y" (
    echo  Create a .txt file with one gallery URL per line.
    echo  Lines starting with # are treated as comments and ignored.
    echo.
    set /p BATCH_FILE="  Path to file: "
    set BATCH_ARG=--batch "!BATCH_FILE!"
) else (
    echo.
    set /p GALLERY_URL="Gallery URL: "
    if "!GALLERY_URL!"=="" (
        echo [!] No URL entered.
        pause
        exit /b 1
    )
    set URL_ARG="!GALLERY_URL!"
)

echo.
echo [*] Starting download...
echo.

python downloader.py !URL_ARG! !BATCH_ARG! !COOKIES_ARG! !HIRES_ARG!

echo.
pause
