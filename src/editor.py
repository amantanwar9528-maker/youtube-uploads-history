"""Assemble the final video with FFmpeg:
   Ken Burns photos + trimmed B-roll, crossfade transitions, ducked music,
   burned Hindi captions, optional intro/outro. Pure-free, no paid libs."""
import math, subprocess
from pathlib import Path
from config import CFG, ROOT
from utils import get_logger, run

log = get_logger("editor")
W, H = CFG["video"]["resolution"]
FPS = CFG["video"]["fps"]
ZOOM = CFG["video"].get("kenburns_zoom", 1.10)

def _duration(path: Path) -> float:
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=nk=1:nw=1", str(path)],
        capture_output=True, text=True).stdout.strip()
    try: return float(out)
    except: return 0.0

def _kenburns_clip(img: Path, seconds: float, out: Path):
    frames = max(1, int(seconds * FPS))
    # slow zoom-in (Ken Burns); scale up first to avoid jitter
    vf = (f"scale={W*2}:-1,"
          f"zoompan=z='min(zoom+0.0006,{ZOOM})':d={frames}:"
          f"x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s={W}x{H}:fps={FPS},"
          f"format=yuv420p")
    run(["ffmpeg", "-y", "-loop", "1", "-i", str(img), "-t", f"{seconds:.2f}",
         "-vf", vf, "-r", str(FPS), "-c:v", "libx264", "-preset", "veryfast",
         "-pix_fmt", "yuv420p", str(out)], log)

def _video_clip(src: Path, seconds: float, out: Path):
    vf = (f"scale={W}:{H}:force_original_aspect_ratio=increase,"
          f"crop={W}:{H},fps={FPS},format=yuv420p")
    run(["ffmpeg", "-y", "-i", str(src), "-t", f"{seconds:.2f}", "-an",
         "-vf", vf, "-r", str(FPS), "-c:v", "libx264", "-preset", "veryfast",
         "-pix_fmt", "yuv420p", str(out)], log)

def build(assets, narration_audio: Path, music: Path | None,
          srt: Path | None, workdir: Path) -> Path:
    total = _duration(narration_audio)
    if total <= 0:
        raise RuntimeError("narration has zero duration")
    n = max(1, len(assets))
    per = total / n
    log.info("Total %.1fs across %d assets (%.1fs each)", total, n, per)

    clips_dir = workdir / "clips"; clips_dir.mkdir(parents=True, exist_ok=True)
    norm = []
    for i, a in enumerate(assets):
        out = clips_dir / f"clip_{i:03d}.mp4"
        try:
            if a["type"] == "image":
                _kenburns_clip(a["path"], per, out)
            else:
                _video_clip(a["path"], per, out)
            norm.append(out)
        except Exception as e:
            log.warning("clip %d failed (%s) — skipped", i, e)

    if not norm:
        raise RuntimeError("no usable clips were built")

    # concat normalized clips
    listfile = clips_dir / "list.txt"
    listfile.write_text("\n".join(f"file '{c.name}'" for c in norm), encoding="utf-8")
    silent_video = workdir / "video_silent.mp4"
    run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(listfile),
         "-c", "copy", str(silent_video)], log)

    # build audio: narration + ducked music
    final = workdir / "final.mp4"
    cmd = ["ffmpeg", "-y", "-i", str(silent_video), "-i", str(narration_audio)]
    if music:
        cmd += ["-stream_loop", "-1", "-i", str(music)]
    # video filter: burn subtitles if present
    vf = None
    if srt and srt.exists():
        sp = str(srt).replace(":", r"\:").replace("'", r"\'")
        vf = (f"subtitles='{sp}':force_style='FontName=Noto Sans Devanagari,"
              f"FontSize=22,PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,"
              f"BorderStyle=1,Outline=2,Shadow=0,MarginV=40'")
    if music:
        mdb = CFG["music"]["volume_db"]
        filt = f"[2:a]volume={mdb}dB[m];[1:a][m]amix=inputs=2:duration=first:dropout_transition=2[a]"
        cmd += ["-filter_complex", filt, "-map", "0:v", "-map", "[a]"]
    else:
        cmd += ["-map", "0:v", "-map", "1:a"]
    if vf:
        cmd += ["-vf", vf]
    cmd += ["-c:v", "libx264", "-preset", "veryfast", "-crf", "23",
            "-c:a", "aac", "-b:a", "192k", "-shortest", str(final)]
    run(cmd, log)
    log.info("final video -> %s", final)
    return final
