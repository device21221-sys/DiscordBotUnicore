import discord
from discord import app_commands
from discord.ext import commands, tasks
import os
import random
import re
from datetime import timedelta, datetime
from collections import defaultdict
from keep_alive import keep_alive

# ================== CONFIG ==================
GUILD_ID = 1344670393092280481

# Roles
ADMIN_ROLE = "Administrator"
MOD_ROLE   = "Moderator"
STAFF_ROLE = "Staff Team"
SUPPORT_ROLE = "Support Team"

# Log channels (FILL or set via ?Mod-Logs / ?Adm-Logs)
MOD_LOGS_CHANNEL_ID = 0  # logs only regular users
ADM_LOGS_CHANNEL_ID = 0  # logs everyone

# Member navigation channels
RULES_CHANNEL_ID    = 1351689723369754634
INFO_CHANNEL_ID     = 1425554175231529054
SUPPORT_PANEL_ID    = 1411789053921202286
EXECUTORS_CHANNEL_ID= 1404173340125429792
SCRIPT_PANEL_ID     = 1352959561996173382

# ================== INTENTS / BOT ==================
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix="?", intents=intents)

# ================== DATA ==================
warns_data = defaultdict(int)
mutes_data = {}  # user_id -> seconds left

# ================== HELPERS ==================
def has_role(member: discord.Member, role_name: str):
    return any(role.name == role_name for role in member.roles)

def is_admin(member: discord.Member):
    return has_role(member, ADMIN_ROLE)

def is_mod(member: discord.Member):
    return has_role(member, MOD_ROLE) or is_admin(member)

def is_staff_or_support(member: discord.Member):
    return has_role(member, STAFF_ROLE) or has_role(member, SUPPORT_ROLE)

def is_regular_user(member: discord.Member) -> bool:
    return not (is_mod(member) or is_staff_or_support(member))

def create_embed(title: str, description: str):
    # Red embed, NO footer
    return discord.Embed(title=f"**{title}**", description=description, color=0xff0000)

def parse_duration(text: str) -> timedelta:
    """
    Supports 'days-minutes-seconds' like '1-30-0'
    and optional 'Xd Xh Xm Xs' fallback.
    """
    text = text.strip()
    if re.fullmatch(r"\d+-\d+-\d+", text):
        d, m, s = map(int, text.split("-"))
        return timedelta(days=d, minutes=m, seconds=s)
    days = hours = minutes = seconds = 0
    for num, unit in re.findall(r"(\d+)\s*([dhms])", text.lower()):
        num = int(num)
        if unit == "d": days += num
        elif unit == "h": hours += num
        elif unit == "m": minutes += num
        elif unit == "s": seconds += num
    if days or hours or minutes or seconds:
        return timedelta(days=days, hours=hours, minutes=minutes, seconds=seconds)
    return timedelta(minutes=10)

async def mute_user(member: discord.Member, duration: timedelta, reason="No reason provided"):
    muted_role = discord.utils.get(member.guild.roles, name="Muted")
    if not muted_role:
        muted_role = await member.guild.create_role(name="Muted")
        for ch in member.guild.channels:
            try:
                await ch.set_permissions(muted_role, send_messages=False, speak=False, add_reactions=False)
            except:
                pass
    await member.add_roles(muted_role, reason=reason)
    mutes_data[member.id] = duration.total_seconds()
    try:
        await member.send(embed=create_embed("Muted", f"You have been muted for {duration}. Reason: {reason}"))
    except:
        pass

async def unmute_user(member: discord.Member):
    muted_role = discord.utils.get(member.guild.roles, name="Muted")
    if muted_role and muted_role in member.roles:
        await member.remove_roles(muted_role)
    mutes_data.pop(member.id, None)

