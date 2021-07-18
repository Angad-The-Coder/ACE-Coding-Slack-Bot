from pathlib import Path
from dotenv import load_dotenv
import os
from slack_bolt import App
from helpers.numbering_tools import get_numbering
from discordbot import send_notification

# SETUP

# Load environment variables from .env:
env_path = Path(".") / ".env"
load_dotenv(dotenv_path=env_path)
bot_token = os.environ.get("SLACK_BOT_TOKEN")
bot_secret = os.environ.get("SLACK_SIGNING_SECRET")
listening_channels = os.environ.get("SLACK_LISTENING_CHANNELS").split(" ")

# Initialize app with token and signing secret:
app = App(
    token=bot_token,
    signing_secret=bot_secret
)

# HELPER FUNCTIONS:

def format_rich_text(rich_text_section):
    """
    Convert a Slack rich_text_section to Discord-friendly markup.
    """
    formatted_text = ""

    for elem in rich_text_section.get("elements", []):
        elem_type = elem.get("type")
        if elem_type == "broadcast":
            # Convert broadcasts to Discord-friendly pings:
            broadcast_range = elem.get("range")
            if broadcast_range == "channel":
                elem_text = "@everyone"
            elif broadcast_range == "here":
                elem_text = "@here"
        elif elem_type == "emoji":
            emoji_list = app.client.emoji_list().get("emoji", {})
            if emoji_list.get(elem.get("name")):
                elem_text = f":{elem.get('name')}:"
            else:
                print(f"Skipping over nonstandard emoji {elem.get('name', 'NO NAME')}")
                continue
        elif elem_type == "user":
            # Convert @{user ID} to @{user name}:
            user_info = app.client.users_info(
                user=elem.get("user_id")
            ).get("user", {})
            user_name = user_info.get("profile", {}).get("display_name")
            if not user_name:
                # If user has no display_name (is a bot), use real_name:
                user_name = user_info.get("real_name")
            if not user_name:
                # If user has no name, skip mention altogether:
                print("Skipping over user mention with no associated name.")
                continue
            elem_text = f"@{user_name}"
        else:
            elem_text = elem.get("text", "")
        
        style = elem.get("style", {})

        # Prevent plain text from being rendered as markup:
        # (Code blocks by default have no markup)
        if not style.get("code"):
            elem_text = elem_text.replace("_", "\_")
            elem_text = elem_text.replace("*", "\*")
            elem_text = elem_text.replace("`", "\`")
            elem_text = elem_text.replace(">", "\>")

        # Apply appropriate styles to element's text:
        if style.get("bold") or elem_type == "user":
            elem_text = f"**{elem_text}**"
        if style.get("italic"):
            elem_text = f"*{elem_text}*"
        if style.get("strike"):
            elem_text = f"~~{elem_text}~~"
        if style.get("code"):
            elem_text = f"`{elem_text}`"

        # If element is a link, add the URL in Discord-friendly format:
        # "[ hyperlink text ]( URL )"
        if elem_type == "link":
            elem_text = f"[{elem_text}]({elem.get('url')})"

        # add formatted element's text to final markup string:
        formatted_text += elem_text

    # return final markup string:
    return formatted_text


def format_rich_list(rich_text_list):
    """
    Convert a Slack rich_text_list to Discord-friendly markup.
    """
    list_style = rich_text_list.get("style")
    list_indent = rich_text_list.get("indent")
    list_items = []
    for idx, elem in enumerate(rich_text_list.get("elements", [])):
        elem_text = format_rich_text(elem)
        elem_text = "\u3000" * list_indent                        \
                  + get_numbering(idx+1, list_style, list_indent) \
                  + " " + elem_text
        list_items.append(elem_text)
    return "\n".join(list_items) + "\n"

def format_rich_quote(rich_text_quote):
    """
    Convert a Slack rich_text_quote to Discord-friendly markup. 
    """
    rich_text = format_rich_text(rich_text_quote)
    return "> " + "\n> ".join(rich_text.split("\n")) + "\n"

def format_rich_preformatted(rich_text_preformatted):
    """
    Convert a Slack rich_text_preformatted to Discord-friendly markup. 
    """
    preformatted_text = ""
    for elem in rich_text_preformatted.get("elements", []):
        elem_text = elem.get("text")
        if elem_text:
            preformatted_text += elem_text
    return f"```\n{preformatted_text}```"


