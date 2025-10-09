import discord
from discord import app_commands
from discord.ext import commands
import os
from keep_alive import keep_alive  

# ================== CONFIG ==================
GUILD_ID = 1344670393092280481  # заміни на ID твого сервера

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix="?", intents=intents)

# ================== Channel IDs ==================
RULES_CHANNEL_ID = 1351689723369754634
INFO_CHANNEL_ID = 1425554175231529054
SUPPORT_CHANNEL_ID = 1411789053921202286
EXECUTORS_CHANNEL_ID = 1404173340125429792
LOG_CHANNEL_ID = None  # буде встановлюватись через /setchanel-logs

# ================== Admin Data ==================
admin_roles = ["Staff Team", "NexusVision Team"]

warns_data = {}
mutes_data = {}
bans_data = {}

# ================== Helpers ==================
def is_admin(member: discord.Member):
    return any(role.name in admin_roles for role in member.roles)

async def send_log(message: str):
    if LOG_CHANNEL_ID:
        channel = bot.get_channel(LOG_CHANNEL_ID)
        if channel:
            await channel.send(message)

# ================== Events ==================
@bot.event
async def on_ready():
    await bot.tree.sync(guild=discord.Object(id=GUILD_ID))
    print(f"✅ Bot {bot.user} is online and commands synced for guild {GUILD_ID}!")

@bot.event
async def on_message(message: discord.Message):
    if message.author.bot:
        return  

    blocked_words = ["solara", "xeno", "jjsploit"]
    if any(word.lower() in message.content.lower() for word in blocked_words):
        try:
            await message.delete()
        except discord.Forbidden:
            pass

        channel = bot.get_channel(EXECUTORS_CHANNEL_ID)
        lower_content = message.content.lower()
        if "solara" in lower_content:
            name = "Solara"
        elif "xeno" in lower_content:
            name = "Xeno"
        elif "jjsploit" in lower_content:
            name = "JJSploit"
        else:
            name = "Executor"

        embed = discord.Embed(
            description=f"**{name} is not supported!**\n**Go to {channel.mention}!**",
            color=0x57A5FF
        )
        await message.channel.send(embed=embed, delete_after=10)
        return

    await bot.process_commands(message)

# ================== USER SLASH COMMANDS ==================
@bot.tree.command(name="get_ar2_script", description="Get the AR2 Script", guild=discord.Object(id=GUILD_ID))
async def get_ar2_script(interaction: discord.Interaction):
    script = '```lua\nloadstring(game:HttpGet("https://raw.githubusercontent.com/UnicoreRoblox/Unicore/refs/heads/main/ApocalypseRising2.luau"))()\n```'
    await interaction.response.send_message(script, ephemeral=True)

@bot.tree.command(name="get_universal_script", description="Get the Universal Script", guild=discord.Object(id=GUILD_ID))
async def get_universal_script(interaction: discord.Interaction):
    script = '```lua\nloadstring(game:HttpGet("https://raw.githubusercontent.com/NightFallScript/Unicore/refs/heads/main/DoorsUnicore"))()\n```'
    await interaction.response.send_message(script, ephemeral=True)

@bot.tree.command(name="rules", description="Link to rules channel", guild=discord.Object(id=GUILD_ID))
async def rules(interaction: discord.Interaction):
    channel = bot.get_channel(RULES_CHANNEL_ID)
    if channel:
        await interaction.response.send_message(f"📜 Rules are here: {channel.mention}", ephemeral=True)
    else:
        await interaction.response.send_message("❌ Rules channel not found.", ephemeral=True)

@bot.tree.command(name="info", description="Link to info channel", guild=discord.Object(id=GUILD_ID))
async def info(interaction: discord.Interaction):
    channel = bot.get_channel(INFO_CHANNEL_ID)
    if channel:
        await interaction.response.send_message(f"ℹ️ Info is here: {channel.mention}", ephemeral=True)
    else:
        await interaction.response.send_message("❌ Info channel not found.", ephemeral=True)

@bot.tree.command(name="support", description="Link to support channel", guild=discord.Object(id=GUILD_ID))
async def support(interaction: discord.Interaction):
    channel = bot.get_channel(SUPPORT_CHANNEL_ID)
    if channel:
        await interaction.response.send_message(f"🛠️ Support is here: {channel.mention}", ephemeral=True)
    else:
        await interaction.response.send_message("❌ Support channel not found.", ephemeral=True)

@bot.tree.command(name="support_executors", description="Link to executors channel", guild=discord.Object(id=GUILD_ID))
async def support_executors(interaction: discord.Interaction):
    channel = bot.get_channel(EXECUTORS_CHANNEL_ID)
    if channel:
        await interaction.response.send_message(f"⚙️ Executors are here: {channel.mention}", ephemeral=True)
    else:
        await interaction.response.send_message("❌ Executors channel not found.", ephemeral=True)

@bot.tree.command(name="help", description="List all available commands", guild=discord.Object(id=GUILD_ID))
async def help_command(interaction: discord.Interaction):
    embed = discord.Embed(title="📖 Command List", color=0x2b2d31)
    embed.add_field(name="/get_ar2_script", value="Get AR2 Script", inline=False)
    embed.add_field(name="/get_universal_script", value="Get Universal Script", inline=False)
    embed.add_field(name="/rules", value="Show rules channel", inline=False)
    embed.add_field(name="/info", value="Show info channel", inline=False)
    embed.add_field(name="/support", value="Show support channel", inline=False)
    embed.add_field(name="/support_executors", value="Show executors channel", inline=False)
    embed.add_field(name="/all_admin_comands", value="Show all admin commands (Staff/NexusVision only)", inline=False)
    await interaction.response.send_message(embed=embed, ephemeral=True)

