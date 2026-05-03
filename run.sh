#!/usr/bin/env bash
# run.sh — BuE-Hentai Downloader interactive launcher (Linux / macOS)
set -euo pipefail
cd "$(dirname "$(realpath "$0")")"

# ── ANSI codes ────────────────────────────────────────────────────
R=$'\033[0m'    B=$'\033[1m'    D=$'\033[2m'
GRN=$'\033[32m' YLW=$'\033[33m' CYN=$'\033[36m'
RED=$'\033[31m' WHT=$'\033[97m'

# ── UI primitives ─────────────────────────────────────────────────
header() {
    printf '\n'
    printf "  ${B}${WHT}╭──────────────────────────────────────╮${R}\n"
    printf "  ${B}${WHT}│        BuE-Hentai Downloader         │${R}\n"
    printf "  ${B}${WHT}╰──────────────────────────────────────╯${R}\n"
    printf '\n'
}

section() { printf "\n  ${B}${CYN}◆ %s${R}\n\n" "$1"; }
ok()      { printf "    ${GRN}✓${R} %s\n" "$1"; }
info()    { printf "    ${D}· %s${R}\n" "$1"; }
warn()    { printf "    ${YLW}!${R} %s\n" "$1"; }
err()     { printf "    ${RED}✗${R} %s\n" "$1"; exit 1; }

# ask "Prompt text" VARNAME [default] [hint]
# hint overrides the displayed default label (e.g. "y/N")
ask() {
    local _p="$1" _v="$2" _d="${3-}" _h="${4-}"
    if [[ -n "$_h" ]]; then
        printf "    ${YLW}›${R} %s ${D}(%s)${R} " "$_p" "$_h"
    elif [[ -n "$_d" ]]; then
        printf "    ${YLW}›${R} %s ${D}[%s]${R} " "$_p" "$_d"
    else
        printf "    ${YLW}›${R} %s " "$_p"
    fi
    IFS= read -r "$_v" || true
    local _t="${!_v}"
    _t="${_t#"${_t%%[![:space:]]*}"}"
    _t="${_t%"${_t##*[![:space:]]}"}"
    printf -v "$_v" '%s' "$_t"
    if [[ -z "${!_v}" && -n "$_d" ]]; then
        printf -v "$_v" '%s' "$_d"
    fi
}

# ─────────────────────────────────────────────────────────────────
header

# ── Environment ──────────────────────────────────────────────────
section "Environment"

if [[ ! -f ".venv/bin/activate" ]]; then
    info "Creating virtual environment..."
    if ! python3 -m venv .venv; then
        err "Failed to create venv. Is Python 3 installed?"
    fi
fi

# shellcheck disable=SC1091
source .venv/bin/activate

info "Checking dependencies..."
if ! .venv/bin/python3 -m pip install -q -r requirements.txt; then
    err "Failed to install dependencies."
fi
ok "Environment ready"

# ── Login ────────────────────────────────────────────────────────
section "Login"

COOKIE_STR=""
HIRES=false

ask_hires() {
    ask "Download original resolution? (requires GP)" _hires "n" "y/N"
    case "$_hires" in [yY]) HIRES=true ;; esac
}

do_fresh_login() {
    printf '\n'
    info "How to get your cookie string:"
    printf "      ${D}1. Open e-hentai.org and log in${R}\n"
    printf "      ${D}2. Press F12 and go to the Console tab${R}\n"
    printf "      ${D}3. Type: document.cookie  and press Enter${R}\n"
    printf "      ${D}4. Copy the full output${R}\n"
    printf '\n'
    ask "Paste cookie string:" COOKIE_STR
    printf '%s\n' "$COOKIE_STR" > cookies.txt
    ok "Login saved to cookies.txt"
    ask_hires
}

if [[ -f "cookies.txt" ]]; then
    info "Saved login detected"
    printf '\n'
    printf "      ${D}1${R}  Use saved login\n"
    printf "      ${D}2${R}  Log in again\n"
    printf "      ${D}3${R}  Continue without login\n"
    printf '\n'
    ask "Choice" _login_choice "1"
else
    printf "      ${D}1${R}  Log in\n"
    printf "      ${D}2${R}  Continue without login\n"
    printf '\n'
    ask "Choice" _login_raw "2"
    if [[ "$_login_raw" == "1" ]]; then
        _login_choice="2"
    else
        _login_choice="3"
    fi
fi

case "$_login_choice" in
    1)
        COOKIE_STR="$(cat cookies.txt)"
        ok "Using saved login"
        ask_hires
        ;;
    2) do_fresh_login ;;
    3) info "Continuing without login" ;;
    *) warn "Invalid choice — continuing without login" ;;
esac

# ── Download loop ────────────────────────────────────────────────
while true; do
    section "Download"

    printf "      ${D}1${R}  Single gallery URL\n"
    printf "      ${D}2${R}  Batch file  ${D}(one URL per line)${R}\n"
    printf '\n'
    ask "Mode" _dl_mode "1"

    GALLERY_URL=""
    BATCH_FILE=""

    if [[ "$_dl_mode" == "2" ]]; then
        info "One gallery URL per line. Lines starting with # are ignored."
        printf '\n'
        ask "Path to file:" BATCH_FILE
    else
        ask "Gallery URL:" GALLERY_URL
        if [[ -z "$GALLERY_URL" ]]; then
            warn "No URL entered."
            continue
        fi
    fi

    # Build command array — no eval, no quoting hacks
    cmd=(.venv/bin/python3 downloader.py)
    if [[ -n "$GALLERY_URL" ]]; then cmd+=("$GALLERY_URL"); fi
    if [[ -n "$BATCH_FILE"  ]]; then cmd+=(--batch "$BATCH_FILE"); fi
    if [[ -n "$COOKIE_STR"  ]]; then cmd+=(--cookies "$COOKIE_STR"); fi
    if [[ "$HIRES" == true  ]]; then cmd+=(--hires); fi

    printf '\n'
    info "Starting download..."
    printf '\n'

    "${cmd[@]}" || true

    printf '\n'
    ask "Download another gallery?" _again "n" "y/N"
    case "$_again" in [yY]) ;; *) break ;; esac
done

section "Done"
info "Goodbye."
printf '\n'
