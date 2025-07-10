from discord.ext import commands
from discord import ui, Interaction
import discord
from utils.database import postgres
from settings import CATEGORY_DICT

class RoleMultiSelect(ui.Select):
    def __init__(self, roles, category, callback):
        options = [
            discord.SelectOption(label=role['role_name'], value=str(role['id']))
            for role in roles
        ]
        super().__init__(
            placeholder=f"Assign roles to {CATEGORY_DICT[category]['label']}",
            min_values=0,
            max_values=len(options),
            options=options
        )
        self.category = category
        self.callback_fn = callback

    async def callback(self, interaction: Interaction):
        await self.callback_fn(interaction, self.values, self.category)

class CategoryRoleAssignView(ui.View):
    def __init__(self, roles, category, callback):
        super().__init__(timeout=300)
        self.add_item(RoleMultiSelect(roles, category, callback))

class RoleCategorySetup(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="setup_role_categories", help="Assign categories to roles in batches.")
    @commands.is_owner()
    async def setup_role_categories(self, ctx):
        admin = ctx.author
        roles = await postgres.fetch("SELECT id, role_name, category FROM discord_roles ORDER BY id")
        roles_missing = [r for r in roles if not r['category']]

        if not roles_missing:
            await ctx.send("All roles already have categories.")
            return

        dm_channel = await admin.create_dm()
        summary = []
        # Group roles by categories to present choices
        for cat, info in CATEGORY_DICT.items():
            uncat_roles = [r for r in roles_missing if not r['category']]
            if not uncat_roles:
                break
            if not uncat_roles:
                continue

            async def assign_callback(interaction, selected_ids, category):
                if not selected_ids:
                    await interaction.response.send_message(f"No roles assigned to {info['label']}.", ephemeral=True)
                    return
                await postgres.execute(
                    "UPDATE discord_roles SET category = $1 WHERE id = ANY($2::bigint[])",
                    category, [int(rid) for rid in selected_ids]
                )
                summary.append(f"Assigned {len(selected_ids)} role(s) to {info['label']}.")
                await interaction.response.send_message(f"Assigned {len(selected_ids)} role(s) to {info['label']}.", ephemeral=True)

            embed = discord.Embed(
                title=f"Assign Roles to Category: {info['label']}",
                description="Select all roles to assign to this category (Ctrl+Click for multi-select)."
            )
            view = CategoryRoleAssignView(uncat_roles, cat, assign_callback)
            await dm_channel.send(embed=embed, view=view)

        await dm_channel.send("Category setup complete!\n" + "\n".join(summary) if summary else "No roles were assigned.")

async def setup(bot):
    await bot.add_cog(RoleCategorySetup(bot))
