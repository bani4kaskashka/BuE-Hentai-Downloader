import argparse
import json
import logging
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from threading import Lock
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup
from tqdm import tqdm

MIN_FILE_SIZE = 1024
DEFAULT_RETRIES = 3
DEFAULT_WORKERS = 3
DEFAULT_DELAY = 1.0

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    )
}

log = logging.getLogger(__name__)


def setup_logging(log_file=None):
    fmt = "[%(levelname)s] %(message)s"
    handlers = [logging.StreamHandler()]
    if log_file:
        handlers.append(logging.FileHandler(log_file, encoding="utf-8"))
    logging.basicConfig(level=logging.INFO, format=fmt, handlers=handlers)


def sanitize_name(name):
    return re.sub(r'[<>:"/\\|?*]', "_", name).strip()


def parse_cookie_string(s):
    cookies = {}
    for part in s.split(";"):
        if "=" in part:
            k, v = part.strip().split("=", 1)
            cookies[k.strip()] = v.strip()
    return cookies


def make_session(member_id=None, pass_hash=None, cookie_str=None):
    session = requests.Session()
    if cookie_str:
        for k, v in parse_cookie_string(cookie_str).items():
            session.cookies.set(k, v, domain=".e-hentai.org")
    elif member_id and pass_hash:
        session.cookies.set("ipb_member_id", member_id, domain=".e-hentai.org")
        session.cookies.set("ipb_pass_hash", pass_hash, domain=".e-hentai.org")
    return session


def fetch_with_retry(session, url, retries=DEFAULT_RETRIES, stream=False):
    last_err = None
    for attempt in range(1, retries + 1):
        try:
            resp = session.get(url, headers=HEADERS, stream=stream, timeout=30)
            if resp.status_code == 429:
                wait = 15 * attempt
                tqdm.write(f"  [warn] Rate limited. Waiting {wait}s (attempt {attempt}/{retries})")
                time.sleep(wait)
                continue
            resp.raise_for_status()
            return resp
        except requests.Timeout:
            last_err = f"timed out (attempt {attempt}/{retries})"
        except requests.HTTPError as e:
            last_err = f"HTTP {e.response.status_code} (attempt {attempt}/{retries})"
        except requests.RequestException as e:
            last_err = f"{e} (attempt {attempt}/{retries})"
        if attempt < retries:
            time.sleep(2 ** attempt)
    raise requests.RequestException(last_err)


def fetch_gallery(session, gallery_url, retries=DEFAULT_RETRIES):
    viewer_urls = []
    title = None
    url = gallery_url

    while url:
        resp = fetch_with_retry(session, url, retries=retries)
        soup = BeautifulSoup(resp.text, "html.parser")

        if title is None:
            tag = soup.find("h1", id="gn")
            if tag:
                title = tag.get_text(strip=True)

        gdt = soup.find("div", id="gdt")
        if gdt:
            for a in gdt.find_all("a", href=True):
                if "/s/" in a["href"]:
                    viewer_urls.append(a["href"])
        else:
            log.warning("Could not find image grid — page structure may have changed.")

        next_url = None
        pager = soup.find("table", class_="ptt")
        if pager:
            for td in pager.find_all("td"):
                a = td.find("a")
                if a and a.get_text(strip=True) == ">":
                    next_url = a["href"]
                    break
        url = next_url

    return title or "gallery", viewer_urls


def fetch_image_url(session, viewer_url, hires=False, retries=DEFAULT_RETRIES):
    resp = fetch_with_retry(session, viewer_url, retries=retries)
    soup = BeautifulSoup(resp.text, "html.parser")

    if hires:
        div = soup.find("div", id="i7")
        if div:
            a = div.find("a", href=True)
            if a:
                return a["href"]
        tqdm.write("  [warn] Original resolution link not found, falling back to standard.")

    img = soup.find("img", id="img")
    if img and img.get("src"):
        return img["src"]

    return None


def download_image(session, img_url, dest, retries=DEFAULT_RETRIES):
    resp = fetch_with_retry(session, img_url, retries=retries, stream=True)
    tmp = dest.with_suffix(".tmp")
    try:
        with open(tmp, "wb") as f:
            for chunk in resp.iter_content(chunk_size=8192):
                f.write(chunk)
        size = tmp.stat().st_size
        if size < MIN_FILE_SIZE:
            tmp.unlink()
            raise ValueError(f"File too small ({size} bytes), likely an error page.")
        tmp.rename(dest)
    except Exception:
        if tmp.exists():
            tmp.unlink()
        raise


