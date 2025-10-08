# bot.py — повний бот з Flask API для ключів
import os
import json
import time
import random
import string
import threading

import discord
from discord import app_commands
from discord.ext import commands
from flask import Flask, request, jsonify

# ============== CONFIG ==============
GUILD_ID = 123456789012345678  # <-- Заміни на свій сервер ID (int)
# Якщо хочеш глобальні команди — видали guild=... аргументи у @bot.tree.command

TOKEN = os.getenv("TOKEN")  # бот токен у змінних середовища
ADMIN_API_KEY = os.getenv("ADMIN_API_KEY", "change_this_to_secret")  # секрет для admin API
FLASK_HOST = "0.0.0.0"
FLASK_PORT = int(os.getenv("PORT", "8080"))

# Канали
RULES_CHANNEL_ID = 1351689723369754634
INFO_CHANNEL_ID = 1351690459923349634
SUPPORT_CHANNEL_ID = 1411789053921202286
EXECUTORS_CHANNEL_ID = 1404173340125429792

# Ролі
STAFF_ROLES = ["Staff Team", "NexusVision Team"]
NEXUS_ONLY = ["NexusVision Team"]

# Файл з ключами
KEYS_FILE = "keys.json"

# ============== HELPERS ==============
def load_keys():
    try:
        with open(KEYS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def save_keys(keys):
    with open(KEYS_FILE, "w", encoding="utf-8") as f:
        json.dump(keys, f, indent=4, ensure_ascii=False)

def generate_random_key():
    return "-".join("".join(random.choices(string.ascii_uppercase + string.digits, k=4)) for _ in range(4))

def has_any_role_member(member: discord.Member, allowed_roles: list):
    return any(role.name in allowed_roles for role in member.roles)

def has_any_role_interaction(interaction: discord.Interaction, allowed_roles: list):
    return any(role.name in allowed_roles for role in interaction.user.roles)

# ============== FLASK API (keep-alive + endpoints) ==============
app = Flask("key_api")

@app.route("/")
def index():
    return "OK", 200

@app.route("/api/checkkey", methods=["GET"])
def api_checkkey():
    # public endpoint used by Lua script
    key = request.args.get("key")
    if not key:
        return jsonify({"valid": False, "error": "no key provided"}), 400

    keys = load_keys()
    entry = keys.get(key)
    if not entry:
        return jsonify({"valid": False, "error": "not found"}), 200

    if not entry.get("active", False):
        return jsonify({"valid": False, "error": "inactive"}), 200

    expires = int(entry.get("expires", 0))
    now_ts = int(time.time())
    if expires and expires < now_ts:
        return jsonify({"valid": False, "error": "expired"}), 200

    return jsonify({
        "valid": True,
        "expires": expires,
        "active": True
    }), 200

# Admin endpoints protected by ADMIN_API_KEY in header "X-API-KEY"
def _admin_check(req):
    token = req.headers.get("X-API-KEY") or req.args.get("api_key")
    return token == ADMIN_API_KEY

@app.route("/api/listkeys", methods=["GET"])
def api_listkeys():
    if not _admin_check(request):
        return jsonify({"error": "unauthorized"}), 401
    keys = load_keys()
    return jsonify(keys), 200

@app.route("/api/deletekey", methods=["POST"])
def api_deletekey():
    if not _admin_check(request):
        return jsonify({"error": "unauthorized"}), 401
    data = request.get_json(silent=True) or {}
    key = data.get("key")
    if not key:
        return jsonify({"error": "no key provided"}), 400
    keys = load_keys()
    if key in keys:
        del keys[key]
        save_keys(keys)
        return jsonify({"ok": True}), 200
    return jsonify({"error": "not found"}), 200

def run_flask():
    # запускаємо Flask в окремому потоці (Render/Replit зазвичай очікують такий сервер)
    app.run(host=FLASK_HOST, port=FLASK_PORT)

# ============== DISCORD BOT ==============
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix="?", intents=intents)

