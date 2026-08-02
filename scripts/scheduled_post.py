"""
Runs on a GitHub Actions cron schedule (see ../.github/workflows/scheduled_post.yml),
independent of any local machine being awake. Looks up which slug is due "today"
(UTC calendar date, which matches the Europe/Amsterdam date at the 10:00 UTC /
12:00 CEST trigger time) and posts it if not already posted.

Usage: python scheduled_post.py [slug]
  - With no argument: posts whatever DATE_TO_SLUG maps to today's UTC date (the
    normal cron path). Silently does nothing if today has no scheduled slug.
  - With an explicit slug: posts that slug regardless of date (manual catch-up
    via workflow_dispatch).
"""
import datetime
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from post_to_meta import post_to_instagram, post_to_facebook, post_carousel_to_instagram, post_carousel_to_facebook

REPO_ROOT = os.path.join(os.path.dirname(__file__), "..")
LOG_PATH = os.path.join(REPO_ROOT, "posting_log.txt")

HASHTAGS = "\n.\n.\n.\n#nervoussystem #nervoussystemregulation #somatichealing #polyvagal #traumainformed #emotionalregulation #anxietyrelief #bodywisdom #selfregulation #mentalhealthawareness"

# Calendar date (UTC) -> slug. Extend this as new content gets scheduled.
DATE_TO_SLUG = {
    "2026-07-28": "sigh",
    "2026-07-29": "grounding",
    "2026-07-30": "rest",
    "2026-07-31": "words",
    "2026-08-01": "remembers",
}

POSTS = {
    "sigh": {
        "caption": " If you only learn one breathing technique, let it be this one \U0001F32C️ Two inhales through the nose, no pause between them, then one long, slow exhale through the mouth. It's called the physiological sigh, and it's one of the fastest ways to calm your nervous system that's actually backed by research, not folklore.\n\nNot five minutes. Just one breath, whenever you need it.",
        "video_filename": "day4_sigh.mp4",
        "kind": "reel",
    },
    "grounding": {
        "caption": " Floating above yourself, checked out, not quite here, whatever word fits for you, it's one of the most common and least talked about nervous system states. These five techniques aren't about forcing yourself back. They're about giving your body something real enough to land on.\n\nIn The Reset Kit you'll find daily grounding practices designed to become lasting habits, so floating days like this get further apart. Link's in my bio.",
        "video_filename": "day3_grounding.mp4",
        "kind": "video",
    },
    "rest": {
        "caption": " There's a quiet belief a lot of us carry without ever really choosing it, that rest has to be earned, that we need to have done enough first. Your body doesn't work off that ledger. It needs rest the way it needs water, regardless of what's still sitting on the list.\n\nLetting yourself stop isn't a reward. It's maintenance.",
        "video_filename": "day6_rest.mp4",
        "kind": "reel",
    },
    "words": {
        "caption": " Some feelings never got a name, so we either shrink them to fit words that don't quite work, or stop trying to name them at all.\n\nFive phrases for the specific, hard-to-place states that show up in the body more than in language. Swipe through slowly, see if one finally fits.",
        "video_filename": "day5_words.mp4",
        "kind": "video",
    },
    "remembers": {
        "caption": " Your mind can forget a lot. Your body rarely does \U0001F33E The tension that shows up for no clear reason, the way certain sounds or spaces make you brace without deciding to, that's not random. It's memory, stored somewhere language doesn't reach.\n\nYou don't have to remember the whole story for your body to finally be allowed to put it down. That's the quiet work this whole page is here for.",
        "video_filename": "day7_remembers.mp4",
        "kind": "reel",
    },
}

if __name__ == "__main__":
    if len(sys.argv) > 1:
        slug = sys.argv[1]
    else:
        today = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d")
        slug = DATE_TO_SLUG.get(today)
        if slug is None:
            print(f"No post scheduled for {today}, nothing to do.")
            sys.exit(0)

    post = POSTS[slug]
    full_caption = post["caption"] + HASHTAGS

    if os.path.exists(LOG_PATH):
        with open(LOG_PATH, encoding="utf-8") as f:
            if any(line.startswith(f"{slug}: IG=") for line in f):
                print(f"{slug}: already posted successfully, skipping (idempotency guard)")
                sys.exit(0)

    try:
        # "carousel" = real swipeable multi-image post (separate image_filenames list).
        # Do NOT use the old "video" kind for new carousel-style content -- that rendered
        # a single slideshow video that only looked like slides, it was never swipeable.
        if post["kind"] == "carousel":
            ig_id = post_carousel_to_instagram(full_caption, post["image_filenames"])
            fb_result = post_carousel_to_facebook(post["caption"] + HASHTAGS, post["image_filenames"])
        else:
            is_reel = post["kind"] == "reel"
            thumb_offset_ms = 300 if post["kind"] == "video" else None
            ig_id = post_to_instagram(full_caption, video_filename=post["video_filename"], is_reel=is_reel, thumb_offset_ms=thumb_offset_ms)
            fb_result = post_to_facebook(post["caption"] + HASHTAGS, video_filename=post["video_filename"])
        with open(LOG_PATH, "a", encoding="utf-8") as f:
            f.write(f"{slug}: IG={ig_id} FB={fb_result}\n")
        print(f"{slug}: posted. IG={ig_id} FB={fb_result}")
    except Exception as e:
        with open(LOG_PATH, "a", encoding="utf-8") as f:
            f.write(f"{slug}: FAILED {e}\n")
        print(f"{slug}: FAILED {e}")
        raise
