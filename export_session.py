from telethon.sync import TelegramClient
from telethon.sessions import StringSession

api_id =25597983
api_hash ="46dcec10980c2d7e0b6987af8c9def40"

with TelegramClient(StringSession(), api_id, api_hash) as client:
    print("👉 Tvoj session string:")
    print(client.session.save())
