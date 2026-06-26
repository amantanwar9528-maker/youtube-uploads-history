"""Auto-generate a YouTube thumbnail (1280x720) from a key image + Hindi hook."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from config import ROOT
from utils import get_logger
log = get_logger("thumb")

def _font(size):
    for p in [ROOT / "assets/fonts/NotoSansDevanagari-Bold.ttf",
              Path("/usr/share/fonts/truetype/noto/NotoSansDevanagari-Bold.ttf"),
              Path("/usr/share/fonts/truetype/lohit-devanagari/Lohit-Devanagari.ttf"),
              Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf")]:
        try:
            if Path(p).exists(): return ImageFont.truetype(str(p), size)
        except Exception: pass
    return ImageFont.load_default()

def make(bg_image: Path, text: str, workdir: Path) -> Path:
    out = workdir / "thumbnail.png"
    try:
        img = Image.open(bg_image).convert("RGB").resize((1280, 720))
    except Exception:
        img = Image.new("RGB", (1280, 720), (20, 20, 30))
    img = Image.blend(img, Image.new("RGB", (1280, 720), (0, 0, 0)), 0.35)
    draw = ImageDraw.Draw(img)
    font = _font(86)
    words, lines, cur = (text or "").split(), [], ""
    for w in words:
        if draw.textlength((cur + " " + w).strip(), font=font) < 1140:
            cur = (cur + " " + w).strip()
        else:
            lines.append(cur); cur = w
    if cur: lines.append(cur)
    y = 720 - (len(lines) * 100) - 50
    for ln in lines:
        for dx in (-3, 3):
            for dy in (-3, 3):
                draw.text((60 + dx, y + dy), ln, font=font, fill=(0, 0, 0))
        draw.text((60, y), ln, font=font, fill=(255, 215, 0)); y += 100
    img.save(out)
    log.info("thumbnail -> %s", out)
    return out
