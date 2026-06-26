"""Pick the next unused topic. Tops up the pool via Gemini when low."""
from config import CFG, path
from utils import load_json, save_json, get_logger, slugify
import gemini_client

log = get_logger("topic")

def _pool_file():  return path("data_dir") / "topic_pool.json"
def _used_file():  return path("data_dir") / "used_topics.json"

def _topup_if_low(pool):
    if len(pool["topics"]) >= 3:
        return pool
    log.info("Topic pool low — asking Gemini for fresh ideas")
    prompt = (
        "Tu ek Hindi history YouTube channel ka producer hai. 12 aise TRUE historical "
        "topics suggest kar jo 30-45 minute ki ek single documentary me poori ho jayein. "
        "Har topic dramatic, factually real, aur 'reason behind the event' wala ho. "
        "Sirf JSON array de: [{\"title\":\"...\",\"era\":\"...\",\"region\":\"...\"}]"
    )
    import json, re
    try:
        raw = gemini_client.ask(prompt, temperature=0.9)
        raw = re.search(r"\[.*\]", raw, re.S).group(0)
        pool["topics"].extend(json.loads(raw))
    except Exception as e:
        log.warning("Top-up failed (%s) — using existing pool", e)
    return pool

def next_topic():
    pool = load_json(_pool_file())
    used = load_json(_used_file(), {"used": []})
    used_slugs = {u["slug"] for u in used["used"]}

    pool = _topup_if_low(pool)
    for t in pool["topics"]:
        slug = slugify(t["title"])
        if slug not in used_slugs:
            t["slug"] = slug
            return t
    raise RuntimeError("No unused topics available")

def mark_used(topic, video_id=None):
    used = load_json(_used_file(), {"used": []})
    used["used"].append({"slug": topic["slug"], "title": topic["title"], "youtube_id": video_id})
    save_json(_used_file(), used)
