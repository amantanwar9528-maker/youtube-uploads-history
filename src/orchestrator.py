"""End-to-end pipeline for ONE video. Designed for hands-off runs (cron / CI).
   topic -> research -> script -> voice -> media -> edit -> thumbnail -> upload."""
import json, sys, traceback
from datetime import datetime
from pathlib import Path
from config import CFG, path
from utils import get_logger, slugify
import topic_picker, researcher, scriptwriter, voiceover, media_fetcher, music, editor, subtitles, thumbnail, youtube_uploader, reels_maker

log = get_logger("run")

def run_once(post_instagram=False):
    topic = topic_picker.next_topic()
    slug = topic["slug"]
    workdir = path("output_dir") / f"{datetime.now():%Y%m%d}_{slug}"
    workdir.mkdir(parents=True, exist_ok=True)
    log.info("=== Building video: %s ===", topic["title"])

    res = researcher.research(topic)
    script = scriptwriter.write_script(res)
    (workdir / "script.txt").write_text(script["narration"], encoding="utf-8")
    (workdir / "meta.json").write_text(json.dumps(script, ensure_ascii=False, indent=2), encoding="utf-8")

    audio = voiceover.narrate(script["narration"], workdir)
    assets = media_fetcher.fetch_for_scenes(
        script["scenes"], workdir,
        per_minute=CFG["media"]["images_per_minute"],
        video_ratio=CFG["media"]["stock_video_ratio"])
    track = music.get_track(workdir)
    srt = subtitles.make_srt(audio, workdir) if CFG["video"]["captions"] else None
    final = editor.build(assets, audio, track, srt, workdir)

    thumb_bg = next((a["path"] for a in assets if a["type"] == "image"), None)
    thumb = thumbnail.make(thumb_bg, script.get("thumbnail_text", topic["title"]), workdir) if thumb_bg else None

    vid = youtube_uploader.upload(
        final, script["yt_title"], script["yt_description"],
        CFG["channel"]["default_tags"], thumb)
    topic_picker.mark_used(topic, vid)

    # build reel for later local posting (saved next to outputs)
    if CFG["reels"]["enabled"]:
        reel = reels_maker.make(final, script.get("reel_hook", topic["title"]), workdir)
        if post_instagram:
            import instagram_poster
            instagram_poster.post_reel(reel, script.get("reel_hook", ""), f"https://youtu.be/{vid}")
    log.info("=== DONE: https://youtu.be/%s ===", vid)
    return vid

if __name__ == "__main__":
    try:
        run_once(post_instagram="--ig" in sys.argv)
    except Exception:
        log.error("PIPELINE FAILED:\n%s", traceback.format_exc())
        sys.exit(1)