@bot.event
async def on_ready():
    guild = discord.Object(id=GUILD_ID)
    # sync commands to guild for instant availability
    await bot.tree.sync(guild=guild)
    print(f"✅ Bot {bot.user} is online and synced commands for guild {GUILD_ID}!")
    print(f"🔁 Total commands: {len(bot.tree.get_commands())}")

# ---------- /changerole ----------
@bot.tree.command(
    name="changerole",
    description="Change a user's role (Staff/NexusVision only)",
    guild=discord.Object(id=GUILD_ID)
)
@app_commands.describe(user="Select a user", role="Select a role to assign")
async def changerole(interaction: discord.Interaction, user: discord.Member, role: discord.Role):
    await interaction.response.defer(ephemeral=True)
    if not has_any_role_interaction(interaction, STAFF_ROLES):
        await interaction.followup.send("🚫 You don't have permission to use this command.", ephemeral=True)
        return

    try:
        await user.add_roles(role)
        await interaction.followup.send(f"✅ {user.mention} has been given the role {role.mention}", ephemeral=True)
    except Exception as e:
        await interaction.followup.send(f"❌ Failed to change role: {e}", ephemeral=True)

# ---------- /generatekey ----------
@bot.tree.command(
    name="generatekey",
    description="Generate a premium key (NexusVision only)",
    guild=discord.Object(id=GUILD_ID)
)
@app_commands.describe(
    active="Is the key active (True/False)?",
    days="Duration in days (7, 30, 90, 100000)"
)
async def generatekey(interaction: discord.Interaction, active: bool, days: int):
    await interaction.response.defer(ephemeral=True)
    if not has_any_role_interaction(interaction, NEXUS_ONLY):
        await interaction.followup.send("🚫 You don't have permission to generate keys.", ephemeral=True)
        return

    if days not in [7, 30, 90, 100000]:
        await interaction.followup.send("❌ Invalid duration. Choose 7, 30, 90, or 100000 days.", ephemeral=True)
        return

    key = generate_random_key()
    keys = load_keys()
    expires_ts = int(time.time()) + days * 24 * 60 * 60 if days != 100000 else int(time.time()) + (100000 * 24 * 60 * 60)
    keys[key] = {
        "active": bool(active),
        "expires": expires_ts,
        "generated_by": interaction.user.id,
        "days": days
    }
    save_keys(keys)

    embed = discord.Embed(title="🔑 Key Generated", color=0x00ff88)
    embed.add_field(name="Key", value=f"`{key}`", inline=False)
    embed.add_field(name="Active", value=str(active), inline=True)
    embed.add_field(name="Days", value=str(days), inline=True)
    embed.set_footer(text=f"Generated by {interaction.user.display_name}")
    await interaction.followup.send(embed=embed, ephemeral=True)

# ---------- /listkeys (guild command for Staff) ----------
@bot.tree.command(
    name="listkeys",
    description="List stored keys (Staff/NexusVision only)",
    guild=discord.Object(id=GUILD_ID)
)
async def listkeys(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    if not has_any_role_interaction(interaction, STAFF_ROLES):
        await interaction.followup.send("🚫 You don't have permission to list keys.", ephemeral=True)
        return
    keys = load_keys()
    if not keys:
        await interaction.followup.send("There are no keys stored.", ephemeral=True)
        return

    # build short message (avoid huge messages)
    lines = []
    for k, v in keys.items():
        expires = v.get("expires", 0)
        expires_str = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime(expires)) if expires else "never"
        lines.append(f"{k} — active={v.get('active')} days={v.get('days')} expires={expires_str}")

    # send in chunks if too long
    msg = "\n".join(lines)
    if len(msg) < 1900:
        await interaction.followup.send(f"```\n{msg}\n```", ephemeral=True)
    else:
        # if too long, send as file
        filename = "keys_list.txt"
        with open(filename, "w", encoding="utf-8") as f:
            f.write(msg)
        await interaction.followup.send("Keys list is large, sending file...", ephemeral=True)
        await interaction.followup.send(file=discord.File(filename), ephemeral=True)
        os.remove(filename)

