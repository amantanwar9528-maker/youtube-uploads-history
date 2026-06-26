"""Generate a burned-in Hindi .srt aligned to the narration audio (free, CPU)."""
from pathlib import Path
from utils import get_logger
log = get_logger("subs")

def make_srt(audio_path: Path, workdir: Path) -> Path | None:
    """Uses faster-whisper to transcribe the narration we already generated,
    giving word-timed Hindi captions. Optional — skips gracefully if unavailable."""
    try:
        from faster_whisper import WhisperModel
    except Exception:
        log.warning("faster-whisper not installed — skipping captions")
        return None
    model = WhisperModel("small", device="cpu", compute_type="int8")
    segments, _ = model.transcribe(str(audio_path), language="hi")
    srt = workdir / "captions.srt"
    with open(srt, "w", encoding="utf-8") as f:
        for i, s in enumerate(segments, 1):
            f.write(f"{i}\n{_ts(s.start)} --> {_ts(s.end)}\n{s.text.strip()}\n\n")
    return srt

def _ts(t):
    h, t = divmod(t, 3600); m, s = divmod(t, 60)
    ms = int((s - int(s)) * 1000)
    return f"{int(h):02d}:{int(m):02d}:{int(s):02d},{ms:03d}"
