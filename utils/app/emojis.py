# utils/app/emojis.py
import discord

async def get_app_emojis_by_category(bot: discord.Client):
    """
    Fetches all application emojis and organizes them into categories based on the name's first underscore.
    Returns a dict: {category: [emoji, ...]}
    """
    emojis = await bot.fetch_application_emojis()
    categories = {}
    for emoji in emojis:
        if "_" in emoji.name:
            category, shortname = emoji.name.split("_", 1)
        else:
            category, shortname = "Uncategorized", emoji.name
        # You can return the whole emoji object or a dict with details
        entry = {
            "id": emoji.id,
            "name": emoji.name,
            "shortname": shortname,
            "category": category,
            "url": str(emoji.url),
            "animated": emoji.animated
        }
        categories.setdefault(category, []).append(entry)
    return categories