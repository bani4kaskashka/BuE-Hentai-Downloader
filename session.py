import re
import threading
import time

import requests
from tqdm import tqdm

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    )
}

DEFAULT_RETRIES = 3
_local = threading.local()


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


def get_thread_session(cookie_kwargs):
    """Returns a per-thread session, creating one on first access."""
    if not hasattr(_local, "session"):
        _local.session = make_session(**cookie_kwargs)
    return _local.session


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
