"""Fixed branded INTRO + OUTRO (same in EVERY video).
INTRO = 3 parts (voice spoken in Hindi, on-screen text in ROMAN/English):
  1) intro text card  ->  2) 'Swagat...' line = BANNER  ->  3) intro text card
OUTRO = like/subscribe/bell message + soft slowed music + banner.
Voice text is Devanagari (correct Hindi pronunciation); captions are Roman."""
import subprocess
from pathlib import Path
from config import CFG, ROOT
from utils import get_logger, run
import voiceover

log = get_logger("introoutro")
W, H, FPS = 1920, 1080, 30

# --- spoken (Devanagari) vs shown-on-screen (Roman/English letters) ---
P1_VOICE = ("हर दीवार के पीछे एक कहानी छुपी है। हर तलवार ने इतिहास बदला है। "
            "और हर साम्राज्य ने अपनी एक अलग पहचान छोड़ी है।")
P1_TEXT  = ("Har deewar ke peeche ek kahani chhupi hai...\n"
            "Har talwar ne itihaas badla hai...\n"
            "Aur har samrajya ne apni ek alag pehchaan chhodi hai.")

P2_VOICE = "स्वागत है आपका... इतिहास में!"          # BANNER shows here (no caption)

P3_VOICE = ("यहाँ हम लेकर आते हैं हिस्ट्री के वो राज़, लेजेंड्स और अनटोल्ड स्टोरीज़, "
            "जो हर किसी को नहीं पता। तो चलिए, वक़्त के सफ़र पर चलते हैं।")
P3_TEXT  = ("Yahaan hum lekar aate hain history ke woh raaz, legends aur untold "
            "stories... jo har kisi ko nahi pata.\n"
            "Toh chaliye... waqt ke safar par chalte hain.")

OUTRO_VOICE = (
    "अगर आज का सफ़र पसंद आया हो, तो वीडियो को लाइक करें, चैनल को सब्सक्राइब करें "
    "और बेल आइकन ज़रूर दबाएँ, ताकि इतिहास की हर नई कहानी सबसे पहले आप तक पहुँच सके। "
    "मिलते हैं अगले एपिसोड में, एक और नए इतिहास के पन्ने के साथ। "
    "तब तक के लिए... जय हिन्द, और जुड़े रहिए... इतिहास के साथ!")

def _dur(p):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                          "-of", "default=nk=1:nw=1", str(p)],
                         capture_output=True, text=True).stdout.strip()
    try: return float(out)
    except: return 0.0

def _font(size, latin=True):
    order = ([Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"),
              ROOT / "assets/fonts/NotoSansDevanagari-Bold.ttf"] if latin else
             [ROOT / "assets/fonts/NotoSansDevanagari-Bold.ttf",
              Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf")])
    from PIL import ImageFont
    for fp in order:
        try:
            if Path(fp).exists(): return ImageFont.truetype(str(fp), size)
        except Exception: pass
    return ImageFont.load_default()

def _text_card(text, dest):
    """Dark cinematic background with the intro text centered (Roman letters)."""
    from PIL import Image, ImageDraw
    img = Image.new("RGB", (W, H), (10, 9, 14))
    d = ImageDraw.Draw(img, "RGBA")
    font = _font(66, latin=True)
    lines = []
    for para in text.split("\n"):
        para = para.strip()
        if not para: continue
        words, cur = para.split(), ""
        for w in words:
            if d.textlength((cur + " " + w).strip(), font=font) < 1480:
                cur = (cur + " " + w).strip()
            else:
                lines.append(cur); cur = w
        if cur: lines.append(cur)
    total = len(lines) * (font.size + 22)
    y = (H - total) // 2
    for ln in lines:
        x = (W - d.textlength(ln, font=font)) / 2
        for dx in (-3, 0, 3):
            for dy in (-3, 0, 3):
                d.text((x + dx, y + dy), ln, font=font, fill=(0, 0, 0, 255))
        d.text((x, y), ln, font=font, fill=(255, 214, 120, 255))   # warm gold
        y += font.size + 22
    img.save(dest); return dest

def _title_card(dest):
    from PIL import Image, ImageDraw
    img = Image.new("RGB", (W, H), (12, 10, 16)); d = ImageDraw.Draw(img)
    f = _font(190, latin=True); t = "ITIHAAS"; w = d.textlength(t, font=f)
    for dx in (-4, 0, 4):
        for dy in (-4, 0, 4):
            d.text(((W - w) / 2 + dx, H / 2 - 120 + dy), t, font=f, fill=(0, 0, 0))
    d.text(((W - w) / 2, H / 2 - 120), t, font=f, fill=(255, 200, 0))
    img.save(dest); return dest

def _banner(workdir):
    for p in [ROOT / "assets/branding/banner.png", ROOT / "assets/branding/banner.jpg"]:
        if p.exists(): return p
    return _title_card(workdir / "_titlecard.png")

def _kenburns(bg, dur, out):
    vf = (f"scale={W*2}:-1,zoompan=z='min(zoom+0.0003,1.05)':d={int(dur*FPS)}:"
          f"x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s={W}x{H}:fps={FPS},format=yuv420p")
    run(["ffmpeg", "-y", "-loop", "1", "-i", str(bg), "-t", f"{dur:.2f}", "-vf", vf,
         "-r", str(FPS), "-c:v", "libx264", "-preset", "veryfast", "-pix_fmt", "yuv420p",
         str(out)], log)
    return out

def _concat_copy(files, out):
    lst = out.parent / (out.stem + "_list.txt")
    lst.write_text("\n".join(f"file '{Path(f).name}'" for f in files), encoding="utf-8")
    run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(lst), "-c", "copy", str(out)], log)
    return out

def _mix(silent, voice, music, out, music_db, tempo=1.0):
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
    return out

def build_intro(workdir, assets=None):
    music = ROOT / "assets/branding/intro_music.mp3"
    rate = CFG.get("intro", {}).get("voice_rate", "+18%")
    parts = [
        {"voice": P1_VOICE, "bg": _text_card(P1_TEXT, workdir / "intro_card1.png")},
        {"voice": P2_VOICE, "bg": _banner(workdir)},                 # banner ONLY here
        {"voice": P3_VOICE, "bg": _text_card(P3_TEXT, workdir / "intro_card3.png")},
    ]
    voices, clips = [], []
    for i, p in enumerate(parts):
        v = workdir / f"intro_v{i}.mp3"
        voiceover.synth_text(p["voice"], v, rate=rate); voices.append(v)
        d = max(2.0, _dur(v)) + (0.5 if i == 1 else 0.4)
        clips.append(_kenburns(p["bg"], d, workdir / f"intro_c{i}.mp4"))
    intro_voice = voiceover.concat_audio(voices, workdir / "intro_voice.mp3")
    intro_silent = _concat_copy(clips, workdir / "intro_silent.mp4")
    out = workdir / "intro.mp4"
    _mix(intro_silent, intro_voice, music, out, music_db=-5)
    log.info("intro built (text cards + banner on Swagat line) -> %s", out)
    return out

def build_outro(workdir):
    music = ROOT / "assets/branding/intro_music.mp3"
    voice = workdir / "outro_voice.mp3"
    voiceover.synth_text(OUTRO_VOICE, voice, rate="+0%")
    d = max(3.0, _dur(voice)) + 0.6
    silent = _kenburns(_banner(workdir), d, workdir / "outro_silent.mp4")
    out = workdir / "outro.mp4"
    _mix(silent, voice, music, out, music_db=-16, tempo=0.85)
    log.info("outro built -> %s", out)
    return out

def assemble(intro, main, outro, out):
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
