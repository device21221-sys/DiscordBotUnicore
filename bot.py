import discord
from discord import app_commands
from discord.ext import commands
import os
from keep_alive import keep_alive  

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="?", intents=intents)

# ================== Channel IDs (replace with your real ones) ==================
RULES_CHANNEL_ID = 1351689723369754634
INFO_CHANNEL_ID = 1351690459923349634
SUPPORT_CHANNEL_ID = 1411789053921202286
EXECUTORS_CHANNEL_ID = 1404173340125429792

# ================== Events ==================
@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"✅ Bot {bot.user} is online and slash commands synced!")

@bot.event
async def on_message(message: discord.Message):
    if message.author.bot:
        return  # ігнор ботів

    content = message.content.lower()
    if any(word in content for word in ["solara", "jjsploit", "xeno", "Solara", "Xeno", "JJSploit"]):
        try:
            await message.delete()
        except discord.Forbidden:
            pass  # якщо бот не має прав на видалення

        channel = bot.get_channel(EXECUTORS_CHANNEL_ID)
        if channel:
            # Визначаємо яке саме слово і робимо embed
            if "solara" in content:
                title = "Solara is not supported!"
            elif "jjsploit" in content:
                title = "JJSploit is not supported!"
            elif "xeno" in content:
                title = "Xeno is not supported!"
            else:
                title = "That executor is not supported!"

            embed = discord.Embed(
                description=f"**{title}**\nGo to {channel.mention}!",
                color=0x2b2d31  # темно-сірий стиль, як на скріні
            )
            await message.channel.send(embed=embed, delete_after=10)
    # обов’язково, щоб працювали команди
    await bot.process_commands(message)

# ================== Slash Commands ==================
@bot.tree.command(name="get_ar2_script", description="Get the AR2 Script")
async def get_ar2_script(interaction: discord.Interaction):
    script = '```lua\nloadstring(game:HttpGet("https://raw.githubusercontent.com/UnicoreRoblox/Unicore/refs/heads/main/ApocalypseRising2.luau"))()\n```'
    await interaction.response.send_message(script, ephemeral=True)

@bot.tree.command(name="get_universal_script", description="Get the Universal Script")
async def get_universal_script(interaction: discord.Interaction):
    script = '```lua\nloadstring(game:HttpGet("https://raw.githubusercontent.com/NightFallScript/Unicore/refs/heads/main/DoorsUnicore"))()\n```'
    await interaction.response.send_message(script, ephemeral=True)

@bot.tree.command(name="rules", description="Link to rules channel")
async def rules(interaction: discord.Interaction):
    channel = bot.get_channel(RULES_CHANNEL_ID)
    if channel:
        await interaction.response.send_message(f"📜 Rules are here: {channel.mention}", ephemeral=True)
    else:
        await interaction.response.send_message("❌ Rules channel not found.", ephemeral=True)

@bot.tree.command(name="info", description="Link to info channel")
async def info(interaction: discord.Interaction):
    channel = bot.get_channel(INFO_CHANNEL_ID)
    if channel:
        await interaction.response.send_message(f"ℹ️ Info is here: {channel.mention}", ephemeral=True)
    else:
        await interaction.response.send_message("❌ Info channel not found.", ephemeral=True)

@bot.tree.command(name="help", description="List all available commands")
async def help_command(interaction: discord.Interaction):
    embed = discord.Embed(title="📖 Command List", color=0x2b2d31)
    embed.add_field(name="/get_ar2_script", value="Get AR2 Script", inline=False)
    embed.add_field(name="/get_universal_script", value="Get Universal Script", inline=False)
    embed.add_field(name="/rules", value="Show rules channel", inline=False)
    embed.add_field(name="/info", value="Show info channel", inline=False)
    embed.add_field(name="/support", value="Show support channel", inline=False)
    embed.add_field(name="/support_executors", value="Show executors channel", inline=False)
    await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.tree.command(name="support", description="Link to support channel")
async def support(interaction: discord.Interaction):
    channel = bot.get_channel(SUPPORT_CHANNEL_ID)
    if channel:
        await interaction.response.send_message(f"🛠️ Support is here: {channel.mention}", ephemeral=True)
    else:
        await interaction.response.send_message("❌ Support channel not found.", ephemeral=True)

@bot.tree.command(name="support_executors", description="Link to executors channel")
async def support_executors(interaction: discord.Interaction):
    channel = bot.get_channel(EXECUTORS_CHANNEL_ID)
    if channel:
        await interaction.response.send_message(f"⚙️ Executors are here: {channel.mention}", ephemeral=True)
    else:
        await interaction.response.send_message("❌ Executors channel not found.", ephemeral=True)

# ================== Legacy Panel (?scripts) ==================
@bot.command(name="scripts")
async def scripts(ctx):
    embed = discord.Embed(
        title="📜 Script Panel",
        description="This script panel is for the project : **Unicore**\n\n"
                    "Use the buttons below to get Universal Script or AR2 Script",
        color=0x2b2d31
    )

    view = discord.ui.View()

    # Button for Universal Script
    async def universal_callback(interaction: discord.Interaction):
        script = '```lua\nloadstring(game:HttpGet("https://raw.githubusercontent.com/NightFallScript/Unicore/refs/heads/main/DoorsUnicore"))()\n```'
        await interaction.response.send_message(script, ephemeral=True)

    universal_button = discord.ui.Button(label="📜 Get Universal Script", style=discord.ButtonStyle.secondary)
    universal_button.callback = universal_callback
    view.add_item(universal_button)

    # Button for AR2 Script
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
