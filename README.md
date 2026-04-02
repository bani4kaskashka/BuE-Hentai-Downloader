# BuE-Hentai Downloader

Downloads galleries from e-hentai as images. Useful if torrents aren't an option.

## Getting the project

You will need [Git](https://git-scm.com/downloads) and [Python 3.10+](https://www.python.org/downloads/) installed first.

Open a terminal (press `Win + R`, type `cmd`, hit Enter) and run:

```
git clone https://github.com/bani4kaskashka/BuE-Hentai-Downloader.git
cd BuE-Hentai-Downloader
```

That downloads the project to a folder called `BuE-Hentai-Downloader` wherever you ran the command. You only need to do this once.

If the project gets updated later and you want the latest version, open a terminal inside the folder and run:

```
git pull
```

## Requirements

- Python 3.10+

## Setup

Double-click `run.bat`. It handles everything on first run, creates a virtual environment and installs dependencies automatically.

## Usage

Run `run.bat` and follow the prompts:

1. **Login** - choose whether to use your account or not
2. **Cookies** - if logging in, paste your `ipb_member_id` and `ipb_pass_hash` values (see below)
3. **Original resolution** - only available when logged in, downloads the uncompressed originals instead of the viewer-resized versions
4. **Gallery URL** - paste the gallery URL (e.g. `https://e-hentai.org/g/XXXXX/XXXXXXXXXX/`)

Images are saved to `downloads/<gallery title>/` in the script's folder, numbered `001.jpg`, `002.jpg`, etc. Interrupted downloads can be resumed, already downloaded files are skipped.

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