async def send_log(to_mod: bool, to_adm: bool, interaction: discord.Interaction):
    try:
        user = interaction.user
        cmd = interaction.command.qualified_name if interaction.command else "unknown"
        now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
        roles = ', '.join([r.name for r in user.roles if r.name != '@everyone']) or 'None'

        # формуємо два вертикальні стовпчики
        left = [
            "Command Used:",
            f"/{cmd}",
            "",
            "User Info:",
            f"{user.display_name}",
            "",
            "Time:",
            f"{now}"
        ]

        right = [
            "Discord Name:",
            f"{user}",
            "",
            "Discord ID:",
            f"{user.id}",
            "",
            "Roles:",
            f"{roles}"
        ]

        # робимо рівні рядки для Discord коду
        formatted = []
        for i in range(max(len(left), len(right))):
            l = left[i] if i < len(left) else ""
            r = right[i] if i < len(right) else ""
            formatted.append(f"{l:<28}{r}")
        text_block = "```fix\n" + "\n".join(formatted) + "\n```"

        embed = discord.Embed(
            title="Command Log",
            description=text_block,
            color=0xff0000
        )

        if to_mod and MOD_LOGS_CHANNEL_ID:
            ch = bot.get_channel(MOD_LOGS_CHANNEL_ID)
            if isinstance(ch, discord.TextChannel):
                await ch.send(embed=embed)

        if to_adm and ADM_LOGS_CHANNEL_ID:
            ch = bot.get_channel(ADM_LOGS_CHANNEL_ID)
            if isinstance(ch, discord.TextChannel):
                await ch.send(embed=embed)

    except Exception as e:
        print(f"[LOG ERROR] {e}")

@bot.event
async def on_ready():
    guild = discord.Object(id=GUILD_ID)
    print("🧹 Clearing ALL old commands (global + guild)...")
    try:
        for cmd in await bot.tree.fetch_commands():
            await bot.tree.delete_command(cmd.id)
            print(f"❌ Deleted GLOBAL command: {cmd.name}")
    except Exception as e:
        print(f"⚠️ Global delete error: {e}")
    try:
        for cmd in await bot.tree.fetch_commands(guild=guild):
            await bot.tree.delete_command(cmd.id, guild=guild)
            print(f"❌ Deleted GUILD command: {cmd.name}")
    except Exception as e:
        print(f"⚠️ Guild delete error: {e}")

    try:
        await bot.tree.sync(guild=guild)
        print(f"✅ Synced to guild {GUILD_ID}")
    except Exception as e:
        print(f"⚠️ Sync error: {e}")

    mute_tick.start()
    print(f"✅ Logged in as {bot.user}")

@tasks.loop(seconds=5)
async def mute_tick():
    remove_ids = []
    for uid, secs in list(mutes_data.items()):
        secs -= 5
        if secs <= 0:
            remove_ids.append(uid)
        else:
            mutes_data[uid] = secs
    for uid in remove_ids:
        for g in bot.guilds:
            m = g.get_member(uid)
            if m:
                await unmute_user(m)

@bot.tree.error
async def on_app_command_error(interaction: discord.Interaction, error):
    # fallback if response not yet sent
    try:
        await interaction.response.send_message(embed=create_embed("Error", f"{error}"), ephemeral=True)
    except:
        await interaction.followup.send(embed=create_embed("Error", f"{error}"), ephemeral=True)

# ================== PERMISSION CHECKS ==================
def mod_perm():
    async def predicate(interaction: discord.Interaction):
        if not is_mod(interaction.user):
            await interaction.response.send_message(embed=create_embed("Error", "You don’t have permission."), ephemeral=True)
            return False
        return True
    return app_commands.check(predicate)

def admin_perm():
    async def predicate(interaction: discord.Interaction):
        if not is_admin(interaction.user):
            await interaction.response.send_message(embed=create_embed("Error", "You don’t have permission."), ephemeral=True)
            return False
        return True
    return app_commands.check(predicate)

# ================== MEMBER CMDS ==================
@bot.tree.command(name="help", description="Show available commands", guild=discord.Object(id=GUILD_ID))
async def help_cmd(interaction: discord.Interaction):
    member_cmds = ["/faq", "/help", "/support", "/support-executors", "/script-panel", "/get-script", "/rules", "/stats"]
    mod_cmds    = ["/ban", "/unban", "/mute", "/unmute", "/warn", "/unwarn", "/kick", "/lock", "/unlock", "/userinfo"]
    fun_cmds    = ["/meme", "/8ball", "/coinflip", "/dice", "/joke", "/slap", "/hug"]

    desc = "**Member:**\n" + ", ".join(member_cmds)
    if is_mod(interaction.user):
        desc += "\n\n**Mod:**\n" + ", ".join(mod_cmds)
    desc += "\n\n**Fun:**\n" + ", ".join(fun_cmds)
    desc += "\n\n**Dev (prefix ?):** `?Script`, `?Mod-Logs`, `?Adm-Logs`"
    await interaction.response.send_message(embed=create_embed("Help", desc), ephemeral=True)
    await send_log(is_regular_user(interaction.user), True, interaction)

@bot.tree.command(name="faq", description="Frequently asked questions", guild=discord.Object(id=GUILD_ID))
async def faq(interaction: discord.Interaction):
    txt = "• How to get the script? Use `/get-script`.\n• Supported executors — `/support-executors`.\n• Need help — `/support`."
    await interaction.response.send_message(embed=create_embed("FAQ", txt), ephemeral=True)
    await send_log(is_regular_user(interaction.user), True, interaction)

