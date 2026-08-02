"""
Posts a single piece of content to Instagram and/or Facebook via the Graph API.
Runs inside this repo's checkout (GitHub Actions or local), so local video files
are read directly from ../week1/, and the same files are also reachable publicly
via raw.githubusercontent.com for Instagram's video_url requirement.

Usage as a library:
    from post_to_meta import post_to_instagram, post_to_facebook
"""
import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request

GRAPH = "https://graph.facebook.com/v21.0"
MEDIA_REPO_RAW = "https://raw.githubusercontent.com/TheBodyWisdom/body-wisdom-media"
REPO_ROOT = os.path.join(os.path.dirname(__file__), "..")


def _request(url, data=None, method="GET"):
    body = urllib.parse.urlencode(data).encode() if data else None
    req = urllib.request.Request(url, data=body, method=method)
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"Graph API error {e.code}: {e.read().decode()}")


def raw_github_url(filename, folder="week1"):
    return f"{MEDIA_REPO_RAW}/main/{folder}/{filename}"


def post_to_instagram(caption, image_filename=None, video_filename=None, is_reel=True, thumb_offset_ms=None, folder="week1"):
    ig_id = os.environ["META_IG_BUSINESS_ID"]
    token = os.environ["META_USER_ACCESS_TOKEN"]

    params = {"caption": caption, "access_token": token}
    if video_filename:
        params["video_url"] = raw_github_url(video_filename, folder=folder)
        # Instagram deprecated media_type=VIDEO for feed video posts (2026-07-26 API error,
        # error_subcode 2207067) -- all video uploads must use REELS now, regardless of
        # whether the content is reel-style or a plain feed video like "reframe".
        params["media_type"] = "REELS"
        if thumb_offset_ms is not None:
            # The carousel-style slide videos fade in from black, so frame 0 -- which IG
            # uses as the grid/cover thumbnail by default -- is solid black. thumb_offset
            # picks a later frame, past the fade, as the cover.
            params["thumb_offset"] = str(thumb_offset_ms)
    elif image_filename:
        params["image_url"] = raw_github_url(image_filename, folder=folder)
    else:
        raise ValueError("need image_filename or video_filename")

    container = _request(f"{GRAPH}/{ig_id}/media", data=params, method="POST")
    container_id = container["id"]

    if video_filename:
        for _ in range(60):
            status = _request(f"{GRAPH}/{container_id}?fields=status_code&access_token={token}")
            if status["status_code"] == "FINISHED":
                break
            if status["status_code"] == "ERROR":
                raise RuntimeError(f"Container processing failed: {status}")
            time.sleep(5)
        else:
            raise RuntimeError("Timed out waiting for video container to finish processing")

    published = _request(
        f"{GRAPH}/{ig_id}/media_publish",
        data={"creation_id": container_id, "access_token": token},
        method="POST",
    )
    return published["id"]


def post_carousel_to_instagram(caption, image_filenames):
    """Real swipeable IG carousel: each image becomes its own unpublished child
    container (is_carousel_item=true), then a parent CAROUSEL container references
    all children by id, then that parent gets published. This is NOT the same as
    the old approach of rendering one slideshow-style video (kind="video") -- that
    produced a single Reel that just looked like slides, it was never swipeable.
    """
    ig_id = os.environ["META_IG_BUSINESS_ID"]
    token = os.environ["META_USER_ACCESS_TOKEN"]

    if not (2 <= len(image_filenames) <= 10):
        raise ValueError("Instagram carousels need between 2 and 10 items")

    child_ids = []
    for filename in image_filenames:
        params = {
            "image_url": raw_github_url(filename),
            "is_carousel_item": "true",
            "access_token": token,
        }
        child = _request(f"{GRAPH}/{ig_id}/media", data=params, method="POST")
        child_ids.append(child["id"])

    parent_params = {
        "caption": caption,
        "media_type": "CAROUSEL",
        "children": ",".join(child_ids),
        "access_token": token,
    }
    parent = _request(f"{GRAPH}/{ig_id}/media", data=parent_params, method="POST")
    parent_id = parent["id"]

    published = _request(
        f"{GRAPH}/{ig_id}/media_publish",
        data={"creation_id": parent_id, "access_token": token},
        method="POST",
    )
    return published["id"]


