#!/usr/bin/env bash
# BuE-Hentai Downloader — Linux/macOS launcher
set -euo pipefail
cd "$(dirname "$(realpath "$0")")"

echo "==================================="
echo "   BuE-Hentai Downloader"
echo "==================================="
echo

# -----------------------------------------------
# Virtual environment
# -----------------------------------------------
if [ ! -f ".venv/bin/activate" ]; then
    echo "[*] Creating virtual environment..."
    python3 -m venv .venv || {
        echo "[!] Failed to create venv. Make sure Python 3 is installed."
        exit 1
    }
fi

# shellcheck disable=SC1091
source .venv/bin/activate

echo "[*] Checking dependencies..."
pip install -q -r requirements.txt || {
    echo "[!] Failed to install dependencies."
    exit 1
}
echo

# -----------------------------------------------
# Login
# -----------------------------------------------
COOKIES_ARG=""
HIRES_ARG=""

ask_hires() {
    read -rp "  Download original resolution? (y/n): " USE_HIRES
    USE_HIRES="${USE_HIRES,,}"   # lowercase
    if [ "$USE_HIRES" = "y" ]; then
        HIRES_ARG="--hires"
    fi
}

if [ -f "cookies.txt" ]; then
    echo "  A saved login was found."
    echo "  [1] Use saved login"
    echo "  [2] Log in again  (replaces saved)"
    echo "  [3] Continue without login"
    echo
    read -rp "  Choice (1/2/3) [1]: " LOGIN_CHOICE
    LOGIN_CHOICE="${LOGIN_CHOICE:-1}"
else
    echo "  [1] Log in"
    echo "  [2] Continue without login"
    echo
    read -rp "  Choice (1/2) [2]: " LOGIN_CHOICE_RAW
    LOGIN_CHOICE_RAW="${LOGIN_CHOICE_RAW:-2}"
    # Remap so the rest of the logic is consistent
    if [ "$LOGIN_CHOICE_RAW" = "1" ]; then
        LOGIN_CHOICE="2"   # treat as "fresh login" branch
    else
        LOGIN_CHOICE="3"   # no login
    fi
fi

do_fresh_login() {
    echo
    echo "  How to get your cookie string:"
    echo "  1. Open e-hentai.org in your browser and log in"
    echo "  2. Press F12 to open DevTools, go to the Console tab"
    echo "  3. Type:  document.cookie  and press Enter"
    echo "  4. Copy the full output and paste it below"
    echo
    read -rp "  Paste cookie string: " COOKIE_STR
    COOKIES_ARG="--cookies \"$COOKIE_STR\""
    echo "$COOKIE_STR" > cookies.txt
    echo "  [+] Login saved to cookies.txt"
    echo
    ask_hires
}

case "$LOGIN_CHOICE" in
    1)
        SAVED_COOKIES="$(cat cookies.txt)"
        COOKIES_ARG="--cookies \"$SAVED_COOKIES\""
        echo "  [+] Using saved login."
        echo
        ask_hires
        ;;
    2)
        do_fresh_login
        ;;
    3)
        # no login
        ;;
    *)
        echo "[!] Invalid choice — continuing without login."
        ;;
esac

# -----------------------------------------------
# Download loop
# -----------------------------------------------
download_loop() {
    while true; do
        echo
        read -rp "Download from a URL list file? (y/n): " BATCH_MODE
        BATCH_MODE="${BATCH_MODE,,}"

        URL_ARG=""
        BATCH_ARG=""

        if [ "$BATCH_MODE" = "y" ]; then
            echo "  Create a .txt file with one gallery URL per line."
            echo "  Lines starting with # are treated as comments and ignored."
            echo
            read -rp "  Path to file: " BATCH_FILE
            BATCH_ARG="--batch \"$BATCH_FILE\""
        else
            echo
            read -rp "Gallery URL: " GALLERY_URL
            if [ -z "$GALLERY_URL" ]; then
                echo "[!] No URL entered."
                continue
            fi
            URL_ARG="\"$GALLERY_URL\""
        fi

        echo
        echo "[*] Starting download..."
        echo

        # eval lets quoted args with spaces pass correctly to python
        eval python3 downloader.py $URL_ARG $BATCH_ARG $COOKIES_ARG $HIRES_ARG

        echo
        read -rp "Download another gallery? (y/n): " AGAIN
        AGAIN="${AGAIN,,}"
        if [ "$AGAIN" != "y" ]; then
            break
        fi
    done
}

download_loop

echo
echo "Bye!"
sleep 2
