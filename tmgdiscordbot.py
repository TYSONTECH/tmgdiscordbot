import asyncio
import discord
from discord.ext import tasks
from discord import app_commands
from googleapiclient.discovery import build

# ========= CONFIG (FILL THESE IN PRIVATELY) =========

DISCORD_BOT_TOKEN = "YOUR_DISCORD_BOT_TOKEN_HERE"
YOUTUBE_API_KEY = "YOUR_YOUTUBE_API_KEY_HERE"

# find your youtube channel id and put it here, if you don't have multiple just delete the ones you don't use.
YOUTUBE_CHANNELS = [
    "YOUTUBE_CHANNEL_ID_1",
    "YOUTUBE_CHANNEL_ID_2",
    "YOUTUBE_CHANNEL_ID_3",
    "YOUTUBE_CHANNEL_ID_4",
]

# specific users you want to DM
USERS_TO_DM = [
    111111111111111111,
    222222222222222222,
    333333333333333333,
    444444444444444444,
    555555555555555555,
    666666666666666666,
]

# ========= END CONFIG =========

# youtube api stuff, again just put your api key
youtube = build("youtube", "v3", developerKey=YOUTUBE_API_KEY)

# discord client and the slash command tree
intents = discord.Intents.default()
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

# guild_id -> channel_id mapping (where to post in each server)
guild_channels: dict[int, int] = {}

# channel_id (YouTube) -> last seen video id
last_video_ids: dict[str, str] = {}


async def get_latest_video(channel_id: str):
    """Return (video_id, title, url) for the latest upload on a channel."""
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
    """Background loop that checks YouTube every 5 minutes."""
    await client.wait_until_ready()

    for yt_channel in YOUTUBE_CHANNELS:
        try:
            latest = await asyncio.to_thread(get_latest_video, yt_channel)
            if latest is None:
                continue

            video_id, title, url = latest

            # first time: just store and skip sending (so it doesn't spam old videos at startup)
            if yt_channel not in last_video_ids:
                last_video_ids[yt_channel] = video_id
                continue

            # new video detected
            if last_video_ids[yt_channel] != video_id:
                last_video_ids[yt_channel] = video_id

                msg = f"📢 New video uploaded: **{title}**\n{url}"

                # send to all configured guild channels
                for guild_id, channel_id in guild_channels.items():
                    channel = client.get_channel(channel_id)
                    if channel is not None:
                        try:
                            await channel.send(msg)
                        except Exception as e:
                            print(f"Failed to send message to channel {channel_id}: {e}")

                # DM all configured users
                for user_id in USERS_TO_DM:
                    try:
                        user = await client.fetch_user(user_id)
                        await user.send(msg)
                    except Exception as e:
                        print(f"failed to dm {user_id}: {e}")

        except Exception as e:
            print(f"Error while checking channel {yt_channel}: {e}")


@client.event
async def on_ready():
    print(f"Logged in as {client.user} (ID: {client.user.id})")

    # sync slash commands to all guilds the bot is in
    try:
        await tree.sync()
        print("Slash commands synced.")
    except Exception as e:
        print(f"Failed to sync commands: {e}")

    # start background task
    if not check_new_videos.is_running():
        check_new_videos.start()


# ========= SLASH COMMANDS =========

@tree.command(name="channel", description="Set which channel gets YouTube upload notifications.")
@app_commands.describe(target_channel="Channel to receive notifications")
async def set_channel(
    interaction: discord.Interaction,
    target_channel: discord.TextChannel
):
    """Slash command: /channel #channel"""
    guild = interaction.guild
    if guild is None:
        await interaction.response.send_message(
            "This command can only be used in a server.",
            ephemeral=True
        )
        return

    guild_channels[guild.id] = target_channel.id
    await interaction.response.send_message(
        f"Notifications will now be sent in {target_channel.mention}.",
        ephemeral=True
    )


# ========= RUN BOT =========

client.run(DISCORD_BOT_TOKEN)
