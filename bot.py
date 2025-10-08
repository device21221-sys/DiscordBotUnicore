import discord
from discord import app_commands
from discord.ext import commands
import os
import random
import string
from keep_alive import keep_alive  

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix="?", intents=intents)

# ================== Channel IDs (заміни на свої) ==================
RULES_CHANNEL_ID = 1351689723369754634
INFO_CHANNEL_ID = 1351690459923349634
SUPPORT_CHANNEL_ID = 1411789053921202286
EXECUTORS_CHANNEL_ID = 1404173340125429792

# ================== Role Names (для доступу) ==================
STAFF_ROLE_NAME = "Staff Team"
NEXUS_ROLE_NAME = "NexusVision Team"

# ================== Події ==================
@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"✅ Bot {bot.user} is online and slash commands synced!")

# ================== Slash-команди ==================
@bot.tree.command(name="get_ar2_script", description="Get the AR2 Script")
async def get_ar2_script(interaction: discord.Interaction):
    script = '```lua\nloadstring(game:HttpGet("https://raw.githubusercontent.com/UnicoreRoblox/Unicore/refs/heads/main/ApocalypseRising2.luau"))()\n```'
    await interaction.response.send_message(script, ephemeral=True)

@bot.tree.command(name="get_universal_script", description="Get the Universal Script")
async def get_universal_script(interaction: discord.Interaction):
    script = '```lua\nloadstring(game:HttpGet("https://raw.githubusercontent.com/NightFallScript/Unicore/refs/heads/main/DoorsUnicore"))()\n```'
    await interaction.response.send_message(script, ephemeral=True)

@bot.tree.command(name="rules", description="Link to rules channel")
async def rules(interaction: discord.Interaction):
    channel = bot.get_channel(RULES_CHANNEL_ID)
    if channel:
        await interaction.response.send_message(f"📜 Rules are here: {channel.mention}", ephemeral=True)
    else:
        await interaction.response.send_message("❌ Rules channel not found.", ephemeral=True)

@bot.tree.command(name="info", description="Link to info channel")
async def info(interaction: discord.Interaction):
    channel = bot.get_channel(INFO_CHANNEL_ID)
    if channel:
        await interaction.response.send_message(f"ℹ️ Info is here: {channel.mention}", ephemeral=True)
    else:
        await interaction.response.send_message("❌ Info channel not found.", ephemeral=True)

@bot.tree.command(name="support", description="Link to support channel")
async def support(interaction: discord.Interaction):
    channel = bot.get_channel(SUPPORT_CHANNEL_ID)
    if channel:
        await interaction.response.send_message(f"🛠️ Support is here: {channel.mention}", ephemeral=True)
    else:
        await interaction.response.send_message("❌ Support channel not found.", ephemeral=True)

@bot.tree.command(name="support_executors", description="Link to executors channel")
async def support_executors(interaction: discord.Interaction):
    channel = bot.get_channel(EXECUTORS_CHANNEL_ID)
    if channel:
        await interaction.response.send_message(f"⚙️ Executors are here: {channel.mention}", ephemeral=True)
    else:
        await interaction.response.send_message("❌ Executors channel not found.", ephemeral=True)

@bot.tree.command(name="help", description="List all available commands")
async def help_command(interaction: discord.Interaction):
    embed = discord.Embed(title="📖 Command List", color=0x2b2d31)
    embed.add_field(name="/get_ar2_script", value="Get AR2 Script", inline=False)
    embed.add_field(name="/get_universal_script", value="Get Universal Script", inline=False)
    embed.add_field(name="/rules", value="Show rules channel", inline=False)
    embed.add_field(name="/info", value="Show info channel", inline=False)
    embed.add_field(name="/support", value="Show support channel", inline=False)
    embed.add_field(name="/support_executors", value="Show executors channel", inline=False)
    embed.add_field(name="/changerole", value="Change user roles (Staff/Nexus only)", inline=False)
    embed.add_field(name="/generatekey", value="Generate key (Nexus only)", inline=False)
    await interaction.response.send_message(embed=embed, ephemeral=True)