# ---------- other informative commands (deferred) ----------
@bot.tree.command(name="get_ar2_script", description="Get the AR2 Script", guild=discord.Object(id=GUILD_ID))
async def get_ar2_script(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    script = '```lua\nloadstring(game:HttpGet("https://raw.githubusercontent.com/UnicoreRoblox/Unicore/refs/heads/main/ApocalypseRising2.luau"))()\n```'
    await interaction.followup.send(script, ephemeral=True)

@bot.tree.command(name="get_universal_script", description="Get the Universal Script", guild=discord.Object(id=GUILD_ID))
async def get_universal_script(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    script = '```lua\nloadstring(game:HttpGet("https://raw.githubusercontent.com/NightFallScript/Unicore/refs/heads/main/DoorsUnicore"))()\n```'
    await interaction.followup.send(script, ephemeral=True)

@bot.tree.command(name="rules", description="Link to rules channel", guild=discord.Object(id=GUILD_ID))
async def rules(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    channel = bot.get_channel(RULES_CHANNEL_ID)
    if channel:
        await interaction.followup.send(f"📜 Rules are here: {channel.mention}", ephemeral=True)
    else:
        await interaction.followup.send("❌ Rules channel not found.", ephemeral=True)

@bot.tree.command(name="info", description="Link to info channel", guild=discord.Object(id=GUILD_ID))
async def info(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    channel = bot.get_channel(INFO_CHANNEL_ID)
    if channel:
        await interaction.followup.send(f"ℹ️ Info is here: {channel.mention}", ephemeral=True)
    else:
        await interaction.followup.send("❌ Info channel not found.", ephemeral=True)

@bot.tree.command(name="support", description="Link to support channel", guild=discord.Object(id=GUILD_ID))
async def support(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    channel = bot.get_channel(SUPPORT_CHANNEL_ID)
    if channel:
        await interaction.followup.send(f"🛠️ Support is here: {channel.mention}", ephemeral=True)
    else:
        await interaction.followup.send("❌ Support channel not found.", ephemeral=True)

@bot.tree.command(name="support_executors", description="Link to executors channel", guild=discord.Object(id=GUILD_ID))
async def support_executors(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    channel = bot.get_channel(EXECUTORS_CHANNEL_ID)
    if channel:
        await interaction.followup.send(f"⚙️ Executors are here: {channel.mention}", ephemeral=True)
    else:
        await interaction.followup.send("❌ Executors channel not found.", ephemeral=True)

@bot.tree.command(name="help", description="List all available commands", guild=discord.Object(id=GUILD_ID))
async def help_command(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    embed = discord.Embed(title="📖 Command List", color=0x2b2d31)
    embed.add_field(name="/get_ar2_script", value="Get AR2 Script", inline=False)
    embed.add_field(name="/get_universal_script", value="Get Universal Script", inline=False)
    embed.add_field(name="/rules", value="Show rules channel", inline=False)
    embed.add_field(name="/info", value="Show info channel", inline=False)
    embed.add_field(name="/support", value="Show support channel", inline=False)
    embed.add_field(name="/support_executors", value="Show executors channel", inline=False)
    embed.add_field(name="/changerole", value="Change user role (Staff/NexusVision only)", inline=False)
    embed.add_field(name="/generatekey", value="Generate a key (NexusVision only)", inline=False)
    embed.add_field(name="/listkeys", value="List keys (Staff/NexusVision only)", inline=False)
    await interaction.followup.send(embed=embed, ephemeral=True)

# ============== RUN ==============
if __name__ == "__main__":
    # start flask
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()
    print(f"Flask started on {FLASK_HOST}:{FLASK_PORT}")

    # run discord bot
    if not TOKEN:
        print("ERROR: TOKEN environment variable is not set.")
    else:
        bot.run(TOKEN)
