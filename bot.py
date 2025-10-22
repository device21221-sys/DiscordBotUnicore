import discord
from discord import app_commands
from discord.ext import commands, tasks
import os
from keep_alive import keep_alive
import asyncio
from collections import defaultdict
from datetime import datetime, timedelta

# ================== CONFIG ==================
GUILD_ID = 1344670393092280481  # Your server ID

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix="?", intents=intents)

# ================== CHANNELS ==================
RULES_CHANNEL_ID = 1351689723369754634
INFO_CHANNEL_ID = 1425554175231529054
SUPPORT_CHANNEL_ID = 1411789053921202286
EXECUTORS_CHANNEL_ID = 1404173340125429792
STATUS_CHANNEL_ID = None  # can be set later
LOG_CHANNEL_ID = None

# ================== ROLES ==================
ADMIN_ROLES = ["Staff Team", "NexusVision Team"]

# ================== DATA ==================
warns_data = defaultdict(int)
mutes_data = {}  # {user_id: unmute_time}
bans_data = {}   # {user_id: reason}

# ================== HELPERS ==================
def is_admin(member: discord.Member):
    return any(role.name in ADMIN_ROLES for role in member.roles)

def create_embed(title: str, description: str, color=0x2b2d31):
    embed = discord.Embed(title=title, description=description, color=color)
    embed.set_footer(text="NexusVision.lua.bot • System")
    return embed

async def send_log(message: str):
    if LOG_CHANNEL_ID:
        channel = bot.get_channel(LOG_CHANNEL_ID)
        if channel:
            await channel.send(message)

async def mute_user(user: discord.Member, duration: timedelta, reason="No reason provided"):
    muted_role = discord.utils.get(user.guild.roles, name="Muted")
    if not muted_role:
        muted_role = await user.guild.create_role(name="Muted")
        for ch in user.guild.channels:
            await ch.set_permissions(muted_role, send_messages=False, speak=False)
    await user.add_roles(muted_role, reason=reason)
    mutes_data[user.id] = datetime.utcnow() + duration
    await send_log(f"{user.mention} muted for {duration}. Reason: {reason}")

async def unmute_user(user: discord.Member, reason="No reason provided"):
    muted_role = discord.utils.get(user.guild.roles, name="Muted")
    if muted_role in user.roles:
        await user.remove_roles(muted_role, reason=reason)
    if user.id in mutes_data:
        del mutes_data[user.id]
    await send_log(f"{user.mention} unmuted. Reason: {reason}")

# ================== EVENTS ==================
@bot.event
async def on_ready():
    guild = discord.Object(id=GUILD_ID)
    try:
        print("Cleaning old commands...")
        guild_cmds = await bot.tree.fetch_commands(guild=guild)
        for cmd in guild_cmds:
            await bot.tree.delete_command(cmd.id, guild=guild)
        await bot.tree.sync(guild=guild)
        print(f"Bot online! Synced {len(await bot.tree.fetch_commands(guild=guild))} commands.")
    except Exception as e:
        print(f"Command sync failed: {e}")

    check_mutes.start()

@bot.event
async def on_message(message: discord.Message):
    if message.author.bot:
        return

    # Block executors
    blocked_words = ["solara", "xeno", "jjsploit"]
    if any(word.lower() in message.content.lower() for word in blocked_words):
        try:
            await message.delete()
        except discord.Forbidden:
            pass
        await mute_user(message.author, timedelta(hours=1), reason="Executor not supported")
        channel = bot.get_channel(EXECUTORS_CHANNEL_ID)
        mention = channel.mention if channel else "support-executors"
        await message.channel.send(f"Executor not supported, please go to {mention}", delete_after=10)
        return

    # Simple spam check (sending more than 5 messages in 10 seconds)
    if not hasattr(bot, "user_messages"):
        bot.user_messages = defaultdict(list)

    now = datetime.utcnow()
    bot.user_messages[message.author.id].append(now)
    # Remove old messages
    bot.user_messages[message.author.id] = [t for t in bot.user_messages[message.author.id] if now - t < timedelta(seconds=10)]
    if len(bot.user_messages[message.author.id]) > 5:
        await mute_user(message.author, timedelta(days=1), reason="Spamming")
        await message.channel.send("Stop spamming!", delete_after=10)
        bot.user_messages[message.author.id].clear()

    await bot.process_commands(message)

# ================== TASKS ==================
@tasks.loop(seconds=60)
async def check_mutes():
    now = datetime.utcnow()
    to_unmute = [user_id for user_id, unmute_time in mutes_data.items() if now >= unmute_time]
    for user_id in to_unmute:
        user = bot.get_user(user_id)
        if user:
            await unmute_user(user, reason="Mute duration expired")

