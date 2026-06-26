"""Loads config.yaml + .env into one settings object."""
import os, yaml
from pathlib import Path
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")

with open(ROOT / "config.yaml", "r", encoding="utf-8") as f:
    CFG = yaml.safe_load(f)

# secrets from environment (GitHub Secrets in CI, .env locally)
SECRETS = {
    "GEMINI_API_KEY":        os.getenv("GEMINI_API_KEY", ""),
    "PEXELS_API_KEY":        os.getenv("PEXELS_API_KEY", ""),
    "PIXABAY_API_KEY":       os.getenv("PIXABAY_API_KEY", ""),
    "YOUTUBE_CLIENT_ID":     os.getenv("YOUTUBE_CLIENT_ID", ""),
    "YOUTUBE_CLIENT_SECRET": os.getenv("YOUTUBE_CLIENT_SECRET", ""),
    "YOUTUBE_REFRESH_TOKEN": os.getenv("YOUTUBE_REFRESH_TOKEN", ""),
    "IG_USERNAME":           os.getenv("IG_USERNAME", ""),
    "IG_PASSWORD":           os.getenv("IG_PASSWORD", ""),
}

def path(key: str) -> Path:
    p = ROOT / CFG["paths"][key]
    p.mkdir(parents=True, exist_ok=True)
    return p
