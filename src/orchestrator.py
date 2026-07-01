"""End-to-end pipeline for ONE video (hands-off, cron/CI).
topic -> research -> script -> voice -> media -> edit -> intro+outro
-> Ghibli thumbnail -> upload -> HOOK/BUILD/CLIFFHANGER short (YT Short + IG reel)."""
import json, sys, shutil, traceback
from datetime import datetime
from pathlib import Path
from config import CFG, ROOT, path
from utils import get_logger
import topic_picker, researcher, scriptwriter, voiceover, media_fetcher, music, editor, subtitles, thumbnail, youtube_uploader, intro_outro, shorts

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
    track = music.get_track(workdir, script.get("music_mood", "epic cinematic"))

    srt = None
    if CFG["video"]["captions"]:
        try:
            srt = subtitles.make_srt(audio, workdir)
        except Exception as e:
            log.warning("captions skipped (non-fatal): %s", e)

    body = editor.build(assets, audio, track, srt, workdir)

    # ---- fixed branded intro + outro ----
    final = body
    if CFG.get("intro", {}).get("enabled", True):
        try:
            intro = intro_outro.build_intro(workdir, assets)
            outro = intro_outro.build_outro(workdir)
            full = workdir / "final_full.mp4"
            intro_outro.assemble(intro, body, outro, full)
            final = full
        except Exception as e:
            log.warning("intro/outro skipped (non-fatal): %s", e)

    # ---- realistic/Ghibli AI thumbnail (no text) ----
    thumb = None
    try:
        ai_prompt = script.get("thumbnail_prompt") or topic["title"]
        fallback_bg = next((a["path"] for a in assets if a["type"] == "image"), None)
        thumb = thumbnail.make(script.get("thumbnail_heading", ""), ai_prompt, workdir, fallback_bg)
    except Exception as e:
        log.warning("thumbnail skipped (non-fatal): %s", e)

    vid = youtube_uploader.upload(
        final, script["yt_title"], script["yt_description"],
        CFG["channel"]["default_tags"], thumb)
    topic_picker.mark_used(topic, vid)

    # ---- short-form: YouTube Short + Instagram Reel ----
    if CFG["reels"]["enabled"]:
        try:
            short = shorts.write_short_script(topic["title"], script["narration"][:3500])
            short_path = shorts.build_short(short, workdir, main_url=f"https://youtu.be/{vid}")
            hashtags = " ".join(short.get("hashtags", []))
            s_desc = f"{short.get('description','')}\n\nFull video: https://youtu.be/{vid}\n{hashtags}"

            # upload as a YouTube Short
            try:
                s_title = (short.get("title") or topic["title"])[:38] + " #Shorts"
                s_tags = CFG["channel"]["default_tags"] + ["shorts", "reels", "history shorts"]
                svid = youtube_uploader.upload(short_path, s_title, s_desc, s_tags)
                log.info("YouTube Short uploaded: https://youtu.be/%s", svid)
            except Exception as e:
                log.warning("shorts YT upload failed (non-fatal): %s", e)

            # queue for Instagram Reels (local PC posts it)
            outbox = ROOT / "reels_to_post"; outbox.mkdir(exist_ok=True)
            name = f"{workdir.name}_{vid}"
            shutil.copy(short_path, outbox / f"{name}.mp4")
            ig_cap = f"{short.get('description','')}\nPoori kahani YouTube par! (link in bio)\n{hashtags}"
            (outbox / f"{name}.txt").write_text(ig_cap, encoding="utf-8")
            log.info("short queued for Instagram: %s.mp4", name)

            if post_instagram:
                import instagram_poster
                instagram_poster.post_reel(short_path, ig_cap)
        except Exception as e:
            log.warning("short-form step skipped (non-fatal): %s", e)

    log.info("=== DONE: https://youtu.be/%s ===", vid)
    return vid

if __name__ == "__main__":
    try:
        run_once(post_instagram="--ig" in sys.argv)
    except Exception:
        log.error("PIPELINE FAILED:\n%s", traceback.format_exc())
        sys.exit(1)
