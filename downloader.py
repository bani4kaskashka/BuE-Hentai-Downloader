import argparse
import json
import logging
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from threading import Lock
from urllib.parse import urlparse

from tqdm import tqdm

from session import make_session, get_thread_session, fetch_with_retry, DEFAULT_RETRIES
from scraper import fetch_gallery, fetch_image_url

MIN_FILE_SIZE = 1024
DEFAULT_WORKERS = 3
DEFAULT_DELAY = 1.0

log = logging.getLogger(__name__)


def setup_logging(log_file=None):
    fmt = "[%(levelname)s] %(message)s"
    handlers = [logging.StreamHandler()]
    if log_file:
        handlers.append(logging.FileHandler(log_file, encoding="utf-8"))
    logging.basicConfig(level=logging.INFO, format=fmt, handlers=handlers)


def sanitize_name(name):
    return re.sub(r'[<>:"/\\|?*]', "_", name).strip()


def download_file(session, img_url, dest, retries=DEFAULT_RETRIES):
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
    viewer_url, folder, base, hires, retries, delay, cookie_kwargs = task

    if list(folder.glob(f"{base}.*")):
        return viewer_url, "skipped", None

    try:
        session = get_thread_session(cookie_kwargs)
        img_url = fetch_image_url(session, viewer_url, hires=hires, retries=retries)
        if not img_url:
            return viewer_url, "error", "No image URL found on viewer page"
        ext = Path(urlparse(img_url).path).suffix or ".jpg"
        download_file(session, img_url, folder / f"{base}{ext}", retries=retries)
        time.sleep(delay)
        return viewer_url, "ok", None
    except Exception as e:
        return viewer_url, "error", str(e)


def save_failed(folder, failed_viewer_urls, gallery_url):
    path = folder / "failed.txt"
    with open(path, "w", encoding="utf-8") as f:
        f.write(f"# gallery: {gallery_url}\n")
        for url in failed_viewer_urls:
            f.write(url + "\n")
    log.info(f"Saved failed URLs to: {path}")


def load_failed(folder):
    path = Path(folder) / "failed.txt"
    if not path.exists():
        return None, []
    gallery_url = None
    failed = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line.startswith("# gallery:"):
            gallery_url = line.split("# gallery:", 1)[1].strip()
        elif line and not line.startswith("#"):
            failed.append(line)
    return gallery_url, failed


def download_gallery(cookie_kwargs, gallery_url, output, delay, hires, retries, workers, retry_urls=None):
    session = make_session(**cookie_kwargs)

    log.info(f"Fetching: {gallery_url}")
    title, all_viewer_urls = fetch_gallery(session, gallery_url, retries=retries)
    total = len(all_viewer_urls)

    if total == 0:
        log.error("No images found. Check the URL or your login cookies.")
        return

    folder = Path(output) / sanitize_name(title)
    folder.mkdir(parents=True, exist_ok=True)

    pad = len(str(total))

    if retry_urls:
        url_to_idx = {url: i + 1 for i, url in enumerate(all_viewer_urls)}
        work = [(url_to_idx[url], url) for url in retry_urls if url in url_to_idx]
        unmatched = len(retry_urls) - len(work)
        if unmatched:
            log.warning(f"{unmatched} failed URL(s) no longer found in gallery (skipped).")
        if not work:
            log.error("No failed URLs matched the current gallery.")
            return
        log.info(f"Retrying {len(work)} failed page(s).")
    else:
        work = list(enumerate(all_viewer_urls, start=1))

    res_label = "original" if hires else "standard"
    log.info(f"Saving {len(work)} images [{res_label}] to: {folder}")

    tasks = [
        (viewer_url, folder, str(idx).zfill(pad), hires, retries, delay, cookie_kwargs)
        for idx, viewer_url in work
    ]

    stats = {"ok": 0, "skipped": 0, "error": 0}
    failed_viewer_urls = []
    lock = Lock()

    with tqdm(total=len(tasks), unit="img") as bar:
        with ThreadPoolExecutor(max_workers=workers) as pool:
            futures = {pool.submit(process_page, t): t for t in tasks}
            for future in as_completed(futures):
                viewer_url, status, msg = future.result()
                with lock:
                    stats[status] += 1
                    if status == "error":
                        failed_viewer_urls.append(viewer_url)
                        tqdm.write(f"  [error] {msg}")
                    bar.set_postfix(ok=stats["ok"], failed=stats["error"], skip=stats["skipped"])
                    bar.update(1)

    log.info(f"Finished: {stats['ok']} ok, {stats['skipped']} skipped, {stats['error']} failed.")

    if failed_viewer_urls:
        save_failed(folder, failed_viewer_urls, gallery_url)
        log.info(f'To retry: python downloader.py --retry-failed "{folder}"')


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
    parser.add_argument("--retry-failed", metavar="FOLDER", help="Retry failed pages from a previous run (pass the gallery folder path)")
    parser.add_argument("--output", "-o", default=cfg.get("output", "./downloads"))
    parser.add_argument("--delay", type=float, default=cfg.get("delay", DEFAULT_DELAY))
    parser.add_argument("--retries", type=int, default=cfg.get("retries", DEFAULT_RETRIES))
    parser.add_argument("--workers", type=int, default=cfg.get("workers", DEFAULT_WORKERS))
    parser.add_argument("--member-id", default=cfg.get("member_id"))
    parser.add_argument("--pass-hash", default=cfg.get("pass_hash"))
    parser.add_argument("--cookies", default=cfg.get("cookies"))
    parser.add_argument("--hires", action="store_true", default=cfg.get("hires", False))
    parser.add_argument("--log-file", default=cfg.get("log_file"))
    args = parser.parse_args()

    setup_logging(args.log_file)

    if args.hires and not (args.cookies or (args.member_id and args.pass_hash)):
        log.error("--hires requires login cookies.")
        return

    cookie_kwargs = {
        "member_id": args.member_id,
        "pass_hash": args.pass_hash,
        "cookie_str": args.cookies,
    }

    if args.retry_failed:
        gallery_url, failed_urls = load_failed(args.retry_failed)
        if args.urls:
            gallery_url = args.urls[0]
        if not gallery_url:
            log.error("Could not find gallery URL. Ensure failed.txt has a '# gallery:' line or pass the URL as an argument.")
            return
        if not failed_urls:
            log.info("No failed URLs found in failed.txt. Nothing to retry.")
            return
        download_gallery(
            cookie_kwargs=cookie_kwargs,
            gallery_url=gallery_url,
            output=args.output,
            delay=args.delay,
            hires=args.hires,
            retries=args.retries,
            workers=args.workers,
            retry_urls=failed_urls,
        )
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

    for url in gallery_urls:
        download_gallery(
            cookie_kwargs=cookie_kwargs,
            gallery_url=url,
            output=args.output,
            delay=args.delay,
            hires=args.hires,
            retries=args.retries,
            workers=args.workers,
        )


if __name__ == "__main__":
    main()
