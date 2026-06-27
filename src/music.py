"""Topic/mood-based background music — FREE, no API key.
Primary: Openverse Audio API (CC-licensed). Fallback: local assets/music/*.mp3.
The editor loops + ducks the track under the narration automatically."""
import requests, random
from pathlib import Path
from config import CFG, ROOT
from utils import get_logger
log = get_logger("music")
HEAD = {"User-Agent": "ItihaasBot/0.1 (history channel)"}

def _dl_audio(url, dest):
    try:
        r = requests.get(url, headers=HEAD, timeout=60)
        ct = r.headers.get("Content-Type", "").lower()
        ok_type = ("audio" in ct) or url.lower().split("?")[0].endswith((".mp3", ".ogg", ".wav", ".flac"))
        if r.ok and ok_type and len(r.content) > 80000:
            dest.write_bytes(r.content); return True
    except Exception as e:
        log.warning("music dl fail: %s", e)
    return False

def _openverse_audio(mood, workdir):
    """Mood-based CC music via Openverse (no key). e.g. 'epic cinematic instrumental'."""
    try:
        r = requests.get("https://api.openverse.org/v1/audio/", headers=HEAD,
                         params={"q": mood, "category": "music", "page_size": 12},
                         timeout=30)
        if r.status_code != 200 or not r.text.strip():
            return None
        results = r.json().get("results", [])
        random.shuffle(results)
        dest = workdir / "bg_music.mp3"
        for item in results:
            cands = [item.get("url"), item.get("download_url")]
            cands += [a.get("url") for a in (item.get("alt_files") or []) if a.get("url")]
            for u in cands:
                if u and _dl_audio(u, dest):
                    log.info("music from Openverse (%s): %s", mood, item.get("title", "")[:40])
                    return dest
    except Exception as e:
        log.warning("openverse audio: %s", e)
    return None

def _local():
    folder = ROOT / CFG["music"]["folder"]; folder.mkdir(parents=True, exist_ok=True)
    local = list(folder.glob("*.mp3"))
    if local:
        ch = random.choice(local); log.info("music from local: %s", ch.name); return ch
    return None

def get_track(workdir, mood="epic cinematic instrumental"):
    mood = (mood or "epic cinematic").strip() + " instrumental"
    t = _openverse_audio(mood, workdir)
    if t: return t
    log.warning("Openverse music miss -> trying local folder")
    return _local()
