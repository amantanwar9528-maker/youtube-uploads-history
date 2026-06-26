"""Fetch free images + stock video for each scene keyword.
History-first, copyright-safe sources (tried in order, stop at first hit):
  Wikimedia Commons -> Library of Congress -> The Met -> Internet Archive
  -> Openverse -> Pexels.  Video: Pexels.
If a scene finds nothing, a clean placeholder slide is generated so the
video ALWAYS renders."""
import requests, random, time, colorsys
from pathlib import Path
from config import CFG, SECRETS
from utils import get_logger, slugify

log = get_logger("media")
HEAD = {"User-Agent": "ItihaasBot/0.1 (https://github.com/; contact amantanwar9528@gmail.com)"}

def _clean_query(q: str) -> str:
    q = q.split(",")[0].split(".")[0].strip()
    return q[:80]

def _save(url, dest):
    try:
        r = requests.get(url, headers=HEAD, timeout=30)
        if r.ok and len(r.content) > 8000:
            dest.write_bytes(r.content); return True
    except Exception as e:
        log.warning("dl fail %s: %s", str(url)[:60], e)
    return False

# ---------- image sources (each returns a list of image URLs) ----------
def _wikimedia_images(q, n):
    q = _clean_query(q)
    url = ("https://commons.wikimedia.org/w/api.php?action=query&generator=search"
           f"&gsrnamespace=6&gsrsearch={requests.utils.quote(q)}&gsrlimit={n}"
           "&prop=imageinfo&iiprop=url&iiurlwidth=1600&format=json")
    out = []
    try:
        resp = requests.get(url, headers=HEAD, timeout=30)
        if resp.status_code != 200 or not resp.text.strip(): return []
        for p in resp.json().get("query", {}).get("pages", {}).values():
            info = p.get("imageinfo", [{}])[0]
            link = info.get("thumburl") or info.get("url")
            if link and link.lower().endswith((".jpg", ".jpeg", ".png")):
                out.append(link)
    except Exception as e:
        log.warning("wikimedia: %s", e)
    return out

def _loc_images(q, n):
    """Library of Congress — millions of public-domain historical photos."""
    out = []
    try:
        resp = requests.get("https://www.loc.gov/search/", headers=HEAD,
            params={"q": _clean_query(q), "fo": "json", "at": "results",
                    "c": max(5, n)}, timeout=30)
        if resp.status_code != 200 or not resp.text.strip(): return []
        for r in resp.json().get("results", []):
            imgs = r.get("image_url") or []
            if imgs:
                link = imgs[-1]
                if link.startswith("//"): link = "https:" + link
                if link.startswith("http"): out.append(link)
            if len(out) >= n: break
    except Exception as e:
        log.warning("loc: %s", e)
    return out

def _met_images(q, n):
    """The Met Museum Open Access — public-domain paintings/art."""
    out = []
    try:
        s = requests.get("https://collectionapi.metmuseum.org/public/collection/v1/search",
            params={"q": _clean_query(q), "hasImages": "true"}, timeout=30)
        ids = (s.json().get("objectIDs") or [])[:n * 3]
        for oid in ids:
            if len(out) >= n: break
            o = requests.get(
                f"https://collectionapi.metmuseum.org/public/collection/v1/objects/{oid}",
                timeout=30).json()
            if o.get("primaryImage") and o.get("isPublicDomain"):
                out.append(o["primaryImage"])
    except Exception as e:
        log.warning("met: %s", e)
    return out

def _archive_images(q, n):
    """Internet Archive — public-domain historical images."""
    out = []
    try:
        resp = requests.get("https://archive.org/advancedsearch.php", headers=HEAD,
            params={"q": f"{_clean_query(q)} AND mediatype:image",
                    "fl[]": "identifier", "rows": max(5, n), "output": "json"}, timeout=30)
        if resp.status_code != 200 or not resp.text.strip(): return []
        for d in resp.json().get("response", {}).get("docs", []):
            ident = d.get("identifier")
            if ident: out.append(f"https://archive.org/services/img/{ident}")
            if len(out) >= n: break
    except Exception as e:
        log.warning("archive: %s", e)
    return out

