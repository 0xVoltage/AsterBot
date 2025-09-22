#!/usr/bin/env python3
"""
Script to run AsterBot with multiple symbols
"""

import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from asterbot.bot import AsterBot
import asyncio


async def main():
    if len(sys.argv) < 2:
        print("Usage: python run_bot.py <path_to_config.json>")
        return

    config_path = sys.argv[1]
    if not os.path.exists(config_path):
        print(f"Configuration file not found: {config_path}")
        return

    bot = AsterBot(config_path)
    await bot.run()


if __name__ == "__main__":
    asyncio.run(main())