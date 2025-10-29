import discord
from discord import app_commands
from discord.ext import commands
import os
from datetime import timedelta
from collections import defaultdict
from keep_alive import keep_alive

# ================== CONFIG ==================
GUILD_ID = 1344670393092280481
ADMIN_ROLE = "Administrator"
MOD_ROLE = "Moderator"

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix="?", intents=intents)

# ================== CHANNELS ==================
RULES_CHANNEL_ID = 1351689723369754634
INFO_CHANNEL_ID = 1425554175231529054
SUPPORT_PANEL_ID = 1411789053921202286
EXECUTORS_CHANNEL_ID = 1404173340125429792
SCRIPT_PANEL_ID = 1404173340125429792

# ================== DATA ==================
warns_data = defaultdict(int)
mutes_data = {}

# ================== HELPERS ==================
def has_role(member: discord.Member, role_name: str):
    return any(role.name == role_name for role in member.roles)

def create_embed(title: str, description: str):
    embed = discord.Embed(
        title=f"**{title}**",
        description=description,
        color=0xff0000  # червона рамка
    )
    embed.set_footer(text="NexusVision.lua • System")
    return embed

async def mute_user(member: discord.Member, duration: timedelta, reason="No reason provided"):
    muted_role = discord.utils.get(member.guild.roles, name="Muted")
    if not muted_role:
        muted_role = await member.guild.create_role(name="Muted")
        for ch in member.guild.channels:
            await ch.set_permissions(muted_role, send_messages=False, speak=False)

    await member.add_roles(muted_role, reason=reason)
    mutes_data[member.id] = duration.total_seconds()
    try:
        await member.send(embed=create_embed("Muted", f"You have been muted for {duration}. Reason: {reason}"))
    except:
        pass

async def unmute_user(member: discord.Member):
    muted_role = discord.utils.get(member.guild.roles, name="Muted")
    if muted_role in member.roles:
        await member.remove_roles(muted_role)
    if member.id in mutes_data:
        del mutes_data[member.id]

# ================== EVENTS ==================
@bot.event
async def on_ready():
    guild = discord.Object(id=GUILD_ID)

    # ===== Delete old global commands =====
    global_cmds = await bot.tree.fetch_commands()
    for cmd in global_cmds:
        await bot.tree.delete_command(cmd.id)

    # ===== Delete old guild commands =====
    guild_cmds = await bot.tree.fetch_commands(guild=guild)
    for cmd in guild_cmds:
        await bot.tree.delete_command(cmd.id, guild=guild)

    # ===== Sync new commands =====
    await bot.tree.sync(guild=guild)
    print(f"✅ Commands cleared and synced. Bot online as {bot.user}")

# ================== USER COMMANDS ==================
@bot.tree.command(name="get-script", description="Get the NexusVision script")
async def get_script(interaction: discord.Interaction):
    embed = create_embed(
        "NexusVision Script",
        "Hello!\nNexusVision script is public to use :\n\nHere your script :\n```lua\nloadstring(game:HttpGet(\"https://raw.githubusercontent.com/NightFallScript/Unicore/refs/heads/main/ApocalypseRising2.luau\"))()\n```"
    )
    await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.tree.command(name="info", description="Show info channel")
async def info(interaction: discord.Interaction):
    channel = bot.get_channel(INFO_CHANNEL_ID)
    text = f"Information channel: {channel.mention}" if channel else "Info channel not found."
    await interaction.response.send_message(embed=create_embed("Info", text), ephemeral=True)

@bot.tree.command(name="rules", description="Show rules channel")
async def rules(interaction: discord.Interaction):
    channel = bot.get_channel(RULES_CHANNEL_ID)
    text = f"Rules channel: {channel.mention}" if channel else "Rules channel not found."
    await interaction.response.send_message(embed=create_embed("Rules", text), ephemeral=True)

@bot.tree.command(name="script-panel", description="Show script panel channel")
async def script_panel(interaction: discord.Interaction):
    channel = bot.get_channel(SCRIPT_PANEL_ID)
    text = f"Script panel: {channel.mention}" if channel else "Script panel not found."
    await interaction.response.send_message(embed=create_embed("Script Panel", text), ephemeral=True)

@bot.tree.command(name="support-executors", description="Show supported executors")
async def support_executors(interaction: discord.Interaction):
    channel = bot.get_channel(EXECUTORS_CHANNEL_ID)
    text = f"Supported executors: {channel.mention}" if channel else "Executors channel not found."
    await interaction.response.send_message(embed=create_embed("Supported Executors", text), ephemeral=True)

@bot.tree.command(name="support-panel", description="Show support panel")
async def support_panel(interaction: discord.Interaction):
    channel = bot.get_channel(SUPPORT_PANEL_ID)
    text = f"Support panel: {channel.mention}" if channel else "Support panel not found."
    await interaction.response.send_message(embed=create_embed("Support Panel", text), ephemeral=True)

