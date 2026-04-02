import logging

from bs4 import BeautifulSoup
from tqdm import tqdm

from session import fetch_with_retry, DEFAULT_RETRIES

log = logging.getLogger(__name__)

BAN_MARKERS = [
    "your ip address has been temporarily banned",
    "you have been banned from e-hentai",
]

LOGIN_MARKERS = [
    "you must be logged in to view this page",
    "this gallery requires a login",
    "please sign in",
]


def detect_page_issue(text):
    lower = text.lower()
    for m in BAN_MARKERS:
        if m in lower:
            return "banned"
    for m in LOGIN_MARKERS:
        if m in lower:
            return "login_required"
    return None


def fetch_gallery(session, gallery_url, retries=DEFAULT_RETRIES):
    viewer_urls = []
    title = None
    url = gallery_url

    while url:
        resp = fetch_with_retry(session, url, retries=retries)
        soup = BeautifulSoup(resp.text, "html.parser")

        issue = detect_page_issue(resp.text)
        if issue == "banned":
            raise RuntimeError("Your IP has been temporarily banned.")
        if issue == "login_required":
            raise RuntimeError("This gallery requires a login. Use --cookies to authenticate.")

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
            log.warning("Could not find image grid. The gallery may require login or the page structure changed.")

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

    issue = detect_page_issue(resp.text)
    if issue:
        raise RuntimeError(f"Unexpected page ({issue}): {viewer_url}")

    if hires:
        div = soup.find("div", id="i7")
        if div:
            a = div.find("a", href=True)
            if a and a.get("href"):
                return a["href"]
        tqdm.write("  [warn] Original resolution link not found, falling back to standard.")

    # Primary selector
    img = soup.find("img", id="img")
    if img and img.get("src"):
        return img["src"]

    # Fallback: search known viewer containers for any image
    for container_id in ("i3", "i1"):
        container = soup.find("div", id=container_id)
        if container:
            img = container.find("img", src=True)
            if img:
                log.warning(f"Used fallback image selector for: {viewer_url}")
                return img["src"]

    return None
