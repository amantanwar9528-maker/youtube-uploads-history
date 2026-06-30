"""Hindi narration script: confident, FLOWING delivery (minimal pauses), NO stage
directions / music cues / greetings (channel intro+outro are added separately).
Also outputs YT meta, English thumbnail heading, music mood, AI image prompt."""
import json, re
from config import CFG
from utils import get_logger
import gemini_client

log = get_logger("script")

def _target_words():
    return int(CFG["video"]["target_minutes"] * 150)

SCENE_RE = re.compile(r"\[\[(.+?)\]\]")

def _clean_narration(text: str) -> str:
    text = re.sub(r"\[\[.*?\]\]", " ", text, flags=re.S)     # scene cues
    text = re.sub(r"\[.*?\]", " ", text, flags=re.S)          # [stage directions]
    text = re.sub(r"\(.*?\)", " ", text, flags=re.S)          # (parentheticals)
    text = re.sub(r"[*_#`>]+", "", text)                      # markdown
    # drop obvious music/sound direction sentences (e.g. "संगीत शुरू होता है, धीमा...")
    text = re.sub(r"(?im)[^।\n.!?]*\b(संगीत|बैकग्राउंड|पृष्ठभूमि|background music|sound effect|music starts?)\b[^।\n.!?]*[।.!?]?", " ", text)
    text = text.replace("…", " ").replace("...", " ").replace("..", " ")  # remove dramatic-pause dots
    # drop a leading greeting sentence if one slips through (intro is separate)
    text = re.sub(r"^\s*[^।.!?]*\b(नमस्कार|नमस्ते|स्वागत|welcome|doston?)\b[^।.!?]*[।.!?]", " ", text, count=1, flags=re.I)
    text = re.sub(r"(?:\s*,\s*){2,}", ", ", text)             # collapse repeated commas
    text = re.sub(r"[ \t]{2,}", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()

def write_script(research: dict) -> dict:
    words = _target_words()
    log.info("Writing script (~%d words / %d min)", words, CFG["video"]["target_minutes"])

    prompt = f"""Tu ek master Hindi documentary storyteller hai (style: confident, cinematic, "asli kahani").
Research brief:
{research['brief'][:8000]}

Ek YouTube documentary script likh, Hindi me, approx {words} words ({CFG['video']['target_minutes']} min).
SAKHT NIYAM:
- Script SEEDHA kahani ke hook se shuru kar. 'Namaskar', 'Swagat hai', 'doston', 'aaj hum baat karenge', ya koi music/background-score/stage-direction line BILKUL mat likh — channel ka intro aur outro alag se lagta hai.
- Koi bracket, stage direction, sound/music cue, '[ ]' ya '( )' notes, heading ya markdown narration me mat daal. Sirf bolne wale shabd.
- Delivery CONFIDENT aur SMOOTH ho — vaakya behte rahein. Comma aur pause ka kam se kam use kar, baar-baar mat rukwa. '...' (teen dots) BILKUL mat use kar.
- Flow: hook -> build-up -> conflict -> climax -> the REAL reason -> short reflection.
- Har 2-3 line ke baad ek visual cue is format me: [[scene: <english keywords for image/video search>]]
- 100% factually accurate. Galat date/naam nahi.
- Ant me 'milte hain agle episode' ya 'subscribe karein' type outro mat likh — wo alag se lagta hai. Bas kahani ko ek natural reflection par khatam kar.
"""
    text = gemini_client.ask(prompt, temperature=0.85)

    scenes = []
    for m in SCENE_RE.finditer(text):
        kw = m.group(1).replace("scene:", "").strip()
        scenes.append(kw)
    narration = _clean_narration(SCENE_RE.sub(" ", text))

    meta = _meta(research["title"], narration[:1500])
    return {"narration": narration, "scenes": scenes, **meta}

def _meta(topic_title, opening):
    prompt = f"""Topic: {topic_title}. Opening: {opening}
Sirf JSON do (no extra text):
{{"yt_title": "<60 char clickable Hindi title>",
"yt_description": "<150-word Hindi description with 5 hashtags>",
"thumbnail_heading": "<2 to 5 word CATCHY thumbnail heading in ENGLISH ONLY (translate topic to English), e.g. 'Jallianwala Bagh Massacre'>",
"reel_hook": "<one-line Hindi hook for Instagram reel>",
"music_mood": "<1 to 3 ENGLISH words for background music mood, e.g. epic dramatic, tense suspense, somber emotional, triumphant heroic>",
"thumbnail_prompt": "<short ENGLISH visual scene description of this historical topic for an AI image; describe place/people/era/mood; NO text/words in the image>"}}"""
    try:
        raw = gemini_client.ask(prompt, temperature=0.7)
        return json.loads(re.search(r"\{.*\}", raw, re.S).group(0))
    except Exception as e:
        log.warning("meta gen failed: %s", e)
        return {"yt_title": topic_title, "yt_description": topic_title,
                "thumbnail_heading": topic_title, "reel_hook": topic_title,
                "thumbnail_prompt": topic_title, "music_mood": "epic cinematic"}
