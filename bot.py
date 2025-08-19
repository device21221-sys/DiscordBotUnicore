import discord
from discord.ext import commands
from datetime import datetime

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

class ScriptButtons(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="📰 ┃Get Universal Script", style=discord.ButtonStyle.secondary)
    async def universal(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(
            title="Here you Universal Script :",
            description="```lua\nloadstring(game:HttpGet(\"https://raw.githubusercontent.com/UnicoreRoblox/Unicore/refs/heads/main/Universal\"))()\n```",
            color=0x2b2d31
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @discord.ui.button(label="📃┃Get AR2 Script", style=discord.ButtonStyle.secondary)
    async def ar2(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(
            title="Here you AR2 Script :",
            description="```lua\nprint(\"coming soon\")\n```",
            color=0x2b2d31
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)


@bot.event
async def on_ready():
    print(f"✅ Bot {bot.user} запущений!")


@bot.command()
async def scripts(ctx):
    now = datetime.now().strftime("%d/%m/%Y %I:%M:%S %p")  # формат як на скріні (12h + AM/PM)

    embed = discord.Embed(
        title="📜 Script Panel",
        description="This script panel is for the project : **Unicore**\n"
                    "Use the buttons below to Get Universal Script, Get AR2 Script                      ",
        color=0x2b2d31
    )

    # робимо маленький текст внизу + аватарку юзера
    embed.set_footer(
        text=f"Sent by {ctx.author.display_name} • {now}",
        icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url
    )

    view = ScriptButtons()
    await ctx.send(embed=embed, view=view)

bot.run("")
