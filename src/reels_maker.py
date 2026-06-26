"""Build a vertical 9:16 ADVERTISEMENT reel (<=60s) from the final video.
Promotes BOTH the video (hook) and the channel (CTA + subscribe end-card).
Hindi hook is rendered via a Devanagari font; CTAs use simple text."""
from pathlib import Path
from config import CFG, ROOT
from utils import get_logger, run
log = get_logger("reels")

def _font() -> str:
    for p in [ROOT / "assets/fonts/NotoSansDevanagari-Bold.ttf",
              Path("/usr/share/fonts/truetype/noto/NotoSansDevanagari-Bold.ttf"),
              Path("/usr/share/fonts/truetype/lohit-devanagari/Lohit-Devanagari.ttf"),
              Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf")]:
        if p.exists():
            return str(p)
    return "DejaVuSans"  # last resort

def _duration(path: Path) -> float:
    import subprocess
    out = subprocess.run(["ffprobe","-v","error","-show_entries","format=duration",
                          "-of","default=nk=1:nw=1",str(path)],
                         capture_output=True, text=True).stdout.strip()
    try: return float(out)
    except: return 0.0

def make(final_video: Path, hook_text: str, workdir: Path) -> Path:
    secs = min(58, int(CFG["reels"].get("length_seconds", 50)))
    out = workdir / "reel.mp4"
    chan = CFG["channel"]["name"]

    # start a bit into the story (skip the very intro), but stay inside the video
    total = _duration(final_video)
    start = 30 if total > (30 + secs + 5) else max(0, int(total * 0.08))

    # hook text -> file (avoids ffmpeg escaping issues with Hindi/punctuation)
    hookfile = workdir / "hook.txt"
    hookfile.write_text((hook_text or "").strip()[:120], encoding="utf-8")
    font = _font()

    # 1) hook at top (whole reel)  2) CTA bottom (whole reel)
    # 3) subscribe end-card (last 6s)
    end_from = max(1, secs - 6)
    vf = (
        "crop=ih*9/16:ih,scale=1080:1920,fps=30,"
        f"drawtext=fontfile='{font}':textfile='{hookfile}':reload=0:"
        "fontcolor=white:fontsize=54:box=1:boxcolor=black@0.55:boxborderw=22:"
        "x=(w-text_w)/2:y=150:line_spacing=14,"
        f"drawtext=fontfile='{font}':text='Poori kahani YouTube par':"
        "fontcolor=yellow:fontsize=46:box=1:boxcolor=black@0.65:boxborderw=18:"
        "x=(w-text_w)/2:y=h-300,"
        f"drawtext=fontfile='{font}':text='{chan} - Subscribe!':"
        "fontcolor=white:fontsize=44:box=1:boxcolor=red@0.75:boxborderw=18:"
        f"x=(w-text_w)/2:y=h-210:enable='gte(t,{end_from})'"
    )
    run(["ffmpeg","-y","-ss",str(start),"-i",str(final_video),"-t",str(secs),
         "-vf",vf,"-c:v","libx264","-preset","veryfast","-crf","23",
         "-c:a","aac","-b:a","128k", str(out)], log)
    log.info("ad-reel -> %s (%ds from %ds)", out, secs, start)
    return out
