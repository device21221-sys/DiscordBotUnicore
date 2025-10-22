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
ADMIN_ROLES = ["Staff Team", "NexusVision Team"]

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix="?", intents=intents)

# ================== CHANNELS ==================
RULES_CHANNEL_ID = 1351689723369754634
INFO_CHANNEL_ID = 1425554175231529054
SUPPORT_CHANNEL_ID = 1411789053921202286
EXECUTORS_CHANNEL_ID = 1404173340125429792
STATUS_CHANNEL_ID = None
LOG_CHANNEL_ID = None

# ================== DATA ==================
warns_data = defaultdict(int)
mutes_data = {}
bans_data = {}

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
    print("Cleaning old commands...")

    guild = discord.Object(id=GUILD_ID)

    # ===== Delete global commands =====
    global_cmds = await bot.tree.fetch_commands()
    for cmd in global_cmds:
        await bot.tree.delete_command(cmd.id)
    print(f"Deleted {len(global_cmds)} global commands")

    # ===== Delete guild commands =====
    guild_cmds = await bot.tree.fetch_commands(guild=guild)
    for cmd in guild_cmds:
        await bot.tree.delete_command(cmd.id, guild=guild)
    print(f"Deleted {len(guild_cmds)} guild commands")

    # Sync new commands
    await bot.tree.sync(guild=guild)
    print("✅ Commands fully cleared and synced")
    print(f"Bot is online as {bot.user}")

    # Start tasks
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

    # Spam detection
    if not hasattr(bot, "user_messages"):
        bot.user_messages = defaultdict(list)

    now = datetime.utcnow()
    bot.user_messages[message.author.id].append(now)
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

# ================== RUN ==================
keep_alive()
bot.run(os.getenv("TOKEN"))
