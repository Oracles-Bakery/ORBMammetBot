import discord
from discord import ui
from utils.discord.interactions import create_dropdown_view, assign_roles

# Better format: custom_id -> dict of display settings
VIEW_CONFIGS = {
    "ff_activities": {"category": "FF Activities", "placeholder": "Select activities...", "label": "FF Activities"},
    "ff_roles": {"category": "FF Role", "placeholder": "Select roles...", "label": "FF Roles"},
    "pronouns": {"category": "Pronouns", "placeholder": "Select pronouns...", "label": "Pronouns"},
    "interests": {"category": "Interests", "placeholder": "Select interests...", "label": "Interests"},
}


class RoleCategoryButton(ui.Button):
    def __init__(self, label: str, custom_id: str, bot):
        self.display_label = label  # Preserve for later use
        super().__init__(label=label, style=discord.ButtonStyle.primary, custom_id=custom_id)

    async def callback(self, interaction: discord.Interaction):
        config = VIEW_CONFIGS.get(self.custom_id)
        if config:
            category = config.get("category")
            placeholder = config.get("placeholder")
            try:
                view = await create_dropdown_view(category, placeholder, interaction.user, bot)
            except ValueError as e:
                await interaction.response.send_message(str(e), ephemeral=True)
                return

            await interaction.response.send_message(
                f"Select your {self.display_label.lower()} preferences:",
                view=view,
                ephemeral=True
            )
        if not config:
            await interaction.response.send_message(
            "Something went wrong — unknown role category.",
            ephemeral=True
            )
        return



class RoleCategoryView(ui.View):
    def __init__(self, bot):
        super().__init__(timeout=None)
        for custom_id, config in VIEW_CONFIGS.items():
            self.add_item(RoleCategoryButton(label=config["label"], custom_id=custom_id, bot=bot))