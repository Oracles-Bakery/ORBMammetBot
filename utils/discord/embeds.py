# utils/discord/embeds.py
import discord
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any

def base_embed(
    title: Optional[str] = None,
    description: Optional[str] = None,
    colour: Optional[discord.Color] = discord.Color.blurple(),
    url: Optional[str] = None,
    timestamp: Optional[datetime] = None,
    author: Optional[Dict[str, Any]] = None,
    thumbnail: Optional[str] = None,
    image: Optional[str] = None,
    footer: Optional[Dict[str, Any]] = None,
    fields: Optional[List[Dict[str, Any]]] = None
) -> discord.Embed:
    """
    Fully featured Embed helper for Discord bots.
    Supports all core embed parameters, including author, thumbnail, image, footer, and fields.
    """
    if timestamp is None:
        timestamp = datetime.now(timezone.utc)

    embed = discord.Embed(
        title=title,
        description=description,
        colour=colour,
        url=url,
        timestamp=timestamp
    )

    # Author
    embed.set_author(
        name=author.get('name'),
        url=author.get('url'),
        icon_url=author.get('icon_url')
    )

    # Thumbnail
    if thumbnail:
        embed.set_thumbnail(url=thumbnail)

    # Image
    if image:
        embed.set_image(url=image)

    # Footer
    if footer:
        embed.set_footer(
            text=footer.get('text', discord.Embed.Empty),
            icon_url=footer.get('icon_url', discord.Embed.Empty)
        )

    # Fields
    if fields:
        for field in fields:
            embed.add_field(
                name=field.get('name', '\u200b'),
                value=field.get('value', '\u200b'),
                inline=field.get('inline', True)
            )

    return embed

def error_embed(message: str, **kwargs) -> discord.Embed:
    return base_embed(
        title="Error",
        description=message,
        colour=discord.Color.red(),
        **kwargs
    )

def success_embed(message: str, **kwargs) -> discord.Embed:
    return base_embed(
        title="Success",
        description=message,
        colour=discord.Color.green(),
        **kwargs
    )
