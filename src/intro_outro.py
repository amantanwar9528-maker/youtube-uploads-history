"""Fixed branded INTRO + OUTRO (same in EVERY video).
- Intro: faster Hindi voice + your uploaded intro music + channel banner.
- Outro: like/subscribe/bell message + soft slowed music + banner.
Lines are stored in Devanagari so the Hindi voice pronounces them naturally
(they are the exact Hinglish lines you gave, just written for correct speech)."""
import subprocess
from pathlib import Path
from config import CFG, ROOT
from utils import get_logger, run
import voiceover

log = get_logger("introoutro")
W, H, FPS = 1920, 1080, 30

INTRO_TEXT = (
    "हर दीवार के पीछे एक कहानी छुपी है। हर तलवार ने इतिहास बदला है। "
    "और हर साम्राज्य ने अपनी एक अलग पहचान छोड़ी है। "
    "स्वागत है आपका... इतिहास में! "
    "यहाँ हम लेकर आते हैं हिस्ट्री के वो राज़, लेजेंड्स और अनटोल्ड स्टोरीज़, "
    "जो हर किसी को नहीं पता। "
    "तो चलिए, वक़्त के सफ़र पर चलते हैं।"
)
OUTRO_TEXT = (
    "अगर आज का सफ़र पसंद आया हो, तो वीडियो को लाइक करें, चैनल को सब्सक्राइब करें "
    "और बेल आइकन ज़रूर दबाएँ, ताकि इतिहास की हर नई कहानी सबसे पहले आप तक पहुँच सके। "
    "मिलते हैं अगले एपिसोड में, एक और नए इतिहास के पन्ने के साथ। "
    "तब तक के लिए... जय हिन्द, और जुड़े रहिए... इतिहास के साथ!"
)

def _dur(p):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                          "-of", "default=nk=1:nw=1", str(p)],
                         capture_output=True, text=True).stdout.strip()
    try: return float(out)
    except: return 0.0

def _title_card(dest):
    from PIL import Image, ImageDraw, ImageFont
    img = Image.new("RGB", (W, H), (12, 10, 16)); d = ImageDraw.Draw(img)
    f = None
    for fp in [ROOT / "assets/fonts/NotoSansDevanagari-Bold.ttf",
               Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf")]:
        try:
            if Path(fp).exists(): f = ImageFont.truetype(str(fp), 190); break
        except Exception: pass
    if f is None: f = ImageFont.load_default()
    t = "ITIHAAS"; w = d.textlength(t, font=f)
    for dx in (-4, 0, 4):
        for dy in (-4, 0, 4):
            d.text(((W - w) / 2 + dx, H / 2 - 120 + dy), t, font=f, fill=(0, 0, 0))
    d.text(((W - w) / 2, H / 2 - 120), t, font=f, fill=(255, 200, 0))
    img.save(dest); return dest

def _bg_image(workdir):
    for p in [ROOT / "assets/branding/banner.png", ROOT / "assets/branding/banner.jpg"]:
        if p.exists(): return p
    card = workdir / "_titlecard.png"
    return _title_card(card)

def _segment(text, music, workdir, name, rate, music_db, tempo=1.0):
    voice = workdir / f"{name}_voice.mp3"
    voiceover.synth_text(text, voice, rate=rate)
    dur = max(3.0, _dur(voice)) + 0.6
    bg = _bg_image(workdir)
    silent = workdir / f"{name}_silent.mp4"
    vf = (f"scale={W*2}:-1,zoompan=z='min(zoom+0.0004,1.06)':d={int(dur*FPS)}:"
          f"x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s={W}x{H}:fps={FPS},format=yuv420p")
    run(["ffmpeg", "-y", "-loop", "1", "-i", str(bg), "-t", f"{dur:.2f}", "-vf", vf,
         "-r", str(FPS), "-c:v", "libx264", "-preset", "veryfast", "-pix_fmt", "yuv420p",
         str(silent)], log)
    out = workdir / f"{name}.mp4"
    cmd = ["ffmpeg", "-y", "-i", str(silent), "-i", str(voice)]
    if music and Path(music).exists():
        cmd += ["-stream_loop", "-1", "-i", str(music)]
        af = (f"atempo={tempo}," if tempo != 1.0 else "") + f"volume={music_db}dB"
        filt = f"[2:a]{af}[m];[1:a][m]amix=inputs=2:duration=first:dropout_transition=2[a]"
        cmd += ["-filter_complex", filt, "-map", "0:v", "-map", "[a]"]
    else:
        cmd += ["-map", "0:v", "-map", "1:a"]
    cmd += ["-c:v", "libx264", "-preset", "veryfast", "-crf", "23",
            "-c:a", "aac", "-b:a", "192k", "-ar", "44100", "-ac", "2", "-shortest", str(out)]
    run(cmd, log)
    log.info("%s segment -> %s (%.1fs)", name, out, dur)
    return out

def build_intro(workdir):
    music = ROOT / "assets/branding/intro_music.mp3"
    rate = CFG.get("intro", {}).get("voice_rate", "+18%")
    return _segment(INTRO_TEXT, music, workdir, "intro", rate, -5)

def build_outro(workdir):
    music = ROOT / "assets/branding/intro_music.mp3"
    return _segment(OUTRO_TEXT, music, workdir, "outro", "+0%", -16, tempo=0.85)

def assemble(intro, main, outro, out):
    """Concat intro + main + outro into one video (audio/video normalized)."""
    parts = [intro, main, outro]
    cmd = ["ffmpeg", "-y"]
    for p in parts:
        cmd += ["-i", str(p)]
    fc = ""
    for i in range(len(parts)):
        fc += (f"[{i}:v]scale={W}:{H}:force_original_aspect_ratio=decrease,"
               f"pad={W}:{H}:(ow-iw)/2:(oh-ih)/2,setsar=1,fps={FPS}[v{i}];"
               f"[{i}:a]aresample=44100,aformat=sample_fmts=fltp:channel_layouts=stereo[a{i}];")
    fc += "".join(f"[v{i}][a{i}]" for i in range(len(parts))) + f"concat=n={len(parts)}:v=1:a=1[v][a]"
    cmd += ["-filter_complex", fc, "-map", "[v]", "-map", "[a]",
            "-c:v", "libx264", "-preset", "veryfast", "-crf", "23",
            "-c:a", "aac", "-b:a", "192k", str(out)]
    run(cmd, log)
    log.info("assembled intro+main+outro -> %s", out)
    return out
