# utils/app/security.py
import settings
from discord.ext import commands
import utils.database.postgres as postgres
from cryptography.fernet import Fernet
import base64
import os
from typing import cast

# This is a command check used pretty liberally in the admin commands
# If the user or role matches, it'll go through fine
# Currently you wanna be using this with things like ROLE_GUILDMASTER and USER_ORACLE
def is_user_allowed(*setting_names: str):
    async def predicate(ctx):
        if not ctx.guild:
            return False  # Must be used in a guild context

        member = ctx.guild.get_member(ctx.author.id)
        if not member:
            return False

        for setting_name in setting_names:
            # Check for direct user ID match
            if setting_name.startswith("USER_"):
                user_id = getattr(settings, setting_name, None)
                if user_id is None:
                    continue  # Skip invalid settings
                if ctx.author.id == user_id:
                    return True

            # Check if member has the required role
            elif setting_name.startswith("ROLE_"):
                role_id = getattr(settings, setting_name, None)
                if role_id is None:
                    continue
                if any(role.id == role_id for role in member.roles):
                    return True

        return False  # No match found, get outta here

    return commands.check(predicate)

########################
### ENCRYPTION SETUP ###
########################

# Ensure the Fernet key is a valid base64 string
key_str = settings.FERNET_SECRET_KEY
if not isinstance(key_str, str):
    raise ValueError("FERNET_SECRET_KEY must be a base64 string.")

# Decode the key and create the Fernet instance
key_bytes = key_str.encode()
fernet = Fernet(key_bytes)
