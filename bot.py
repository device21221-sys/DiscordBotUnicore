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
            embed = discord.Embed(description=message, color=0x5865F2)
            await channel.send(embed=embed)

def create_embed(title=None, description=None, color=0x2b2d31):
    embed = discord.Embed(color=color)
    if title:
        embed.title = title
    if description:
        embed.description = description
    return embed

# ================== Events ==================
@bot.event
async def on_ready():
    guild = discord.Object(id=GUILD_ID)
    await bot.tree.sync(guild=guild)
    print(f"✅ Bot {bot.user} is online and commands synced for guild {GUILD_ID}!")

@bot.event
async def on_message(message: discord.Message):
    if message.author.bot:
        return

    blocked_words = ["solara", "xeno", "jjsploit"]
    if any(word in message.content.lower() for word in blocked_words):
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

        embed = create_embed(
            description=f"❌ **{name} is not supported!**\nPlease go to {channel.mention} for help.",
            color=0x57A5FF
        )
        await message.channel.send(embed=embed, delete_after=10)
        return

    await bot.process_commands(message)

# ================== USER SLASH COMMANDS ==================
@bot.tree.command(name="get_ar2_script", description="Get the AR2 Script", guild=discord.Object(id=GUILD_ID))
async def get_ar2_script(interaction: discord.Interaction):
    script = "```lua\nloadstring(game:HttpGet('https://raw.githubusercontent.com/UnicoreRoblox/Unicore/refs/heads/main/ApocalypseRising2.luau'))()\n```"
    embed = create_embed("📜 AR2 Script", script)
    await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.tree.command(name="get_universal_script", description="Get the Universal Script", guild=discord.Object(id=GUILD_ID))
async def get_universal_script(interaction: discord.Interaction):
    script = "```lua\nloadstring(game:HttpGet('https://raw.githubusercontent.com/NightFallScript/Unicore/refs/heads/main/DoorsUnicore'))()\n```"
    embed = create_embed("📜 Universal Script", script)
    await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.tree.command(name="rules", description="Link to rules channel", guild=discord.Object(id=GUILD_ID))
async def rules(interaction: discord.Interaction):
    channel = bot.get_channel(RULES_CHANNEL_ID)
    desc = f"📜 Rules are here: {channel.mention}" if channel else "❌ Rules channel not found."
    embed = create_embed("Rules", desc)
    await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.tree.command(name="info", description="Link to info channel", guild=discord.Object(id=GUILD_ID))
async def info(interaction: discord.Interaction):
    channel = bot.get_channel(INFO_CHANNEL_ID)
    desc = f"ℹ️ Info is here: {channel.mention}" if channel else "❌ Info channel not found."
    embed = create_embed("Information", desc)
    await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.tree.command(name="support", description="Link to support channel", guild=discord.Object(id=GUILD_ID))
async def support(interaction: discord.Interaction):
    channel = bot.get_channel(SUPPORT_CHANNEL_ID)
    desc = f"🛠️ Support is here: {channel.mention}" if channel else "❌ Support channel not found."
    embed = create_embed("Support", desc)
    await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.tree.command(name="support_executors", description="Link to executors channel", guild=discord.Object(id=GUILD_ID))
async def support_executors(interaction: discord.Interaction):
    channel = bot.get_channel(EXECUTORS_CHANNEL_ID)
    desc = f"⚙️ Executors are here: {channel.mention}" if channel else "❌ Executors channel not found."
    embed = create_embed("Executors Support", desc)
    await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.tree.command(name="help", description="List all available commands", guild=discord.Object(id=GUILD_ID))
async def help_command(interaction: discord.Interaction):
    embed = create_embed("📖 Command List")
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
        return await interaction.response.send_message(embed=create_embed("Error", "❌ VIP role not found."), ephemeral=True)

    if action.lower() == "add":
        await user.add_roles(vip_role)
        msg = f"✅ VIP role added to {user.mention}"
        await send_log(f"{interaction.user.mention} added VIP role to {user.mention}")
    elif action.lower() == "remove":
        await user.remove_roles(vip_role)
        msg = f"✅ VIP role removed from {user.mention}"
        await send_log(f"{interaction.user.mention} removed VIP role from {user.mention}")
    else:
        msg = "❌ Action must be 'add' or 'remove'."

    await interaction.response.send_message(embed=create_embed("VIP Role Update", msg), ephemeral=True)

@app_commands.checks.has_any_role("Staff Team", "NexusVision Team")
@bot.tree.command(name="warn", description="Warn a user", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(user="Select user", reason="Reason for warning")
async def warn(interaction: discord.Interaction, user: discord.Member, reason: str):
    warns_data[user.id] = warns_data.get(user.id, 0) + 1
    total_warns = warns_data[user.id]
    msg = f"⚠️ {user.mention} warned for: {reason} (Total warns: {total_warns}/3)"
    await interaction.response.send_message(embed=create_embed("Warning Issued", msg), ephemeral=True)
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
    msg = f"⚠️ {user.mention} has {total_warns}/3 warns"
    await interaction.response.send_message(embed=create_embed("Warns List", msg), ephemeral=True)

@app_commands.checks.has_any_role("Staff Team", "NexusVision Team")
@bot.tree.command(name="bans_list", description="Show banned users", guild=discord.Object(id=GUILD_ID))
async def bans_list(interaction: discord.Interaction):
    banned_users = [f"<@{uid}>: {days} day(s)" for uid, days in bans_data.items()]
    msg = "\n".join(banned_users) if banned_users else "No banned users."
    await interaction.response.send_message(embed=create_embed("🔨 Banned Users", msg), ephemeral=True)

@app_commands.checks.has_any_role("Staff Team", "NexusVision Team")
@bot.tree.command(name="mutes_list", description="Show muted users", guild=discord.Object(id=GUILD_ID))
async def mutes_list(interaction: discord.Interaction):
    muted_users = [f"<@{uid}>: {days} day(s)" for uid, days in mutes_data.items()]
    msg = "\n".join(muted_users) if muted_users else "No muted users."
    await interaction.response.send_message(embed=create_embed("🔇 Muted Users", msg), ephemeral=True)

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
    embed = create_embed("🛠️ Admin Commands", "\n".join(commands_list))
    await interaction.response.send_message(embed=embed, ephemeral=True)

@app_commands.checks.has_any_role("Staff Team", "NexusVision Team")
@bot.tree.command(name="setchanel_logs", description="Set log channel", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(channel="Select channel for logs")
async def setchanel_logs(interaction: discord.Interaction, channel: discord.TextChannel):
    global LOG_CHANNEL_ID
    LOG_CHANNEL_ID = channel.id
    embed = create_embed("✅ Log Channel Updated", f"Log channel set to {channel.mention}")
    await interaction.response.send_message(embed=embed, ephemeral=True)
    await send_log(f"{interaction.user.mention} set the log channel to {channel.mention}")

# ================== Run ==================
keep_alive()
bot.run(os.getenv("TOKEN"))
