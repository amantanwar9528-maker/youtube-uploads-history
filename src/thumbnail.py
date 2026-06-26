"""Auto-generate a YouTube thumbnail (1280x720) from a key image + hook text."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from config import ROOT
from utils import get_logger
log = get_logger("thumb")

FONT = ROOT / "assets" / "fonts" / "NotoSansDevanagari-Bold.ttf"

def make(bg_image: Path, text: str, workdir: Path) -> Path:
    out = workdir / "thumbnail.png"
    try:
        img = Image.open(bg_image).convert("RGB").resize((1280, 720))
    except Exception:
        img = Image.new("RGB", (1280, 720), (20, 20, 30))
    # darken bottom for text contrast
    overlay = Image.new("RGB", (1280, 720), (0, 0, 0))
    img = Image.blend(img, overlay, 0.35)
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype(str(FONT), 86)
    except Exception:
        font = ImageFont.load_default()
    # word-wrap
    words, lines, cur = text.split(), [], ""
    for w in words:
        if draw.textlength(cur + " " + w, font=font) < 1140:
            cur = (cur + " " + w).strip()
        else:
            lines.append(cur); cur = w
    if cur: lines.append(cur)
    y = 720 - (len(lines) * 100) - 50
    for ln in lines:
        x = 60
        # outline
        for dx in (-3, 3):
            for dy in (-3, 3):
                draw.text((x+dx, y+dy), ln, font=font, fill=(0, 0, 0))
        draw.text((x, y), ln, font=font, fill=(255, 215, 0))
        y += 100
    img.save(out)
    log.info("thumbnail -> %s", out)
    return out
