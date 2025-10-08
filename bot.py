# bot.py — Full Discord bot + Flask key API (Render-ready)
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

# ================= CONFIG =================
GUILD_ID = 123456789012345678  # <-- Replace with your actual Discord server ID

TOKEN = os.getenv("TOKEN")  # Bot token from Render environment
ADMIN_API_KEY = os.getenv("ADMIN_API_KEY", "change_this_secret")
FLASK_HOST = "0.0.0.0"
FLASK_PORT = int(os.getenv("PORT", "8080"))

# Channels (replace with yours)
RULES_CHANNEL_ID = 1351689723369754634
INFO_CHANNEL_ID = 1351690459923349634
SUPPORT_CHANNEL_ID = 1411789053921202286
EXECUTORS_CHANNEL_ID = 1404173340125429792

# Roles
STAFF_ROLES = ["Staff Team", "NexusVision Team"]
NEXUS_ONLY = ["NexusVision Team"]

# Keys file
KEYS_FILE = "keys.json"

# ================= HELPERS =================
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

def has_any_role(member: discord.Member, roles: list):
    return any(r.name in roles for r in member.roles)

# ================= FLASK API =================
app = Flask("key_api")

@app.route("/")
def index():
    return "OK", 200

@app.route("/api/checkkey", methods=["GET"])
def api_checkkey():
    key = request.args.get("key")
    if not key:
        return jsonify({"valid": False, "error": "no key provided"}), 400

    keys = load_keys()
    data = keys.get(key)
    if not data:
        return jsonify({"valid": False, "error": "not found"}), 200

    if not data.get("active", False):
        return jsonify({"valid": False, "error": "inactive"}), 200

    if int(data["expires"]) < int(time.time()):
        return jsonify({"valid": False, "error": "expired"}), 200

    return jsonify({"valid": True, "expires": data["expires"], "active": True}), 200

def _admin_check(req):
    token = req.headers.get("X-API-KEY") or req.args.get("api_key")
    return token == ADMIN_API_KEY

@app.route("/api/listkeys", methods=["GET"])
def api_listkeys():
    if not _admin_check(request):
        return jsonify({"error": "unauthorized"}), 401
    return jsonify(load_keys()), 200

@app.route("/api/deletekey", methods=["POST"])
def api_deletekey():
    if not _admin_check(request):
        return jsonify({"error": "unauthorized"}), 401
    data = request.get_json() or {}
    key = data.get("key")
    if not key:
        return jsonify({"error": "no key"}), 400
    keys = load_keys()
    if key not in keys:
        return jsonify({"error": "not found"}), 200
    del keys[key]
    save_keys(keys)
    return jsonify({"ok": True}), 200

def run_flask():
    app.run(host=FLASK_HOST, port=FLASK_PORT)

# ================= DISCORD BOT =================
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    guild = discord.Object(id=GUILD_ID)
    await bot.tree.sync(guild=guild)
    print(f"✅ Logged in as {bot.user} — Commands synced to {GUILD_ID}")

