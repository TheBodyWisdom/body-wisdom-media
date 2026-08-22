"""
Uploads a video to YouTube as a Short via the YouTube Data API v3 resumable
upload flow. Standard library only (urllib), matching post_to_meta.py's style
so no extra pip install step is needed in the GitHub Actions workflow.

Requires env vars: YOUTUBE_CLIENT_ID, YOUTUBE_CLIENT_SECRET, YOUTUBE_REFRESH_TOKEN
"""
import json
import os
import urllib.request
import urllib.parse
import urllib.error

TOKEN_URL = "https://oauth2.googleapis.com/token"
UPLOAD_URL = "https://www.googleapis.com/upload/youtube/v3/videos?uploadType=resumable&part=snippet,status"


def _get_access_token():
    data = urllib.parse.urlencode({
        "client_id": os.environ["YOUTUBE_CLIENT_ID"],
        "client_secret": os.environ["YOUTUBE_CLIENT_SECRET"],
        "refresh_token": os.environ["YOUTUBE_REFRESH_TOKEN"],
        "grant_type": "refresh_token",
    }).encode()
    req = urllib.request.Request(TOKEN_URL, data=data, method="POST")
    with urllib.request.urlopen(req) as res:
        return json.loads(res.read())["access_token"]


def post_to_youtube(title, description, video_path, privacy_status="public"):
    """
    title: video title, e.g. include "#Shorts" for the Shorts shelf
    description: full caption/description text
    video_path: absolute or relative path to the local mp4 file
    Returns the YouTube video id on success.
    """
    access_token = _get_access_token()

    metadata = json.dumps({
        "snippet": {
            "title": title,
            "description": description,
            "categoryId": "26",  # Howto & Style; close enough for wellness content
        },
        "status": {
            "privacyStatus": privacy_status,
            "selfDeclaredMadeForKids": False,
        },
    }).encode()

    init_req = urllib.request.Request(
        UPLOAD_URL,
        data=metadata,
        method="POST",
        headers={
            "Authorization": "Bearer " + access_token,
            "Content-Type": "application/json; charset=UTF-8",
            "X-Upload-Content-Type": "video/mp4",
        },
    )
    with urllib.request.urlopen(init_req) as res:
        upload_url = res.headers.get("Location")

    with open(video_path, "rb") as f:
        video_bytes = f.read()

    upload_req = urllib.request.Request(
        upload_url,
        data=video_bytes,
        method="PUT",
        headers={
            "Authorization": "Bearer " + access_token,
            "Content-Type": "video/mp4",
            "Content-Length": str(len(video_bytes)),
        },
    )
    with urllib.request.urlopen(upload_req) as res:
        result = json.loads(res.read())

    return result["id"]


if __name__ == "__main__":
    import sys
    if len(sys.argv) != 4:
        print("Usage: python post_to_youtube.py <title> <description> <video_path>")
        sys.exit(1)
    video_id = post_to_youtube(sys.argv[1], sys.argv[2], sys.argv[3])
    print("Posted: https://youtube.com/shorts/" + video_id)
