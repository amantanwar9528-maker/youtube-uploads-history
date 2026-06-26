"""End-to-end pipeline for ONE video. Designed for hands-off runs (cron / CI).
   topic -> research -> script -> voice -> media -> edit -> thumbnail -> upload
   -> ad-reel saved to reels_to_post/ (local PC posts it to Instagram)."""
import json, sys, shutil, traceback
from datetime import datetime
from pathlib import Path
from config import CFG, ROOT, path
from utils import get_logger
import topic_picker, researcher, scriptwriter, voiceover, media_fetcher, music, editor, subtitles, thumbnail, youtube_uploader, reels_maker

log = get_logger("run")

def _ig_caption(script, channel, vid):
    hook = script.get("reel_hook") or script.get("yt_title", "")
    return (
        f"{hook}\n\n"
        f"Poori kahani (full video) YouTube par dekhein! Link bio mein.\n"
        f"▶ {channel} ko abhi Subscribe karein.\n\n"
        f"#history #itihaas #historyinhindi #truestory #facts #reels #explore #bharat"
    )

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

    srt = None
    if CFG["video"]["captions"]:
        try:
            srt = subtitles.make_srt(audio, workdir)   # non-fatal
        except Exception as e:
            log.warning("captions skipped (non-fatal): %s", e)

    final = editor.build(assets, audio, track, srt, workdir)

    thumb = None
    try:
        thumb_bg = next((a["path"] for a in assets if a["type"] == "image"), None)
        if thumb_bg:
            thumb = thumbnail.make(thumb_bg, script.get("thumbnail_text", topic["title"]), workdir)
    except Exception as e:
        log.warning("thumbnail skipped (non-fatal): %s", e)

    vid = youtube_uploader.upload(
        final, script["yt_title"], script["yt_description"],
        CFG["channel"]["default_tags"], thumb)
    topic_picker.mark_used(topic, vid)

    # ---- ad-reel -> reels_to_post/ (PC posts to Instagram later) ----
    if CFG["reels"]["enabled"]:
        try:
            reel = reels_maker.make(final, script.get("reel_hook", topic["title"]), workdir)
            outbox = ROOT / "reels_to_post"; outbox.mkdir(exist_ok=True)
            name = f"{workdir.name}_{vid}"
            shutil.copy(reel, outbox / f"{name}.mp4")
            (outbox / f"{name}.txt").write_text(
                _ig_caption(script, CFG["channel"]["name"], vid), encoding="utf-8")
            log.info("reel queued for Instagram: %s.mp4", name)
            if post_instagram:                      # only when run locally with --ig
                import instagram_poster
                instagram_poster.post_reel(reel, script.get("reel_hook", ""), f"https://youtu.be/{vid}")
        except Exception as e:
            log.warning("reel step skipped (non-fatal): %s", e)

    log.info("=== DONE: https://youtu.be/%s ===", vid)
    return vid

if __name__ == "__main__":
    try:
        run_once(post_instagram="--ig" in sys.argv)
    except Exception:
        log.error("PIPELINE FAILED:\n%s", traceback.format_exc())
        sys.exit(1)
