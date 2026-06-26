"""YouTube thumbnail = Studio-Ghibli-style AI image (Pollinations.ai, FREE, no key)
   + the topic heading written on top in Hindi. Falls back to a real photo if the
   AI image fails, so a thumbnail is ALWAYS produced."""
import random, urllib.parse, requests
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from config import ROOT
from utils import get_logger
log = get_logger("thumb")
HEAD = {"User-Agent": "ItihaasBot/0.1"}

def _font(size):
    for p in [ROOT / "assets/fonts/NotoSansDevanagari-Bold.ttf",
              Path("/usr/share/fonts/truetype/noto/NotoSansDevanagari-Bold.ttf"),
              Path("/usr/share/fonts/truetype/lohit-devanagari/Lohit-Devanagari.ttf"),
              Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf")]:
        try:
            if Path(p).exists(): return ImageFont.truetype(str(p), size)
        except Exception: pass
    return ImageFont.load_default()

def _ghibli_image(ai_prompt, dest) -> bool:
    """Generate a Ghibli-style image via Pollinations (free, no key)."""
    prompt = ("Studio Ghibli style anime illustration, " + (ai_prompt or "epic historical scene") +
              ", cinematic dramatic lighting, soft hand-painted background, highly detailed, "
              "emotional, epic historical atmosphere, no text, no words, no letters, no captions")
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

def _wrap(draw, text, font, maxw):
    words, lines, cur = (text or "").split(), [], ""
    for w in words:
        if draw.textlength((cur + " " + w).strip(), font=font) < maxw:
            cur = (cur + " " + w).strip()
        else:
            lines.append(cur); cur = w
    if cur: lines.append(cur)
    return lines

def make(heading, ai_prompt, workdir, fallback_bg=None):
    out = workdir / "thumbnail.png"
    raw = workdir / "thumb_raw.png"

    base = None
    if _ghibli_image(ai_prompt, raw):
        try:
            base = Image.open(raw).convert("RGB").resize((1280, 720))
            log.info("ghibli AI thumbnail generated")
        except Exception:
            base = None
    if base is None and fallback_bg:
        try:
            base = Image.open(fallback_bg).convert("RGB").resize((1280, 720))
            log.info("thumbnail using fallback photo")
        except Exception:
            base = None
    if base is None:
        base = Image.new("RGB", (1280, 720), (25, 20, 40))

    draw = ImageDraw.Draw(base, "RGBA")
    # dark scrim at the bottom for text readability
    draw.rectangle([0, 455, 1280, 720], fill=(0, 0, 0, 150))

    # heading: wrap + auto-shrink so it fits in <=3 lines
    font = _font(82)
    lines = _wrap(draw, heading, font, 1180)
    while len(lines) > 3 and font.size > 46:
        font = _font(font.size - 8)
        lines = _wrap(draw, heading, font, 1180)

    y = 700 - len(lines) * (font.size + 12)
    for ln in lines:
        x = 50
        for dx in (-3, 0, 3):                 # black outline
            for dy in (-3, 0, 3):
                draw.text((x + dx, y + dy), ln, font=font, fill=(0, 0, 0, 255))
        draw.text((x, y), ln, font=font, fill=(255, 221, 0, 255))  # golden text
        y += font.size + 12

    base.convert("RGB").save(out)
    log.info("thumbnail -> %s", out)
    return out
