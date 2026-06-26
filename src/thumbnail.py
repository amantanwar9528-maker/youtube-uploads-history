"""YouTube thumbnail = realistic, cinematic AI image (Pollinations.ai, FREE, no key)
   + a bold HINGLISH topic heading on top. Falls back to a real photo if the AI
   image fails, so a thumbnail is ALWAYS produced."""
import random, urllib.parse, requests
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from config import ROOT
from utils import get_logger
log = get_logger("thumb")
HEAD = {"User-Agent": "ItihaasBot/0.1"}

# realistic + attractive look (NOT cartoon)
STYLE = ("cinematic photorealistic, ultra realistic, dramatic cinematic lighting, "
         "highly detailed, epic historical movie poster, depth of field, volumetric light, "
         "rich colors, 8k, sharp focus, no text, no words, no letters, no watermark")

def _font(size):
    for p in [ROOT / "assets/fonts/NotoSansDevanagari-Bold.ttf",
              Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"),
              Path("/usr/share/fonts/truetype/noto/NotoSans-Bold.ttf")]:
        try:
            if Path(p).exists(): return ImageFont.truetype(str(p), size)
        except Exception: pass
    return ImageFont.load_default()

def _ghibli_image(ai_prompt, dest) -> bool:
    """Generate a realistic cinematic image via Pollinations (free, no key)."""
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
            log.info("realistic AI thumbnail generated")
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

    # cinematic bottom gradient (transparent -> dark) for text pop
    grad = Image.new("L", (1, 720), 0)
    for yy in range(720):
        grad.putpixel((0, yy), 0 if yy < 360 else int((yy - 360) / 360 * 210))
    alpha = grad.resize((1280, 720))
    shade = Image.new("RGB", (1280, 720), (0, 0, 0))
    base = Image.composite(shade, base, alpha)

    draw = ImageDraw.Draw(base, "RGBA")
    heading = (heading or "").strip().upper()      # bold uppercase = punchy

    font = _font(96)
    lines = _wrap(draw, heading, font, 1180)
    while len(lines) > 2 and font.size > 54:
        font = _font(font.size - 8)
        lines = _wrap(draw, heading, font, 1180)

    y = 690 - len(lines) * (font.size + 14)
    for ln in lines:
        x = 55
        for dx in (-4, -2, 0, 2, 4):               # thick black outline
            for dy in (-4, -2, 0, 2, 4):
                draw.text((x + dx, y + dy), ln, font=font, fill=(0, 0, 0, 255))
        draw.text((x, y), ln, font=font, fill=(255, 210, 0, 255))   # bold golden
        y += font.size + 14

    base.convert("RGB").save(out)
    log.info("thumbnail -> %s", out)
    return out
