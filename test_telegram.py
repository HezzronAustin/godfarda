import asyncio
import os
import json
from dotenv import load_dotenv
from src.tools.telegram.message import TelegramMessageTool

async def main():
    # Load environment variables
    load_dotenv()
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    
    # Initialize the tool
    tool = TelegramMessageTool()
    
    # Get updates
    result = await tool.execute({
        "action": "get_updates",
        "token": token
    })
    
    if result.success:
        updates = result.data["updates"]
        print("Raw updates data:")
        print(json.dumps(updates, indent=2))
        
        if updates:
            # Get the most recent message
            latest_update = updates[-1]
            if "message" in latest_update:
                chat_id = str(latest_update["message"]["chat"]["id"])
                print(f"\nFound chat ID: {chat_id}")
                
                # Send a test message back
                send_result = await tool.execute({
                    "action": "send_message",
                    "token": token,
                    "chat_id": chat_id,
                    "message": "Greetings, Don! Your AI Mafia bot is at your service. 🎩🤝\nI am ready to receive your commands."
                })
                
                if send_result.success:
                    print("Message sent successfully!")
                else:
                    print(f"Failed to send message: {send_result.error}")
            else:
                print("No message found in the update")
        else:
            print("\nNo updates found. Please send a message to the bot first.")
    else:
        print(f"Error getting updates: {result.error}")

if __name__ == "__main__":
    asyncio.run(main())
