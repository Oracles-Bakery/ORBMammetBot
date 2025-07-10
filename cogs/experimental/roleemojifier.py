from discord.ext import commands
from discord import ui, Interaction
import discord
from utils.database import postgres
from settings import CATEGORY_DICT
import asyncio

MAX_EMOJI_PER_PAGE = 25

class EmojiDropdown(ui.Select):
    """Dropdown menu for picking an app emoji."""
    def __init__(self, role_id, emoji_options, callback):
        options = [
            discord.SelectOption(
                label=emoji.name,
                value=str(emoji.id),
                emoji=emoji
            )
            for emoji in emoji_options
        ]
        super().__init__(
            placeholder="Choose an emoji for this role...",
            min_values=1, max_values=1,
            options=options,
            custom_id=f"emojipick_{role_id}"
        )
        self.role_id = role_id
        self.callback_fn = callback

    async def callback(self, interaction: Interaction):
        await self.callback_fn(interaction, self.values[0], self.role_id)

class PageButton(ui.Button):
    """Button to go to previous/next emoji page."""
    def __init__(self, label, direction, callback):
        super().__init__(
            style=discord.ButtonStyle.secondary,
            label=label,
            custom_id=f"pagination_{label.lower()}"
        )
        self.direction = direction
        self.callback_fn = callback

    async def callback(self, interaction: Interaction):
        await self.callback_fn(interaction, self.direction)

class EmojiSelectView(ui.View):
    """
    Dynamic View for picking emojis for multiple roles in one embed.
    Handles emoji paging, selection, and switching roles.
    """
    def __init__(self, admin_id, role_data, app_emojis, assign_callback):
        super().__init__(timeout=300)
        self.admin_id = admin_id
        self.role_data = role_data      # [(role_id, role_name, category), ...]
        self.app_emojis = app_emojis
        self.assign_callback = assign_callback
        self.page = 0
        self.role_idx = 0               # Which role we're working on

        self.update_items()

    def update_items(self):
        """Refreshes select menu/buttons based on current role & page."""
        self.clear_items()
        role_id, role_name, category = self.role_data[self.role_idx]
        emoji_prefix = CATEGORY_DICT[category]['emoji_prefix']
        matching_emojis = [e for e in self.app_emojis if emoji_prefix and e.name.startswith(emoji_prefix + "_")]
        total_pages = (len(matching_emojis) + MAX_EMOJI_PER_PAGE - 1) // MAX_EMOJI_PER_PAGE or 1
        start = self.page * MAX_EMOJI_PER_PAGE
        end = start + MAX_EMOJI_PER_PAGE
        page_emojis = matching_emojis[start:end]

        if page_emojis:
            self.add_item(EmojiDropdown(role_id, page_emojis, self.on_emoji_selected))
        if total_pages > 1:
            if self.page > 0:
                self.add_item(PageButton("Previous", -1, self.on_page))
            if self.page < total_pages - 1:
                self.add_item(PageButton("Next", 1, self.on_page))

    async def on_emoji_selected(self, interaction: Interaction, emoji_id, role_id):
        # Security: Only admin can use
        if interaction.user.id != self.admin_id:
            await interaction.response.send_message("You're not allowed to assign emojis.", ephemeral=True)
            return

        await self.assign_callback(interaction, emoji_id, role_id, self.role_idx)
        self.role_idx += 1
        self.page = 0
        # Move to next role or finish
        if self.role_idx >= len(self.role_data):
            self.clear_items()
            await interaction.response.edit_message(embed=discord.Embed(
                title="All done!",
                description="All roles have been assigned emojis."
            ), view=self)
        else:
            self.update_items()
            await interaction.response.edit_message(embed=self._current_embed(), view=self)

    async def on_page(self, interaction: Interaction, direction):
        # Security: Only admin can use
        if interaction.user.id != self.admin_id:
            await interaction.response.send_message("You're not allowed to page.", ephemeral=True)
            return
        self.page += direction
        self.page = max(0, self.page)
        self.update_items()
        await interaction.response.edit_message(embed=self._current_embed(), view=self)

    def _current_embed(self):
        role_id, role_name, category = self.role_data[self.role_idx]
        emoji_prefix = CATEGORY_DICT[category]['emoji_prefix']
        return discord.Embed(
            title=f"Assign Emoji to Role ({self.role_idx+1}/{len(self.role_data)})",
            description=f"Role: `{role_name}` (ID: {role_id})\nCategory: `{category}`\nPrefix: `{emoji_prefix}`"
        )