@bot.tree.command(name="support", description="Show support panel", guild=discord.Object(id=GUILD_ID))
async def support(interaction: discord.Interaction):
    ch = bot.get_channel(SUPPORT_PANEL_ID)
    txt = f"Support panel: {ch.mention}" if ch else "Support panel not found."
    await interaction.response.send_message(embed=create_embed("Support", txt), ephemeral=True)
    await send_log(is_regular_user(interaction.user), True, interaction)

@bot.tree.command(name="support-executors", description="Show supported executors", guild=discord.Object(id=GUILD_ID))
async def support_executors(interaction: discord.Interaction):
    ch = bot.get_channel(EXECUTORS_CHANNEL_ID)
    txt = f"Supported executors: {ch.mention}" if ch else "Executors channel not found."
    await interaction.response.send_message(embed=create_embed("Supported Executors", txt), ephemeral=True)
    await send_log(is_regular_user(interaction.user), True, interaction)

@bot.tree.command(name="script-panel", description="Show script panel channel", guild=discord.Object(id=GUILD_ID))
async def script_panel(interaction: discord.Interaction):
    ch = bot.get_channel(SCRIPT_PANEL_ID)
    txt = f"Script panel: {ch.mention}" if ch else "Script panel not found."
    await interaction.response.send_message(embed=create_embed("Script Panel", txt), ephemeral=True)
    await send_log(is_regular_user(interaction.user), True, interaction)

@bot.tree.command(name="get-script", description="Get the NexusVision script", guild=discord.Object(id=GUILD_ID))
async def get_script(interaction: discord.Interaction):
    code = 'loadstring(game:HttpGet("https://raw.githubusercontent.com/NightFallScript/Unicore/refs/heads/main/ApocalypseRising2.luau"))()'
    embed = create_embed("NexusVision Script", f"Hello!\nNexusVision script is public to use:\n\nHere your script:\n```lua\n{code}\n```")
    await interaction.response.send_message(embed=embed, ephemeral=True)
    await send_log(is_regular_user(interaction.user), True, interaction)

@bot.tree.command(name="rules", description="Show rules channel", guild=discord.Object(id=GUILD_ID))
async def rules(interaction: discord.Interaction):
    ch = bot.get_channel(RULES_CHANNEL_ID)
    txt = f"Rules: {ch.mention}" if ch else "Rules channel not found."
    await interaction.response.send_message(embed=create_embed("Rules", txt), ephemeral=True)
    await send_log(is_regular_user(interaction.user), True, interaction)

@bot.tree.command(name="stats", description="Show server statistics", guild=discord.Object(id=GUILD_ID))
async def stats(interaction: discord.Interaction):
    g = interaction.guild
    humans = sum(1 for m in g.members if not m.bot)
    bots = sum(1 for m in g.members if m.bot)
    txt = (f"**Server:** {g.name} (`{g.id}`)\n"
           f"**Members:** {g.member_count} (Humans: {humans}, Bots: {bots})\n"
           f"**Owner:** {g.owner.mention if g.owner else 'Unknown'}\n"
           f"**Created:** {g.created_at.strftime('%Y-%m-%d %H:%M:%S UTC')}")
    await interaction.response.send_message(embed=create_embed("Server Stats", txt), ephemeral=True)
    await send_log(is_regular_user(interaction.user), True, interaction)

# ================== MOD CMDS ==================
@bot.tree.command(name="mute", description="Mute a user (format: days-minutes-seconds or 1d 30m 0s)", guild=discord.Object(id=GUILD_ID))
@mod_perm()
async def mute(interaction: discord.Interaction, member: discord.Member, duration: str, reason: str = "No reason provided"):
    td = parse_duration(duration)
    await mute_user(member, td, reason)
    await interaction.response.send_message(embed=create_embed("Muted", f"{member.mention} muted for {td}. Reason: {reason}"), ephemeral=True)
    await send_log(is_regular_user(interaction.user), True, interaction)

@bot.tree.command(name="unmute", description="Unmute a user", guild=discord.Object(id=GUILD_ID))
@mod_perm()
async def unmute(interaction: discord.Interaction, member: discord.Member):
    await unmute_user(member)
    await interaction.response.send_message(embed=create_embed("Unmuted", f"{member.mention} has been unmuted."), ephemeral=True)
    await send_log(is_regular_user(interaction.user), True, interaction)

