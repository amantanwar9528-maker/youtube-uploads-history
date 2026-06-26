"""Cut a vertical 9:16 teaser (default 45s) from the final video for Instagram.
Adds the reel_hook caption on top. Does NOT post the full video."""
from pathlib import Path
from config import CFG, ROOT
from utils import get_logger, run
log = get_logger("reels")

def make(final_video: Path, hook_text: str, workdir: Path) -> Path:
    secs = CFG["reels"]["length_seconds"]
    out = workdir / "reel.mp4"
    # take an engaging chunk ~12% into the video (past the very intro)
    start = 8
    safe = hook_text.replace(":", r"\:").replace("'", r"’")
    font = ROOT / "assets" / "fonts" / "NotoSansDevanagari-Bold.ttf"
    drawtext = (f"drawtext=fontfile='{font}':text='{safe}':"
                f"fontcolor=white:fontsize=46:box=1:boxcolor=black@0.5:boxborderw=18:"
                f"x=(w-text_w)/2:y=120:line_spacing=10")
    vf = (f"crop=ih*9/16:ih,scale=1080:1920,fps=30,{drawtext}")
    run(["ffmpeg", "-y", "-ss", str(start), "-i", str(final_video), "-t", str(secs),
         "-vf", vf, "-c:v", "libx264", "-preset", "veryfast", "-crf", "23",
         "-c:a", "aac", "-b:a", "128k", str(out)], log)
    log.info("reel -> %s", out)
    return out
