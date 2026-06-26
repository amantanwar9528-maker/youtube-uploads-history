"""RUN ON YOUR PC (not the cloud). Posts the ad-reels that the cloud queued
in reels_to_post/ to Instagram via your username/password.

One-time on PC:   pip install instagrapi PyYAML python-dotenv
Then just run:     python src/run_local_instagram.py
It remembers what it already posted (data/posted_reels.json)."""
import time
from pathlib import Path
from config import ROOT, SECRETS
from utils import get_logger, load_json, save_json
import instagram_poster

log = get_logger("ig-local")
OUTBOX = ROOT / "reels_to_post"
LEDGER = ROOT / "data" / "posted_reels.json"

def main():
    if not SECRETS["IG_USERNAME"] or not SECRETS["IG_PASSWORD"]:
        log.error("Add IG_USERNAME and IG_PASSWORD to your local .env first."); return
    posted = load_json(LEDGER, {"posted": []})
    done = set(posted["posted"])
    todo = [r for r in sorted(OUTBOX.glob("*.mp4")) if r.stem not in done]
    if not todo:
        log.info("No new reels to post. (Pull latest from GitHub Desktop first.)"); return
    log.info("%d new reel(s) to post", len(todo))
    for reel in todo:
        cap = reel.with_suffix(".txt")
        caption = cap.read_text(encoding="utf-8") if cap.exists() else ""
        try:
            instagram_poster.post_reel(reel, caption)
            posted["posted"].append(reel.stem); save_json(LEDGER, posted)
            log.info("done: %s", reel.name)
            time.sleep(40)   # gentle spacing so Instagram doesn't flag bursts
        except Exception as e:
            log.error("could not post %s: %s", reel.name, e)

if __name__ == "__main__":
    main()
