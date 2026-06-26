"""Post the teaser reel to Instagram using username/password (instagrapi).
RUN THIS LOCALLY (run_local_instagram.py) — cloud/datacenter IPs get banned.
Reuses a saved session file to avoid repeated logins/challenges."""
from pathlib import Path
from config import SECRETS, ROOT
from utils import get_logger
log = get_logger("instagram")

SESSION = ROOT / "ig_settings.json"

def _client():
    from instagrapi import Client
    cl = Client()
    if SESSION.exists():
        cl.load_settings(SESSION)
    cl.login(SECRETS["IG_USERNAME"], SECRETS["IG_PASSWORD"])
    cl.dump_settings(SESSION)
    return cl

def post_reel(reel: Path, caption: str, youtube_url: str = ""):
    if not SECRETS["IG_USERNAME"]:
        log.warning("IG creds missing — skipping reel post"); return None
    cap = f"{caption}\n\nPoori kahani YouTube par 👉 (link in bio)\n#history #itihaas #reels #truestory"
    cl = _client()
    media = cl.clip_upload(reel, caption=cap)
    log.info("posted reel: %s", getattr(media, "code", "ok"))
    return media
