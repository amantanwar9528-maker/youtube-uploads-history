"""Purpose-built YouTube Shorts / Instagram Reels generator for 'Itihaas'.
Turns a long-form topic/story into a HOOK -> BUILD -> CLIFFHANGER -> CTA short:
 - Gemini writes the short-form script (dramatic, factually accurate, no spoilers)
 - renders a 9:16 video: TTS narration + matching free visuals + burned captions
   + cinematic royalty-free music + CTA overlay on the last frame.
Returns (video_path, meta) for YouTube Shorts upload + Instagram queue."""
import json, re, subprocess
from pathlib import Path
from config import CFG, ROOT
from utils import get_logger, run
import gemini_client, voiceover, media_fetcher
import music as music_mod

log = get_logger("shorts")
W, H, FPS = 1080, 1920, 30

def _font(size):
    from PIL import ImageFont
    for fp in [ROOT / "assets/fonts/NotoSansDevanagari-Bold.ttf",
               Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf")]:
        try:
            if Path(fp).exists(): return str(fp)
        except Exception: pass
    return "DejaVuSans"

def _fontfile():
    for fp in [ROOT / "assets/fonts/NotoSansDevanagari-Bold.ttf",
               Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf")]:
        if Path(fp).exists(): return str(fp)
    return "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

def _dur(p):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                          "-of", "default=nk=1:nw=1", str(p)], capture_output=True, text=True).stdout.strip()
    try: return float(out)
    except: return 0.0

def _wrap(text, width=22):
    words, lines, cur = (text or "").split(), [], ""
    for w in words:
        if len((cur + " " + w).strip()) <= width:
            cur = (cur + " " + w).strip()
        else:
            lines.append(cur); cur = w
    if cur: lines.append(cur)
    return "\n".join(lines[:3])

# ---------- 1) script ----------
def write_short_script(topic_title, story_text):
    prompt = f"""You are a short-form (YouTube Shorts / Reels) strategist for a Hindi history channel "Itihaas".
Long-form topic: {topic_title}
Story facts (use ONLY these, stay factually accurate):
{story_text[:3500]}

Make a 30-50 second vertical short. Spoken narration in HINDI, on-screen captions in short HINGLISH (Roman).
Structure: HOOK (shocking fact/claim/question, NO greeting) -> BUILD (2-4 punchy facts, each sentence <=12 words, escalating curiosity) -> CLIFFHANGER (stop before the climax, do NOT reveal the ending).
Return ONLY JSON:
{{"title":"<under 38 chars, catchy>",
"hook":{{"voice":"<Hindi spoken hook>","caption":"<short Hinglish caption>","visual":"<english image search keywords>"}},
"build":[{{"voice":"<Hindi>","caption":"<Hinglish>","visual":"<english keywords>"}}],
"cliffhanger":{{"voice":"<Hindi, no spoiler>","caption":"<Hinglish>","visual":"<english keywords>"}},
"cta_text":"Poori kahani Itihaas par",
"description":"<1-2 line Hindi hook>",
"hashtags":["#history","#shorts","#itihaas","#indianhistory","#forgottenhistory"],
"audio_style":"<cinematic tension | orchestral swell | epic drums | somber>"}}
build me 2 se 4 items ho."""
    raw = gemini_client.ask(prompt, temperature=0.95)
    data = json.loads(re.search(r"\{.*\}", raw, re.S).group(0))
    return data

# ---------- 2) render ----------
def _seg_clip(img, caption, voice_mp3, dur, workdir, idx, cta=None):
    out = workdir / f"sh_clip_{idx:02d}.mp4"
    capfile = workdir / f"sh_cap_{idx:02d}.txt"
    capfile.write_text(_wrap(caption), encoding="utf-8")
    ff = _fontfile()
    frames = max(1, int(dur * FPS))
    vf = (
        "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,"
        f"zoompan=z='min(zoom+0.0006,1.10)':d={frames}:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s=1080x1920:fps={FPS},"
        f"drawtext=fontfile='{ff}':textfile='{capfile}':fontcolor=white:fontsize=58:"
        "box=1:boxcolor=black@0.6:boxborderw=20:x=(w-text_w)/2:y=h*0.66:line_spacing=10"
    )
    if cta:
        safe = cta.replace(":", " ").replace("'", "")
        vf += (f",drawtext=fontfile='{ff}':text='{safe}':fontcolor=yellow:fontsize=52:"
               "box=1:boxcolor=black@0.75:boxborderw=18:x=(w-text_w)/2:y=200")
    src = str(img) if img and Path(img).exists() else None
    if src:
        cmd = ["ffmpeg", "-y", "-loop", "1", "-i", src, "-i", str(voice_mp3), "-t", f"{dur:.2f}", "-vf", vf]
    else:
        cmd = ["ffmpeg", "-y", "-f", "lavfi", "-i", f"color=c=0x140f1e:s=1080x1920:d={dur:.2f}",
               "-i", str(voice_mp3), "-t", f"{dur:.2f}", "-vf", vf.replace(
                   "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,", "")]
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
    segs = [short["hook"]] + list(short.get("build", []))[:4] + [short["cliffhanger"]]
    visuals = [s.get("visual", "history archival") for s in segs]
    assets = media_fetcher.fetch_for_scenes(visuals, workdir, video_ratio=0.0)
    clips = []
    for i, s in enumerate(segs):
        img = assets[i]["path"] if i < len(assets) else None
        voice = workdir / f"sh_v{i}.mp3"
        voiceover.synth_text(s.get("voice", ""), voice, rate="+16%")
        d = max(2.0, _dur(voice)) + 0.35
        is_last = (i == len(segs) - 1)
        clips.append(_seg_clip(img, s.get("caption", ""), voice, d, workdir, i,
                               cta=short.get("cta_text") if is_last else None))
    concat = _concat_norm(clips, workdir / "short_concat.mp4")
    track = music_mod.get_track(workdir, short.get("audio_style", "cinematic tension"))
    out = workdir / "short.mp4"
    _add_music(concat, track, out)
    log.info("short built -> %s (%.1fs)", out, _dur(out))
    return out
