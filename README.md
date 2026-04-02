# BuE-Hentai Downloader

Downloads galleries from e-hentai as images. Useful if torrents aren't an option.

**Features:**
- Supports both public and logged-in downloads
- Original resolution downloads (requires account with GP)
- Concurrent downloads (3 images at a time by default)
- Automatic retries on failure with backoff
- Validates downloads to catch corrupt files
- Detects rate limiting and slows down automatically
- Batch mode - download a whole list of galleries from a text file
- Skips already downloaded files so interrupted downloads can be resumed
- Optional config file to save your preferred settings

---

## Getting the project

You will need [Git](https://git-scm.com/downloads) and [Python 3.10+](https://www.python.org/downloads/) installed first.

Open a terminal (press `Win + R`, type `cmd`, hit Enter) and run:

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

---

## Setup

Double-click `run.bat`. On first run it creates a virtual environment and installs all dependencies automatically.

---

## Usage

Run `run.bat` and follow the prompts:

1. **Login** - choose whether to use your account or not
2. **Cookie string** - if logging in, paste your cookie string from the browser console (see below)
3. **Original resolution** - only available when logged in, downloads the full uncompressed originals
4. **Batch mode** - download multiple galleries from a text file, or just paste a single URL

Images are saved to `downloads/<gallery title>/` inside the project folder, numbered `001.jpg`, `002.jpg`, etc.

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

Then choose "y" when `run.bat` asks about URL list mode and point it to that file.

---

## Terminal usage

For more control you can run the script directly:

```
python downloader.py "<gallery url>" [options]

Options:
  --output, -o    Output directory (default: ./downloads)
  --delay         Seconds to wait between requests per worker (default: 1.0)
  --workers       Number of parallel downloads (default: 3)
  --retries       Retry attempts per request (default: 3)
  --cookies       Full cookie string from browser console
  --member-id     ipb_member_id cookie value (alternative to --cookies)
  --pass-hash     ipb_pass_hash cookie value (alternative to --cookies)
  --hires         Download original resolution (requires login)
  --batch         Path to a .txt file with one URL per line
  --log-file      Save log output to a file
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

Any setting in `config.json` becomes your new default. CLI arguments and `run.bat` prompts still override it.

---

## Notes

- Increasing `--workers` speeds things up but be reasonable, going too high risks getting rate limited
- If you keep getting rate limited, increase `--delay` or reduce `--workers`
- Original resolution downloads cost GP on your e-hentai account
