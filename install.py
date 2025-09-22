#!/usr/bin/env python3
"""
AsterBot Automatic Installer
This script checks and installs all necessary dependencies
"""

import sys
import subprocess
import os
import platform
from pathlib import Path

def print_step(step, description):
    """Print installation step"""
    print(f"\n[STEP {step}] {description}")
    print("=" * 50)

def check_python_version():
    """Check Python version"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("ERROR: Python 3.8 or higher is required!")
        print(f"Current version: {version.major}.{version.minor}.{version.micro}")
        print("Please install a newer version of Python.")
        return False

    print(f"✓ Python {version.major}.{version.minor}.{version.micro} detected")
    return True

def install_package(package):
    """Install Python package"""
    try:
        print(f"  Installing {package}...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", package],
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print(f"  ✓ {package} installed successfully")
        return True
    except subprocess.CalledProcessError:
        print(f"  ✗ Failed to install {package}")
        return False

def install_dependencies():
    """Install all dependencies"""
    print("Installing AsterBot dependencies...")

    # Main dependencies
    main_packages = [
        "requests>=2.31.0",
        "websocket-client>=1.6.0",
        "pandas>=2.0.0",
        "numpy>=1.24.0",
        "ta>=0.10.2",
        "python-dotenv>=1.0.0",
        "aiohttp>=3.8.0",
        "asyncio-throttle>=1.0.2",
    ]

    # Web interface dependencies
    web_packages = [
        "Flask==2.3.2",
        "Flask-SocketIO==5.3.4",
        "python-socketio==5.8.0",
        "python-engineio==4.6.1"
    ]

    all_packages = main_packages + web_packages

    failed_packages = []

    for package in all_packages:
        if not install_package(package):
            failed_packages.append(package)

    if failed_packages:
        print(f"\n⚠️  Failed to install: {', '.join(failed_packages)}")
        return False

    print("\n✓ All dependencies installed successfully!")
    return True

def create_startup_script():
    """Create simple startup script"""
    script_content = '''@echo off
title AsterBot - Interface Web
echo.
echo ==========================================
echo          ASTERBOT - INTERFACE WEB
echo ==========================================
echo.
echo Starting web interface...
echo Access: http://localhost:5000
echo.
echo To stop, close this window or press Ctrl+C
echo.

cd /d "%~dp0"
python run_web.py

echo.
echo Interface closed. Press any key to exit.
pause > nul
'''

    with open('START_ASTERBOT.bat', 'w', encoding='utf-8') as f:
        f.write(script_content)

    print("✓ Startup script created: START_ASTERBOT.bat")

def create_readme():
    """Create simplified README for end users"""
    readme_content = """# 🤖 AsterBot - Automatic Trading Bot

## 🚀 How to Use (Super Simple!)

### 1️⃣ First Time (Installation)
1. **Double click on `install.py`** - Installs everything automatically
2. **Wait** until you see "Installation completed!"

### 2️⃣ Using the Bot
1. **Double click on `START_ASTERBOT.bat`**
2. **Open your browser** and go to: `http://localhost:5000`
3. **Configure your keys** from Aster Dex in the interface
4. **Click "Start Bot"**

## ⚙️ Available Settings

### 🔑 API Keys
- **API Key**: Your Aster Dex public key
- **Secret Key**: Your Aster Dex secret key

### 💰 Risk Control
- **Margin per Trade**: 10%, 20%, 30%, 40% or 50%
- **Take Profit**: Minimum profit to close (default: 0.8%)
- **Stop Loss**: Maximum loss (default: 2.0%)

### 📊 Dashboard
- **Active Positions**: How many open positions
- **Margin Used**: % of total margin in use
- **Total P&L**: Accumulated profit/loss
- **Logs**: Follow actions in real time

## 🎯 Trading Pairs

The bot automatically operates on the main pairs:
- BTC/USDT
- ETH/USDT
- SOL/USDT
- BNB/USDT
- XRP/USDT
- DOGE/USDT

## ⚡ Features

- ✅ **10x Leverage** on all trades
- ✅ **Automated scalping** for high frequency
- ✅ **Intelligent risk management**
- ✅ **Synchronization** with real exchange positions
- ✅ **Easy-to-use web interface**
- ✅ **Real-time data**

## ⚠️ Importante

⚠️ **TRADING INVOLVES RISKS** ⚠️

- Only use capital you can afford to lose
- Always test with small amounts first
- Monitor the bot regularly
- Keep your API keys secure

## 🆘 Problems?

1. **Installation error**: Run as administrator
2. **Bot doesn't start**: Check your API keys
3. **Connection error**: Check your internet
4. **Interface doesn't load**: Close and reopen

## 📁 Important Files

- `START_ASTERBOT.bat` - Click to start
- `install.py` - Automatic installer
- `config/` - Saved configurations
- `logs/` - System logs

---

🤖 **AsterBot** - Simplified automated trading!
"""

    with open('USER_README.md', 'w', encoding='utf-8') as f:
        f.write(readme_content)

    print("✓ Documentation created: USER_README.md")

def main():
    """Main installer function"""
    os.system('cls' if platform.system() == 'Windows' else 'clear')

    print("ASTERBOT - AUTOMATIC INSTALLER")
    print("=" * 50)
    print("This installer will:")
    print("• Check system requirements")
    print("• Install necessary dependencies")
    print("• Create startup scripts")
    print("• Prepare documentation")
    print()

    input("Press ENTER to continue...")

    # Step 1: Check Python
    print_step(1, "Checking Python")
    if not check_python_version():
        input("\nPress ENTER to exit...")
        return

    # Step 2: Install dependencies
    print_step(2, "Installing Dependencies")
    if not install_dependencies():
        print("\n❌ Installation failed!")
        input("Press ENTER to exit...")
        return

    # Step 3: Create startup script
    print_step(3, "Creating Startup Scripts")
    create_startup_script()

    # Step 4: Create documentation
    print_step(4, "Preparing Documentation")
    create_readme()

    # Success!
    print("\n" + "=" * 50)
    print("INSTALLATION COMPLETED SUCCESSFULLY!")
    print("=" * 50)
    print()
    print("NEXT STEPS:")
    print("1. Double click on 'START_ASTERBOT.bat'")
    print("2. Open your browser at: http://localhost:5000")
    print("3. Configure your Aster Dex keys")
    print("4. Click 'Start Bot'")
    print()
    print("Read 'USER_README.md' for more details")
    print()

    input("Press ENTER to finish...")

if __name__ == "__main__":
    main()