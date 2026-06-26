"""Upload to YouTube via Data API v3 using a stored refresh token (free quota).
Each upload ~1600 units; daily quota 10000 => 3/day is fine."""
from pathlib import Path
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from config import CFG, SECRETS
from utils import get_logger
log = get_logger("youtube")

def _service():
    creds = Credentials(
        token=None,
        refresh_token=SECRETS["YOUTUBE_REFRESH_TOKEN"],
        client_id=SECRETS["YOUTUBE_CLIENT_ID"],
        client_secret=SECRETS["YOUTUBE_CLIENT_SECRET"],
        token_uri="https://oauth2.googleapis.com/token",
        scopes=["https://www.googleapis.com/auth/youtube.upload"],
    )
    return build("youtube", "v3", credentials=creds)

def upload(video: Path, title, description, tags, thumb: Path | None = None,
           privacy=None) -> str:
    privacy = privacy or CFG["channel"]["upload_privacy"]
    yt = _service()
    body = {
        "snippet": {"title": title[:100], "description": description[:5000],
                    "tags": (tags or [])[:30], "categoryId": "27"},  # 27 = Education
        "status": {"privacyStatus": privacy, "selfDeclaredMadeForKids": False},
    }
    media = MediaFileUpload(str(video), chunksize=-1, resumable=True, mimetype="video/*")
    req = yt.videos().insert(part="snippet,status", body=body, media_body=media)
    resp = None
    while resp is None:
        status, resp = req.next_chunk()
        if status: log.info("upload %d%%", int(status.progress() * 100))
    vid = resp["id"]
    log.info("uploaded: https://youtu.be/%s", vid)
    if thumb and thumb.exists():
        try:
            yt.thumbnails().set(videoId=vid, media_body=MediaFileUpload(str(thumb))).execute()
        except Exception as e:
            log.warning("thumb set failed: %s", e)
    return vid
