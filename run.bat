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

:: -----------------------------------------------
:: Login
:: -----------------------------------------------
set COOKIES_ARG=
set HIRES_ARG=

if exist "cookies.txt" (
    echo  A saved login was found.
    echo  [1] Use saved login
    echo  [2] Log in again  ^(replaces saved^)
    echo  [3] Continue without login
    echo.
    set LOGIN_CHOICE=1
    set /p LOGIN_CHOICE="  Choice (1/2/3): "
) else (
    echo  [1] Log in
    echo  [2] Continue without login
    echo.
    set LOGIN_CHOICE=2
    set /p LOGIN_CHOICE="  Choice (1/2): "
    :: Remap so the rest of the logic is consistent
    if "!LOGIN_CHOICE!"=="1" set LOGIN_CHOICE=2_fresh
    if "!LOGIN_CHOICE!"=="2" set LOGIN_CHOICE=3
)

if "!LOGIN_CHOICE!"=="1" (
    :: Load saved cookies
    set /p SAVED_COOKIES=<cookies.txt
    set COOKIES_ARG=--cookies "!SAVED_COOKIES!"
    echo  [+] Using saved login.
    echo.
    set USE_HIRES=n
    set /p USE_HIRES="  Download original resolution? (y/n): "
    if /i "!USE_HIRES!"=="y" set HIRES_ARG=--hires
)

if "!LOGIN_CHOICE!"=="2" goto :do_fresh_login
if "!LOGIN_CHOICE!"=="2_fresh" goto :do_fresh_login
goto :after_login

:do_fresh_login
echo.
echo  How to get your cookie string:
echo  1. Open e-hentai.org in your browser and log in
echo  2. Press F12 to open DevTools, go to the Console tab
echo  3. Type:  document.cookie  and press Enter
echo  4. Copy the full output and paste it below
echo.
set /p COOKIE_STR="  Paste cookie string: "
set COOKIES_ARG=--cookies "!COOKIE_STR!"

:: Save to file
echo !COOKIE_STR!>cookies.txt
echo  [+] Login saved to cookies.txt
echo.
set USE_HIRES=n
set /p USE_HIRES="  Download original resolution? (y/n): "
if /i "!USE_HIRES!"=="y" set HIRES_ARG=--hires

:after_login

:: -----------------------------------------------
:: Download loop
:: -----------------------------------------------
:download_loop

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
        goto download_loop
    )
    set URL_ARG="!GALLERY_URL!"
)

echo.
echo [*] Starting download...
echo.

python downloader.py !URL_ARG! !BATCH_ARG! !COOKIES_ARG! !HIRES_ARG!

echo.
set AGAIN=n
set /p AGAIN="Download another gallery? (y/n): "
if /i "!AGAIN!"=="y" goto download_loop

echo.
echo Bye!
timeout /t 2 >nul
