<img width="1502" height="1241" alt="image" src="https://github.com/user-attachments/assets/f3727114-f499-4ccd-b7df-a4cf77662ade" />

# YouTube discord bot

a discord bot for discord that watches multiple youtube channels and sends notifications to discord text channels and selected users via dm when new videos are uploaded.

---

## features

- monitors multiple youtube channels for new uploads.  
- announces new videos in a configurable text channel per discord server.  
- sends dms to a fixed list of user ids for every new upload.  
- uses slash command `/channel` to set the notification channel.  
- polls youtube every 5 minutes using the youtube data api v3.  

---

## requirements

- python 3.11+ installed.  
- a discord bot application and bot token.  
- a google cloud project with youtube data api v3 enabled and an api key.  
- python packages:  
  - `discord.py` (2.x)  
  - `google-api-python-client`  
  
---

## configuration

edit the top of `tmgdiscordbot.py`:

DISCORD_BOT_TOKEN = "your_discord_bot_token_here"
YOUTUBE_API_KEY = "your_youtube_api_key_here"

YOUTUBE_CHANNELS = [
"youtube_channel_id_1",
"youtube_channel_id_2",
"youtube_channel_id_3",
"youtube_channel_id_4",

USERS_TO_DM = [
111111111111111111,
222222222222222222,
333333333333333333,
444444444444444444,
555555555555555555,
666666666666666666,
777777777777777777,


- `youtube_channels`: ids of the channels the bot should watch.  
- `users_to_dm`: discord user ids that should receive dms for every new upload.  

keep the token and api key private and never commit them to git.

---

## how it works

- on startup the bot:  
  - logs in with the discord bot token.  
  - syncs slash commands globally.  
  - starts a background task loop that checks youtube every 5 minutes.  
- for each configured youtube channel:  
  - `get_latest_video(channel_id)` fetches the latest upload (video id, title, url).  
  - the first time a channel is seen, its latest video id is cached in `last_video_ids` with no notification (prevents spamming old videos).  
  - on later checks, if the video id changes, this is treated as a new upload.  
- when a new upload is detected:  
  - the bot sends a message to every configured guild channel.  
  - the bot sends a dm with the same message to each user in `users_to_dm`.  

---

## slash command

### `/channel #channel`

sets which text channel in the current guild receives upload notifications.

behavior:

- only works inside servers (not dms).  
- stores a mapping `guild_id -> channel_id` in memory.  
- replies ephemerally to confirm the channel selection.  

---

## running the bot

from the directory containing `tmgdiscordbot.py`:


you should see log output similar to:

- `discord.client logging in using static token`  
- `logged in as <botname>`  
- `slash commands synced.`  

leave this process running while you want the bot watching for new uploads. This runs locally on your machine, weather that's a raspberry pi or computer. You do have to run it everytime you turn off and on you're computer. But personally I might be looking into running it on my Synology NAS, so there's a lot of possibities that's there.

---

## recent changes compared to the original version

- converted the original youtube polling function into a normal `def get_latest_video(...)` and call it through `asyncio.to_thread(...)`, fixing the “coroutine was never awaited” and “cannot unpack non-iterable coroutine object” errors.  
- added a `last_video_ids` dictionary keyed by youtube channel id so the bot skips notifications on the very first check and only announces real new uploads.  
- introduced a `guild_channels` dictionary and a `/channel` slash command so each server can dynamically choose its notification channel instead of using hard-coded ids.  
- centralized configuration for `discord_bot_token`, `youtube_api_key`, `youtube_channels`, and `users_to_dm` at the top of the script for easier editing.  
- wrapped channel sends and dms in try/except blocks so a failure to message one channel or user does not stop the background loop.




