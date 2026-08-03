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
    # Week 2 (post02-post15) is intentionally NOT scheduled yet. Nicole has not
    # approved this content -- she wants to review/revise each post first. Add
    # a "YYYY-MM-DD": "slug" line back here only after she explicitly approves
    # that specific post's final caption + voice + video.
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
    "rest-uncomfortable": {
        "caption": " Most women miss this sign of a tired nervous system \U0001F440\n\nIf rest makes you restless instead of relaxed, that's not you failing at resting. For a nervous system used to being on, stillness can feel unsafe before it feels safe.\n\nThat discomfort isn't a sign to push through. It's a sign to start smaller.\n\nWhich one do you recognise most? Let me know below \U0001F447",
        "video_filename": "post02_rest-uncomfortable.mp4",
        "kind": "reel",
        "folder": "week2",
    },
    "five-things-dont-calm": {
        "caption": " If you always feel wired but exhausted, this might surprise you\n\nPositive thinking on top of a dysregulated body. Pushing yourself to “just get through it.” Endless scrolling as a way to switch off. Forcing yourself to relax on command. Staying busy so you don't have to feel what's underneath.\n\nAll five are common. They just work on the mind, while the stress sits in the body.\n\nSave this for later \U0001F4CC",
        "image_filenames": ["post03_slide1.jpg", "post03_slide2.jpg", "post03_slide3.jpg", "post03_slide4.jpg", "post03_slide5.jpg"],
        "kind": "carousel",
        "folder": "week2",
    },
    "30-second-reset": {
        "caption": " The 30-second reset that actually works ⏱️\n\nFeet flat on the floor. Shoulders drop, even just half an inch. One slow exhale, longer than your inhale. Then gently press your palms together for a few seconds and release.\n\nThirty seconds won't fix a hard day. But it tells your body we're not in danger right now.\n\nTry it right now. Tell me how it felt \U0001F447",
        "video_filename": "post04_30-second-reset.mp4",
        "kind": "reel",
        "folder": "week2",
    },
    "stress-not-just-head": {
        "caption": " Stress isn't just in your head (most people don't realise this)\n\nYou can understand exactly why you're stressed, fully believe you should be fine, and still feel your chest tight and your stomach in knots. Stress is stored in the body, not just reasoned through in the mind.\n\nThis is why just don't think about it so rarely works.\n\nSend this to someone who needs to hear it \U0001F48C",
        "video_filename": "post05_stress-not-just-head.mp4",
        "kind": "reel",
        "folder": "week2",
    },
    "fight-flight-freeze-fawn": {
        "caption": " Which one are you? Fight, flight, freeze or fawn \U0001F440\n\nFight looks like irritability and snapping over small things. Flight looks like restlessness and overworking. Freeze looks like shutting down and going blank. Fawn looks like people-pleasing and saying yes when you mean no.\n\nMost people move through more than one in a single day.\n\nComment your number below \U0001F447",
        "video_filename": "post06_fight-flight-freeze-fawn.mp4",
        "kind": "reel",
        "folder": "week2",
    },
    "morning-habit": {
        "caption": " This morning habit is quietly wrecking your nervous system \U0001F4F5\n\nChecking your phone in the first sixty seconds after waking up. Before your body has even settled into being awake, it's already taking in notifications and things to react to.\n\nA few minutes of not reaching for it changes how the whole day lands on your body.\n\nReady to break the habit? Link in bio \U0001F517",
        "video_filename": "post07_morning-habit.mp4",
        "kind": "reel",
        "folder": "week2",
    },
    "hormones": {
        "caption": " 5 ways stress is messing with your hormones (number 3 surprised me)\n\nSleep hormones, hunger cues, your cycle, cortisol, and the hormones connected to feeling calm and connected to others. None of this means you did something wrong. It's your body responding to sustained pressure exactly as designed.\n\nSave this for later \U0001F4CC",
        "image_filenames": ["post08_slide1.jpg", "post08_slide2.jpg", "post08_slide3.jpg", "post08_slide4.jpg", "post08_slide5.jpg"],
        "kind": "carousel",
        "folder": "week2",
    },
    "before-bed": {
        "caption": " Do this 2 minutes before bed and thank me later \U0001F319\n\nLie down, hand on your belly. In through the nose for a count of four, out through the mouth for a count of six; exhale longer than the inhale, every time.\n\nA longer exhale reliably tells your nervous system it's safe to power down.\n\nTry it tonight. Let me know how it goes \U0001F447",
        "video_filename": "post09_before-bed.mp4",
        "kind": "reel",
        "folder": "week2",
    },
    "stopped-believing-about-rest": {
        "caption": " Things I stopped believing about rest \U0001F4AD\n\nThat it has to be earned. That it only counts if it's a whole day off. That pushing through tiredness is discipline. That rest comes after everything else is done.\n\nUnlearning these happened one small rest at a time, taken without asking permission first.\n\nWhich one hits home? Tell me below \U0001F447",
        "video_filename": "post10_stopped-believing-about-rest.mp4",
        "kind": "reel",
        "folder": "week2",
    },
    "signs-body-begging": {
        "caption": " Signs your body is begging you to slow down \U0001F6D1\n\nGetting sick right when you finally slow down. Losing patience faster than usual. Forgetting small things. Feeling touched-out. Daydreaming about doing absolutely nothing.\n\nThese aren't random. They're requests; usually quiet ones, at first.\n\nSave this for when you need the reminder \U0001F516",
        "video_filename": "post11_signs-body-begging.mp4",
        "kind": "reel",
        "folder": "week2",
    },
    "myths": {
        "caption": " Nervous system myths that are keeping you stuck ❌✅\n\nMyth: calming down is a mindset. Fact: it's a physical process your body has to go through. Myth: if you're not panicking, you're not dysregulated. Fact: numbness and shutdown are dysregulation too. Myth: more willpower fixes it. Fact: safety cues do. Myth: this is just how you are. Fact: nervous systems recalibrate, at any age.\n\nWhich myth did you believe? Let me know \U0001F447",
        "image_filenames": ["post12_slide1.jpg", "post12_slide2.jpg", "post12_slide3.jpg", "post12_slide4.jpg", "post12_slide5.jpg"],
        "kind": "carousel",
        "folder": "week2",
    },
    "body-language": {
        "caption": " What your body is trying to tell you (and why you're ignoring it) \U0001FAF6\n\nTension you can't relax on command. A stomach that reacts before you register you're anxious. A jaw clenched in your sleep.\n\nThese aren't malfunctions. They're your body's language.\n\nFollow along if this is new to you \U0001F331",
        "video_filename": "post13_body-language.mp4",
        "kind": "reel",
        "folder": "week2",
    },
    "journal-prompt": {
        "caption": " What does your body need most today? \U0001F90D\n\n“Where in my body do I usually feel it first when something is wrong, before I've even named what's wrong?”\n\nSit with that one for a minute before you write anything.\n\nLet me know today \U0001F447",
        "image_filename": "post14_static.jpg",
        "kind": "static",
        "folder": "week2",
    },
    "physiological-sigh": {
        "caption": " The fastest way to calm your nervous system (it's not what you think) \U0001F32C️\n\nTwo inhales through the nose, no pause between them, then one long, slow exhale through the mouth. It's called the physiological sigh. It's one of the fastest ways to calm your body that's actually backed by research.\n\nNot five minutes. Just one breath, whenever you need it.\n\nReady to feel calmer? Link in bio for more like this \U0001F517",
        "video_filename": "post15_physiological-sigh.mp4",
        "kind": "reel",
        "folder": "week2",
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
        folder = post.get("folder", "week1")
        # "carousel" = real swipeable multi-image post (separate image_filenames list).
        # Do NOT use the old "video" kind for new carousel-style content -- that rendered
        # a single slideshow video that only looked like slides, it was never swipeable.
        if post["kind"] == "carousel":
            ig_id = post_carousel_to_instagram(full_caption, post["image_filenames"], folder=folder)
            fb_result = post_carousel_to_facebook(post["caption"] + HASHTAGS, post["image_filenames"], folder=folder)
        elif post["kind"] == "static":
            ig_id = post_to_instagram(full_caption, image_filename=post["image_filename"], folder=folder)
            fb_result = post_to_facebook(post["caption"] + HASHTAGS, image_filename=post["image_filename"], folder=folder)
        else:
            is_reel = post["kind"] == "reel"
            thumb_offset_ms = 300 if post["kind"] == "video" else None
            ig_id = post_to_instagram(full_caption, video_filename=post["video_filename"], is_reel=is_reel, thumb_offset_ms=thumb_offset_ms, folder=folder)
            fb_result = post_to_facebook(post["caption"] + HASHTAGS, video_filename=post["video_filename"], folder=folder)
        with open(LOG_PATH, "a", encoding="utf-8") as f:
            f.write(f"{slug}: IG={ig_id} FB={fb_result}\n")
        print(f"{slug}: posted. IG={ig_id} FB={fb_result}")
    except Exception as e:
        with open(LOG_PATH, "a", encoding="utf-8") as f:
            f.write(f"{slug}: FAILED {e}\n")
        print(f"{slug}: FAILED {e}")
        raise
