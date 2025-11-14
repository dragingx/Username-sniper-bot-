import discord
from discord.ext import commands, tasks
from discord import app_commands
import requests
import random
import string
import asyncio

# Constants
TOKEN = 'your_discord_bot_token'  # Replace with your bot's token
CHANNEL_ID = 123456789012345678  # Replace with your channel ID
UPDATE_INTERVAL = 60  # Time interval in seconds to update the embed
MESSAGE_ID = None  # This will be set after the initial message is sent

# Initialize the bot
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='/', intents=intents)

def make_username(length, letter):
    letters = string.ascii_lowercase + string.digits
    if letter:
        letters = letter + string.ascii_lowercase + string.digits
    return ''.join(random.choice(letters) for _ in range(length))

def check_username(username):
    url = f'https://auth.roblox.com/v1/usernames/validate?request.username={username}'
    response = requests.get(url, timeout=5)  # Set a timeout of 5 seconds
    response.raise_for_status()  # Raise an error for bad responses
    return response.json().get('code')

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name}')
    try:
        synced = await bot.tree.sync()
        print(f'Synced {len(synced)} command(s)')
    except Exception as e:
        print(e)
    update_available_usernames.start()  # Start the background task to update the embed

class GenerateModal(discord.ui.Modal):
    def __init__(self):
        super().__init__(title="Generate Usernames")
        self.letter_input = discord.ui.InputText(label="Letter to include", placeholder="Enter a letter")
        self.count_input = discord.ui.InputText(label="Number of usernames to generate", placeholder="Enter a number")
        self.length_input = discord.ui.InputText(label="Length of usernames", placeholder="Enter a number (3, 4, or 5)")

        self.add_item(self.letter_input)
        self.add_item(self.count_input)
        self.add_item(self.length_input)

    async def on_submit(self, interaction: discord.Interaction):
        letter = self.letter_input.value if self.letter_input.value else None
        count = int(self.count_input.value) if self.count_input.value.isdigit() else 10
        length = int(self.length_input.value) if self.length_input.value.isdigit() and self.length_input.value in ['3', '4', '5'] else 3

        await interaction.response.send_message(f"Generating {count} usernames with length {length} and letter {letter if letter else 'none'}...", ephemeral=True)

        available_usernames = []
        for _ in range(count):
            try:
                username = make_username(length, letter)
                code = check_username(username)

                if code == 0:
                    available_usernames.append(username)
                    await interaction.followup.send(f'@here A new username is available: {username}')
                    with open('available_usernames.txt', 'a+') as f:
                        f.write(f"{username}\n")

            except requests.exceptions.RequestException as e:
                print('Network error:', e)
            except Exception as e:
                print('Error:', e)

            await asyncio.sleep(0.1)  # Increased sleep time to avoid overwhelming the API

        if available_usernames:
            available_list = "\n".join(available_usernames)
            await interaction.followup.send(f'List of available usernames:\n{available_list}')

@bot.tree.command(name='generate')
async def generate(interaction: discord.Interaction):
    modal = GenerateModal()
    await interaction.response.send_modal(modal)

@bot.tree.command(name='test')
async def test(interaction: discord.Interaction):
    await interaction.response.send_message('This is a test message from the bot.')

@tasks.loop(seconds=UPDATE_INTERVAL)
async def update_available_usernames():
    global MESSAGE_ID
    channel = bot.get_channel(CHANNEL_ID)
    if channel:
        available_usernames = []
        try:
            with open('available_usernames.txt', 'r') as f:
                available_usernames = f.read().splitlines()
        except FileNotFoundError:
            pass  # File does not exist yet, no available usernames to display

        available_list = "\n".join(available_usernames)
        embed = discord.Embed(title="Available Usernames", description=f"List of available usernames:\n{available_list}", color=discord.Color.green())
        embed.set_footer(text="Username Finder")

        if MESSAGE_ID:
            try:
                message = await channel.fetch_message(MESSAGE_ID)
                await message.edit(embed=embed)
            except discord.errors.NotFound:
                message = await channel.send(embed=embed)
                MESSAGE_ID = message.id
        else:
            message = await channel.send(embed=embed)
            MESSAGE_ID = message.id

# Run the bot
bot.run(TOKEN)