def post_carousel_to_facebook(message, image_filenames):
    """Real multi-photo FB post: upload each photo unpublished to get its id,
    then create a feed post that attaches all of them via attached_media.
    """
    page_id = os.environ["META_PAGE_ID"]
    token = os.environ["META_PAGE_ACCESS_TOKEN"]
    local_dir = os.path.join(REPO_ROOT, "week1")

    media_ids = []
    for filename in image_filenames:
        path = os.path.join(local_dir, filename)
        boundary = "----BodyWisdomBoundary"
        with open(path, "rb") as f:
            file_data = f.read()
        parts = [
            f"--{boundary}\r\nContent-Disposition: form-data; name=\"published\"\r\n\r\nfalse\r\n".encode(),
            f"--{boundary}\r\nContent-Disposition: form-data; name=\"access_token\"\r\n\r\n{token}\r\n".encode(),
            f"--{boundary}\r\nContent-Disposition: form-data; name=\"source\"; filename=\"{os.path.basename(path)}\"\r\nContent-Type: application/octet-stream\r\n\r\n".encode()
            + file_data + b"\r\n",
            f"--{boundary}--\r\n".encode(),
        ]
        req = urllib.request.Request(f"{GRAPH}/{page_id}/photos", data=b"".join(parts), method="POST")
        req.add_header("Content-Type", f"multipart/form-data; boundary={boundary}")
        try:
            with urllib.request.urlopen(req, timeout=180) as resp:
                media_ids.append(json.loads(resp.read().decode())["id"])
        except urllib.error.HTTPError as e:
            raise RuntimeError(f"Facebook unpublished photo upload failed {e.code}: {e.read().decode()}")

    attached_media = [{"media_fbid": mid} for mid in media_ids]
    data = {
        "message": message,
        "attached_media": json.dumps(attached_media),
        "access_token": token,
    }
    return _request(f"{GRAPH}/{page_id}/feed", data=data, method="POST")


def post_to_facebook(message, video_filename=None, image_filename=None, folder="week1"):
    """Uses direct binary upload via multipart, no public URL needed for Facebook."""
    page_id = os.environ["META_PAGE_ID"]
    token = os.environ["META_PAGE_ACCESS_TOKEN"]

    local_dir = os.path.join(REPO_ROOT, folder)

    if video_filename:
        path = os.path.join(local_dir, video_filename)
        endpoint = f"{GRAPH}/{page_id}/videos"
        file_field = "source"
        extra = {"description": message}
    elif image_filename:
        path = os.path.join(local_dir, image_filename)
        endpoint = f"{GRAPH}/{page_id}/photos"
        file_field = "source"
        extra = {"caption": message}
    else:
        raise ValueError("need image_filename or video_filename")

    boundary = "----BodyWisdomBoundary"
    with open(path, "rb") as f:
        file_data = f.read()

    parts = []
    for k, v in {**extra, "access_token": token}.items():
        parts.append(f"--{boundary}\r\nContent-Disposition: form-data; name=\"{k}\"\r\n\r\n{v}\r\n".encode())
    parts.append(
        f"--{boundary}\r\nContent-Disposition: form-data; name=\"{file_field}\"; filename=\"{os.path.basename(path)}\"\r\nContent-Type: application/octet-stream\r\n\r\n".encode()
        + file_data
        + b"\r\n"
    )
    parts.append(f"--{boundary}--\r\n".encode())
    body = b"".join(parts)

    req = urllib.request.Request(endpoint, data=body, method="POST")
    req.add_header("Content-Type", f"multipart/form-data; boundary={boundary}")
    try:
        with urllib.request.urlopen(req, timeout=180) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"Facebook post failed {e.code}: {e.read().decode()}")
