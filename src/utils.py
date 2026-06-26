"""Shared helpers: logging, JSON ledgers, slugify, ffmpeg runner."""
import json, logging, re, subprocess, sys
from pathlib import Path
from datetime import datetime

def get_logger(name="bot"):
    log = logging.getLogger(name)
    if not log.handlers:
        h = logging.StreamHandler(sys.stdout)
        h.setFormatter(logging.Formatter("%(asctime)s | %(levelname)s | %(message)s"))
        log.addHandler(h)
        log.setLevel(logging.INFO)
    return log

def load_json(p: Path, default=None):
    p = Path(p)
    if p.exists():
        return json.loads(p.read_text(encoding="utf-8"))
    return default if default is not None else {}

def save_json(p: Path, data):
    Path(p).write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

def slugify(text: str) -> str:
    text = re.sub(r"[^\w\s-]", "", text, flags=re.UNICODE).strip().lower()
    return re.sub(r"[\s_-]+", "-", text)[:60] or datetime.now().strftime("%Y%m%d%H%M")

def run(cmd: list, log=None):
    """Run a shell command (ffmpeg etc.) and raise on failure."""
    if log: log.info("RUN: %s", " ".join(map(str, cmd))[:300])
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        raise RuntimeError(f"cmd failed:\n{res.stderr[-2000:]}")
    return res.stdout
