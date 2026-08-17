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
    # Week 2/3 (post02-post15), approved 2026-08-04 after 3 review rounds
    # (format/music/voice fixes, then pacing fix, then speed pass). post02
    # (rest-uncomfortable) was posted manually on 2026-08-04 itself since the
    # day's 10:00 UTC cron window had already passed before approval landed;
    # remaining dates start the next day.
    "2026-08-04": "rest-uncomfortable",
    "2026-08-05": "five-things-dont-calm",
    "2026-08-06": "30-second-reset",
    "2026-08-07": "stress-not-just-head",
    "2026-08-08": "fight-flight-freeze-fawn",
    "2026-08-09": "morning-habit",
    "2026-08-10": "hormones",
    "2026-08-11": "before-bed",
    "2026-08-12": "stopped-believing-about-rest",
    "2026-08-13": "signs-body-begging",
    "2026-08-14": "myths",
    "2026-08-15": "body-language",
    "2026-08-16": "journal-prompt",
    "2026-08-17": "physiological-sigh",
    # Week 3 (15 posts: intro relaunch + 14 reels), approved 2026-08-17, drawn
    # from the ~85-item review batch. See folder "week3".
    "2026-08-18": "welcome-questions",
    "2026-08-19": "brain-fog",
    "2026-08-20": "three-signals",
    "2026-08-21": "cold-water-vagus",
    "2026-08-22": "one-hormone-test",
    "2026-08-23": "reset-when-scattered",
    "2026-08-24": "three-stages-breath",
    "2026-08-25": "vagus-nerve-101",
    "2026-08-26": "ache-shows-up-late",
    "2026-08-27": "starting-things-easier",
    "2026-08-28": "capacity-changes-daily",
    "2026-08-29": "small-recoveries",
    "2026-08-30": "overwhelm-realization",
    "2026-08-31": "energy-drop-before-period",
    "2026-09-01": "chronic-stress-personality",
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
        "caption": " One of the most overlooked signs of a tired nervous system \U0001F440\n\nIf resting makes you feel restless instead of relaxed, you're not failing at rest.\n\nFor a nervous system that's used to being “on,” stillness can feel unfamiliar, or even unsafe, before it starts to feel safe.\n\nThat discomfort isn't a sign to push through.\n\nIt's a sign to start smaller.\n\nDo you recognise this in yourself? Let me know in the comments. \U0001F447",
        "video_filename": "post02_rest-uncomfortable.mp4",
        "kind": "reel",
        "folder": "week2",
    },
    "five-things-dont-calm": {
        "caption": " If relaxing feels impossible, your nervous system may be doing exactly what it has learned to do \U0001F440\n\nWhen your body has been in survival mode for a long time, slowing down doesn't always feel calming.\n\nIt can feel uncomfortable. You might suddenly notice your thoughts racing. Feel restless. Want to grab your phone. Start cleaning. Or find something, anything, to keep yourself busy.\n\nNot because you're bad at resting.\n\nBut because your nervous system has learned that doing feels safer than being.\n\nThe goal isn't to force yourself to relax. It's to help your body discover that slowing down is safe again, one small moment at a time.\n\nHave you ever noticed this happening? \U0001F447",
        "image_filenames": ["post03_slide1.jpg", "post03_slide2.jpg", "post03_slide3.jpg", "post03_slide4.jpg", "post03_slide5.jpg"],
        "kind": "carousel",
        "folder": "week2",
    },
    "30-second-reset": {
        "caption": " Your nervous system responds to your body before it responds to your thoughts \U0001F440\n\nThat's why telling yourself “calm down” often doesn't work.\n\nYour body needs signals of safety too.\n\nTry this 30-second reset. Place both feet on the floor. Let your shoulders soften. Take one slow exhale, slightly longer than your inhale. Gently press your palms together for a few seconds, then release.\n\nYou're not forcing yourself to relax.\n\nYou're giving your nervous system a new message: I can slow down right now.\n\nThirty seconds won't fix everything.\n\nBut small moments like this teach your body a different pattern over time.\n\nTry it now. Notice what changes. \U0001F447",
        "video_filename": "post04_30-second-reset.mp4",
        "kind": "reel",
        "folder": "week2",
    },
    "stress-not-just-head": {
        "caption": " Stress isn't just in your head. Your body is part of the conversation \U0001F440\n\nYou can understand exactly why you're stressed. You can know you're safe. You can tell yourself, “I should be fine.”\n\nAnd still feel your chest tighten, your jaw clench, or your stomach knot.\n\nThat's because your nervous system doesn't only respond to your thoughts. It responds to patterns your body has learned over time.\n\nThis is why thinking your way out of stress isn't always enough.\n\nSometimes your body needs to experience safety, not just understand it.\n\nSave this for when you need the reminder \U0001F4CC",
        "video_filename": "post05_stress-not-just-head.mp4",
        "kind": "reel",
        "folder": "week2",
    },
    "fight-flight-freeze-fawn": {
        "caption": " Which stress response do you recognise most? \U0001F440\n\nWhen your nervous system senses stress, it tries to protect you.\n\nIt may move into fight: irritability, frustration, snapping over small things.\n\nOr flight: restlessness, overworking, always needing to do more.\n\nOr freeze: shutting down, feeling numb, going blank.\n\nOr fawn: people-pleasing, avoiding conflict, saying yes when you mean no.\n\nThese aren't personality flaws.\n\nThey're protective responses your body learned to use.\n\nAnd most people move between more than one, sometimes even in the same day.\n\nWhich one do you notice most in yourself? \U0001F447",
        "video_filename": "post06_fight-flight-freeze-fawn.mp4",
        "kind": "reel",
        "folder": "week2",
    },
    "morning-habit": {
        "caption": " Which stress response do you recognise most? \U0001F440\n\nWhen your nervous system senses stress, it tries to protect you.\n\nIt may move into fight: irritability, frustration, snapping over small things.\n\nOr flight: restlessness, overworking, always needing to do more.\n\nOr freeze: shutting down, feeling numb, going blank.\n\nOr fawn: people-pleasing, avoiding conflict, saying yes when you mean no.\n\nThese aren't personality flaws.\n\nThey're protective patterns your nervous system uses to help you cope.\n\nThe good news? These patterns can be gently shifted through awareness, safety and new experiences in the body.\n\nThat's exactly what the Nervous System Reset Kit was created for: simple daily tools to help you reconnect with your body and create more moments of calm.\n\nExplore the Reset Kit through the link in bio \U0001F331",
        "video_filename": "post07_morning-habit.mp4",
        "kind": "reel",
        "folder": "week2",
    },
    "hormones": {
        "caption": " 5 ways chronic stress can affect your hormones (and your body's signals)\n\nStress doesn't just affect your thoughts. Your body is constantly adjusting to the signals it receives.\n\nWhen stress becomes ongoing, your nervous system can start prioritising survival over balance.\n\nThis can influence your sleep, appetite, energy, cycle and even how connected you feel to yourself and others.\n\nIt doesn't mean your body is broken.\n\nIt means your body has been trying to protect you.\n\nLearning to listen to these signals is the first step toward supporting your nervous system.\n\nSave this for when you need the reminder \U0001F4CC",
        "image_filenames": ["post08_slide1.jpg", "post08_slide2.jpg", "post08_slide3.jpg", "post08_slide4.jpg", "post08_slide5.jpg", "post08_slide6.jpg"],
        "kind": "carousel",
        "folder": "week2",
    },
    "before-bed": {
        "caption": " Try this 2-minute reset before bed \U0001F319\n\nIf your body feels tired but your mind is still switched on, try this.\n\nLie down and place one hand on your belly.\n\nBreathe in through your nose for a count of 4. Exhale slowly for a count of 6. Repeat.\n\nA longer exhale can support your nervous system in shifting out of a stress state and into a more restful state.\n\nYou're not forcing yourself to sleep.\n\nYou're creating a moment of safety and slowing down.\n\nWant more simple practices like this? Find the Nervous System Reset Kit through the link in bio \U0001F331",
        "video_filename": "post09_before-bed.mp4",
        "kind": "reel",
        "folder": "week2",
    },
    "stopped-believing-about-rest": {
        "caption": " Things I stopped believing about rest \U0001F4AD\n\nThat rest has to be earned.\n\nThat it only counts if I have a whole day with nothing planned.\n\nThat pushing through exhaustion is discipline.\n\nThat I can only slow down once everything is finished.\n\nThe truth? Rest isn't something you have to deserve. It's something your body needs to function, regulate and reconnect.\n\nUnlearning these beliefs happened slowly, one small moment of rest at a time.\n\nNot because I had permission.\n\nBecause I started listening.\n\nWhich one do you need to let go of? \U0001F447",
        "video_filename": "post10_stopped-believing-about-rest.mp4",
        "kind": "reel",
        "folder": "week2",
    },
    "signs-body-begging": {
        "caption": " Subtle signs your body may be asking you to slow down \U0001F6D1\n\nGetting sick right when you finally slow down.\n\nLosing patience faster than usual.\n\nForgetting small things.\n\nFeeling touched-out or overwhelmed by little things.\n\nDaydreaming about doing absolutely nothing.\n\nThese aren't random signs.\n\nThey're often your body's way of telling you that your capacity has been stretched for too long.\n\nYour body usually whispers before it starts shouting.\n\nSave this for the days you need the reminder \U0001F516",
        "video_filename": "post11_signs-body-begging.mp4",
        "kind": "reel",
        "folder": "week2",
    },
    "myths": {
        "caption": " Nervous system myths that are keeping you stuck ❌✅\n\nMyth: calming down is a mindset. Fact: it's a physical process your body has to go through.\n\nMyth: if you're not panicking, you're not dysregulated. Fact: numbness and shutdown are dysregulation too.\n\nMyth: more willpower fixes it. Fact: safety cues do.\n\nMyth: this is just how you are. Fact: nervous systems recalibrate, at any age.\n\nMyth: once you're 'healed', you'll feel calm all the time. Fact: regulation means flexibility, not permanent calm.\n\nWhich myth did you believe? Let me know \U0001F447",
        "image_filenames": ["post12_slide1.jpg", "post12_slide2.jpg", "post12_slide3.jpg", "post12_slide4.jpg", "post12_slide5.jpg", "post12_slide6.jpg"],
        "kind": "carousel",
        "folder": "week2",
    },
    "body-language": {
        "caption": " Your body can react to a threat before your conscious mind even registers what happened \U0001F440\n\nThat's why your stomach can drop, or your jaw can clench, before you consciously know why.\n\nIt's not overreacting. It's your nervous system scanning for safety faster than your thinking brain can keep up.\n\nScientists call this neuroception: a constant background scan for danger or safety that runs underneath your awareness.\n\nThe more familiar you get with your own early signals, tight shoulders, a held breath, a clenched jaw, the sooner you can respond instead of just reacting.\n\nWhat's the first place you usually feel it? \U0001F447",
        "video_filename": "post13_body-language.mp4",
        "kind": "reel",
        "folder": "week2",
    },
    "journal-prompt": {
        "caption": " What does your body need most today? \U0001F90D\n\nMost of us notice a feeling in our head first: a thought, a worry, a story. But your body usually feels it first, if you know how to check.\n\n“Where in my body do I usually feel it first when something is wrong, before I've even named what's wrong?”\n\nSit with that one for a minute before you write anything.\n\nLet me know today \U0001F447",
        "image_filename": "post14_static.jpg",
        "kind": "static",
        "folder": "week2",
    },
    "physiological-sigh": {
        "caption": " The fastest way to calm your nervous system takes less than 30 seconds, and it's not deep breathing \U0001F32C️\n\nTwo short inhales through the nose, no pause between them, followed by one long, slow exhale through the mouth.\n\nIt's called the physiological sigh, and unlike most breathing techniques, it's backed by actual research on how the body regulates itself.\n\nThe double inhale fully reinflates your lungs, and the long exhale signals your nervous system to slow your heart rate down, right there in the moment.\n\nNot five minutes. Just one breath, whenever you need it.\n\nTry it right now. Notice what shifts \U0001F447",
        "video_filename": "post15_physiological-sigh.mp4",
        "kind": "reel",
        "folder": "week2",
    },
    'welcome-questions': {
        "caption": 'You know your body. But were you ever taught how to understand it? 🌿\n\nWhy does your energy change throughout your cycle?\nWhy can your body feel restless when your mind feels completely fine?\nWhy does a deep breath sometimes change more than you expected? 🫁\nWhy can the same experience feel completely different from one day to the next?\n\nThese are the kinds of questions we explore here.\n\n𝐓𝐡𝐞 𝐁𝐨𝐝𝐲 𝐖𝐢𝐬𝐝𝐨𝐦 brings together nervous system awareness, hormonal health, cycle wisdom, body awareness, and simple practices to help you understand yourself a little better.\n\n𝑁𝑜𝑡𝑖𝑐𝑒. 𝑈𝑛𝑑𝑒𝑟𝑠𝑡𝑎𝑛𝑑. 𝑅𝑒𝑠𝑝𝑜𝑛𝑑.\n\nWelcome. This is where we begin. 🤍',
        "video_filename": 'post01_welcome-questions.mp4',
        "kind": "reel",
        "folder": "week3",
    },
    'brain-fog': {
        "caption": 'This is something I see people misunderstand all the time: 𝐛𝐫𝐚𝐢𝐧 𝐟𝐨𝐠 gets blamed on sleep almost by default. Not enough of it, or not the right kind. ✨\n\nSleep matters, but hormonal shifts across the month can also affect focus and mental clarity on their own. Which means a foggy week that follows good sleep isn\'t automatically a mystery.\n\nIt might just be a different part of the cycle asking for a different kind of attention. 💜',
        "video_filename": 'post02_brain-fog.mp4',
        "kind": "reel",
        "folder": "week3",
    },
    'three-signals': {
        "caption": 'There are 𝑡ℎ𝑟𝑒𝑒 𝑤𝑎𝑦𝑠 your body typically asks for attention, from quietest to loudest. 👉\n\n𝐅𝐢𝐫𝐬𝐭: a subtle shift, slightly less energy, slightly more tension, easy to miss.\n𝐒𝐞𝐜𝐨𝐧𝐝: a repeated pattern, the same ache or fog showing up again and again.\n𝐓𝐡𝐢𝐫𝐝: the one that finally gets a response, a symptom loud enough to actually stop you.\n\nCatching it at stage one usually takes far less than waiting for stage three. ✨\n\nThe 𝐑𝐞𝐬𝐞𝐭 𝐊𝐢𝐭 is built for exactly that first stage, short daily practices that help you catch the subtle shift before it becomes a pattern.\n\nLink in bio if you want to start there. 💜',
        "video_filename": 'post03_three-signals.mp4',
        "kind": "reel",
        "folder": "week3",
    },
    'cold-water-vagus': {
        "caption": 'Ever splash cold water on your face when you\'re overwhelmed and feel an almost instant shift? 🫁\n\nThat\'s not just a mental reset, it\'s a real physiological one. Cold on the face triggers what\'s called the 𝐝𝐢𝐯𝐞 𝐫𝐞𝐟𝐥𝐞𝐱, which slows your heart rate through the 𝐯𝐚𝐠𝐮𝐬 𝐧𝐞𝐫𝐯𝐞 almost immediately. It\'s one of the fastest ways to interrupt a spiral, faster than most breathing techniques on their own.\n\n👉 Next time you\'re activated: thirty seconds of cold water on your face and jaw, over your eyes if you can.\n\nWorth having in your back pocket. ✨\n\nMore practices like this live inside the Reset Kit, short, guided ways to work with your nervous system in the moment.\n\nLink in bio. 💜',
        "video_filename": 'post04_cold-water-vagus.mp4',
        "kind": "reel",
        "folder": "week3",
    },
    'one-hormone-test': {
        "caption": 'A result comes back in range, you still feel how you feel, and now you also feel unreasonable for asking. 🍃\n\nMost hormones move by the hour and by the week. A single sample catches 𝐨𝐧𝐞 𝐟𝐫𝐚𝐦𝐞 of that movement, like a 𝑝ℎ𝑜𝑡𝑜, 𝑛𝑜𝑡 𝑎 𝑓𝑖𝑙𝑚. Same body, different morning, different number, and both can be accurate.\n\nThis isn\'t a reason to distrust testing. It\'s a reason to hold one data point loosely and pay attention to your own pattern over weeks. That\'s information no single draw can give you. ✨',
        "video_filename": 'post05_one-hormone-test.mp4',
        "kind": "reel",
        "folder": "week3",
    },
    'reset-when-scattered': {
        "caption": 'A 𝟑𝟎-𝐬𝐞𝐜𝐨𝐧𝐝 𝐫𝐞𝐬𝐞𝐭 for when you feel scattered. Not a fix, just a small interruption. 🌿\n\n👉 Try this when you notice you\'ve been running on autopilot: name five things you can see without moving your head, then notice one thing you can feel, the chair, your feet, your own hands.\n\nThirty seconds, and your attention has somewhere to land. This is one of several resets built into the Reset Kit, ready for exactly this kind of moment. ✨\n\nLink in bio. 💜',
        "video_filename": 'post06_reset-when-scattered.mp4',
        "kind": "reel",
        "folder": "week3",
    },
    'three-stages-breath': {
        "caption": 'There are three stages to a breath you didn\'t know you were holding, and the third one is the important part. 🫁\n\n𝐅𝐢𝐫𝐬𝐭: a shallow pattern that\'s been running for a while without you noticing.\n𝐒𝐞𝐜𝐨𝐧𝐝: a tightness across the chest or upper back that seems to come from nowhere.\n𝐓𝐡𝐢𝐫𝐝: the moment you finally exhale fully and feel how much you\'d actually been holding.\n\nThat third moment is usually 𝑡ℎ𝑒 𝑓𝑖𝑟𝑠𝑡 𝑠𝑖𝑔𝑛 of how long the first two had been running. ✨',
        "video_filename": 'post07_three-stages-breath.mp4',
        "kind": "reel",
        "folder": "week3",
    },
    'vagus-nerve-101': {
        "caption": 'If you keep hearing \'𝐯𝐚𝐠𝐮𝐬 𝐧𝐞𝐫𝐯𝐞\' and aren\'t totally sure what it means, start here. 🫁\n\nIt\'s the longest nerve in your body, running from your brainstem down through your neck, chest, and abdomen. It\'s the main driver of your parasympathetic nervous system, the part responsible for rest, digestion, and recovery. A well-toned vagus nerve tends to mean quicker recovery from stress, better digestion, and steadier mood.\n\n👉 It responds to things you can actually practice: slow breathing, cold exposure, humming, and social connection.\n\nThat\'s the whole picture, we\'ll go deeper from here. ✨\n\nYou\'ll find more of this kind of breakdown, plus the practices that go with it, on the website and in our tools.\n\nLink in bio. 💜',
        "video_filename": 'post08_vagus-nerve-101.mp4',
        "kind": "reel",
        "folder": "week3",
    },
    'ache-shows-up-late': {
        "caption": 'This is something I see people misunderstand all the time: the ache shows up on Wednesday, but the week that caused it happened days ago. ✨\n\nWe tend to assume the body reacts in real time, matching stress to soreness minute by minute. Often it doesn\'t. It 𝐥𝐨𝐠𝐬, and it releases later, sometimes once the pressure has actually started to ease.\n\nWhich is why 𝑡ℎ𝑒 𝑡𝑒𝑛𝑠𝑖𝑜𝑛 𝑐𝑎𝑛 𝑎𝑟𝑟𝑖𝑣𝑒 𝑟𝑖𝑔ℎ𝑡 𝑤ℎ𝑒𝑛 𝑡ℎ𝑖𝑛𝑔𝑠 𝑓𝑖𝑛𝑎𝑙𝑙𝑦 𝑐𝑎𝑙𝑚 𝑑𝑜𝑤𝑛. 🌿',
        "video_filename": 'post09_ache-shows-up-late.mp4',
        "kind": "reel",
        "folder": "week3",
    },
    'starting-things-easier': {
        "caption": 'An idea that felt like a mountain two weeks ago suddenly feels doable, and nothing about the idea changed. 🍃\n\nIn the days after a period, 𝐞𝐬𝐭𝐫𝐨𝐠𝐞𝐧 tends to rise, and for a lot of people that overlaps with more appetite for new things and slightly more tolerance for uncertainty. Not a rule, a pattern worth checking against your own months.\n\n👉 If it does hold for you, it\'s usable: start the hard thing in the week starting is cheap, and let the other weeks carry it. 💜',
        "video_filename": 'post10_starting-things-easier.mp4',
        "kind": "reel",
        "folder": "week3",
    },
    'capacity-changes-daily': {
        "caption": 'Your 𝐜𝐚𝐩𝐚𝐜𝐢𝐭𝐲 can change from day to day. Not because you\'re inconsistent, because your nervous system isn\'t running the same script every day, even when your schedule looks identical. ✨\n\nSleep, food, noise, other people\'s moods, all of it counts.\n\n𝑆𝑜𝑚𝑒 𝑑𝑎𝑦𝑠 ℎ𝑜𝑙𝑑 𝑚𝑜𝑟𝑒. 𝑆𝑜𝑚𝑒 𝑑𝑎𝑦𝑠 ℎ𝑜𝑙𝑑 𝑙𝑒𝑠𝑠. 𝐵𝑜𝑡ℎ 𝑎𝑟𝑒 𝑠𝑡𝑖𝑙𝑙 𝑦𝑜𝑢. 💜',
        "video_filename": 'post11_capacity-changes-daily.mp4',
        "kind": "reel",
        "folder": "week3",
    },
    'small-recoveries': {
        "caption": 'The plan is always the same: get through this, then recover properly. The proper recovery never quite arrives. ✨\n\nLoad builds continuously, so recovery that only happens afterwards is always working against a 𝐛𝐚𝐜𝐤𝐥𝐨𝐠. Small returns during the day are working against a much smaller number.\n\n👉 Two minutes between tasks. Eating one meal without a screen. A walk without a podcast in your ears. 𝑈𝑛𝑖𝑚𝑝𝑟𝑒𝑠𝑠𝑖𝑣𝑒, 𝑎𝑛𝑑 𝑡ℎ𝑒𝑦 𝑐𝑜𝑢𝑛𝑡.\n\nIf you\'d like a version that fits into the day you already have, the free assessment points you to the right one. 💜',
        "video_filename": 'post12_small-recoveries.mp4',
        "kind": "reel",
        "folder": "week3",
    },
    'overwhelm-realization': {
        "caption": 'A small realization worth having about overwhelm. ✨\n\nIt\'s not always a sign something\'s wrong. Sometimes it\'s just a nervous system that hasn\'t been given a way to 𝐝𝐢𝐬𝐜𝐡𝐚𝐫𝐠𝐞 𝐚𝐜𝐭𝐢𝐯𝐚𝐭𝐢𝐨𝐧. The feeling can build even when nothing new is happening, simply because it never got a chance to move through.\n\nWhich means the fix isn\'t always solving a problem, sometimes it\'s just movement:\n\n👉 a walk, a shake-out, a few minutes of humming.\n\nSmall realization, different first response next time. 🌿\n\nIf movement is the thing that helps, the Reset Kit has a short practice built around exactly that kind of release.\n\nLink in bio. 💜',
        "video_filename": 'post13_overwhelm-realization.mp4',
        "kind": "reel",
        "folder": "week3",
    },
    'energy-drop-before-period': {
        "caption": 'Why does your energy sometimes drop a full day before your period actually starts? It can feel like your body is 𝑎 𝑠𝑡𝑒𝑝 𝑎ℎ𝑒𝑎𝑑 𝑜𝑓 𝑡ℎ𝑒 𝑐𝑎𝑙𝑒𝑛𝑑𝑎𝑟. 🍃\n\nIn a sense, it often is. Hormone levels can shift noticeably in the day or two before bleeding begins, before there\'s any visible sign at all.\n\nThe dip isn\'t random. It may just be arriving earlier than the evidence does. ✨',
        "video_filename": 'post14_energy-drop-before-period.mp4',
        "kind": "reel",
        "folder": "week3",
    },
    'chronic-stress-personality': {
        "caption": 'I\'m just an anxious person. I\'ve always been impatient. I don\'t really relax, that\'s just me. ✨\n\nWhen something is constant it stops registering as a state. There\'s no contrast left to measure it against, so it quietly gets filed as 𝐜𝐡𝐚𝐫𝐚𝐜𝐭𝐞𝐫 𝐢𝐧𝐬𝐭𝐞𝐚𝐝 𝐨𝐟 𝐜𝐢𝐫𝐜𝐮𝐦𝐬𝐭𝐚𝐧𝐜𝐞.\n\nIt\'s part of why a proper stretch away can be disorienting rather than pleasant. 𝑌𝑜𝑢 𝑚𝑒𝑒𝑡 𝑎 𝑣𝑒𝑟𝑠𝑖𝑜𝑛 𝑜𝑓 𝑦𝑜𝑢𝑟𝑠𝑒𝑙𝑓 𝑦𝑜𝑢\'𝑑 𝑠𝑡𝑜𝑝𝑝𝑒𝑑 𝑒𝑥𝑝𝑒𝑐𝑡𝑖𝑛𝑔 𝑡𝑜 𝑠𝑒𝑒. 💜',
        "video_filename": 'post15_chronic-stress-personality.mp4',
        "kind": "reel",
        "folder": "week3",
    },
}

def already_posted_slugs():
    if not os.path.exists(LOG_PATH):
        return set()
    with open(LOG_PATH, encoding="utf-8") as f:
        return {line.split(":", 1)[0].strip() for line in f if ": IG=" in line}


if __name__ == "__main__":
    if len(sys.argv) > 1:
        slug = sys.argv[1]
    else:
        today = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d")
        posted = already_posted_slugs()
        # Post the OLDEST not-yet-posted scheduled date up to and including today,
        # not just today's exact date. A plain today-only lookup means a single
        # missed run (e.g. a GitHub-hosted-runner infra hiccup, see 2026-08-06)
        # skips that day's post forever with no retry, since tomorrow's run only
        # ever looks at tomorrow's date. This makes a missed day self-heal on the
        # very next run instead.
        slug = None
        for d in sorted(d for d in DATE_TO_SLUG if d <= today):
            candidate = DATE_TO_SLUG[d]
            if candidate not in posted:
                slug = candidate
                break
        if slug is None:
            print(f"No unposted post due by {today}, nothing to do.")
            sys.exit(0)

    post = POSTS[slug]
    full_caption = post["caption"] + HASHTAGS

    if slug in already_posted_slugs():
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
