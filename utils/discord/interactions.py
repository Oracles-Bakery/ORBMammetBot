# utils/discord/interactions.py
import discord
from discord import ui
from typing import Optional, List, Union
from utils.database import postgres


# Discord embed factory for building reusable embeds
class EmbedBuilder:
    def __init__(
        self,
        title: Optional[str] = None,
        description: Optional[str] = None,
        color: Optional[Union[discord.Color, int]] = discord.Color.blue(),
        timestamp=None,
    ):
        self.embed = discord.Embed(
            title=title,
            description=description,
            color=color,
            timestamp=timestamp,
        )
    
    def set_author(self, name: str, icon_url: Optional[str] = None, url: Optional[str] = None):
        self.embed.set_author(name=name, icon_url=icon_url, url=url)
        return self
    
    def add_field(self, name: str, value: str, inline: bool = True):
        self.embed.add_field(name=name, value=value, inline=inline)
        return self
    
    def set_footer(self, text: str, icon_url: Optional[str] = None):
        self.embed.set_footer(text=text, icon_url=icon_url)
        return self
    
    def set_image(self, url: str):
        self.embed.set_image(url=url)
        return self
    
    def set_thumbnail(self, url: str):
        self.embed.set_thumbnail(url=url)
        return self
    
    def build(self) -> discord.Embed:
        return self.embed


# Reusable dropdown UI
class GenericDropdown(ui.Select):
    def __init__(self, placeholder: str, options: list[discord.SelectOption], category: str):
        self.category = category
        super().__init__(placeholder=placeholder, options=options, min_values=0, max_values=len(options))

    async def callback(self, interaction: discord.Interaction):
        await assign_roles(interaction, self.values, self.category)

class GenericDropdownView(ui.View):
    def __init__(self, placeholder: str, options: list[discord.SelectOption], category: str):
        super().__init__(timeout=60)
        self.add_item(GenericDropdown(placeholder, options, category))


# Role assignment logic
async def assign_roles(interaction: discord.Interaction, selected_names: list[str], category: str):
    await interaction.response.defer(ephemeral=True)

    member = interaction.user
    guild = interaction.guild

    # Get all possible roles in this category
    all_role_rows = await postgres.get_roles_by_category(category)
    all_role_names = {row["role_name"] for row in all_role_rows}

    # Roles the member currently has from this category
    current_category_roles = [
        role for role in member.roles
        if role.name in all_role_names
    ]

    # Selected roles (keep), everything else (remove)
    selected_roles = [
    role for name in selected_names
    if (role := discord.utils.get(guild.roles, name=name)) is not None
    ]

    roles_to_remove = [
        role for role in current_category_roles if role.name not in selected_names
    ]

    # Remove unselected roles
    try:
        if roles_to_remove:
            await member.remove_roles(*roles_to_remove, reason=f"Unselected {category} roles")

        if selected_roles:
            await member.add_roles(*selected_roles, reason=f"Selected {category} roles")

    except discord.Forbidden:
        await interaction.followup.send("I don't have permission to update some roles.", ephemeral=True)
        return
    except Exception as e:
        await interaction.followup.send(f"Error updating roles: {e}", ephemeral=True)
        return

    await interaction.followup.send(
        f"Your roles for **{category}** have been updated.",
        ephemeral=True
    )

# Factory to generate the view
async def create_dropdown_view(category: str, placeholder: str, member: discord.Member, bot: discord.Client) -> ui.View:
    role_rows = await postgres.get_roles_by_category(category)
    user_role_names = {role.name for role in member.roles}

    options = []
    for row in role_rows:
        # Determine emoji it needs to pull
        if row.get("unicode_emoji"):
            emoji = row["unicode_emoji"]
        elif row.get("emoji_id"):
            emoji = bot.get_emoji(row["emoji_id"])
        else:
            emoji = None

        options.append(
            discord.SelectOption(
                label=row["role_name"],
                emoji=emoji,
                default=(row["role_name"] in user_role_names)
            )
        )

    if not options:
        raise ValueError(f"No options available for category '{category}'")

    return GenericDropdownView(placeholder, options, category)
