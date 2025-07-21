""" Hosts the settings that the bot will inherit information from """

import os
import pathlib
import logging
from logging.config import dictConfig
import sys

from dotenv import load_dotenv

load_dotenv()

# Make sure we're pulling an integer so we're typesafe
def env_int(name):
    val = os.getenv(name)
    return int(val) if val is not None else None

################################
###### ENVIRONMENT  PULLS ######
################################

# TOKENS N SHIT
TOKEN = os.getenv("TOKEN")
BOT_USER_AGENT = os.getenv("BOT_USER_AGENT")
FREESTUFF_API = os.getenv("FREESTUFF_API")

# GUILD
GUILD_ID = env_int("GUILD_ID")

# PEOPLE
USER_ORACLE = env_int("USER_ORACLE")
USER_BOT_OWNER = env_int("USER_BOT_OWNER")
# ROLES
ROLE_GUILDMASTER = env_int("ROLE_GUILDMASTER")
ROLE_MODERATOR = env_int("ROLE_MODERATOR")
ROLE_EVENTSCOUNCIL = env_int("ROLE_EVENTSCOUNCIL")
ROLE_MYSTIC = env_int("ROLE_MYSTIC")
# CHANNELS
CHANNEL_ORACLENOTES = env_int("CHANNEL_ORACLENOTES")
CHANNEL_BOTTESTS = env_int("CHANNEL_BOTTESTS")
CHANNEL_BOTLOGS = env_int("CHANNEL_BOTLOGS")
CHANNEL_BOTDISCORDCAPTURES = env_int("CHANNEL_BOTDISCORDCAPTURES")
CHANNEL_MODERATION = env_int("CHANNEL_MODERATION")
CHANNEL_EVENTSCOUNCIL = env_int("CHANNEL_EVENTSCOUNCIL")
CHANNEL_LEVELLEDCONTENT = env_int("CHANNEL_LEVELLEDCONTENT")
CHANNEL_UNLEVELLEDCONTENT = env_int("CHANNEL_UNLEVELLEDCONTENT")
CHANNEL_DISCORDCONTENT = env_int("CHANNEL_DISCORDCONTENT")
CHANNEL_ROLESELECTION = env_int("CHANNEL_ROLESELECTION")
CHANNEL_FREEGAMES = env_int("CHANNEL_FREEGAMES")

# PATHS
# BASE_DIR is the absolute root of the project, and we DO NOT move settings.py or main.py from there.
BASE_DIR = pathlib.Path(__file__).parent
# These extend the base directory and make them available as strings for easy access.
CMDS_DIR = BASE_DIR / "cmds"
COGS_DIR = BASE_DIR / "cogs"
LOGS_DIR = BASE_DIR / "logs"
EXTS_DIR = BASE_DIR / "exts"
UTIL_DIR = BASE_DIR / "utils"

# SECURITY
# This is the secret key used for various security purposes, such as signing cookies.
# Do not mess with it once it's set unless it's absolutely necessary.
FERNET_SECRET_KEY = os.getenv("FERNET_SECRET_KEY")

# DATABASE
DATABASE_URL = os.getenv("DATABASE_URL")
REDIS_URL = os.getenv("REDIS_URL")


# The role categoriser and emojifier need this dictionary to function, update as needed.
# expects application emojis to use a category_emoji naming convention
# e.g. "FFRole_Tank"  "FFIcon_InGPose" "FFJob_PLD"  "FFActivity_Roulettes"
CATEGORY_CHOICES = [
    # key               label                    emoji_prefix   is_unicode
    ("fc_ranks",        "Free Company Ranks",    "FFIcon",      0),
    ("pronouns",        "Pronouns",              None,          1),
    ("ff_jobs",         "FFXIV Jobs",            "FFJob",       0),
    ("ff_activities",   "FFXIV Activities",      "FFActivity",  0),
    ("ff_roles",        "FFXIV Roles",           "FFRole",      0),
    ("interests",       "Interest",              None,          1),
    ("interests_group", "Interest Group",        None,          1),
]
CATEGORY_DICT = {
    key: {
        "label": label,
        "emoji_prefix": emoji_prefix,
        "is_unicode": bool(is_unicode)
    }
    for key, label, emoji_prefix, is_unicode in CATEGORY_CHOICES
}

################################
###### ENVIRONMENT CHECKS ######
################################

if not TOKEN or not TOKEN.strip():
    raise RuntimeError("TOKEN is not set. Bot cannot start.") # Bot API key needs setting
if not USER_ORACLE or not USER_BOT_OWNER:
    raise RuntimeError("Critical user ID(s) missing from environment.") # Server and Bot owner IDs need setting
if not DATABASE_URL:
    raise RuntimeError("Missing DATABASE_URL.") # Postgres server isn't hooked up
if not REDIS_URL:
    raise RuntimeError("Missing REDIS_URL.") # Redis server isn't hooked up


################################
######   LOGGING  SETUP   ######
################################

class MaxLevelFilter(logging.Filter):
    """Filter to pass only log records with level <= configured level."""
    def __init__(self, level):
        self.level = level
    def filter(self, record):
        return record.levelno <= self.level

log_dir = os.path.join(os.path.dirname(__file__), "logs") # Ensure the logs directory exists
if not os.path.exists(log_dir):
    os.makedirs(log_dir, exist_ok=True)

LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "filters": {
        "max_info": {
            "()": MaxLevelFilter,
            "level": logging.INFO
        }
    },
    "formatters": {
        "verbose": {
            "format": "%(levelname)-10s - %(asctime)s - %(module)-15s : %(message)s"
        },
        "standard": {
            "format": "%(levelname)-10s - %(name)-15s : %(message)s"
        }
    },
    "handlers": {
        "stdout": {
            "class": "logging.StreamHandler",
            "level": "DEBUG",
            "formatter": "standard",
            "stream": sys.stdout,
            "filters": ["max_info"]
        },
        "stderr": {
            "class": "logging.StreamHandler",
            "level": "WARNING",
            "formatter": "verbose",
            "stream": sys.stderr
        },
        "file": {
            "class": "logging.FileHandler",
            "level": "INFO",
            "formatter": "verbose",
            "filename": os.path.join(log_dir, "INFO.log"),
            "mode": "a"
        }
    },
    "loggers": {
        "bot": {
            "handlers": ["stdout", "stderr", "file"],
            "level": "DEBUG",
            "propagate": False
        },
        "discord": {
            "handlers": ["stdout", "stderr", "file"],
            "level": "INFO",
            "propagate": False
        }
    }
}

dictConfig(LOGGING_CONFIG)
