# e-h-downloader

Downloads galleries from e-hentai as images. Useful if torrents aren't an option.

## Requirements

- Python 3.10+

## Setup

Double-click `run.bat`. It handles everything on first run — creates a virtual environment and installs dependencies automatically.

## Usage

Run `run.bat` and follow the prompts:

1. **Login** — choose whether to use your account or not
2. **Cookies** — if logging in, paste your `ipb_member_id` and `ipb_pass_hash` values (see below)
3. **Original resolution** — only available when logged in; downloads the uncompressed originals instead of the viewer-resized versions
4. **Gallery URL** — paste the gallery URL (e.g. `https://e-hentai.org/g/XXXXX/XXXXXXXXXX/`)

Images are saved to `downloads/<gallery title>/` in the script's folder, numbered `001.jpg`, `002.jpg`, etc. Interrupted downloads can be resumed — already downloaded files are skipped.

### Getting your cookies

1. Open e-hentai.org and log in
2. Open DevTools (`F12`) → **Application** → **Cookies** → `https://e-hentai.org`
3. Copy the values for `ipb_member_id` and `ipb_pass_hash`

### Running from the terminal

```
python downloader.py "<gallery url>" [options]

Options:
  --output, -o    Output directory (default: ./downloads)
  --delay         Seconds between requests (default: 1.0)
  --member-id     ipb_member_id cookie value
  --pass-hash     ipb_pass_hash cookie value
  --hires         Download original resolution (requires login)
```
