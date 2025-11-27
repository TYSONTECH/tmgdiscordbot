import asyncio
import discord
from discord.ext import tasks
from discord import app_commands
from googleapiclient.discovery import build

# ========= config (edit these privately) =========

DISCORD_BOT_TOKEN = "YOUR_DISCORD_BOT_TOKEN_HERE"
YOUTUBE_API_KEY   = "YOUR_YOUTUBE_API_KEY_HERE"

# youtube channel ids to track
YOUTUBE_CHANNELS = [
    "sixseven67sixseven,
    "sixseven67sixseven",
    "sixseven67sixseven",
    "sixseven67sixseven",
]

# discord user ids to dm on every new upload, yeah you know I had to do that 6 7
USERS_TO_DM = [
    676767676767676767,
    676767676767676767,
    676767676767676767,
    676767676767676767,
    676767676767676767,
    676767676767676767,
]

# ========= end config =========

# youtube api client
youtube = build("youtube", "v3", developerKey=YOUTUBE_API_KEY)

# discord client + slash-command tree
intents = discord.Intents.default()
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

# guild_id -> channel_id mapping (where to post in each server)
guild_channels: dict[int, int] = {}

# channel_id (youtube) -> last seen video id
last_video_ids: dict[str, str] = {}


def get_latest_video(channel_id: str):
    """return (video_id, title, url) for the latest upload on a channel."""
    # 1. get uploads playlist id
    response = youtube.channels().list(
        part="contentDetails",
        id=channel_id
    ).execute()

    items = response.get("items", [])
    if not items:
        return None

    uploads_playlist_id = items[0]["contentDetails"]["relatedPlaylists"]["uploads"]

    # 2. get most recent item from uploads playlist
    playlist_items = youtube.playlistItems().list(
        part="snippet",
        playlistId=uploads_playlist_id,
        maxResults=1
    ).execute()

    p_items = playlist_items.get("items", [])
    if not p_items:
        return None

    snippet = p_items[0]["snippet"]
    video_id = snippet["resourceId"]["videoId"]
    title = snippet["title"]
    url = f"https://www.youtube.com/watch?v={video_id}"
    return video_id, title, url


@tasks.loop(minutes=5)
async def check_new_videos():
    """background loop that checks youtube every 5 minutes."""
    await client.wait_until_ready()

    for yt_channel in YOUTUBE_CHANNELS:
        try:
            # run blocking youtube call in a separate thread
            latest = await asyncio.to_thread(get_latest_video, yt_channel)
            if latest is None:
                continue

            video_id, title, url = latest

            # first time: just store and skip sending (avoid spam on startup)
            if yt_channel not in last_video_ids:
                last_video_ids[yt_channel] = video_id
                continue

            # new video detected
            if last_video_ids[yt_channel] != video_id:
                last_video_ids[yt_channel] = video_id

                msg = f"📢 new video uploaded: **{title}**\n{url}"

                # send to all configured guild channels
                for guild_id, channel_id in guild_channels.items():
                    channel = client.get_channel(channel_id)
                    if channel is not None:
                        try:
                            await channel.send(msg)
                        except Exception as e:
                            print(f"failed to send message to channel {channel_id}: {e}")

                # dm all configured users
                for user_id in USERS_TO_DM:
                    try:
                        user = await client.fetch_user(user_id)
                        await user.send(msg)
                    except Exception as e:
                        print(f"failed to dm {user_id}: {e}")

        except Exception as e:
            print(f"error while checking channel {yt_channel}: {e}")


@client.event
async def on
