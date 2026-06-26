"""Post a reel to Instagram using username/password (instagrapi).
RUN LOCALLY ONLY — cloud/datacenter IPs get flagged/banned.
A saved session file avoids repeated logins / OTP challenges."""
from pathlib import Path
from config import SECRETS, ROOT
from utils import get_logger
log = get_logger("instagram")

SESSION = ROOT / "ig_settings.json"

def _client():
    from instagrapi import Client
    cl = Client()
    if SESSION.exists():
        try: cl.load_settings(SESSION)
        except Exception: pass
    cl.login(SECRETS["IG_USERNAME"], SECRETS["IG_PASSWORD"])
    cl.dump_settings(SESSION)
    return cl

def post_reel(reel, caption: str = "", youtube_url: str = ""):
    if not SECRETS["IG_USERNAME"] or not SECRETS["IG_PASSWORD"]:
        log.warning("IG creds missing — skipping reel post"); return None
    if not caption:
        caption = "Poori kahani YouTube par! Link in bio.\n#history #itihaas #reels"
    cl = _client()
    media = cl.clip_upload(str(reel), caption=caption)
    log.info("posted reel: %s", getattr(media, "code", "ok"))
    return media
