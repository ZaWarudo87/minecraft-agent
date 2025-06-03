@echo off
setlocal enabledelayedexpansion

echo This is environment setup. :D

REM This is Python checker
where python >nul 2>nul
if errorlevel 1 (
    echo Please install [Python] first.
    pause
    exit /b
) else (
    echo You have Python. Good.
)

REM This is Java checker
java -version >nul 2>nul
if errorlevel 1 (
    echo Please install [OpenJDK] first.
    pause
    exit /b
) else (
    echo You have Java. Good.
)

REM pip modules
python -m pip install --upgrade pip
pip install requests colorama pyNBT cryptography mcstatus msal sortedcontainers pynput pygetwindow mcrcon rich nbtlib anvil-new watchdog
pip install git+https://github.com/ammaraskar/pyCraft.git

echo Setup finished. :D
pause