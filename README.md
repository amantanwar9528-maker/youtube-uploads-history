# Itihaas Auto-Bot 🎬
Fully automated, **zero-cost** Hindi history channel: researches a true historical
event, writes a 30–45 min script, narrates it in a human-like Hindi voice, edits a
hybrid photo+B-roll documentary with music & captions, makes a thumbnail, uploads to
YouTube on schedule (7 AM / 1 PM / 6 PM IST), and prepares an Instagram Reels teaser.

## Pipeline
```
topic_picker → researcher → scriptwriter → voiceover (Edge TTS)
   → media_fetcher (Wikimedia/Pexels/Pixabay) → editor (FFmpeg Ken Burns + B-roll)
   → subtitles → thumbnail → youtube_uploader → reels_maker → (local) instagram_poster
```
Run one video manually:
```bash
pip install -r requirements.txt
python src/orchestrator.py        # add --ig to also post the reel (local only)
```

## Docs
- **TECH_STACK.md** — every free tool & its paid equivalent.
- **SETUP_GUIDE.md** — get keys, deploy to GitHub Actions, go live.

## Layout
```
config.yaml          all settings (voice, length, schedule, sources)
src/                 pipeline modules (one file per stage)
data/                topic pool + used-topic ledger
assets/              fonts, music, optional intro/outro, branding
.github/workflows/   3 daily cron jobs (7AM/1PM/6PM IST)
```