# ================== USER COMMANDS ==================
@bot.tree.command(name="get_script", description="Get the AR2 Script")
async def get_script(interaction: discord.Interaction):
    content = (
        f"Hello {interaction.user.mention}!\n"
        "Script ready to use here:\n"
        "```lua\n"
        'loadstring(game:HttpGet("https://raw.githubusercontent.com/NightFallScript/Unicore/refs/heads/main/ApocalypseRising2.luau"))()\n'
        "```\nby NexusVision Team"
    )
    await interaction.response.send_message(content, ephemeral=True)

@bot.tree.command(name="info", description="Show info channel")
async def info(interaction: discord.Interaction):
    channel = bot.get_channel(INFO_CHANNEL_ID)
    if channel:
        await interaction.response.send_message(f"Info is here: {channel.mention}", ephemeral=True)
    else:
        await interaction.response.send_message("Info channel not found.", ephemeral=True)

@bot.tree.command(name="status", description="Show status channel")
async def status(interaction: discord.Interaction):
    channel = STATUS_CHANNEL_ID and bot.get_channel(STATUS_CHANNEL_ID)
    if channel:
        await interaction.response.send_message(f"Status is here: {channel.mention}", ephemeral=True)
    else:
        await interaction.response.send_message("Status channel not set.", ephemeral=True)

@bot.tree.command(name="rules", description="Link to rules channel")
async def rules(interaction: discord.Interaction):
    channel = bot.get_channel(RULES_CHANNEL_ID)
    if channel:
        await interaction.response.send_message(f"Rules are here: {channel.mention}", ephemeral=True)
    else:
        await interaction.response.send_message("Rules channel not found.", ephemeral=True)

@bot.tree.command(name="support", description="Link to support channel")
async def support(interaction: discord.Interaction):
    channel = bot.get_channel(SUPPORT_CHANNEL_ID)
    if channel:
        await interaction.response.send_message(f"Support is here: {channel.mention}", ephemeral=True)
    else:
        await interaction.response.send_message("Support channel not found.", ephemeral=True)

@bot.tree.command(name="supported_executors", description="Show supported executors channel")
async def supported_executors(interaction: discord.Interaction):
    channel = bot.get_channel(EXECUTORS_CHANNEL_ID)
    if channel:
        await interaction.response.send_message(f"Executors channel: {channel.mention}", ephemeral=True)
    else:
        await interaction.response.send_message("Executors channel not found.", ephemeral=True)

@bot.tree.command(name="help", description="List all available commands")
async def help_command(interaction: discord.Interaction):
    embed = create_embed(
        "Command List",
        "**User Commands:**\n"
        "- /get_script\n- /info\n- /status\n- /rules\n- /support\n- /supported_executors\n"
        "**Admin Commands (NexusVision Team / Staff Team):**\n"
        "- /ban\n- /mute\n- /unmute\n- /warn\n- /unwarn\n- /logs\n- /setupchanellogs\n- /rolegive\n- /kick"
    )
    await interaction.response.send_message(embed=embed, ephemeral=True)

# ================== ADMIN COMMANDS ==================
@app_commands.checks.has_any_role(*ADMIN_ROLES)
@bot.tree.command(name="ban", description="Ban a user")
@app_commands.describe(user="Select user", reason="Reason for ban")
async def ban(interaction: discord.Interaction, user: discord.Member, reason: str):
    await user.ban(reason=reason)
    bans_data[user.id] = reason
    await interaction.response.send_message(f"{user.mention} banned. Reason: {reason}", ephemeral=True)
    await send_log(f"{interaction.user.mention} banned {user.mention}. Reason: {reason}")

@app_commands.checks.has_any_role(*ADMIN_ROLES)
@bot.tree.command(name="kick", description="Kick a user")
@app_commands.describe(user="Select user", reason="Reason for kick")
async def kick(interaction: discord.Interaction, user: discord.Member, reason: str):
    await user.kick(reason=reason)
    await interaction.response.send_message(f"{user.mention} kicked. Reason: {reason}", ephemeral=True)
    await send_log(f"{interaction.user.mention} kicked {user.mention}. Reason: {reason}")

