import discord
from discord import app_commands
from discord.ext import commands
import os
from keep_alive import keep_alive

# ================== CONFIG ==================
GUILD_ID = 1344670393092280481  # твій сервер

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix="?", intents=intents)

# ================== Channel IDs ==================
RULES_CHANNEL_ID = 1351689723369754634
INFO_CHANNEL_ID = 1425554175231529054
SUPPORT_CHANNEL_ID = 1411789053921202286
EXECUTORS_CHANNEL_ID = 1404173340125429792
LOG_CHANNEL_ID = None  # встановлюється через /setchanel_logs

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
    embed.set_footer(text="⚙️ Powered by Unicore", icon_url=bot.user.avatar.url if bot.user and bot.user.avatar else discord.Embed.Empty)
    return embed

# ================== Events ==================
@bot.event
async def on_ready():
    guild = discord.Object(id=GUILD_ID)
    try:
        # 🔥 очистка старих дублікатів команд
        bot.tree.clear_commands(guild=guild)
        await bot.tree.sync(guild=guild)
        print(f"✅ Synced & cleaned all commands for guild {GUILD_ID}!")
    except Exception as e:
        print(f"⚠️ Sync error: {e}")

    print(f"🤖 Bot {bot.user} is now online!")

@bot.event
async def on_message(message: discord.Message):
    if message.author.bot:
        return

    blocked_words = ["solara", "xeno", "jjsploit", "Solara", "Xeno", "JJSploit"]
    if any(word in message.content.lower() for word in blocked_words):
        try:
            await message.delete()
        except discord.Forbidden:
            pass

        channel = bot.get_channel(EXECUTORS_CHANNEL_ID)
        name = next((n.capitalize() for n in blocked_words if n in message.content.lower()), "Executor")

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
    await interaction.response.send_message(embed=create_embed("📜 AR2 Script", script), ephemeral=True)

@bot.tree.command(name="get_universal_script", description="Get the Universal Script", guild=discord.Object(id=GUILD_ID))
async def get_universal_script(interaction: discord.Interaction):
    script = "```lua\nloadstring(game:HttpGet('https://raw.githubusercontent.com/NightFallScript/Unicore/refs/heads/main/DoorsUnicore'))()\n```"
    await interaction.response.send_message(embed=create_embed("📜 Universal Script", script), ephemeral=True)

@bot.tree.command(name="rules", description="Link to rules channel", guild=discord.Object(id=GUILD_ID))
async def rules(interaction: discord.Interaction):
    channel = bot.get_channel(RULES_CHANNEL_ID)
    text = f"📜 Rules are here: {channel.mention}" if channel else "❌ Rules channel not found."
    await interaction.response.send_message(embed=create_embed("Rules", text), ephemeral=True)

@bot.tree.command(name="info", description="Link to info channel", guild=discord.Object(id=GUILD_ID))
async def info(interaction: discord.Interaction):
    channel = bot.get_channel(INFO_CHANNEL_ID)
    text = f"ℹ️ Info is here: {channel.mention}" if channel else "❌ Info channel not found."
    await interaction.response.send_message(embed=create_embed("Information", text), ephemeral=True)

@bot.tree.command(name="support", description="Link to support channel", guild=discord.Object(id=GUILD_ID))
async def support(interaction: discord.Interaction):
    channel = bot.get_channel(SUPPORT_CHANNEL_ID)
    text = f"🛠️ Support is here: {channel.mention}" if channel else "❌ Support channel not found."
    await interaction.response.send_message(embed=create_embed("Support", text), ephemeral=True)

@bot.tree.command(name="support_executors", description="Link to executors channel", guild=discord.Object(id=GUILD_ID))
async def support_executors(interaction: discord.Interaction):
    channel = bot.get_channel(EXECUTORS_CHANNEL_ID)
    text = f"⚙️ Executors are here: {channel.mention}" if channel else "❌ Executors channel not found."
    await interaction.response.send_message(embed=create_embed("Executors", text), ephemeral=True)

@bot.tree.command(name="help", description="List all available commands", guild=discord.Object(id=GUILD_ID))
async def help_command(interaction: discord.Interaction):
    embed = create_embed("📖 Command List")
    embed.add_field(name="/get_ar2_script", value="Get AR2 Script", inline=False)
    embed.add_field(name="/get_universal_script", value="Get Universal Script", inline=False)
    embed.add_field(name="/rules", value="Show rules channel", inline=False)
    embed.add_field(name="/info", value="Show info channel", inline=False)
    embed.add_field(name="/support", value="Show support channel", inline=False)
    embed.add_field(name="/support_executors", value="Show executors channel", inline=False)
    embed.add_field(name="/all_admin_comands", value="Show all admin commands", inline=False)
    await interaction.response.send_message(embed=embed, ephemeral=True)

# ================== ADMIN COMMANDS ==================
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
    total = warns_data[user.id]
    msg = f"⚠️ {user.mention} warned for: {reason} (Total warns: {total}/3)"
    await interaction.response.send_message(embed=create_embed("Warning", msg), ephemeral=True)
    await send_log(msg)

    if total >= 3:
        bans_data[user.id] = 1
        await user.ban(reason="Reached 3/3 warns")
        warns_data[user.id] = 0
        await send_log(f"🔨 {user.mention} automatically banned after 3 warns")

@app_commands.checks.has_any_role("Staff Team", "NexusVision Team")
@bot.tree.command(name="warns_list", description="Show warns of a user", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(user="Select user")
async def warns_list(interaction: discord.Interaction, user: discord.Member):
    total = warns_data.get(user.id, 0)
    await interaction.response.send_message(embed=create_embed("Warns", f"{user.mention} has {total}/3 warns"), ephemeral=True)

@app_commands.checks.has_any_role("Staff Team", "NexusVision Team")
@bot.tree.command(name="bans_list", description="Show banned users", guild=discord.Object(id=GUILD_ID))
async def bans_list(interaction: discord.Interaction):
    if not bans_data:
        msg = "No banned users."
    else:
        msg = "\n".join([f"<@{uid}> - {days} day(s)" for uid, days in bans_data.items()])
    await interaction.response.send_message(embed=create_embed("Banned Users", msg), ephemeral=True)

@app_commands.checks.has_any_role("Staff Team", "NexusVision Team")
@bot.tree.command(name="mutes_list", description="Show muted users", guild=discord.Object(id=GUILD_ID))
async def mutes_list(interaction: discord.Interaction):
    if not mutes_data:
        msg = "No muted users."
    else:
        msg = "\n".join([f"<@{uid}> - {days} day(s)" for uid, days in mutes_data.items()])
    await interaction.response.send_message(embed=create_embed("Muted Users", msg), ephemeral=True)

@app_commands.checks.has_any_role("Staff Team", "NexusVision Team")
@bot.tree.command(name="setchanel_logs", description="Set log channel", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(channel="Select channel for logs")
async def setchanel_logs(interaction: discord.Interaction, channel: discord.TextChannel):
    global LOG_CHANNEL_ID
    LOG_CHANNEL_ID = channel.id
    msg = f"✅ Log channel set to {channel.mention}"
    await interaction.response.send_message(embed=create_embed("Log Channel", msg), ephemeral=True)
    await send_log(f"{interaction.user.mention} set log channel to {channel.mention}")

# ================== Run ==================
keep_alive()
bot.run(os.getenv("TOKEN"))
