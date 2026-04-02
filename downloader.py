import argparse
import re
import time
from pathlib import Path
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup
from tqdm import tqdm

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    )
}


def sanitize_name(name: str) -> str:
    return re.sub(r'[<>:"/\\|?*]', "_", name).strip()


def make_session(member_id: str = None, pass_hash: str = None) -> requests.Session:
    session = requests.Session()
    if member_id and pass_hash:
        session.cookies.set("ipb_member_id", member_id, domain=".e-hentai.org")
        session.cookies.set("ipb_pass_hash", pass_hash, domain=".e-hentai.org")
    return session


def fetch_gallery(session: requests.Session, gallery_url: str):
    viewer_urls = []
    title = None
    url = gallery_url

    while url:
        resp = session.get(url, headers=HEADERS, timeout=30)
        resp.raise_for_status()
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


def fetch_image_url(session: requests.Session, viewer_url: str, hires: bool = False) -> str | None:
    resp = session.get(viewer_url, headers=HEADERS, timeout=30)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    if hires:
        original_div = soup.find("div", id="i7")
        if original_div:
            a = original_div.find("a", href=True)
            if a:
                return a["href"]

    img = soup.find("img", id="img")
    if img and img.get("src"):
        return img["src"]
    return None


def download_image(session: requests.Session, img_url: str, dest: Path) -> None:
    resp = session.get(img_url, headers=HEADERS, stream=True, timeout=60)
    resp.raise_for_status()
    with open(dest, "wb") as f:
        for chunk in resp.iter_content(chunk_size=8192):
            f.write(chunk)


def main():
    parser = argparse.ArgumentParser(description="Download an e-hentai gallery.")
    parser.add_argument("url", help="Gallery URL")
    parser.add_argument("--output", "-o", default="./downloads")
    parser.add_argument("--delay", type=float, default=1.0)
    parser.add_argument("--member-id", default=None, help="ipb_member_id cookie value")
    parser.add_argument("--pass-hash", default=None, help="ipb_pass_hash cookie value")
    parser.add_argument("--hires", action="store_true", help="Download original resolution (requires login)")
    args = parser.parse_args()

    if args.hires and not (args.member_id and args.pass_hash):
        print("[!] --hires requires --member-id and --pass-hash (login cookies).")
        return

    session = make_session(args.member_id, args.pass_hash)

    print(f"Fetching gallery: {args.url}")
    title, viewer_urls = fetch_gallery(session, args.url)
    total = len(viewer_urls)

    if total == 0:
        print("No images found. Check the URL, or the gallery may require a login.")
        return

    folder = Path(args.output) / sanitize_name(title)
    folder.mkdir(parents=True, exist_ok=True)

    res_label = "original" if args.hires else "standard"
    print(f"Saving {total} images [{res_label}] to: {folder}")

    pad = len(str(total))

    with tqdm(total=total, unit="img") as bar:
        for i, viewer_url in enumerate(viewer_urls, start=1):
            bar.set_description(f"{i}/{total}")
            base = str(i).zfill(pad)

            if list(folder.glob(f"{base}.*")):
                bar.update(1)
                continue

            try:
                img_url = fetch_image_url(session, viewer_url, hires=args.hires)
                if not img_url:
                    tqdm.write(f"  [warn] No image found on page {i}, skipping.")
                    bar.update(1)
                    continue

                ext = Path(urlparse(img_url).path).suffix or ".jpg"
                download_image(session, img_url, folder / f"{base}{ext}")
            except requests.RequestException as e:
                tqdm.write(f"  [error] Page {i}: {e}")

            bar.update(1)
            time.sleep(args.delay)

    print("Done.")


if __name__ == "__main__":
    main()
