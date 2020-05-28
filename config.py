from config_base import config

config.update({
    # system
    "token": "DISCORD_BOT_TOKEN_HERE",
    "blahjack_exe": "BLAHJACK_EXE_HERE",

    # owner
    "owner_id": DISCORD_ACCOUNT_ID_FOR_NOTIFICATIONS,
    "notify_channel_id": NOTIFICATION_CHANNEL_ID
})

"""
Use this config by creating additional config_user.py scripts with the following content:

from config import config
from config_base import cooldown_normal

config.update({
    "profile_id": "example",
    "user_id": DISCORD_ACCOUNT_ID_OF_BOTTED_ACCOUNT,
    "type_channel_id": CHANNEL_ID_TO_BOT_IN,
    "type_url": "https://discord.com/channels/SERVER_ID_TO_BOT_IN/CHANNEL_ID_TO_BOT_IN",
    "cooldown": cooldown_normal, # or cooldown_donator
    "event_notify": False # whether to notify on events
})
"""