# ================== MODERATOR COMMANDS ==================
@bot.tree.command(name="mute", description="Mute a user")
async def mute(interaction: discord.Interaction, member: discord.Member, minutes: int, reason: str = "No reason provided"):
    if not has_role(interaction.user, MOD_ROLE) and not has_role(interaction.user, ADMIN_ROLE):
        return await interaction.response.send_message(embed=create_embed("Error", "You don’t have permission."), ephemeral=True)
    await mute_user(member, timedelta(minutes=minutes), reason)
    await interaction.response.send_message(embed=create_embed("Muted", f"{member.mention} muted for {minutes}m. Reason: {reason}"), ephemeral=True)

@bot.tree.command(name="unmute", description="Unmute a user")
async def unmute(interaction: discord.Interaction, member: discord.Member):
    if not has_role(interaction.user, MOD_ROLE) and not has_role(interaction.user, ADMIN_ROLE):
        return await interaction.response.send_message(embed=create_embed("Error", "You don’t have permission."), ephemeral=True)
    await unmute_user(member)
    await interaction.response.send_message(embed=create_embed("Unmuted", f"{member.mention} has been unmuted."), ephemeral=True)

@bot.tree.command(name="kick", description="Kick a user")
async def kick(interaction: discord.Interaction, member: discord.Member, reason: str = "No reason provided"):
    if not has_role(interaction.user, MOD_ROLE) and not has_role(interaction.user, ADMIN_ROLE):
        return await interaction.response.send_message(embed=create_embed("Error", "You don’t have permission."), ephemeral=True)
    await member.kick(reason=reason)
    await interaction.response.send_message(embed=create_embed("Kicked", f"{member.mention} was kicked. Reason: {reason}"), ephemeral=True)

@bot.tree.command(name="warn", description="Warn a user")
async def warn(interaction: discord.Interaction, member: discord.Member, reason: str = "No reason provided"):
    if not has_role(interaction.user, MOD_ROLE) and not has_role(interaction.user, ADMIN_ROLE):
        return await interaction.response.send_message(embed=create_embed("Error", "You don’t have permission."), ephemeral=True)
    warns_data[member.id] += 1
    await interaction.response.send_message(embed=create_embed("Warn", f"{member.mention} received a warning.\nReason: {reason}\nTotal warns: {warns_data[member.id]}"), ephemeral=True)

@bot.tree.command(name="unwarn", description="Remove a warning from a user")
async def unwarn(interaction: discord.Interaction, member: discord.Member):
    if not has_role(interaction.user, MOD_ROLE) and not has_role(interaction.user, ADMIN_ROLE):
        return await interaction.response.send_message(embed=create_embed("Error", "You don’t have permission."), ephemeral=True)
    if warns_data[member.id] > 0:
        warns_data[member.id] -= 1
    await interaction.response.send_message(embed=create_embed("Unwarn", f"{member.mention} warnings reduced to {warns_data[member.id]}"), ephemeral=True)

@bot.tree.command(name="clear", description="Clear messages in a channel")
async def clear(interaction: discord.Interaction, amount: int):
    if not has_role(interaction.user, MOD_ROLE) and not has_role(interaction.user, ADMIN_ROLE):
        return await interaction.response.send_message(embed=create_embed("Error", "You don’t have permission."), ephemeral=True)
    await interaction.channel.purge(limit=amount)
    await interaction.response.send_message(embed=create_embed("Clear", f"Deleted {amount} messages."), ephemeral=True)

# ================== ADMIN COMMANDS ==================
@bot.tree.command(name="ban", description="Ban a user")
async def ban(interaction: discord.Interaction, member: discord.Member, reason: str = "No reason provided"):
    if not has_role(interaction.user, ADMIN_ROLE):
        return await interaction.response.send_message(embed=create_embed("Error", "You don’t have permission."), ephemeral=True)
    await member.ban(reason=reason)
    await interaction.response.send_message(embed=create_embed("Banned", f"{member.mention} has been banned. Reason: {reason}"), ephemeral=True)

@bot.tree.command(name="unban", description="Unban a user")
async def unban(interaction: discord.Interaction, user_id: int):
    if not has_role(interaction.user, ADMIN_ROLE):
        return await interaction.response.send_message(embed=create_embed("Error", "You don’t have permission."), ephemeral=True)
    user = await bot.fetch_user(user_id)
    await interaction.guild.unban(user)
    await interaction.response.send_message(embed=create_embed("Unbanned", f"{user.mention} has been unbanned."), ephemeral=True)

# ================== HELP ==================
@bot.tree.command(name="help", description="Show available commands")
async def help_command(interaction: discord.Interaction):
    user = interaction.user
    cmds = ["`/get-script`", "`/help`", "`/info`", "`/rules`", "`/script-panel`", "`/support-executors`", "`/support-panel`"]

    if has_role(user, MOD_ROLE) or has_role(user, ADMIN_ROLE):
        cmds += ["`/mute`", "`/unmute`", "`/kick`", "`/warn`", "`/unwarn`", "`/clear`"]
    if has_role(user, ADMIN_ROLE):
        cmds += ["`/ban`", "`/unban`"]

    embed = create_embed("Command List", "\n".join(cmds))
    await interaction.response.send_message(embed=embed, ephemeral=True)

# ================== RUN ==================
keep_alive()
bot.run(os.getenv("TOKEN"))

