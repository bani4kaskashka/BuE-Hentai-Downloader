# BuE-Hentai Downloader — Project Guide

Gallery image downloader for e-hentai.org. Written in Python 3.10+.
No web framework, no database — pure CLI tool.

---

## File map

```
downloader.py   Entry point, CLI parsing, orchestration, download loop
session.py      HTTP session factory, cookie parsing, retry logic
scraper.py      HTML parsing — gallery index pages and image viewer pages
run.sh          Interactive launcher for Linux / macOS (bash, ANSI styled)
run.ps1         Interactive launcher for Windows (PowerShell, color styled)
run.bat         Two-line wrapper — calls: powershell ... run.ps1
requirements.txt  requests, beautifulsoup4, tqdm
config.json     Optional local config (gitignored, user-created)
cookies.txt     Saved login cookie string (gitignored, written by launchers)
```

---

## Download pipeline

```
run.sh / run.ps1
    -> python3 downloader.py <url> [flags]
        -> main() parses args + config.json
        -> download_gallery()
            -> scraper.fetch_gallery()      # walks all gallery pages, collects viewer URLs
            -> ThreadPoolExecutor           # DEFAULT_WORKERS = 3 concurrent threads
                -> process_page(task)       # one task per image
                    -> scraper.fetch_image_url()   # resolves viewer page -> direct image URL
                    -> download_file()             # streams to .tmp, renames on success
```

---

## Module responsibilities

### session.py
- `make_session(member_id, pass_hash, cookie_str)` — builds a `requests.Session` with cookies
- `get_thread_session(cookie_kwargs)` — returns a per-thread session (uses `threading.local`)
- `fetch_with_retry(session, url, retries, stream)` — handles 429 rate-limiting and HTTP errors with exponential backoff
- `parse_cookie_string(s)` — splits the raw browser `document.cookie` string into a dict

### scraper.py
- `fetch_gallery(session, gallery_url)` — paginates through the gallery index, collects all `/s/` viewer URLs, returns `(title, [viewer_urls])`
- `fetch_image_url(session, viewer_url, hires)` — parses a viewer page; hi-res path looks for `div#i7 > a`, standard path looks for `img#img`, then falls back to `div#i3` / `div#i1`
- `detect_page_issue(text)` — checks for ban / login-wall markers in page text; called before parsing on every page

### downloader.py
- `download_gallery(...)` — main orchestration; creates output folder `downloads/<sanitized title>/`, distributes work to thread pool, collects stats, writes `failed.txt` if any errors
- `process_page(task)` — runs in worker threads; skips if file already exists (resume support)
- `download_file(session, img_url, dest)` — streams to `<dest>.tmp`, validates size > 1 KB, renames to final path
- `load_config(path)` — loads `config.json` if present; all values become argparse defaults
- `load_failed(folder)` / `save_failed(...)` — reads and writes `failed.txt` inside a gallery folder for `--retry-failed`

---

## CLI flags (downloader.py)

| Flag | Default | Notes |
|---|---|---|
| `urls` (positional) | - | One or more gallery URLs |
| `--batch FILE` | - | .txt file, one URL per line, `#` = comment |
| `--retry-failed FOLDER` | - | Retry from `failed.txt` in that folder |
| `--output / -o` | `./downloads` | Output root directory |
| `--delay` | `1.0` | Seconds between requests per worker |
| `--workers` | `3` | Concurrent download threads |
| `--retries` | `3` | Per-request retry attempts |
| `--cookies` | - | Full `document.cookie` string |
| `--member-id` | - | `ipb_member_id` value (alternative to --cookies) |
| `--pass-hash` | - | `ipb_pass_hash` value (alternative to --cookies) |
| `--hires` | false | Download original resolution (requires login + GP) |
| `--log-file` | - | Append log output to a file |

---

## Auth system

Cookies are passed in one of two ways:
1. Full cookie string (`--cookies "ipb_member_id=123; ipb_pass_hash=abc; ..."`) — parsed by `parse_cookie_string()` and set on the session for `.e-hentai.org`
2. Explicit values (`--member-id` + `--pass-hash`) — set directly as named cookies

The launchers save/load the cookie string to `cookies.txt` (gitignored). `--hires` requires a logged-in session.

---

## Config file (config.json)

All CLI flags except URLs can have defaults set in `config.json`:
```json
{
  "output": "./downloads",
  "delay": 1.0,
  "workers": 3,
  "retries": 3,
  "hires": false,
  "log_file": null,
  "cookies": null,
  "member_id": null,
  "pass_hash": null
}
```
`config.json` is gitignored — it is a user-local file.

---

## Launcher architecture

Both launchers share the same visual language:
- `╭─╮` box header
- `◆ Section` in cyan for section headers
- `› Prompt [default]` in yellow for every user input
- `✓` green / `·` dim / `!` yellow / `✗` red for status messages

**run.sh** (bash): uses ANSI escape codes, bash arrays for the python command (no `eval`), `set -euo pipefail`.

**run.ps1** (PowerShell): uses `Write-Host -ForegroundColor`, `[Console]::ReadLine()` for clean prompts (avoids Read-Host's `: ` suffix), `$script:` scope for variables modified inside helper functions. Calls `.venv\Scripts\python.exe` and `.venv\Scripts\pip.exe` directly instead of activating the venv.

**run.bat**: two lines — just calls `powershell -NoProfile -ExecutionPolicy Bypass -File run.ps1`.

---

## Key constants (downloader.py)

```python
MIN_FILE_SIZE = 1024   # bytes — files smaller than this are treated as error pages
DEFAULT_WORKERS = 3
DEFAULT_DELAY = 1.0    # seconds
DEFAULT_RETRIES = 3    # also defined in session.py
```

---

## Things to be aware of

- `process_page` skips a file if **any** file matching `<base>.*` already exists in the folder — this is the resume mechanism.
- `download_file` always writes to a `.tmp` file first and only renames on success + size check. Partial files never litter the output folder.
- The thread pool shares `cookie_kwargs` (a plain dict) across threads; each thread gets its own `requests.Session` via `threading.local` in `get_thread_session`.
- `tqdm.write()` is used instead of `print()` or `log.*` inside threaded code to avoid breaking the progress bar.
- Gallery pagination: `scraper.fetch_gallery` follows the `>` link in the `table.ptt` pager until there are no more pages.
- Hi-res images are behind a link in `div#i7` on the viewer page; they cost GP on the user's account.
