"""Loads config.yaml + .env into one settings object."""
import os, yaml
from pathlib import Path
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")

with open(ROOT / "config.yaml", "r", encoding="utf-8") as f:
    CFG = yaml.safe_load(f)

def _env(k: str) -> str:
    # .strip() kills stray newlines/spaces pasted into GitHub Secrets
    return (os.getenv(k) or "").strip()

SECRETS = {
    "GEMINI_API_KEY":        _env("GEMINI_API_KEY"),
    "PEXELS_API_KEY":        _env("PEXELS_API_KEY"),
    "PIXABAY_API_KEY":       _env("PIXABAY_API_KEY"),
    "YOUTUBE_CLIENT_ID":     _env("YOUTUBE_CLIENT_ID"),
    "YOUTUBE_CLIENT_SECRET": _env("YOUTUBE_CLIENT_SECRET"),
    "YOUTUBE_REFRESH_TOKEN": _env("YOUTUBE_REFRESH_TOKEN"),
    "IG_USERNAME":           _env("IG_USERNAME"),
    "IG_PASSWORD":           _env("IG_PASSWORD"),
}

def path(key: str) -> Path:
    p = ROOT / CFG["paths"][key]
    p.mkdir(parents=True, exist_ok=True)
    return p
