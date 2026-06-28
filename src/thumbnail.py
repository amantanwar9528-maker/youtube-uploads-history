"""YouTube thumbnail = Studio-Ghibli-style AI image (Pollinations.ai, FREE, no key).
NO text/title on the thumbnail — just a beautiful, scroll-stopping illustration.
Falls back to a real photo if the AI image fails, so a thumbnail always exists."""
import random, urllib.parse, requests
from pathlib import Path
from PIL import Image
from config import ROOT
from utils import get_logger
log = get_logger("thumb")
HEAD = {"User-Agent": "ItihaasBot/0.1"}

# Studio Ghibli / anime illustration look (attractive, clickable)
STYLE = ("Studio Ghibli style, anime art, Makoto Shinkai style, beautiful detailed "
         "illustration, soft warm cinematic lighting, vibrant glowing colors, dramatic "
         "atmosphere, highly detailed, scenic, emotional, masterpiece, trending on artstation, "
         "no text, no words, no letters, no watermark")

def _ai_image(ai_prompt, dest) -> bool:
    prompt = (ai_prompt or "epic historical scene") + ", " + STYLE
    url = ("https://image.pollinations.ai/prompt/" + urllib.parse.quote(prompt) +
           "?width=1280&height=720&nologo=true&model=flux&seed=" + str(random.randint(1, 999999)))
    for attempt in range(2):
        try:
            r = requests.get(url, headers=HEAD, timeout=120)
            if r.ok and len(r.content) > 15000:
                dest.write_bytes(r.content); return True
            log.warning("pollinations status %s len %s", r.status_code, len(r.content))
        except Exception as e:
            log.warning("pollinations try %d: %s", attempt + 1, e)
    return False

def make(heading, ai_prompt, workdir, fallback_bg=None):
    # `heading` kept for compatibility but intentionally NOT drawn (no text on thumbnail)
    out = workdir / "thumbnail.png"
    raw = workdir / "thumb_raw.png"
    base = None
    if _ai_image(ai_prompt, raw):
        try:
            base = Image.open(raw).convert("RGB").resize((1280, 720))
            log.info("ghibli AI thumbnail generated (no text)")
        except Exception:
            base = None
    if base is None and fallback_bg:
        try:
            base = Image.open(fallback_bg).convert("RGB").resize((1280, 720))
            log.info("thumbnail using fallback photo")
        except Exception:
            base = None
    if base is None:
        base = Image.new("RGB", (1280, 720), (20, 18, 32))
    base.save(out)
    log.info("thumbnail -> %s", out)
    return out
