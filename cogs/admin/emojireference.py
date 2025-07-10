import discord
from discord.ext import commands
from discord import app_commands, ui, Interaction
from utils.app.security import is_user_allowed

EMOJIS_PER_PAGE = 40

class EmojiPaginatorView(ui.View):
    def __init__(self, pages, author_id):
        super().__init__(timeout=180)
        self.pages = pages
        self.current = 0
        self.author_id = author_id

        if len(pages) > 1:
            self.add_item(self.PreviousButton(self))
            self.add_item(self.NextButton(self))

    class PreviousButton(ui.Button):
        def __init__(self, parent):
            super().__init__(style=discord.ButtonStyle.secondary, label='Previous', row=0)
            self.parent = parent

        async def callback(self, interaction: Interaction):
            if interaction.user.id != self.parent.author_id:
                await interaction.response.send_message("Not your paginator!", ephemeral=True)
                return
            self.parent.current -= 1
            if self.parent.current < 0:
                self.parent.current = len(self.parent.pages) - 1
            await interaction.response.edit_message(embed=self.parent.pages[self.parent.current], view=self.parent)

    class NextButton(ui.Button):
        def __init__(self, parent):
            super().__init__(style=discord.ButtonStyle.secondary, label='Next', row=0)
            self.parent = parent

        async def callback(self, interaction: Interaction):
            if interaction.user.id != self.parent.author_id:
                await interaction.response.send_message("Not your paginator!", ephemeral=True)
                return
            self.parent.current += 1
            if self.parent.current >= len(self.parent.pages):
                self.parent.current = 0
            await interaction.response.edit_message(embed=self.parent.pages[self.parent.current], view=self.parent)

class AdminEmojiReference(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="emojiref", description="Show a paginated embed of all application emojis with names (admin only).")
    @is_user_allowed( "USER_ORACLE", "ROLE_GUILDMASTER", "BOT_OWNER")
    async def emojiref(self, interaction: discord.Interaction):
        # Fetch application emojis
        emojis = await self.bot.fetch_application_emojis()
        if not emojis:
            await interaction.response.send_message("No application emojis found.", ephemeral=True)
            return

        # Paginate
        pages = []
        for i in range(0, len(emojis), EMOJIS_PER_PAGE):
            chunk = emojis[i:i+EMOJIS_PER_PAGE]
            desc = '\n'.join(f"{str(e)} — `{e.name}`" for e in chunk)
            embed = discord.Embed(
                title=f"Application Emojis (Page {i//EMOJIS_PER_PAGE+1}/{(len(emojis)-1)//EMOJIS_PER_PAGE+1})",
                description=desc or "No emojis.",
                color=discord.Color.blurple()
            )
            pages.append(embed)

        view = EmojiPaginatorView(pages, interaction.user.id)
        await interaction.response.send_message(embed=pages[0], view=view, ephemeral=True)

async def setup(bot):
    await bot.add_cog(AdminEmojiReference(bot))