"""Turn the research brief into a ~35-45 min Hindi narration script with scene cues,
plus YouTube meta, a realistic English image prompt, and a catchy HINGLISH
thumbnail heading (Roman script) for the thumbnail."""
import json, re
from config import CFG
from utils import get_logger
import gemini_client

log = get_logger("script")

def _target_words():
    return int(CFG["video"]["target_minutes"] * 150)

SCENE_RE = re.compile(r"\[\[(.+?)\]\]")

def write_script(research: dict) -> dict:
    words = _target_words()
    log.info("Writing script (~%d words / %d min)", words, CFG["video"]["target_minutes"])

    prompt = f"""Tu ek master Hindi documentary storyteller hai (style: dramatic, cinematic, "asli kahani").
Research brief:
{research['brief'][:8000]}

Ek YouTube documentary script likh, Hindi me, approx {words} words ({CFG['video']['target_minutes']} min).
Rules:
- Strong HOOK opening (pehle 30 sec me curiosity).
- Pure storytelling flow: build-up -> conflict -> climax -> the REAL reason -> reflection.
- Har 2-3 line ke baad ek visual cue daal is format me: [[scene: <english keywords for image/video search>]]
- Sirf narration text + scene cues. No headings, no markdown.
- 100% factually accurate. Koi galat date/naam mat daal.
- End me ek subtle call-to-action (subscribe) natural tarike se.
"""
    text = gemini_client.ask(prompt, temperature=0.8)

    scenes = []
    for m in SCENE_RE.finditer(text):
        kw = m.group(1).replace("scene:", "").strip()
        scenes.append(kw)
    narration = SCENE_RE.sub("", text).strip()

    meta = _meta(research["title"], narration[:1500])
    return {"narration": narration, "scenes": scenes, **meta}

def _meta(topic_title, opening):
    prompt = f"""Topic: {topic_title}. Opening: {opening}
Sirf JSON do (no extra text):
{{"yt_title": "<60 char clickable Hindi title>",
"yt_description": "<150-word Hindi description with 5 hashtags>",
"thumbnail_heading": "<2 to 5 word CATCHY thumbnail heading in HINGLISH (Roman/English letters ONLY, NO Devanagari). e.g. 'Jallianwala Bagh', 'Titanic Ka Sach'>",
"reel_hook": "<one-line Hindi hook for Instagram reel>",
"thumbnail_prompt": "<short ENGLISH visual scene description of this historical topic for a photorealistic AI image; describe place/people/era/mood; NO text/words in the image>"}}"""
    try:
        raw = gemini_client.ask(prompt, temperature=0.7)
        return json.loads(re.search(r"\{.*\}", raw, re.S).group(0))
    except Exception as e:
        log.warning("meta gen failed: %s", e)
        return {"yt_title": topic_title, "yt_description": topic_title,
                "thumbnail_heading": topic_title, "reel_hook": topic_title,
                "thumbnail_prompt": topic_title}