@app_commands.checks.has_any_role(*ADMIN_ROLES)
@bot.tree.command(name="mute", description="Mute a user")
@app_commands.describe(user="Select user", duration="1h, 7h, 1d, 3d, 7d, 30d", reason="Reason for mute")
async def mute(interaction: discord.Interaction, user: discord.Member, duration: str, reason: str):
    mapping = {"1h": 1, "7h": 7, "1d": 24, "3d": 72, "7d": 168, "30d": 720}
    hours = mapping.get(duration.lower())
    if hours:
        await mute_user(user, timedelta(hours=hours), reason=reason)
        await interaction.response.send_message(f"{user.mention} muted for {duration}. Reason: {reason}", ephemeral=True)
    else:
        await interaction.response.send_message("Invalid duration.", ephemeral=True)

@app_commands.checks.has_any_role(*ADMIN_ROLES)
@bot.tree.command(name="unmute", description="Unmute a user")
@app_commands.describe(user="Select user", reason="Reason for unmute")
async def unmute(interaction: discord.Interaction, user: discord.Member, reason: str):
    await unmute_user(user, reason=reason)
    await interaction.response.send_message(f"{user.mention} unmuted. Reason: {reason}", ephemeral=True)

@app_commands.checks.has_any_role(*ADMIN_ROLES)
@bot.tree.command(name="warn", description="Warn a user")
@app_commands.describe(user="Select user", reason="Reason for warn")
async def warn(interaction: discord.Interaction, user: discord.Member, reason: str):
    warns_data[user.id] += 1
    total = warns_data[user.id]
    await interaction.response.send_message(f"{user.mention} warned ({total}/3). Reason: {reason}", ephemeral=True)
    await send_log(f"{interaction.user.mention} warned {user.mention}. Reason: {reason}")
    if total >= 3:
        if is_admin(user):
            staff_role = discord.utils.get(user.guild.roles, name="Staff Team")
            if staff_role in user.roles:
                await user.remove_roles(staff_role, reason="3/3 warns")
        else:
            await user.kick(reason="3/3 warns")
        warns_data[user.id] = 0

@app_commands.checks.has_any_role(*ADMIN_ROLES)
@bot.tree.command(name="unwarn", description="Remove warn from user")
@app_commands.describe(user="Select user", reason="Reason for unwarn")
async def unwarn(interaction: discord.Interaction, user: discord.Member, reason: str):
    warns_data[user.id] = max(warns_data[user.id] - 1, 0)
    await interaction.response.send_message(f"{user.mention} unwarned. Reason: {reason}", ephemeral=True)
    await send_log(f"{interaction.user.mention} removed a warn from {user.mention}. Reason: {reason}")

@app_commands.checks.has_any_role(*ADMIN_ROLES)
@bot.tree.command(name="rolegive", description="Give role to user")
@app_commands.describe(user="Select user", role="Role to give")
async def rolegive(interaction: discord.Interaction, user: discord.Member, role: str):
    role_obj = discord.utils.get(interaction.guild.roles, name=role)
    if role_obj:
        await user.add_roles(role_obj)
        await interaction.response.send_message(f"{role} role given to {user.mention}", ephemeral=True)
        await send_log(f"{interaction.user.mention} gave {role} role to {user.mention}")
    else:
        await interaction.response.send_message(f"Role {role} not found.", ephemeral=True)

@app_commands.checks.has_any_role(*ADMIN_ROLES)
@bot.tree.command(name="logs", description="Show server logs and roles")
async def logs(interaction: discord.Interaction):
    roles_info = "\n".join([f"{role.name}: {len(role.members)} members" for role in interaction.guild.roles])
    bans_info = "\n".join([f"<@{uid}>: {reason}" for uid, reason in bans_data.items()]) or "None"
    mutes_info = "\n".join([f"<@{uid}>: unmute at {time}" for uid, time in mutes_data.items()]) or "None"
    warns_info = "\n".join([f"<@{uid}>: {count}/3" for uid, count in warns_data.items()]) or "None"

    embed = create_embed(
        "Server Logs",
        f"**Roles:**\n{roles_info}\n\n**Bans:**\n{bans_info}\n\n**Mutes:**\n{mutes_info}\n\n**Warns:**\n{warns_info}"
    )
    await interaction.response.send_message(embed=embed, ephemeral=True)

@app_commands.checks.has_any_role(*ADMIN_ROLES)
@bot.tree.command(name="setupchanellogs", description="Set up automatic logs (hourly)")
@app_commands.describe(channel="Channel to send logs")
async def setupchanellogs(interaction: discord.Interaction, channel: discord.TextChannel):
    global LOG_CHANNEL_ID
    LOG_CHANNEL_ID = channel.id
    await interaction.response.send_message(f"Logs channel set to {channel.mention}", ephemeral=True)

# ================== RUN ==================
keep_alive()
bot.run(os.getenv("TOKEN"))