# ================== ADMIN SLASH COMMANDS ==================
@app_commands.checks.has_any_role("Staff Team", "NexusVision Team")
@bot.tree.command(name="change_vip_role", description="Add or remove VIP role", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(user="Select user", action="Add or Remove")
async def change_vip_role(interaction: discord.Interaction, user: discord.Member, action: str):
    vip_role = discord.utils.get(interaction.guild.roles, name="VIP")
    if not vip_role:
        await interaction.response.send_message("❌ VIP role not found.", ephemeral=True)
        return
    if action.lower() == "add":
        await user.add_roles(vip_role)
        await interaction.response.send_message(f"✅ VIP role added to {user.mention}", ephemeral=True)
        await send_log(f"{interaction.user.mention} added VIP role to {user.mention}")
    elif action.lower() == "remove":
        await user.remove_roles(vip_role)
        await interaction.response.send_message(f"✅ VIP role removed from {user.mention}", ephemeral=True)
        await send_log(f"{interaction.user.mention} removed VIP role from {user.mention}")
    else:
        await interaction.response.send_message("❌ Action must be 'add' or 'remove'.", ephemeral=True)

@app_commands.checks.has_any_role("Staff Team", "NexusVision Team")
@bot.tree.command(name="warn", description="Warn a user", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(user="Select user", reason="Reason for warning")
async def warn(interaction: discord.Interaction, user: discord.Member, reason: str):
    warns_data[user.id] = warns_data.get(user.id, 0) + 1
    total_warns = warns_data[user.id]
    await interaction.response.send_message(f"⚠️ {user.mention} warned for: {reason} (Total warns: {total_warns}/3)", ephemeral=True)
    await send_log(f"{interaction.user.mention} warned {user.mention}. Reason: {reason}. Total warns: {total_warns}/3")
    if total_warns >= 3:
        bans_data[user.id] = 1
        await user.ban(reason="Reached 3/3 warns")
        await send_log(f"🔨 {user.mention} automatically banned for reaching 3/3 warns")
        warns_data[user.id] = 0

@app_commands.checks.has_any_role("Staff Team", "NexusVision Team")
@bot.tree.command(name="warns_list", description="Show warns of a user", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(user="Select user")
async def warns_list(interaction: discord.Interaction, user: discord.Member):
    total_warns = warns_data.get(user.id, 0)
    await interaction.response.send_message(f"⚠️ {user.mention} has {total_warns}/3 warns", ephemeral=True)

@app_commands.checks.has_any_role("Staff Team", "NexusVision Team")
@bot.tree.command(name="bans_list", description="Show banned users", guild=discord.Object(id=GUILD_ID))
async def bans_list(interaction: discord.Interaction):
    banned_users = [f"<@{uid}>: {days} day(s)" for uid, days in bans_data.items()]
    await interaction.response.send_message("🔨 Banned Users:\n" + ("\n".join(banned_users) if banned_users else "None"), ephemeral=True)

@app_commands.checks.has_any_role("Staff Team", "NexusVision Team")
@bot.tree.command(name="mutes_list", description="Show muted users", guild=discord.Object(id=GUILD_ID))
async def mutes_list(interaction: discord.Interaction):
    muted_users = [f"<@{uid}>: {days} day(s)" for uid, days in mutes_data.items()]
    await interaction.response.send_message("🔇 Muted Users:\n" + ("\n".join(muted_users) if muted_users else "None"), ephemeral=True)

@app_commands.checks.has_any_role("Staff Team", "NexusVision Team")
@bot.tree.command(name="all_admin_comands", description="Show all admin commands", guild=discord.Object(id=GUILD_ID))
async def all_admin_comands(interaction: discord.Interaction):
    commands_list = [
        "/change_vip_role",
        "/warn",
        "/warns_list",
        "/bans_list",
        "/mutes_list",
        "/setchanel_logs"
    ]
    await interaction.response.send_message("🛠️ Admin Commands:\n" + "\n".join(commands_list), ephemeral=True)

@app_commands.checks.has_any_role("Staff Team", "NexusVision Team")
@bot.tree.command(name="setchanel_logs", description="Set log channel", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(channel="Select channel for logs")
async def setchanel_logs(interaction: discord.Interaction, channel: discord.TextChannel):
    global LOG_CHANNEL_ID
    LOG_CHANNEL_ID = channel.id
    await interaction.response.send_message(f"✅ Log channel set to {channel.mention}", ephemeral=True)
    await send_log(f"{interaction.user.mention} set the log channel to {channel.mention}")

# ================== LEGACY (?scripts) ==================
@bot.command(name="scripts")
async def scripts(ctx):
    embed = discord.Embed(
        title="📜 Script Panel",
        description="This script panel is for the project : **Unicore**\n\nUse the buttons below to get Universal Script or AR2 Script",
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

# ================== Run ==================
keep_alive()
bot.run(os.getenv("TOKEN"))
