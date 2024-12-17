"""FastAPI webhook handler for Telegram bot."""

import os
from fastapi import FastAPI, Request
from dotenv import load_dotenv
from .handler import TelegramHandler

# Load environment variables
load_dotenv()

# Get environment variables
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_WEBHOOK_URL = os.getenv('TELEGRAM_WEBHOOK_URL')

if not TELEGRAM_BOT_TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN environment variable is not set")
if not TELEGRAM_WEBHOOK_URL:
    raise ValueError("TELEGRAM_WEBHOOK_URL environment variable is not set")

app = FastAPI(title="Telegram Bot Webhook")
handler = TelegramHandler()

@app.on_event("startup")
async def startup():
    """Initialize the Telegram handler and set up webhook on startup."""
    await handler.initialize(TELEGRAM_BOT_TOKEN)
    
    # Set up webhook on startup
    webhook_url = f"{TELEGRAM_WEBHOOK_URL}/webhook"
    response = await handler.execute({
        "action": "setup_webhook",
        "token": TELEGRAM_BOT_TOKEN,
        "webhook_url": webhook_url
    })
    
    if not response.success:
        raise RuntimeError(f"Failed to set up webhook: {response.error}")

@app.post("/webhook")
async def telegram_webhook(request: Request):
    """Handle incoming webhook updates from Telegram."""
    update = await request.json()
    
    response = await handler.execute({
        "action": "process_update",
        "token": TELEGRAM_BOT_TOKEN,
        "update": update
    })
    
    if not response.success:
        return {"status": "error", "message": response.error}
    
    return {"status": "success", "data": response.data}