# ---------- /generatekey ----------
@bot.tree.command(name="generatekey", description="Generate a new premium key", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(active="Should the key be active?", days="Duration in days (7/30/90/100000)")
async def generatekey(interaction: discord.Interaction, active: bool, days: int):
    if not has_any_role(interaction.user, NEXUS_ONLY):
        await interaction.response.send_message("🚫 You don't have permission to use this command.", ephemeral=True)
        return

    if days not in [7, 30, 90, 100000]:
        await interaction.response.send_message("❌ Invalid duration. Choose 7, 30, 90 or 100000 days.", ephemeral=True)
        return

    key = generate_random_key()
    keys = load_keys()
    keys[key] = {
        "active": active,
        "expires": int(time.time()) + days * 86400,
        "days": days,
        "generated_by": interaction.user.id,
    }
    save_keys(keys)

    embed = discord.Embed(title="🔑 New Key Generated", color=0x00ff88)
    embed.add_field(name="Key", value=f"`{key}`", inline=False)
    embed.add_field(name="Active", value=str(active))
    embed.add_field(name="Days", value=str(days))
    await interaction.response.send_message(embed=embed, ephemeral=True)

# ---------- /listkeys ----------
@bot.tree.command(name="listkeys", description="List all stored keys", guild=discord.Object(id=GUILD_ID))
async def listkeys(interaction: discord.Interaction):
    if not has_any_role(interaction.user, STAFF_ROLES):
        await interaction.response.send_message("🚫 You don't have permission to view keys.", ephemeral=True)
        return

    keys = load_keys()
    if not keys:
        await interaction.response.send_message("🔑 No keys stored.", ephemeral=True)
        return

    lines = []
    for k, v in keys.items():
        exp = time.strftime("%Y-%m-%d", time.gmtime(v["expires"]))
        lines.append(f"{k} — active={v['active']} — days={v['days']} — exp={exp}")
    msg = "\n".join(lines)
    if len(msg) > 1900:
        open("keys.txt", "w").write(msg)
        await interaction.response.send_message(file=discord.File("keys.txt"), ephemeral=True)
        os.remove("keys.txt")
    else:
        await interaction.response.send_message(f"```\n{msg}\n```", ephemeral=True)

# ---------- /activatekey ----------
@bot.tree.command(name="activatekey", description="Activate a key", guild=discord.Object(id=GUILD_ID))
async def activatekey(interaction: discord.Interaction, key: str):
    if not has_any_role(interaction.user, STAFF_ROLES):
        await interaction.response.send_message("🚫 You don't have permission to do that.", ephemeral=True)
        return

    keys = load_keys()
    if key not in keys:
        await interaction.response.send_message("❌ Key not found.", ephemeral=True)
        return

    keys[key]["active"] = True
    save_keys(keys)
    await interaction.response.send_message(f"✅ Key `{key}` has been activated.", ephemeral=True)

# ---------- /deactivatekey ----------
@bot.tree.command(name="deactivatekey", description="Deactivate a key", guild=discord.Object(id=GUILD_ID))
async def deactivatekey(interaction: discord.Interaction, key: str):
    if not has_any_role(interaction.user, STAFF_ROLES):
        await interaction.response.send_message("🚫 You don't have permission to do that.", ephemeral=True)
        return

    keys = load_keys()
    if key not in keys:
        await interaction.response.send_message("❌ Key not found.", ephemeral=True)
        return

    keys[key]["active"] = False
    save_keys(keys)
    await interaction.response.send_message(f"🔒 Key `{key}` has been deactivated.", ephemeral=True)

# ---------- /deletekey ----------
@bot.tree.command(name="deletekey", description="Delete a key", guild=discord.Object(id=GUILD_ID))
async def deletekey(interaction: discord.Interaction, key: str):
    if not has_any_role(interaction.user, STAFF_ROLES):
        await interaction.response.send_message("🚫 You don't have permission to do that.", ephemeral=True)
        return

    keys = load_keys()
    if key not in keys:
        await interaction.response.send_message("❌ Key not found.", ephemeral=True)
        return

    del keys[key]
    save_keys(keys)
    await interaction.response.send_message(f"🗑️ Key `{key}` has been deleted.", ephemeral=True)

# ---------- Informational Commands ----------
@bot.tree.command(name="rules", description="Show the rules channel", guild=discord.Object(id=GUILD_ID))
async def rules(interaction: discord.Interaction):
    ch = bot.get_channel(RULES_CHANNEL_ID)
    await interaction.response.send_message(f"📜 Rules: {ch.mention}" if ch else "❌ Channel not found.", ephemeral=True)

@bot.tree.command(name="info", description="Show the info channel", guild=discord.Object(id=GUILD_ID))
async def info(interaction: discord.Interaction):
    ch = bot.get_channel(INFO_CHANNEL_ID)
    await interaction.response.send_message(f"ℹ️ Info: {ch.mention}" if ch else "❌ Channel not found.", ephemeral=True)

@bot.tree.command(name="support", description="Show the support channel", guild=discord.Object(id=GUILD_ID))
async def support(interaction: discord.Interaction):
    ch = bot.get_channel(SUPPORT_CHANNEL_ID)
    await interaction.response.send_message(f"🛠️ Support: {ch.mention}" if ch else "❌ Channel not found.", ephemeral=True)

@bot.tree.command(name="executors", description="Show the executors channel", guild=discord.Object(id=GUILD_ID))
async def executors(interaction: discord.Interaction):
    ch = bot.get_channel(EXECUTORS_CHANNEL_ID)
    await interaction.response.send_message(f"⚙️ Executors: {ch.mention}" if ch else "❌ Channel not found.", ephemeral=True)

# ---------- /help ----------
@bot.tree.command(name="help", description="Show all available commands", guild=discord.Object(id=GUILD_ID))
async def help_cmd(interaction: discord.Interaction):
    embed = discord.Embed(title="📖 Command List", color=0x5865F2)
    embed.add_field(name="/rules", value="Show rules channel", inline=False)
    embed.add_field(name="/info", value="Show info channel", inline=False)
    embed.add_field(name="/support", value="Show support channel", inline=False)
    embed.add_field(name="/executors", value="Show executors channel", inline=False)
    embed.add_field(name="/generatekey", value="Generate a new key", inline=False)
    embed.add_field(name="/listkeys", value="List all keys", inline=False)
    embed.add_field(name="/activatekey", value="Activate a key", inline=False)
    embed.add_field(name="/deactivatekey", value="Deactivate a key", inline=False)
    embed.add_field(name="/deletekey", value="Delete a key", inline=False)
    await interaction.response.send_message(embed=embed, ephemeral=True)

# ================= RUN =================
if __name__ == "__main__":
    threading.Thread(target=run_flask, daemon=True).start()
    print(f"🌐 Flask API started on port {FLASK_PORT}")
    if not TOKEN:
        print("❌ TOKEN not found in environment!")
    else:
        bot.run(TOKEN)
