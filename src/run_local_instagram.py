"""Run on YOUR PC (not the cloud). Finds the newest reel.mp4 in output/ and
posts it to Instagram via username/password. Keeps the YouTube part in CI."""
import json
from pathlib import Path
from config import path
import instagram_poster
from utils import get_logger
log = get_logger("ig-local")

def latest_reel():
    outs = sorted(path("output_dir").glob("*/reel.mp4"), key=lambda p: p.stat().st_mtime)
    return outs[-1] if outs else None

if __name__ == "__main__":
    reel = latest_reel()
    if not reel:
        log.error("No reel.mp4 found in output/. Run the main pipeline first."); raise SystemExit(1)
    meta = json.loads((reel.parent / "meta.json").read_text(encoding="utf-8"))
    instagram_poster.post_reel(reel, meta.get("reel_hook", ""), "")
