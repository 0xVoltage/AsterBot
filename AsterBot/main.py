#!/usr/bin/env python3
"""
AsterBot - Trading Bot for Aster Dex Perpetuals

Automated trading bot that operates perpetual contracts on Aster Dex
focused on generating trading volume with minimum profit to cover fees.

Usage:
    python main.py config/config.json

Features:
- Automated trading with RSI and moving averages
- Scalping strategy for high volume
- Integrated risk management
- Detailed monitoring and logs
- Automatic stop in case of excessive losses
"""

import asyncio
import sys
import os
import signal
from pathlib import Path

# Add src directory to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from asterbot.bot import AsterBot


def signal_handler(signum, frame):
    print("\nInterruption signal received. Shutting down bot...")
    sys.exit(0)


async def main():
    # Configure handlers for interruption signals
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    print("AsterBot - Trading Bot for Aster Dex")
    print("=" * 50)

    if len(sys.argv) < 2:
        print("ERROR: Configuration file not specified")
        print("\nUsage:")
        print("   python main.py config/config.json")
        print("\nTip: Copy config.example.json to config.json and configure your credentials")
        return

    config_path = sys.argv[1]

    if not os.path.exists(config_path):
        print(f"ERROR: Configuration file not found: {config_path}")
        print("\nCheck if the path is correct or create the configuration file")
        return

    print(f"Loading configuration from: {config_path}")

    try:
        bot = AsterBot(config_path)
        print("Starting AsterBot...")
        await bot.run()
    except KeyboardInterrupt:
        print("\nBot interrupted by user")
    except Exception as e:
        print(f"Unexpected ERROR: {e}")
        sys.exit(1)


if __name__ == "__main__":
    # Check Python version
    if sys.version_info < (3, 7):
        print("ERROR: Python 3.7 or higher is required")
        sys.exit(1)

    # Run bot
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nAsterBot terminated")
    except Exception as e:
        print(f"Fatal ERROR: {e}")
        sys.exit(1)