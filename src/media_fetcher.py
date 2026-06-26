"""Fetch free images + stock video for each scene keyword.
Sources: Wikimedia Commons & Openverse (no key) + Pexels (free key)."""
import requests, random, time
from pathlib import Path
from config import CFG, SECRETS
from utils import get_logger, slugify

log = get_logger("media")
HEAD = {"User-Agent": "ItihaasBot/0.1 (educational history channel)"}

def _save(url, dest):
    try:
        r = requests.get(url, headers=HEAD, timeout=30)
        if r.ok and len(r.content) > 8000:
            dest.write_bytes(r.content); return True
    except Exception as e:
        log.warning("dl fail %s: %s", url, e)
    return False

def _wikimedia_images(q, n):
    url = ("https://commons.wikimedia.org/w/api.php?action=query&generator=search"
           f"&gsrnamespace=6&gsrsearch={requests.utils.quote(q)}&gsrlimit={n}"
           "&prop=imageinfo&iiprop=url&iiurlwidth=1600&format=json")
    out = []
    try:
        data = requests.get(url, headers=HEAD, timeout=30).json()
        for p in data.get("query", {}).get("pages", {}).values():
            info = p.get("imageinfo", [{}])[0]
            link = info.get("thumburl") or info.get("url")
            if link and link.lower().endswith((".jpg", ".jpeg", ".png")):
                out.append(link)
    except Exception as e:
        log.warning("wikimedia: %s", e)
    return out

def _openverse_images(q, n):
    """Openverse — huge free CC image search, NO API key needed."""
    url = "https://api.openverse.org/v1/images/"
    out = []
    try:
        r = requests.get(url, headers=HEAD,
                         params={"q": q, "page_size": max(3, n), "mature": "false"},
                         timeout=30).json()
        for item in r.get("results", []):
            link = item.get("url")
            if link:
                out.append(link)
    except Exception as e:
        log.warning("openverse: %s", e)
    return out

def _pexels(q, n, kind="photos"):
    key = SECRETS["PEXELS_API_KEY"]
    if not key: return []
    base = "https://api.pexels.com/v1/search" if kind == "photos" else "https://api.pexels.com/videos/search"
    try:
        r = requests.get(base, headers={"Authorization": key},
                         params={"query": q, "per_page": n, "orientation": "landscape"}, timeout=30).json()
        if kind == "photos":
            return [p["src"]["large2x"] for p in r.get("photos", [])]
        vids = []
        for v in r.get("videos", []):
            files = sorted(v["video_files"], key=lambda f: f.get("width") or 0, reverse=True)
            if files: vids.append(files[0]["link"])
        return vids
    except Exception as e:
        log.warning("pexels: %s", e); return []

def fetch_for_scenes(scenes, workdir: Path, per_minute=6, video_ratio=0.35):
    media_dir = workdir / "media"; media_dir.mkdir(parents=True, exist_ok=True)
    assets = []  # list of dicts {type, path, keyword}
    for idx, kw in enumerate(scenes):
        want_video = random.random() < video_ratio
        got = None
        if want_video:
            for src in _pexels(kw, 3, "videos"):
                dest = media_dir / f"{idx:03d}_{slugify(kw)}.mp4"
                if _save(src, dest): got = {"type": "video", "path": dest, "keyword": kw}; break
        if not got:
            # Wikimedia (best for history, unlimited) -> Openverse (no key) -> Pexels
            pool = _wikimedia_images(kw, 5) + _openverse_images(kw, 4) + _pexels(kw, 2)
            for src in pool:
                dest = media_dir / f"{idx:03d}_{slugify(kw)}.jpg"
                if _save(src, dest): got = {"type": "image", "path": dest, "keyword": kw}; break
        if got:
            assets.append(got)
        else:
            log.warning("no media for scene '%s'", kw)
        time.sleep(0.3)  # be polite to free APIs
    log.info("fetched %d assets for %d scenes", len(assets), len(scenes))
    return assets