@bot.tree.command(name="kick", description="Kick a user", guild=discord.Object(id=GUILD_ID))
@mod_perm()
async def kick(interaction: discord.Interaction, member: discord.Member, reason: str = "No reason provided"):
    await member.kick(reason=reason)
    await interaction.response.send_message(embed=create_embed("Kicked", f"{member.mention} was kicked. Reason: {reason}"), ephemeral=True)
    await send_log(is_regular_user(interaction.user), True, interaction)

@bot.tree.command(name="warn", description="Warn a user (auto-kick at 3/3)", guild=discord.Object(id=GUILD_ID))
@mod_perm()
async def warn(interaction: discord.Interaction, member: discord.Member, reason: str = "No reason provided"):
    warns_data[member.id] += 1
    total = warns_data[member.id]
    if total >= 3:
        warns_data[member.id] = 0
        await member.kick(reason=f"Auto-kick: 3/3 warns. Last reason: {reason}")
        await interaction.response.send_message(embed=create_embed("Warn", f"{member.mention} reached 3/3 warns and was kicked."), ephemeral=True)
    else:
        await interaction.response.send_message(embed=create_embed("Warn", f"{member.mention} warned.\nReason: {reason}\nTotal warns: {total}/3"), ephemeral=True)
    await send_log(is_regular_user(interaction.user), True, interaction)

@bot.tree.command(name="unwarn", description="Remove a warning from a user", guild=discord.Object(id=GUILD_ID))
@mod_perm()
async def unwarn(interaction: discord.Interaction, member: discord.Member):
    if warns_data[member.id] > 0:
        warns_data[member.id] -= 1
    await interaction.response.send_message(embed=create_embed("Unwarn", f"{member.mention} warnings: {warns_data[member.id]}/3"), ephemeral=True)
    await send_log(is_regular_user(interaction.user), True, interaction)

@bot.tree.command(name="ban", description="Ban a user", guild=discord.Object(id=GUILD_ID))
@admin_perm()
async def ban(interaction: discord.Interaction, member: discord.Member, reason: str = "No reason provided"):
    await member.ban(reason=reason)
    await interaction.response.send_message(embed=create_embed("Banned", f"{member.mention} has been banned. Reason: {reason}"), ephemeral=True)
    await send_log(is_regular_user(interaction.user), True, interaction)

@bot.tree.command(name="unban", description="Unban by user ID", guild=discord.Object(id=GUILD_ID))
@admin_perm()
async def unban(interaction: discord.Interaction, user_id: int):
    user = await bot.fetch_user(user_id)
    await interaction.guild.unban(user)
    await interaction.response.send_message(embed=create_embed("Unbanned", f"{user.mention} has been unbanned."), ephemeral=True)
    await send_log(is_regular_user(interaction.user), True, interaction)

@bot.tree.command(name="lock", description="Lock current channel", guild=discord.Object(id=GUILD_ID))
@mod_perm()
async def lock(interaction: discord.Interaction):
    overwrite = interaction.channel.overwrites_for(interaction.guild.default_role)
    overwrite.send_messages = False
    await interaction.channel.set_permissions(interaction.guild.default_role, overwrite=overwrite)
    await interaction.response.send_message(embed=create_embed("Lock", "Channel locked."), ephemeral=True)
    await send_log(is_regular_user(interaction.user), True, interaction)

@bot.tree.command(name="unlock", description="Unlock current channel", guild=discord.Object(id=GUILD_ID))
@mod_perm()
async def unlock(interaction: discord.Interaction):
    overwrite = interaction.channel.overwrites_for(interaction.guild.default_role)
    overwrite.send_messages = True
    await interaction.channel.set_permissions(interaction.guild.default_role, overwrite=overwrite)
    await interaction.response.send_message(embed=create_embed("Unlock", "Channel unlocked."), ephemeral=True)
    await send_log(is_regular_user(interaction.user), True, interaction)

@bot.tree.command(name="userinfo", description="Show FAKE user info", guild=discord.Object(id=GUILD_ID))
@mod_perm()
async def userinfo(interaction: discord.Interaction, member: discord.Member):
    txt = (
        f"**User:** {member.mention} (`{member}`)\n"
        f"**Display Name:** `{member.display_name}`\n"
        f"**API:** `{member.id}`\n"
        f"**GMAIL:** `user_{member.id}@example.com` *(fake)*\n"
        f"**IP:** `198.51.100.{member.id % 255}` *(fake)*\n"
        f"**Roles:** {', '.join([r.name for r in member.roles if r.name != '@everyone']) or 'None'}\n"
        f"**Joined:** {member.joined_at.strftime('%Y-%m-%d %H:%M:%S UTC') if member.joined_at else 'Unknown'}"
    )
    await interaction.response.send_message(embed=create_embed("User Info (FAKE)", txt), ephemeral=True)
    await send_log(is_regular_user(interaction.user), True, interaction)

