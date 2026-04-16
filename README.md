# BuE-Hentai Downloader

Downloads galleries from e-hentai as images. Useful if torrents aren't an option.

**Features:**
- Supports both public and logged-in downloads
- Original resolution downloads (requires account with GP)
- Concurrent downloads (3 images at a time by default)
- Per-thread sessions (no shared state between workers)
- Automatic retries with backoff on every request
- Validates downloads to catch corrupt/incomplete files
- Detects rate limiting, bans, and login walls explicitly
- Fallback image selectors if the primary one fails
- Live progress bar with ok/failed/skip counts
- Batch mode - download a whole list of galleries from a text file
- Retry failed pages only, without re-downloading everything
- Skips already downloaded files so interrupted downloads can be resumed
- Saves login cookies locally so you only have to paste them once
- Optional config file to save your preferred settings

---

## Getting the project

You will need [Git](https://git-scm.com/downloads) and [Python 3.10+](https://www.python.org/downloads/) installed first.

**Windows** — Press `Win + R`, type `cmd`, hit Enter to open a terminal.

**Linux / macOS** — Open a terminal application (e.g. Terminal, Konsole, iTerm2).

Then run:

```
git clone https://github.com/bani4kaskashka/BuE-Hentai-Downloader.git
cd BuE-Hentai-Downloader
```

That downloads the project to a folder called `BuE-Hentai-Downloader` wherever you ran the command. You only need to do this once.

To get updates later:

```
git pull
```

---

## Requirements

- Python 3.10+

**Linux users:** also make sure `python3-venv` is installed.
On Debian/Ubuntu: `sudo apt install python3-venv`
On Arch/Manjaro: it is included with the `python` package — nothing extra needed.

---

## Setup

**Windows** — Double-click `run.bat`. On first run it creates a virtual environment and installs all dependencies automatically.

**Linux / macOS** — Run `./run.sh` from a terminal inside the project folder:

```bash
cd BuE-Hentai-Downloader
./run.sh
```

On first run it creates a virtual environment and installs all dependencies automatically. If you get a "Permission denied" error, make the script executable first:

```bash
chmod +x run.sh
./run.sh
```

---

## Usage

Run `run.bat` (Windows) or `./run.sh` (Linux / macOS) and follow the prompts:

1. **Login** - choose whether to use your account or not
2. **Cookie string** - if logging in, paste your cookie string from the browser console (see below)
3. **Original resolution** - only available when logged in, downloads the full uncompressed originals
4. **Batch mode** - download multiple galleries from a text file, or just paste a single URL

Images are saved to `downloads/<gallery title>/` inside the project folder, numbered `001.jpg`, `002.jpg`, etc.

### Saved login

The first time you log in, your cookie string is saved to `cookies.txt` in the project folder. On the next run, `run.bat` / `run.sh` will detect it and offer:

```
[1] Use saved login
[2] Log in again (replaces saved)
[3] Continue without login
```

Cookies stay valid for roughly 30 days. When they expire and downloads start failing, pick "Log in again" to refresh them.

`cookies.txt` is listed in `.gitignore` and will never be pushed to the repo.

### Getting your cookie string

1. Open e-hentai.org in your browser and log in
2. Press `F12` to open DevTools and go to the **Console** tab
3. Type `document.cookie` and press Enter
4. Copy the full output and paste it into the prompt

### Batch downloads

Create a plain text file with one gallery URL per line:

```
https://e-hentai.org/g/XXXXX/XXXXXXXXXX/
https://e-hentai.org/g/YYYYY/YYYYYYYYYY/
# this line is a comment and will be ignored
https://e-hentai.org/g/ZZZZZ/ZZZZZZZZZZ/
```

Then choose "y" when `run.bat` / `run.sh` asks about URL list mode and point it to that file.

### Retrying failed pages

If some pages fail during a download, a `failed.txt` file is saved inside the gallery folder. To retry just those pages without re-downloading everything:

```
python downloader.py --retry-failed "downloads/Gallery Title Here"
```

The gallery URL is read automatically from `failed.txt`. You can also override it by passing the URL as an extra argument.

---

## Terminal usage

For more control you can run the script directly:

```
python downloader.py "<gallery url>" [options]

Options:
  --output, -o      Output directory (default: ./downloads)
  --delay           Seconds to wait between requests per worker (default: 1.0)
  --workers         Number of parallel downloads (default: 3)
  --retries         Retry attempts per request (default: 3)
  --cookies         Full cookie string from browser console
  --member-id       ipb_member_id cookie value (alternative to --cookies)
  --pass-hash       ipb_pass_hash cookie value (alternative to --cookies)
  --hires           Download original resolution (requires login)
  --batch           Path to a .txt file with one URL per line
  --retry-failed    Path to a gallery folder to retry failed pages
  --log-file        Save log output to a file
```

Example:

```
python downloader.py "https://e-hentai.org/g/XXXXX/XXXXXXXXXX/" --workers 5 --delay 0.5
```

---

## Config file

If you want persistent settings without typing them every time, create a `config.json` file in the project folder:

```json
{
  "output": "C:/Users/YourName/Pictures/eh-downloads",
  "delay": 1.0,
  "workers": 3,
  "retries": 3,
  "hires": false,
  "log_file": "download.log"
}
```

Any setting in `config.json` becomes your new default. CLI arguments and `run.bat` / `run.sh` prompts still override it.

---

## Project structure

```
downloader.py   main entry point and orchestration
session.py      session creation, cookie handling, HTTP retries
scraper.py      HTML parsing, image URL extraction, page issue detection
run.bat         interactive launcher for Windows
run.sh          interactive launcher for Linux / macOS
```

---

## Notes

- Increasing `--workers` speeds things up but going too high risks getting rate limited
- If you keep getting rate limited, increase `--delay` or reduce `--workers`
- Original resolution downloads cost GP on your e-hentai account