def _openverse_images(q, n):
    out = []
    try:
        resp = requests.get("https://api.openverse.org/v1/images/", headers=HEAD,
            params={"q": _clean_query(q), "page_size": max(3, n), "mature": "false"},
            timeout=30)
        if resp.status_code != 200 or not resp.text.strip(): return []
        for item in resp.json().get("results", []):
            if item.get("url"): out.append(item["url"])
    except Exception as e:
        log.warning("openverse: %s", e)
    return out

def _pexels(q, n, kind="photos"):
    key = SECRETS["PEXELS_API_KEY"]
    if not key: return []
    base = "https://api.pexels.com/v1/search" if kind == "photos" else "https://api.pexels.com/videos/search"
    try:
        r = requests.get(base, headers={"Authorization": key},
                         params={"query": _clean_query(q), "per_page": n,
                                 "orientation": "landscape"}, timeout=30).json()
        if kind == "photos":
            return [p["src"]["large2x"] for p in r.get("photos", [])]
        vids = []
        for v in r.get("videos", []):
            files = sorted(v["video_files"], key=lambda f: f.get("width") or 0, reverse=True)
            if files: vids.append(files[0]["link"])
        return vids
    except Exception as e:
        log.warning("pexels: %s", e); return []

# history-first order; stop at first source that yields a downloadable image
IMAGE_SOURCES = [
    ("wikimedia", _wikimedia_images),
    ("loc",       _loc_images),
    ("met",       _met_images),
    ("archive",   _archive_images),
    ("openverse", _openverse_images),
    ("pexels",    lambda kw, n: _pexels(kw, n, "photos")),
]

def _placeholder(kw, dest, idx):
    try:
        from PIL import Image, ImageDraw, ImageFont
        W, H = 1920, 1080
        hue = (idx * 0.11) % 1.0
        col = tuple(int(c * 90) for c in colorsys.hsv_to_rgb(hue, 0.55, 0.9))
        img = Image.new("RGB", (W, H), col)
        d = ImageDraw.Draw(img)
        font = None
        for fp in ["/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
                   "/usr/share/fonts/truetype/noto/NotoSans-Bold.ttf"]:
            try: font = ImageFont.truetype(fp, 56); break
            except Exception: pass
        if font is None: font = ImageFont.load_default()
        words, lines, cur = kw.split(), [], ""
        for w in words:
            if d.textlength((cur + " " + w).strip(), font=font) < 1500:
                cur = (cur + " " + w).strip()
            else:
                lines.append(cur); cur = w
        if cur: lines.append(cur)
        y = H // 2 - len(lines) * 35
        for ln in lines:
            x = (W - d.textlength(ln, font=font)) / 2
            d.text((x, y), ln, font=font, fill=(255, 255, 255)); y += 70
        img.save(dest); return True
    except Exception as e:
        log.warning("placeholder fail: %s", e); return False

def fetch_for_scenes(scenes, workdir: Path, per_minute=6, video_ratio=0.35):
    media_dir = workdir / "media"; media_dir.mkdir(parents=True, exist_ok=True)
    assets, real = [], 0
    for idx, kw in enumerate(scenes):
        got = None
        if random.random() < video_ratio:
            for src in _pexels(kw, 3, "videos"):
                dest = media_dir / f"{idx:03d}_{slugify(kw)}.mp4"
                if _save(src, dest): got = {"type": "video", "path": dest, "keyword": kw}; break
        if not got:
            for name, fn in IMAGE_SOURCES:
                for src in fn(kw, 3):
                    dest = media_dir / f"{idx:03d}_{slugify(kw)}.jpg"
                    if _save(src, dest):
                        got = {"type": "image", "path": dest, "keyword": kw, "src": name}; break
                if got: break
        if got:
            assets.append(got); real += 1
        else:
            ph = media_dir / f"{idx:03d}_placeholder.jpg"
            if _placeholder(kw, ph, idx):
                assets.append({"type": "image", "path": ph, "keyword": kw, "src": "placeholder"})
        time.sleep(0.3)
    log.info("fetched %d real + %d placeholder = %d total for %d scenes",
             real, len(assets) - real, len(assets), len(scenes))
    return assets
