import discord
from discord.ext import commands, tasks
import random
import importlib
import json
import dotenv
import time
import os

# ----------------------------
# Initialize dotenv
# ----------------------------
dotenv.load_dotenv()
TOKEN = os.getenv('BOT_TOKEN')
print(f"Running bot with token {TOKEN}")

# ----------------------------
# Intents
# ----------------------------
intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)

# ----------------------------
# Global state
# ----------------------------
penguins = []
current_penguin = None
spawn_channel_id = None
userdata_file = "userdata.json"
spawn_time = None  # record spawn time

# ----------------------------
# Load user data
# ----------------------------
def load_userdata():
    if not os.path.exists(userdata_file):
        return {}
    with open(userdata_file, "r") as f:
        return json.load(f)

def save_userdata(data):
    with open(userdata_file, "w") as f:
        json.dump(data, f, indent=4)

userdata = load_userdata()

# ----------------------------
# Load penguins dynamically
# ----------------------------
def load_penguins():
    penguin_list = []
    for file in os.listdir("penguins"):
        if file.endswith(".py") and file != "__init__.py":
            module_name = file[:-3]
            module = importlib.import_module(f"penguins.{module_name}")
            if hasattr(module, "penguin"):
                penguin_list.append(module.penguin)
    return penguin_list

penguins = load_penguins()

# ----------------------------
# Commands
# ----------------------------
@bot.command()
async def help(ctx):
    embed = discord.Embed(title="🐧 Penguin Bot Help", color=0x00ffcc)
    embed.add_field(name="!setupchannel", value="Sets the current channel for penguin spawns.", inline=False)
    embed.add_field(name="!forcespawn", value="Forcefully spawns a penguin in the channel (debug).", inline=False)
    embed.add_field(name="!help", value="Shows this help message.", inline=False)
    embed.set_footer(text="Catch penguins by typing 'pen' when they appear!")
    await ctx.send(embed=embed)

@bot.command()
async def setupchannel(ctx):
    global spawn_channel_id
    spawn_channel_id = ctx.channel.id
    await ctx.send("✅ This channel has been set for penguin spawns!")
    spawn_penguin.start()

@bot.command()
async def forcespawn(ctx):
    """Forcefully spawns a penguin for debugging."""
    global current_penguin, spawn_time

    if spawn_channel_id is None:
        await ctx.send("⚠️ You need to run `!setupchannel` first.")
        return

    if current_penguin:
        await ctx.send(f"⚠️ A {current_penguin.name} penguin is already out! Catch it first.")
        return

    penguin = random.choice(penguins)
    current_penguin = penguin
    spawn_time = time.time()

    await ctx.send("🐧 (Forced Spawn)")
    await ctx.send(penguin.spawn_message())
    await ctx.send(penguin.image_url)

# ----------------------------
# Penguin Spawning (auto)
# ----------------------------
@tasks.loop(seconds=random.randint(30, 90))
async def spawn_penguin():
    global current_penguin, spawn_time
    if spawn_channel_id is None:
        return

    channel = bot.get_channel(spawn_channel_id)
    if current_penguin is None and channel is not None:
        penguin = random.choice(penguins)
        current_penguin = penguin
        spawn_time = time.time()
        await channel.send(penguin.spawn_message())
        await channel.send(penguin.image_url)

# ----------------------------
# Catching Penguins
# ----------------------------
@bot.event
async def on_message(message):
    global current_penguin, spawn_time
    if message.author == bot.user:
        return

    if current_penguin and message.content.lower() == "pen":
        user_id = str(message.author.id)

        # how long it took
        elapsed = round(time.time() - spawn_time, 2)

        if user_id not in userdata:
            userdata[user_id] = {}

        userdata[user_id][current_penguin.name] = userdata[user_id].get(current_penguin.name, 0) + 1
        save_userdata(userdata)

        await message.channel.send(
            f" {message.author.mention} caught a {current_penguin.name} penguin in **{elapsed} seconds**!"
        )

        # reset
        current_penguin = None
        spawn_time = None

    await bot.process_commands(message)

# ----------------------------
# Run bot
# ----------------------------
bot.run(TOKEN)
