"""Human-like Hindi narration via Microsoft Edge neural TTS (free, no API key).
Robust: validates each generated MP3, retries flaky chunks, and concatenates by
re-encoding (so a bad MP3 header can't break the whole run)."""
import asyncio, re, time, subprocess
from pathlib import Path
import edge_tts
from config import CFG
from utils import get_logger, run

log = get_logger("voice")

def _chunks(text, size=2500):
    sents = re.split(r"(?<=[।!?\.])\s+", text)
    buf, out = "", []
    for s in sents:
        if len(buf) + len(s) > size:
            out.append(buf); buf = s
        else:
            buf += " " + s
    if buf.strip(): out.append(buf)
    return out

def _dur(p):
    try:
        o = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                            "-of", "default=nk=1:nw=1", str(p)], capture_output=True, text=True).stdout.strip()
        return float(o)
    except Exception:
        return 0.0

async def _synth(text, out_path, voice, rate, pitch, volume):
    comm = edge_tts.Communicate(text, voice=voice, rate=rate, pitch=pitch, volume=volume)
    await comm.save(str(out_path))

def _vol():
    return CFG["voice"].get("volume", "+0%")

def _synth_valid(text, out_path, voice, rate, pitch, volume, tries=3):
    """Synthesize with retries; returns True only if a valid, non-empty MP3 was made."""
    out_path = Path(out_path)
    for a in range(tries):
        try:
            asyncio.run(_synth(text, out_path, voice, rate, pitch, volume))
            if out_path.exists() and out_path.stat().st_size > 800 and _dur(out_path) > 0.15:
                return True
            log.warning("tts produced invalid/empty audio (try %d)", a + 1)
        except Exception as e:
            log.warning("tts error (try %d): %s", a + 1, e)
        time.sleep(1.5)
    return False

def concat_audio(files, out):
    """Concatenate mp3s via the concat FILTER with direct inputs (no list file,
    so there is zero relative-path ambiguity; also re-encodes = header-safe)."""
    files = [Path(f) for f in files]
    out = Path(out)
    if len(files) == 1:
        run(["ffmpeg", "-y", "-i", str(files[0]), "-c:a", "libmp3lame", "-q:a", "2", str(out)], log)
        return out
    cmd = ["ffmpeg", "-y"]
    for f in files:
        cmd += ["-i", str(f)]
    n = len(files)
    fc = "".join(f"[{i}:a]" for i in range(n)) + f"concat=n={n}:v=0:a=1[a]"
    cmd += ["-filter_complex", fc, "-map", "[a]", "-c:a", "libmp3lame", "-q:a", "2", str(out)]
    run(cmd, log)
    return out

def synth_text(text, out_path, rate=None, pitch=None, volume=None):
    """Single short clip (intro/outro/shorts) with retries."""
    v = CFG["voice"]
    ok = _synth_valid(text, out_path, v["primary"],
                      rate or v["rate"], pitch or v["pitch"], volume or _vol())
    if not ok:
        log.warning("synth_text failed after retries for: %.40s", text)
    return Path(out_path)

def narrate(narration: str, workdir: Path) -> Path:
    v = CFG["voice"]
    parts_dir = workdir / "voice_parts"; parts_dir.mkdir(parents=True, exist_ok=True)
    chunks = [c for c in _chunks(narration) if re.search(r"\w", c)]  # skip empty/punct-only
    files = []
    for i, ch in enumerate(chunks):
        out = parts_dir / f"part_{i:03d}.mp3"
        if _synth_valid(ch, out, v["primary"], v["rate"], v["pitch"], _vol()):
            files.append(out)
            log.info("voiced part %d/%d", i + 1, len(chunks))
        else:
            log.warning("skipping bad part %d/%d (kept going)", i + 1, len(chunks))
    if not files:
        raise RuntimeError("narration TTS failed for every chunk")
    final = workdir / "narration.mp3"
    return concat_audio(files, final)
