# Setup Guide — get the bot live (all free)

Do these once. After that it runs itself 3×/day.

## 1. Get the free API keys (~20 min)
| Key | Where to get it (free) |
|---|---|
| `GEMINI_API_KEY` | https://aistudio.google.com/apikey → "Create API key" |
| `PEXELS_API_KEY` | https://www.pexels.com/api/ → sign up → copy key |
| `PIXABAY_API_KEY` | https://pixabay.com/api/docs/ → sign up → copy key |

## 2. YouTube upload access (one-time)
1. Go to https://console.cloud.google.com → create a project.
2. Enable **YouTube Data API v3**.
3. APIs & Services → Credentials → **Create OAuth client ID** → type **Desktop app**.
4. Download the JSON, rename to `client_secret.json`, put it in the repo root **on your PC**.
5. Run locally:
   ```bash
   pip install -r requirements.txt
   python src/get_youtube_token.py
   ```
   Sign in with the Google account that owns your channel. It prints three values:
   `YOUTUBE_CLIENT_ID`, `YOUTUBE_CLIENT_SECRET`, `YOUTUBE_REFRESH_TOKEN`.

## 3. Put the repo on GitHub (free hosting + scheduler)
```bash
git init && git add . && git commit -m "itihaas bot"
# create a PUBLIC repo on github.com, then:
git remote add origin https://github.com/<you>/itihaas-bot.git
git push -u origin main
```
> Public repo = unlimited free Actions minutes. Your keys are NOT in the code — they live in Secrets (next step).

## 4. Add the keys as GitHub Secrets
Repo → **Settings → Secrets and variables → Actions → New repository secret**. Add each:
`GEMINI_API_KEY`, `PEXELS_API_KEY`, `PIXABAY_API_KEY`,
`YOUTUBE_CLIENT_ID`, `YOUTUBE_CLIENT_SECRET`, `YOUTUBE_REFRESH_TOKEN`.

## 5. Test it
Repo → **Actions → "Auto Video 0700 IST" → Run workflow**. Watch it build & upload one video.
The three schedules (7 AM / 1 PM / 6 PM IST) then run automatically every day.

## 6. Background music
Drop a few free CC0 tracks (mp3) into `assets/music/`. Get them from:
- YouTube Studio → Audio Library, Pixabay Music, or Free Music Archive.
The bot picks one at random per video and ducks it under the narration.

## 7. Instagram Reels (runs on YOUR PC, not the cloud)
The cloud uploads the YouTube video and saves a `reel.mp4`. To post the teaser:
1. Put `IG_USERNAME` / `IG_PASSWORD` in a local `.env` (copy from `.env.example`).
2. After videos are made, run:
   ```bash
   python src/run_local_instagram.py
   ```
   (First login may ask for a code on your phone — instagrapi saves the session after.)
> Tip: schedule this with Windows Task Scheduler a bit after the upload times.
> Posting Instagram from a datacenter IP risks a ban — that's why this stays local.

## 8. Tune quality
- `config.yaml`: `target_minutes` (start at 30), voice (`hi-IN-SwaraNeural` for female),
  `images_per_minute`, `stock_video_ratio`, music volume, captions on/off.
