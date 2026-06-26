# Tech Stack — 100% Free Tools & APIs

Every component below is free. Where the obvious tool is paid, a no-cost alternative is used.

| Stage | What it does | Free tool / API chosen | Paid tool it replaces | Cost / Limits |
|---|---|---|---|---|
| **Topic ideas** | Picks an unused historical topic, tops up the pool | Google **Gemini API** (free tier) | Paid GPT-4 / Claude API | Free; ~15 req/min, 1500/day |
| **Research** | Builds a factual brief + timeline + scene keywords | **Wikipedia API** + Gemini | Paid research APIs | Free, unlimited (fair use) |
| **Script writing** | ~35–45 min Hindi documentary script with scene cues | **Gemini API** (free) | Paid ChatGPT/Kimi | Free tier |
| **Human-like voice** | Hindi neural narration | **Microsoft Edge TTS** (`edge-tts`) — no key | ElevenLabs / Play.ht ($) | 100% free, unlimited |
| **Images** | Historical photos & paintings | **Wikimedia Commons** + **Openverse** (no key) | Getty / Shutterstock ($) | Free, CC-licensed |
| **More images** | Topping up visuals | **Pexels API** + **Pixabay API** | Shutterstock ($) | Free key, generous limits |
| **Stock video (B-roll)** | Cinematic motion clips for the hybrid look | **Pexels Video** + **Pixabay Video** | Storyblocks / Artgrid ($) | Free key |
| **Background music** | Royalty-free, ducked under voice | **Pixabay Music / YouTube Audio Library / Free Music Archive** (local folder) | Epidemic Sound ($) | Free, CC0 |
| **Video editing** | Ken Burns, transitions, cuts, mixing | **FFmpeg** + **MoviePy** | Premiere / After Effects ($) | Free, open-source |
| **Captions/subtitles** | Auto Hindi subtitles, burned in | **faster-whisper** (CPU) | Rev / paid captioning ($) | Free, runs locally |
| **Thumbnail** | Auto 1280×720 with hook text | **Pillow (PIL)** | Canva Pro ($) | Free |
| **YouTube upload** | Scheduled publish, title/desc/tags/thumb | **YouTube Data API v3** | — | Free; 10k units/day (3 uploads OK) |
| **Instagram Reels** | Posts teaser clip via ID+password (no API key) | **instagrapi** | Meta Graph API / Buffer ($) | Free; **run locally** |
| **Reel editing** | 9:16 vertical teaser from the long video | **FFmpeg** | CapCut Pro ($) | Free |
| **Scheduling / hosting** | Runs 7 AM, 1 PM, 6 PM IST hands-off | **GitHub Actions** (cron) | Zapier / cloud VM ($) | Free; unlimited on public repo |
| **Secrets storage** | API keys kept safe | **GitHub Encrypted Secrets** | — | Free |
| **Fonts** | Hindi rendering | **Noto Sans Devanagari** (Google Fonts) | — | Free |

## Honest limitations (so nothing surprises you)
- **Voice** is excellent neural TTS but not 100% indistinguishable from a person — that doesn't exist for free.
- **GitHub Actions** must use a **public** repo for unlimited minutes; rendering 45-min video is heavy, so start at ~30 min and scale up.
- **Instagram** auto-posting from cloud IPs gets accounts banned → the Instagram step runs on **your PC/phone**, not in the cloud.
- **Gemini free tier** has rate limits; the pipeline retries with backoff.
- Always respect each source's license; the bot prefers CC/public-domain media.
