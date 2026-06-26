"""Pick a royalty-free background track (local folder or Pixabay Music)."""
import random, requests
from pathlib import Path
from config import CFG, SECRETS, ROOT
from utils import get_logger

log = get_logger("music")

def get_track(workdir: Path) -> Path | None:
    folder = ROOT / CFG["music"]["folder"]
    folder.mkdir(parents=True, exist_ok=True)
    local = list(folder.glob("*.mp3"))
    if local:
        chosen = random.choice(local)
        log.info("using local music: %s", chosen.name)
        return chosen
    # Pixabay music has no public JSON API key flow that's stable; recommend local files.
    log.warning("No local music in %s — add free CC tracks there (see SETUP_GUIDE).", folder)
    return None
