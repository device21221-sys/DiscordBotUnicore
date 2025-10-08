import discord
from discord import app_commands
from discord.ext import commands
import os
import random
import string
from keep_alive import keep_alive, add_key  

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix="?", intents=intents)

# ================== Channel IDs ==================
RULES_CHANNEL_ID = 1351689723369754634
INFO_CHANNEL_ID = 1351690459923349634
SUPPORT_CHANNEL_ID = 1411789053921202286
EXECUTORS_CHANNEL_ID = 1404173340125429792

# ================== Role Names ==================
STAFF_ROLE_NAME = "Staff Team"
NEXUS_ROLE_NAME = "NexusVision Team"

# ================== Events ==================
@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"✅ Bot {bot.user} is online and slash commands are synced!")

# ================== Slash Commands ==================
@bot.tree.command(name="get_ar2_script", description="Get the AR2 Script")
async def get_ar2_script(interaction: discord.Interaction):
    script = '```lua\nloadstring(game:HttpGet("https://raw.githubusercontent.com/UnicoreRoblox/Unicore/refs/heads/main/ApocalypseRising2.luau"))()\n```'
    await interaction.response.send_message(script, ephemeral=True)

@bot.tree.command(name="get_universal_script", description="Get the Universal Script")
async def get_universal_script(interaction: discord.Interaction):
    script = '```lua\nloadstring(game:HttpGet("https://raw.githubusercontent.com/NightFallScript/Unicore/refs/heads/main/DoorsUnicore"))()\n```'
    await interaction.response.send_message(script, ephemeral=True)

@bot.tree.command(name="rules", description="Show the rules channel")
async def rules(interaction: discord.Interaction):
    channel = bot.get_channel(RULES_CHANNEL_ID)
    if channel:
        await interaction.response.send_message(f"📜 Rules are here: {channel.mention}", ephemeral=True)
    else:
        await interaction.response.send_message("❌ Rules channel not found.", ephemeral=True)

@bot.tree.command(name="info", description="Show the info channel")
async def info(interaction: discord.Interaction):
    channel = bot.get_channel(INFO_CHANNEL_ID)
    if channel:
        await interaction.response.send_message(f"ℹ️ Info is here: {channel.mention}", ephemeral=True)
    else:
        await interaction.response.send_message("❌ Info channel not found.", ephemeral=True)

@bot.tree.command(name="support", description="Show the support channel")
async def support(interaction: discord.Interaction):
    channel = bot.get_channel(SUPPORT_CHANNEL_ID)
    if channel:
        await interaction.response.send_message(f"🛠️ Support is here: {channel.mention}", ephemeral=True)
    else:
        await interaction.response.send_message("❌ Support channel not found.", ephemeral=True)

@bot.tree.command(name="support_executors", description="Show the executors channel")
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
    embed.add_field(name="/changerole", value="Add or remove a role from a member", inline=False)
    embed.add_field(name="/generatekey", value="Generate a new key (NexusVision only)", inline=False)
    await interaction.response.send_message(embed=embed, ephemeral=True)

# ================== /changerole ==================
@bot.tree.command(name="changerole", description="Add or remove a role from a user (Staff/Nexus only)")
@app_commands.describe(
    member="User to modify",
    role="Role to give or remove"
)
async def changerole(interaction: discord.Interaction, member: discord.Member, role: discord.Role):
    if not any(r.name in [STAFF_ROLE_NAME, NEXUS_ROLE_NAME] for r in interaction.user.roles):
        await interaction.response.send_message("❌ You do not have permission to use this command.", ephemeral=True)
        return

    if role in member.roles:
        await member.remove_roles(role)
        await interaction.response.send_message(f"✅ Removed {role.mention} from {member.mention}.", ephemeral=True)
    else:
        await member.add_roles(role)
        await interaction.response.send_message(f"✅ Added {role.mention} to {member.mention}.", ephemeral=True)

# ================== /generatekey ==================
@bot.tree.command(name="generatekey", description="Generate a new access key (NexusVision only)")
@app_commands.describe(
    active="Whether the key is active (True/False)",
    days="How many days it's valid (7, 30, 90, 100000)"
)
async def generatekey(interaction: discord.Interaction, active: bool, days: int):
    if not any(r.name == NEXUS_ROLE_NAME for r in interaction.user.roles):
        await interaction.response.send_message("❌ You do not have permission to use this command.", ephemeral=True)
        return

    if days not in [7, 30, 90, 100000]:
        await interaction.response.send_message("❌ Invalid duration. Use 7, 30, 90, or 100000.", ephemeral=True)
        return

    # Generate key
    key = "-".join(
        "".join(random.choices(string.ascii_uppercase + string.digits, k=4))
        for _ in range(4)
    )

    # Add key to Flask API
    add_key(key, active, days)

    embed = discord.Embed(
        title="🔑 Key Generated",
        color=0x00ff88
    )
    embed.add_field(name="Key", value=f"```{key}```", inline=False)
    embed.add_field(name="Active", value=str(active), inline=True)
    embed.add_field(name="Valid Days", value=str(days), inline=True)
    embed.set_footer(text=f"Generated by {interaction.user}", icon_url=interaction.user.display_avatar.url)

    await interaction.response.send_message(embed=embed, ephemeral=True)

# ================== Legacy Panel (?scripts) ==================
@bot.command(name="scripts")
async def scripts(ctx):
    embed = discord.Embed(
        title="📜 Script Panel",
        description="This script panel is for the project: **Unicore**\n\n"
                    "Use the buttons below to get Universal Script or AR2 Script.",
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

# ================== Run Bot ==================
keep_alive()
bot.run(os.getenv("TOKEN"))
