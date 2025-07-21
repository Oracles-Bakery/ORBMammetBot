# utils/colour.py
"""
Utility functions for color conversions and parsing color strings.
I made this to let people choose CMYK colours as their fav but it might be useful for artists down the line?
Safe for user input. Covers hex, named, and CMYK to Discord integer colors.
"""

from typing import Tuple, Optional, Union
import discord
import logging

# Extend as needed. Only common Discord embed names included by default. Also there's no dark yellow? tf?
COLORS = {
    "red": discord.Color.red().value,
    "orange": discord.Color.orange().value,
    "yellow": discord.Color.yellow().value,
    "green": discord.Color.green().value,
    "teal": discord.Color.teal().value,
    "blue": discord.Color.blue().value,
    "purple": discord.Color.purple().value,
    "fuchsia": discord.Color.fuchsia().value,
    "dark_red": discord.Color.dark_red().value,
    "dark_orange": discord.Color.dark_orange().value,
    "dark_green": discord.Color.dark_green().value,
    "dark_teal": discord.Color.dark_teal().value,
    "dark_blue": discord.Color.dark_blue().value,
    "dark_purple": discord.Color.dark_purple().value,
    "lighter_grey": discord.Color.lighter_grey().value,
    "light_grey": discord.Color.light_grey().value,
    "dark_grey": discord.Color.dark_grey().value,
    "darker_grey": discord.Color.darker_grey().value,
    "blurple": discord.Color.blurple().value,
    "gold": discord.Color.gold().value,
    "dark_gold": discord.Color.dark_gold().value,
    "magenta": discord.Color.magenta().value,
    "dark_magenta": discord.Color.dark_magenta().value
}

def clamp(value: float, minv: float, maxv: float) -> float:
    """Clamp value to [minv, maxv]"""
    return max(minv, min(value, maxv))

def cmyk_to_rgb(c: Union[int, float], m: Union[int, float], y: Union[int, float], k: Union[int, float]) -> Tuple[int, int, int]:
    """
    Converts CMYK values (0-100, int or float) to RGB tuple (0-255 each).
    Out-of-bounds values are clamped.
    """
    c = clamp(float(c), 0, 100) / 100
    m = clamp(float(m), 0, 100) / 100
    y = clamp(float(y), 0, 100) / 100
    k = clamp(float(k), 0, 100) / 100
    r = round(255 * (1 - c) * (1 - k))
    g = round(255 * (1 - m) * (1 - k))
    b = round(255 * (1 - y) * (1 - k))
    return (r, g, b)

def rgb_to_hex(r: int, g: int, b: int) -> str:
    """
    Converts RGB values (0-255 each) to hex string ('FF00FF').
    Out-of-bounds values are clamped.
    """
    r = int(clamp(r, 0, 255))
    g = int(clamp(g, 0, 255))
    b = int(clamp(b, 0, 255))
    return '{:02X}{:02X}{:02X}'.format(r, g, b)

def cmyk_to_hex(c: Union[int, float], m: Union[int, float], y: Union[int, float], k: Union[int, float]) -> str:
    """
    Converts CMYK (0-100, int or float) to hex string ('FF00FF').
    """
    return rgb_to_hex(*cmyk_to_rgb(c, m, y, k))

def parse_colour_string(
    colour_str: Optional[str], 
    logger: Optional[logging.Logger] = None
) -> int:
    """
    Parses a colour string and returns an int for Discord embed color.
    Supports:
        - 'hex|ff00ff' or 'hex|#ff00ff'
        - 'name|red'
        - 'cmyk|0,100,100,0'
    Returns discord.Color.default() if invalid.
    Logs failures if logger provided.
    """
    DISCORD_DEFAULT_COLOR_INT = 0
    if not colour_str or not isinstance(colour_str, str):
        if logger: logger.warning("No colour_str provided or not a string.")
        return DISCORD_DEFAULT_COLOR_INT
    kind, _, value = colour_str.partition("|")
    kind = kind.lower().strip()
    value = value.strip()
    try:
        if kind == "hex":
            hexval = value.lstrip("#")
            if len(hexval) != 6 or any(c not in "0123456789aAbBcCdDeEfF" for c in hexval):
                if logger: logger.warning(f"Invalid hex color '{value}'")
                return DISCORD_DEFAULT_COLOR_INT
            return int(hexval, 16)
        elif kind == "name":
            color = COLORS.get(value.lower())
            if color is None:
                if logger: logger.warning(f"Unknown color name '{value}'")
                return DISCORD_DEFAULT_COLOR_INT
            return color
        elif kind == "cmyk":
            parts = [x.strip() for x in value.split(",")]
            if len(parts) != 4:
                if logger: logger.warning(f"CMYK requires 4 values, got {len(parts)}: {parts}")
                return DISCORD_DEFAULT_COLOR_INT
            c, m, y, k = (float(p) for p in parts)
            hex_code = cmyk_to_hex(c, m, y, k)
            return int(hex_code, 16)
    except Exception as e:
        if logger: logger.exception(f"Failed to parse color string '{colour_str}': {e}")
    return DISCORD_DEFAULT_COLOR_INT

def hex_to_discord_color(hex_str: str) -> discord.Color:
    return discord.Color(int(hex_str.lstrip("#"), 16))