class RoleEmojiSetup(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="setup_role_emojis", help="Assigns emojis to roles based on their categories.")
    @commands.is_owner()
    async def setup_role_emojis(self, ctx):
        """
        Command entrypoint.
        - Unicode roles handled via reactions on the same message, one at a time.
        - App emoji roles handled via select menu/page buttons, all in one embed.
        """
        admin_id = ctx.author.id
        roles = await postgres.fetch("SELECT id, role_name, category, emoji_id, unicode_emoji FROM discord_roles ORDER BY id")
        # Split roles into unicode and application-emoji
        unicode_roles = [
            (r['id'], r['role_name'], r['category'])
            for r in roles
            if r['category'] and CATEGORY_DICT[r['category']]['is_unicode'] and not r['unicode_emoji']
        ]
        app_emoji_roles = [
            (r['id'], r['role_name'], r['category'])
            for r in roles
            if r['category'] and not CATEGORY_DICT[r['category']]['is_unicode'] and not r['emoji_id'] and CATEGORY_DICT[r['category']]['emoji_prefix']
        ]
        app_emojis = await self.bot.fetch_application_emojis()

        # --- Helper for unicode via reactions ---
        async def handle_unicode_assignment(msg, unicode_roles):
            for idx, (role_id, role_name, category) in enumerate(unicode_roles):
                embed = discord.Embed(
                    title=f"Assign Unicode Emoji to Role ({idx+1}/{len(unicode_roles)})",
                    description=(
                        f"Role: `{role_name}` (ID: {role_id})\nCategory: `{category}`\n"
                        f"React to this message with the emoji to assign, or ❌ to skip."
                    )
                )
                await msg.edit(content=None, embed=embed, view=None)
                await msg.clear_reactions()
                await msg.add_reaction("❌")  # Always offer skip

                # Only care about a reaction from the admin and on this message
                def check(reaction, user):
                    return (
                        user.id == admin_id and
                        reaction.message.id == msg.id and
                        (reaction.emoji == "❌" or isinstance(reaction.emoji, str))
                    )
                try:
                    reaction, user = await ctx.bot.wait_for("reaction_add", timeout=120, check=check)
                except asyncio.TimeoutError:
                    await msg.edit(content="No reaction received, skipping this role.", embed=None, view=None)
                    await asyncio.sleep(1)
                    continue

                if reaction.emoji == "❌":
                    await msg.edit(content="Skipped.", embed=None, view=None)
                    await asyncio.sleep(1)
                    continue

                # Save the emoji to the DB
                await postgres.execute("UPDATE discord_roles SET unicode_emoji = $1 WHERE id = $2", reaction.emoji, role_id)
                await msg.edit(content=f"Assigned emoji: {reaction.emoji}", embed=None, view=None)
                await asyncio.sleep(1)  # Delay to prevent rate limits

        # --- Callback for select menu assigns app emoji ---
        async def assign_callback(interaction, emoji_id, role_id, role_idx):
            await postgres.execute("UPDATE discord_roles SET emoji_id = $1 WHERE id = $2", int(emoji_id), role_id)
            # The view will update to next role for you!

        # ---- RUN THE UNICODE ASSIGNER FIRST ----
        if unicode_roles:
            msg = await ctx.send("Starting Unicode emoji assignment...")
            await handle_unicode_assignment(msg, unicode_roles)

        # ---- THEN RUN THE APP EMOJI ASSIGNER ----
        if app_emoji_roles:
            view = EmojiSelectView(admin_id, app_emoji_roles, app_emojis, assign_callback)
            await ctx.send(embed=view._current_embed(), view=view)
        else:
            if not unicode_roles:
                await ctx.send("All categorized roles already have emojis assigned.")

async def setup(bot):
    await bot.add_cog(RoleEmojiSetup(bot))
