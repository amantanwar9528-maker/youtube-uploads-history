"""Pick the next unused topic. Auto-refills the pool via Gemini when the number
of UNUSED topics runs low (never goes dry)."""
import json, re
from config import path
from utils import load_json, save_json, get_logger, slugify
import gemini_client

log = get_logger("topic")
MIN_UNUSED = 6   # refill when fewer than this many unused topics remain

def _pool_file():  return path("data_dir") / "topic_pool.json"
def _used_file():  return path("data_dir") / "used_topics.json"

def _unused(pool, used_slugs):
    return [t for t in pool["topics"] if slugify(t["title"]) not in used_slugs]

def _topup(pool, used_slugs):
    """Ask Gemini for fresh, non-duplicate topics when unused list is low."""
    if len(_unused(pool, used_slugs)) >= MIN_UNUSED:
        return pool
    log.info("Unused topics low -> asking Gemini for fresh ideas")
    existing = {slugify(t["title"]) for t in pool["topics"]} | set(used_slugs)
    prompt = (
        "Tu ek Hindi history YouTube channel ka producer hai. 15 aise naye TRUE historical "
        "topics suggest kar jo 30-45 minute ki ek single documentary me poori ho jayein. "
        "Har topic dramatic, factually real, 'reason behind the event' wala. Title HINGLISH me. "
        "Sirf JSON array de: [{\"title\":\"...\",\"era\":\"...\",\"region\":\"...\"}]")
    try:
        raw = gemini_client.ask(prompt, temperature=0.9)
        items = json.loads(re.search(r"\[.*\]", raw, re.S).group(0))
        added = 0
        for t in items:
            if not t.get("title"):
                continue
            sl = slugify(t["title"])
            if sl not in existing:
                pool["topics"].append({"title": t["title"], "era": t.get("era", ""),
                                       "region": t.get("region", "")})
                existing.add(sl); added += 1
        log.info("added %d fresh topics", added)
    except Exception as e:
        log.warning("top-up failed (%s) — using existing pool", e)
    return pool

def next_topic():
    pool = load_json(_pool_file())
    used = load_json(_used_file(), {"used": []})
    used_slugs = {u["slug"] for u in used["used"]}

    pool = _topup(pool, used_slugs)
    save_json(_pool_file(), pool)   # persist any newly added topics (workflow commits this)

    for t in pool["topics"]:
        sl = slugify(t["title"])
        if sl not in used_slugs:
            t["slug"] = sl
            return t
    raise RuntimeError("No unused topics available")

def mark_used(topic, video_id=None):
    used = load_json(_used_file(), {"used": []})
    used["used"].append({"slug": topic["slug"], "title": topic["title"], "youtube_id": video_id})
    save_json(_used_file(), used)
