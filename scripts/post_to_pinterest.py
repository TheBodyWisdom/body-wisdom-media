"""
Creates a video Pin via the Pinterest API v5. Standard library only (urllib).

Requires env vars: PINTEREST_CLIENT_ID, PINTEREST_CLIENT_SECRET, PINTEREST_REFRESH_TOKEN
Video pins need a two-step upload: register the media, upload the bytes, then
create the pin once Pinterest reports the upload as "succeeded".

Note: while the app only has Trial access, created pins are sandbox-only
(visible only to the authorizing account) until Pinterest approves Standard
access.
"""
import base64
import json
import time
import urllib.request
import urllib.parse
import os

TOKEN_URL = "https://api.pinterest.com/v5/oauth/token"
MEDIA_URL = "https://api.pinterest.com/v5/media"
PINS_URL = "https://api.pinterest.com/v5/pins"


def _get_access_token():
    auth = base64.b64encode(
        (os.environ["PINTEREST_CLIENT_ID"] + ":" + os.environ["PINTEREST_CLIENT_SECRET"]).encode()
    ).decode()
    data = urllib.parse.urlencode({
        "grant_type": "refresh_token",
        "refresh_token": os.environ["PINTEREST_REFRESH_TOKEN"],
    }).encode()
    req = urllib.request.Request(TOKEN_URL, data=data, method="POST", headers={
        "Authorization": "Basic " + auth,
        "Content-Type": "application/x-www-form-urlencoded",
    })
    with urllib.request.urlopen(req) as res:
        return json.loads(res.read())["access_token"]


def _register_media(access_token):
    req = urllib.request.Request(
        MEDIA_URL,
        data=json.dumps({"media_type": "video"}).encode(),
        method="POST",
        headers={
            "Authorization": "Bearer " + access_token,
            "Content-Type": "application/json",
        },
    )
    with urllib.request.urlopen(req) as res:
        return json.loads(res.read())


def _upload_video(upload_url, upload_parameters, video_path):
    boundary = "----BodyWisdomBoundary"
    with open(video_path, "rb") as f:
        video_bytes = f.read()

    body = b""
    for key, value in upload_parameters.items():
        body += ("--" + boundary + "\r\n").encode()
        body += ('Content-Disposition: form-data; name="%s"\r\n\r\n%s\r\n' % (key, value)).encode()
    body += ("--" + boundary + "\r\n").encode()
    body += b'Content-Disposition: form-data; name="file"; filename="video.mp4"\r\n'
    body += b"Content-Type: video/mp4\r\n\r\n"
    body += video_bytes
    body += ("\r\n--" + boundary + "--\r\n").encode()

    req = urllib.request.Request(upload_url, data=body, method="POST", headers={
        "Content-Type": "multipart/form-data; boundary=" + boundary,
    })
    urllib.request.urlopen(req)


def _wait_for_media_ready(access_token, media_id, timeout=120):
    deadline = time.time() + timeout
    while time.time() < deadline:
        req = urllib.request.Request(MEDIA_URL + "/" + media_id, headers={
            "Authorization": "Bearer " + access_token,
        })
        with urllib.request.urlopen(req) as res:
            data = json.loads(res.read())
        if data.get("status") == "succeeded":
            return
        if data.get("status") == "failed":
            raise RuntimeError("Pinterest media processing failed: " + json.dumps(data))
        time.sleep(5)
    raise TimeoutError("Pinterest media did not finish processing in time")


def post_to_pinterest(board_id, title, description, video_path, link=None):
    access_token = _get_access_token()

    media = _register_media(access_token)
    _upload_video(media["upload_url"], media["upload_parameters"], video_path)
    _wait_for_media_ready(access_token, media["media_id"])

    pin_body = {
        "board_id": board_id,
        "title": title,
        "description": description,
        "media_source": {
            "source_type": "video_id",
            "cover_image_content_type": "image/jpeg",
            "media_id": media["media_id"],
        },
    }
    if link:
        pin_body["link"] = link

    req = urllib.request.Request(
        PINS_URL,
        data=json.dumps(pin_body).encode(),
        method="POST",
        headers={
            "Authorization": "Bearer " + access_token,
            "Content-Type": "application/json",
        },
    )
    with urllib.request.urlopen(req) as res:
        result = json.loads(res.read())

    return result["id"]


if __name__ == "__main__":
    import sys
    if len(sys.argv) != 5:
        print("Usage: python post_to_pinterest.py <board_id> <title> <description> <video_path>")
        sys.exit(1)
    pin_id = post_to_pinterest(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4])
    print("Pinned: https://pinterest.com/pin/" + pin_id)
