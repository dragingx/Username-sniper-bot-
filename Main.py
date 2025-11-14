import discord
from discord.ext import commands, tasks
import requests
import random
import string
import asyncio

# Constants
BIRTHDAY = '1999-04-20'  # User's birthday for validation
TOKEN = 'your_discord_bot_token'  # Replace with your bot's token
NAMES = 10  # Amount of usernames to save
FILE = 'valid.txt'  # Automatically creates file
CHANNEL_ID = 123456789012345678  # Replace with your channel ID
UPDATE_INTERVAL = 60  # Time interval in seconds to update the webhook embed

# Color formatting for terminal output
class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    GRAY = '\033[90m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

# Initialize the bot
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='/', intents=intents)

def make_username(length):
    letters = string.ascii_lowercase + string.digits
    return ''.join(random.choice(letters) for _ in range(length))

def check_username(username):
    url = f'https://auth.roblox.com/v1/usernames/validate?request.username={username}&request.birthday={BIRTHDAY}'
    response = requests.get(url, timeout=5)  # Set a timeout of 5 seconds
    response.raise_for_status()  # Raise an error for bad responses
    return response.json().get('code')

@bot.event
async def on_ready():
    print(f'{bcolors.OKBLUE}[+] Logged in as {bot.user.name} {bcolors.ENDC}')
    try:
        synced = await bot.tree.sync()
        print(f'Synced {len(synced)} command(s)')
    except Exception as e:
        print(e)
    update_taken_usernames.start()  # Start the background task to update the embed

@bot.tree.command(name='generate')
async def generate(interaction: discord.Interaction):
    await interaction.response.defer()  # Acknowledge the interaction immediately
    found = 0
    taken_usernames = []
    while found < NAMES:
        try:
            username = make_username(random.choice([3, 4, 5]))
            code = check_username(username)

            if code == 0:
                found += 1
                await interaction.followup.send(f'@here A new username is available: {username}')
                with open(FILE, 'a+') as f:
                    f.write(f"{username}\n")
            else:
                taken_usernames.append(username)

        except requests.exceptions.RequestException as e:
            print('Network error:', e)
        except Exception as e:
            print('Error:', e)

        await asyncio.sleep(0.1)  # Increased sleep time to avoid overwhelming the API

    if taken_usernames:
        taken_list = "\n".join(taken_usernames)
        await interaction.followup.send(f'List of taken usernames:\n{taken_list}')

@bot.tree.command(name='test')
async def test(interaction: discord.Interaction):
    await interaction.response.send_message('This is a test message from the bot.')

@tasks.loop(seconds=UPDATE_INTERVAL)
async def update_taken_usernames():
    channel = bot.get_channel(CHANNEL_ID)
    if channel:
        taken_usernames = []
        with open(FILE, 'r') as f:
            taken_usernames = f.read().splitlines()

        taken_list = "\n".join(taken_usernames)
        embed = discord.Embed(title="Taken Usernames", description=f"List of taken usernames:\n{taken_list}", color=discord.Color.red())
        embed.set_footer(text="Username Finder")

        try:
            message = await channel.fetch_message(MESSAGE_ID)  # Replace MESSAGE_ID with the actual message ID
            await message.edit(embed=embed)
        except discord.errors.NotFound:
            message = await channel.send(embed=embed)
            global MESSAGE_ID
            MESSAGE_ID = message.id

# Run the bot
bot.run(TOKEN)
