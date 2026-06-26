"""Human-like Hindi narration via Microsoft Edge neural TTS (free, no API key)."""
import asyncio, re
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

async def _synth(text, out_path, voice, rate, pitch):
    comm = edge_tts.Communicate(text, voice=voice, rate=rate, pitch=pitch)
    await comm.save(str(out_path))

def narrate(narration: str, workdir: Path) -> Path:
    v = CFG["voice"]
    parts_dir = workdir / "voice_parts"; parts_dir.mkdir(parents=True, exist_ok=True)
    files = []
    for i, ch in enumerate(_chunks(narration)):
        out = parts_dir / f"part_{i:03d}.mp3"
        asyncio.run(_synth(ch, out, v["primary"], v["rate"], v["pitch"]))
        files.append(out)
        log.info("voiced part %d/%d", i + 1, len(_chunks(narration)))
    # concat all parts
    listfile = parts_dir / "list.txt"
    listfile.write_text("\n".join(f"file '{f.name}'" for f in files), encoding="utf-8")
    final = workdir / "narration.mp3"
    run(["ffmpeg", "-y", "-f", "concat", "-safe", "0",
         "-i", str(listfile), "-c", "copy", str(final)], log)
    return final