@app.event("message")
def add_notification(body):
    """
    When a message is posted to a relevant channel, format all text
    and images in the message and send them to the Discord bot as
    a list of dictionaries that can be formatted into embeds 
    """
    event = body.get("event", {})

    # Check that a message was SENT in a channel we are
    # listening to:
    if event.get("channel") not in listening_channels \
    or event.get("subtype") == "message_changed"      \
    or event.get("subtype") == "message_deleted":
        return
    
    # Set up a container for all the notification information:
    notification = []

    # Get general information of team/channel/author:
    team_info = app.client.team_info(
        team=body.get("team_id")
    ).get("team", {})
    team_name = team_info.get("name")
    icon_info = team_info.get("icon")
    team_icon = icon_info.get("image_88", 
                icon_info.get("image_68",
                icon_info.get("image_44",
                icon_info.get("image_34"))))
    channel_name = app.client.conversations_info(
        channel=event.get("channel")
    ).get("channel", {}).get("name")
    author_id = event.get("user")
    author_info = app.client.users_info(
        user=author_id
    ).get("user", {})
    author_name = author_info.get("profile", {}).get("display_name")
    if not author_name:
        # If user has no display_name (is a bot), use real_name:
        author_name = author_info.get("real_name")
    author_profile = author_info.get("profile", {})
    author_icon = author_profile.get("image_72", 
                  author_profile.get("image_48",
                  author_profile.get("image_32")))
    timestamp = float(event.get("ts"))

    # Initialize the first notification text:
    sub_notif = {
        "channel_name": channel_name,
        "author_name": author_name,
        "author_icon": author_icon,
    }

    # Grab all images from the message:
    message_images = [
        file for file in event.get("files", [])
        if file.get("mimetype").split("/")[0] == "image"
    ]

    # Share the images and use their public link:
    for idx, image in enumerate(message_images):
        if not image.get("public_url_shared"):
            app.client.files_sharedPublicURL(
                file=image.get("id"),
                token=os.environ.get("SLACK_USER_TOKEN")
            )
        message_images[idx] = f"{image.get('url_private')}?pub_secret=" \
                              f"{image.get('permalink_public').split('-')[-1]}"

    # Get the text from the message and format it properly:
    message_text = event.get("text")
    if message_text:
        formatted_text = ""
        for block in event.get("blocks", []):
            if block.get("type") != "rich_text":
                print(f"Skipping over block of type {block.get('type')}.")
                continue
            for elem in block.get("elements", {}):
                elem_type = elem.get("type")
                if elem_type == "rich_text_section":
                    formatted_text += format_rich_text(elem)
                elif elem_type == "rich_text_list":
                    formatted_text += format_rich_list(elem)
                elif elem_type == "rich_text_quote":
                    formatted_text += format_rich_quote(elem)
                elif elem_type == "rich_text_preformatted":
                    formatted_text += format_rich_preformatted(elem)
        sub_notif.update({"notif_text": formatted_text})
    
    # Add the images as attachment embeds to notification:
    if len(message_images) > 1:
        # If there are multiple images, they will have to be sent as
        # individual embeds (Discord embeds only support 1 image):
        if sub_notif.get("notif_text"):
            notification.append(sub_notif)
            sub_notif = {}
        for idx, image in enumerate(message_images):
            sub_notif.update({
                "notif_image": image
            })
            if idx == len(message_images) - 1:
                # The last embed should have a footer
                sub_notif.update({
                    "team_name": team_name,
                    "team_icon": team_icon,
                    "timestamp": timestamp
                })
            notification.append(sub_notif)
            sub_notif = {}
    else:
        if len(message_images) == 1:
            # If there is just 1 image, add it to the existing embed:
            sub_notif.update({
                "notif_image": message_images[0]
            })
        sub_notif.update({
            # The last embed should have a footer
            "team_name": team_name,
            "team_icon": team_icon,
            "timestamp": timestamp
        })
        notification.append(sub_notif)
    
    # Send the notification to the Discord Bot
    send_notification(notification)

if __name__ == "__main__":
    app.start(port=int(os.environ.get("PORT", 5000)))