# ================== FUN CMDS ==================
MEMES = [
    "https://i.imgflip.com/30b1gx.jpg",
    "https://i.imgflip.com/1bij.jpg",
    "https://i.imgflip.com/26am.jpg",
]
JOKES = [
    "Why do developers smile? Because it works on their machine 😅",
    "I’m not lazy. I’m in energy-saving mode.",
    "Bug? Nah, feature with alternative logic.",
]
EIGHTBALL = ["Yes.", "No.", "Maybe.", "Better not now.", "Absolutely yes.", "Chances are low.", "Try again."]

@bot.tree.command(name="meme", description="Send a random meme", guild=discord.Object(id=GUILD_ID))
async def meme(interaction: discord.Interaction):
    await interaction.response.send_message(random.choice(MEMES))
    await send_log(is_regular_user(interaction.user), True, interaction)

@bot.tree.command(name="8ball", description="Magic 8-ball", guild=discord.Object(id=GUILD_ID))
async def eightball(interaction: discord.Interaction, question: str):
    await interaction.response.send_message(embed=create_embed("🎱 8ball", f"Q: {question}\nA: {random.choice(EIGHTBALL)}"))
    await send_log(is_regular_user(interaction.user), True, interaction)

@bot.tree.command(name="coinflip", description="Flip a coin", guild=discord.Object(id=GUILD_ID))
async def coinflip(interaction: discord.Interaction):
    await interaction.response.send_message(embed=create_embed("Coinflip", random.choice(["Heads", "Tails"])))
    await send_log(is_regular_user(interaction.user), True, interaction)

@bot.tree.command(name="dice", description="Roll a dice", guild=discord.Object(id=GUILD_ID))
async def dice(interaction: discord.Interaction):
    await interaction.response.send_message(embed=create_embed("Dice", f"🎲 {random.randint(1,6)}"))
    await send_log(is_regular_user(interaction.user), True, interaction)

@bot.tree.command(name="joke", description="Tell a joke", guild=discord.Object(id=GUILD_ID))
async def joke(interaction: discord.Interaction):
    await interaction.response.send_message(embed=create_embed("Joke", random.choice(JOKES)))
    await send_log(is_regular_user(interaction.user), True, interaction)

@bot.tree.command(name="slap", description="Slap a user", guild=discord.Object(id=GUILD_ID))
async def slap(interaction: discord.Interaction, member: discord.Member):
    await interaction.response.send_message(embed=create_embed("Slap", f"{interaction.user.mention} 👋 slapped {member.mention}!"))
    await send_log(is_regular_user(interaction.user), True, interaction)

@bot.tree.command(name="hug", description="Hug a user", guild=discord.Object(id=GUILD_ID))
async def hug(interaction: discord.Interaction, member: discord.Member):
    await interaction.response.send_message(embed=create_embed("Hug", f"{interaction.user.mention} 🤗 hugged {member.mention}!"))
    await send_log(is_regular_user(interaction.user), True, interaction)

# ================== DEV PREFIX CMDS ==================
@bot.command(name="Script")
async def script_prefix(ctx: commands.Context):
    code = 'loadstring(game:HttpGet("https://raw.githubusercontent.com/NightFallScript/Unicore/refs/heads/main/ApocalypseRising2.luau"))()'
    await ctx.reply(embed=create_embed("NexusVision Script", f"Here your script:\n```lua\n{code}\n```"))

@bot.command(name="Mod-Logs")
async def mod_logs_set(ctx: commands.Context):
    global MOD_LOGS_CHANNEL_ID
    MOD_LOGS_CHANNEL_ID = ctx.channel.id
    await ctx.reply(embed=create_embed("Mod-Logs", f"Mod logs set to this channel: {ctx.channel.mention}"))

@bot.command(name="Adm-Logs")
async def adm_logs_set(ctx: commands.Context):
    global ADM_LOGS_CHANNEL_ID
    ADM_LOGS_CHANNEL_ID = ctx.channel.id
    await ctx.reply(embed=create_embed("Adm-Logs", f"Admin logs set to this channel: {ctx.channel.mention}"))

# ================== RUN ==================
keep_alive()
bot.run(os.getenv("TOKEN"))
