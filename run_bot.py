"""Run script for the Telegram bot."""

import os
import sys

# Add src directory to Python path
src_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "src")
sys.path.insert(0, src_dir)

# Run the bot
if __name__ == "__main__":
    from src.tools.communication.telegram.bot import main
    import asyncio
    asyncio.run(main())
