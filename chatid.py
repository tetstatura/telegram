import asyncio
import os
from dotenv import load_dotenv
from telethon import TelegramClient

load_dotenv()

api_id = int(os.getenv("API_ID"))
api_hash = os.getenv("API_HASH")

client = TelegramClient('anon', api_id, api_hash)

async def main():
    await client.start()
    dialogs = await client.get_dialogs()

    print("📋 Lista tvojih chatova:\n")
    for dialog in dialogs:
        name = dialog.name or "N/A"
        entity_id = dialog.id
        print(f"{name} — {entity_id}")

with client:
    client.loop.run_until_complete(main())
