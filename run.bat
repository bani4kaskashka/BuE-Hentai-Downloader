@echo off
setlocal
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

set MEMBER_ID=
set PASS_HASH=
set USE_HIRES=

if /i "%USE_LOGIN%"=="y" (
    echo.
    echo  To get your cookies: open e-hentai.org in your browser,
    echo  open DevTools ^(F12^) ^> Application ^> Cookies ^> e-hentai.org
    echo.
    set /p MEMBER_ID="  ipb_member_id: "
    set /p PASS_HASH="  ipb_pass_hash: "
    echo.
    set /p USE_HIRES="  Download original resolution? (y/n): "
)

echo.
set /p GALLERY_URL="Gallery URL: "
if "%GALLERY_URL%"=="" (
    echo [!] No URL entered.
    pause
    exit /b 1
)

:: Build command
set CMD=python downloader.py "%GALLERY_URL%"

if /i "%USE_LOGIN%"=="y" (
    set CMD=%CMD% --member-id "%MEMBER_ID%" --pass-hash "%PASS_HASH%"
    if /i "%USE_HIRES%"=="y" set CMD=%CMD% --hires
)

echo.
echo [*] Starting download...
echo.
%CMD%

echo.
pause
