from pathlib import Path
from dotenv import load_dotenv
import os
import discord
from discord.ext import commands
from datetime import datetime
import pytz
import asyncio
from threading import Thread

# Load environment variables from .env:
env_path = Path(".") / ".env"
load_dotenv(dotenv_path=env_path)

# Initialize the Discord bot:
client = commands.Bot(command_prefix="%", intents=discord.Intents.all())
posting_channel = None

def send_notification(notification):
    """
    Trigger the on_notification event of the Discord bot.
    """
    client.dispatch("notification", notification)

@client.event
async def on_ready():
    """
    Set up the posting channel and Bot's profile info on start-up:
    """
    global posting_channel
    await client.change_presence(activity=discord.Activity(
        type=discord.ActivityType.watching,
        name="the ACE Coding Slack #announcements channel"))
    posting_channel = client.get_channel(int(os.environ.get("DISCORD_POSTING_CHANNEL")))
    print("Discord bot is ready.")

@client.event
async def on_notification(notification):
    """
    Send out the notification in the form of (an) embed(s):
    """
    # Go through each embed in the notification:
    for notif_dict in notification:
        
        # If the channel is included as an attribute of the notification (It is the first embed),
        # preface the message with a description:
        notif_message = f"<@&{os.environ.get('DISCORD_MENTION_ID')}> New message posted in the " \
                        f"{' '.join(notif_dict.get('channel_name').split('-')).title()} "        \
                         "channel!" if notif_dict.get("channel_name") else ""
        
        # Initialize the embed with the ACE Coding Color™
        notif_embed = discord.Embed(
            colour=discord.Colour.from_rgb(145, 228, 163)
        )

        # Add all information from the notification to the embed:
        if notif_dict.get("notif_text"):
            notif_embed.description = notif_dict.get("notif_text")
        if notif_dict.get("notif_image"):
            notif_embed.set_image(
                url=notif_dict.get("notif_image")
            )
        if notif_dict.get("author_name"):
            notif_embed.set_author(
                name=notif_dict.get("author_name"),
                icon_url=notif_dict.get("author_icon")
            )
        if notif_dict.get("team_name"):
            notif_embed.set_footer(
                text=notif_dict.get("team_name"),
                icon_url=notif_dict.get("team_icon")
            )
        if notif_dict.get("timestamp"):
            notif_embed.timestamp = datetime.fromtimestamp(
                notif_dict.get("timestamp"),
                tz=pytz.timezone("US/Pacific")
            )

        # Send the embed:
        await posting_channel.send(notif_message, embed=notif_embed)

def init():
    """
    Run the Discord bot on its own thread so that it may run in parallel with
    the Slack bot
    """
    loop = asyncio.get_event_loop()
    loop.create_task(client.start(os.environ.get("DISCORD_BOT_TOKEN")))
    Thread(target=loop.run_forever).start()

# Run the bot (even when imported as a module):
init()