def process_page(task):
    session, viewer_url, folder, base, hires, retries, delay = task

    if list(folder.glob(f"{base}.*")):
        return base, "skipped", None

    try:
        img_url = fetch_image_url(session, viewer_url, hires=hires, retries=retries)
        if not img_url:
            return base, "error", "No image URL found on viewer page"
        ext = Path(urlparse(img_url).path).suffix or ".jpg"
        download_image(session, img_url, folder / f"{base}{ext}", retries=retries)
        time.sleep(delay)
        return base, "ok", None
    except Exception as e:
        return base, "error", str(e)


def download_gallery(session, gallery_url, output, delay, hires, retries, workers):
    log.info(f"Fetching: {gallery_url}")
    title, viewer_urls = fetch_gallery(session, gallery_url, retries=retries)
    total = len(viewer_urls)

    if total == 0:
        log.error("No images found. Check the URL or your login cookies.")
        return

    folder = Path(output) / sanitize_name(title)
    folder.mkdir(parents=True, exist_ok=True)

    res_label = "original" if hires else "standard"
    log.info(f"Saving {total} images [{res_label}] to: {folder}")

    pad = len(str(total))
    tasks = [
        (session, url, folder, str(i).zfill(pad), hires, retries, delay)
        for i, url in enumerate(viewer_urls, start=1)
    ]

    failed = []
    lock = Lock()

    with tqdm(total=total, unit="img") as bar:
        with ThreadPoolExecutor(max_workers=workers) as pool:
            futures = {pool.submit(process_page, t): t for t in tasks}
            for future in as_completed(futures):
                base, status, msg = future.result()
                with lock:
                    if status == "error":
                        failed.append(base)
                        tqdm.write(f"  [error] page {base}: {msg}")
                    bar.update(1)

    if failed:
        log.warning(f"{len(failed)} page(s) failed: {', '.join(failed)}")
    log.info("Done.")


def load_config(path="config.json"):
    p = Path(path)
    if p.exists():
        with open(p, encoding="utf-8") as f:
            return json.load(f)
    return {}


def main():
    cfg = load_config()

    parser = argparse.ArgumentParser(description="Download e-hentai galleries as images.")
    parser.add_argument("urls", nargs="*", help="One or more gallery URLs")
    parser.add_argument("--batch", help="Path to a .txt file with one gallery URL per line")
    parser.add_argument("--output", "-o", default=cfg.get("output", "./downloads"))
    parser.add_argument("--delay", type=float, default=cfg.get("delay", DEFAULT_DELAY))
    parser.add_argument("--retries", type=int, default=cfg.get("retries", DEFAULT_RETRIES))
    parser.add_argument("--workers", type=int, default=cfg.get("workers", DEFAULT_WORKERS))
    parser.add_argument("--member-id", default=cfg.get("member_id"))
    parser.add_argument("--pass-hash", default=cfg.get("pass_hash"))
    parser.add_argument("--cookies", default=cfg.get("cookies"), help="Full cookie string from browser console")
    parser.add_argument("--hires", action="store_true", default=cfg.get("hires", False))
    parser.add_argument("--log-file", default=cfg.get("log_file"))
    args = parser.parse_args()

    setup_logging(args.log_file)

    if args.hires and not (args.cookies or (args.member_id and args.pass_hash)):
        log.error("--hires requires login cookies.")
        return

    gallery_urls = list(args.urls)

    if args.batch:
        batch_path = Path(args.batch)
        if not batch_path.exists():
            log.error(f"Batch file not found: {args.batch}")
            return
        for line in batch_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#"):
                gallery_urls.append(line)

    if not gallery_urls:
        log.error("No gallery URLs provided.")
        return

    session = make_session(args.member_id, args.pass_hash, args.cookies)

    for url in gallery_urls:
        download_gallery(
            session=session,
            gallery_url=url,
            output=args.output,
            delay=args.delay,
            hires=args.hires,
            retries=args.retries,
            workers=args.workers,
        )


if __name__ == "__main__":
    main()
