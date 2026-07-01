"""Purpose-built YouTube Shorts / Instagram Reels generator for 'Itihaas'.
Structure: HOOK -> BUILD -> CLIFFHANGER (stop 40-48s) -> BRIDGE LINE (spoken redirect)
No on-screen text at all (no captions, no CTA overlay) — pure visuals + voice + music.
Returns a 9:16 short video + meta (title/description/hashtags) for upload."""
import json, re, subprocess
from pathlib import Path
from config import CFG, ROOT
from utils import get_logger, run
import gemini_client, voiceover, media_fetcher
import music as music_mod

log = get_logger("shorts")
W, H, FPS = 1080, 1920, 30
SHORT_VOICE_RATE = "+20%"           # shorts narration a bit faster than long-form
_BRIDGE_LEDGER = ROOT / "data" / "last_bridge.txt"

def _dur(p):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                          "-of", "default=nk=1:nw=1", str(p)], capture_output=True, text=True).stdout.strip()
    try: return float(out)
    except: return 0.0

# ---------- 1) script ----------
def _last_bridge():
    try: return _BRIDGE_LEDGER.read_text(encoding="utf-8").strip()
    except Exception: return ""

def write_short_script(topic_title, story_text):
    avoid = _last_bridge()
    avoid_line = f"\nPichhli short ki bridge line thi: \"{avoid}\". Isse ALAG style/wording ki bridge line do." if avoid else ""
    prompt = f"""You are a short-form (YouTube Shorts / Reels) strategist for a Hindi history channel "Itihaas".
Long-form topic: {topic_title}
Story facts (use ONLY these, stay factually accurate, NO spoilers of the ending):
{story_text[:3500]}

Make a 30-50 second vertical short. Spoken narration in HINDI. There is NO on-screen text, so everything is spoken.
Structure:
- HOOK (0-3s): shocking fact/bold claim/question. NO greeting, NO channel intro. Must be answerable only by watching more.
- BUILD (3-40s): 2 to 4 fast punchy facts, each spoken sentence <=12 words, one idea per line, escalating curiosity.
- CLIFFHANGER (40-48s): stop right before the climax/twist. Do NOT reveal the ending.
- BRIDGE LINE (spoken, 1 short sentence): turn curiosity into action; imply the full answer is on the Itihaas channel WITHOUT sounding like an ad. Vary the style.{avoid_line}
Return ONLY JSON:
{{"title":"<under 38 chars, catchy Hindi>",
"hook":{{"voice":"<Hindi spoken hook>","visual":"<english image search keywords>"}},
"build":[{{"voice":"<Hindi, <=12 words>","visual":"<english keywords>"}}],
"cliffhanger":{{"voice":"<Hindi, no spoiler>","visual":"<english keywords>"}},
"bridge":{{"voice":"<Hindi spoken bridge line>","visual":"<english keywords>"}},
"description":"<1-2 line Hindi hook>",
"hashtags":["#history","#shorts","#itihaas","#indianhistory","#forgottenhistory"],
"audio_style":"<cinematic tension | orchestral swell | epic drums | somber>"}}
build me 2 se 4 items ho."""
    raw = gemini_client.ask(prompt, temperature=0.95)
    data = json.loads(re.search(r"\{.*\}", raw, re.S).group(0))
    try:
        b = (data.get("bridge") or {}).get("voice", "")
        if b: _BRIDGE_LEDGER.write_text(b, encoding="utf-8")   # remember to avoid repeat
    except Exception: pass
    return data

# ---------- 2) render (no on-screen text) ----------
def _seg_clip(img, voice_mp3, dur, workdir, idx):
    out = workdir / f"sh_clip_{idx:02d}.mp4"
    frames = max(1, int(dur * FPS))
    src = str(img) if img and Path(img).exists() else None
    if src:
        vf = ("scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,"
              f"zoompan=z='min(zoom+0.0006,1.10)':d={frames}:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s=1080x1920:fps={FPS}")
        cmd = ["ffmpeg", "-y", "-loop", "1", "-i", src, "-i", str(voice_mp3), "-t", f"{dur:.2f}", "-vf", vf]
    else:
        cmd = ["ffmpeg", "-y", "-f", "lavfi", "-i", f"color=c=0x140f1e:s=1080x1920:d={dur:.2f}",
               "-i", str(voice_mp3), "-t", f"{dur:.2f}", "-vf", "format=yuv420p"]
    cmd += ["-r", str(FPS), "-c:v", "libx264", "-preset", "veryfast", "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-b:a", "160k", "-ar", "44100", "-ac", "2", "-shortest", str(out)]
    run(cmd, log)
    return out

def _concat_norm(clips, out):
    cmd = ["ffmpeg", "-y"]
    for c in clips: cmd += ["-i", str(c)]
    fc = ""
    for i in range(len(clips)):
        fc += (f"[{i}:v]scale={W}:{H},setsar=1,fps={FPS}[v{i}];"
               f"[{i}:a]aresample=44100,aformat=sample_fmts=fltp:channel_layouts=stereo[a{i}];")
    fc += "".join(f"[v{i}][a{i}]" for i in range(len(clips))) + f"concat=n={len(clips)}:v=1:a=1[v][a]"
    cmd += ["-filter_complex", fc, "-map", "[v]", "-map", "[a]",
            "-c:v", "libx264", "-preset", "veryfast", "-crf", "23", "-c:a", "aac", "-b:a", "160k", str(out)]
    run(cmd, log)
    return out

def _add_music(video, track, out):
    if track and Path(track).exists():
        run(["ffmpeg", "-y", "-i", str(video), "-stream_loop", "-1", "-i", str(track),
             "-filter_complex", "[1:a]volume=-18dB[m];[0:a][m]amix=inputs=2:duration=first:dropout_transition=2[a]",
             "-map", "0:v", "-map", "[a]", "-c:v", "copy", "-c:a", "aac", "-b:a", "160k", "-shortest", str(out)], log)
    else:
        run(["ffmpeg", "-y", "-i", str(video), "-c", "copy", str(out)], log)
    return out

def build_short(short, workdir, main_url=""):
    segs = [short["hook"]] + list(short.get("build", []))[:4] + [short["cliffhanger"], short["bridge"]]
    visuals = [s.get("visual", "history archival") for s in segs]
    assets = media_fetcher.fetch_for_scenes(visuals, workdir, video_ratio=0.0)
    clips = []
    for i, s in enumerate(segs):
        img = assets[i]["path"] if i < len(assets) else None
        voice = workdir / f"sh_v{i}.mp3"
        voiceover.synth_text(s.get("voice", ""), voice, rate=SHORT_VOICE_RATE)
        d = max(1.8, _dur(voice)) + 0.3
        clips.append(_seg_clip(img, voice, d, workdir, i))
    concat = _concat_norm(clips, workdir / "short_concat.mp4")
    track = music_mod.get_track(workdir, short.get("audio_style", "cinematic tension"))
    out = workdir / "short.mp4"
    _add_music(concat, track, out)
    log.info("short built -> %s (%.1fs)", out, _dur(out))
    return out