# ================== /changerole ==================
@bot.tree.command(name="changerole", description="Змінити роль користувача (тільки для Staff Team та NexusVision Team)")
@app_commands.describe(
    member="Користувач, якому хочеш змінити роль",
    role="Роль, яку хочеш видати або забрати"
)
async def changerole(interaction: discord.Interaction, member: discord.Member, role: discord.Role):
    if not any(r.name in [STAFF_ROLE_NAME, NEXUS_ROLE_NAME] for r in interaction.user.roles):
        await interaction.response.send_message("❌ У тебе немає доступу до цієї команди.", ephemeral=True)
        return

    if role in member.roles:
        await member.remove_roles(role)
        await interaction.response.send_message(f"✅ Роль {role.mention} **знято** з {member.mention}.", ephemeral=True)
    else:
        await member.add_roles(role)
        await interaction.response.send_message(f"✅ Роль {role.mention} **видано** {member.mention}.", ephemeral=True)

# ================== /generatekey ==================
@bot.tree.command(name="generatekey", description="Генерує ключ доступу (тільки NexusVision Team)")
@app_commands.describe(
    active="Чи активний ключ (True/False)",
    days="На скільки днів (7, 30, 90, 100000)"
)
async def generatekey(interaction: discord.Interaction, active: bool, days: int):
    if not any(r.name == NEXUS_ROLE_NAME for r in interaction.user.roles):
        await interaction.response.send_message("❌ Ти не маєш доступу до цієї команди.", ephemeral=True)
        return

    if days not in [7, 30, 90, 100000]:
        await interaction.response.send_message("❌ Невірна кількість днів. Використовуй: 7, 30, 90 або 100000.", ephemeral=True)
        return

    # Генерація ключа: 4 блоки по 4 великі букви
    key = "-".join(
        "".join(random.choices(string.ascii_uppercase + string.digits, k=4))
        for _ in range(4)
    )

    embed = discord.Embed(
        title="🔑 Згенеровано ключ",
        color=0x00ff88
    )
    embed.add_field(name="Ключ", value=f"```{key}```", inline=False)
    embed.add_field(name="Активний", value=str(active), inline=True)
    embed.add_field(name="Дійсний (днів)", value=str(days), inline=True)
    embed.set_footer(text=f"Запросив: {interaction.user}", icon_url=interaction.user.display_avatar.url)

    await interaction.response.send_message(embed=embed, ephemeral=True)

# ================== Legacy Panel (?scripts) ==================
@bot.command(name="scripts")
async def scripts(ctx):
    embed = discord.Embed(
        title="📜 Script Panel",
        description="This script panel is for the project : **Unicore**\n\n"
                    "Use the buttons below to get Universal Script or AR2 Script",
        color=0x2b2d31
    )

    view = discord.ui.View()

    async def universal_callback(interaction: discord.Interaction):
        script = '```lua\nloadstring(game:HttpGet("https://raw.githubusercontent.com/NightFallScript/Unicore/refs/heads/main/DoorsUnicore"))()\n```'
        await interaction.response.send_message(script, ephemeral=True)

    universal_button = discord.ui.Button(label="📜 Get Universal Script", style=discord.ButtonStyle.secondary)
    universal_button.callback = universal_callback
    view.add_item(universal_button)

    async def ar2_callback(interaction: discord.Interaction):
        script = '```lua\nloadstring(game:HttpGet("https://raw.githubusercontent.com/UnicoreRoblox/Unicore/refs/heads/main/ApocalypseRising2.luau"))()\n```'
        await interaction.response.send_message(script, ephemeral=True)

    ar2_button = discord.ui.Button(label="📜 Get AR2 Script", style=discord.ButtonStyle.secondary)
    ar2_button.callback = ar2_callback
    view.add_item(ar2_button)

    await ctx.send(embed=embed, view=view)

# ================== Запуск ==================
keep_alive()
bot.run(os.getenv("TOKEN"))
