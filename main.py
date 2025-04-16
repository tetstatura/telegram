import asyncio
import os
import sys
from dotenv import load_dotenv
from telethon import TelegramClient, events
from telethon.tl.types import PeerChannel
from openai import OpenAI
from collections import defaultdict

sys.stdout.reconfigure(encoding='utf-8')
load_dotenv()

api_id = int(os.getenv("API_ID"))
api_hash = os.getenv("API_HASH")
bot_token = os.getenv("BOT_TOKEN")
openai_key = os.getenv("OPENAI_API_KEY")
to_chat_id = int(os.getenv("TO_CHAT_ID"))
group_chat_id = int(os.getenv("GROUP_CHAT_ID"))
channel_inputs = os.getenv("CHANNEL_USERNAMES", "").split(",")

client = TelegramClient("anon", api_id, api_hash)
bot_client = TelegramClient("bot", api_id, api_hash).start(bot_token=bot_token)
openai = OpenAI(api_key=openai_key)

grouped_buffer = defaultdict(list)
group_peer = PeerChannel(int(str(group_chat_id).replace("-100", "")))  # <- BITNO ZA SLANJE U GRUPU

async def handle_combined(event_group):
    if not event_group:
        return

    text = "\n".join([e.raw_text.strip() for e in event_group if e.raw_text.strip()]).strip()
    print("\n[NOVA PORUKA] >>>", text.encode("utf-8", errors="replace").decode())

    try:
        gpt_prompt = [
            {
                "role": "system",
                "content": (
                    "You are a Telegram crypto news assistant. You will receive ONE message at a time. "
                    "Your task is to rephrase this message using different words while keeping the exact same meaning. "
                    "Do not change the topic, do not add or remove content. "
                    "Preserve the full message structure, including emojis, slang, political names, or short statements. "
                    "and make sure massage looks perfectly good feel free to send it with some empty raw if you understood what i'am talking about and feel free to use emoji if it was in original massage"
                    "answers must be in english iif massage waas on other launge translate iit on english and if there are some @ ads od tags remove it if you think something need to be removed for my news chanel what will signal a copy of original remove it and remove text full story or something like that where you need to put a link to click on it"

                )
            },
            {
                "role": "user",
                "content": text
            }
        ]

        response = openai.chat.completions.create(
            model="gpt-4o",
            messages=gpt_prompt,
            temperature=0.7
        )

        new_text = response.choices[0].message.content.strip()
        print(f"🧠 Odgovor GPT-a:\n{new_text}")

        media_files = []
        for ev in event_group:
            if ev.message.media:
                file = await client.download_media(ev.message.media)
                if file:
                    media_files.append(file)

        if media_files:
            await bot_client.send_file(to_chat_id, file=media_files, caption=new_text)
            await bot_client.send_file(group_peer, file=media_files, caption=new_text)
            print("📤 Poslato sa medijima u kanal i grupu!")
        else:
            await bot_client.send_message(to_chat_id, new_text)
            await bot_client.send_message(group_peer, new_text)
            print("📤 Poslato bez medija u kanal i grupu!")

        for f in media_files:
            try:
                os.remove(f)
            except Exception as e:
                print(f"⚠️ Greška pri brisanju fajla: {f} → {e}")

    except Exception as e:
        print(f"⚠️ Greška pri obradi: {e}")

async def main():
    await client.start()
    await bot_client.start()

    listen_chats = []
    for chan in channel_inputs:
        chan = chan.strip()
        if chan.startswith("-100"):
            listen_chats.append(PeerChannel(int(chan.replace("-100", ""))))
        else:
            listen_chats.append(chan)

    print("✅ Bot je povezan i prati kanale:", listen_chats)

    @client.on(events.NewMessage(chats=listen_chats))
    async def handler(event):
        gid = getattr(event.message, "grouped_id", None)
        if gid:
            grouped_buffer[gid].append(event)
            await asyncio.sleep(1.5)
            if grouped_buffer[gid]:
                to_process = grouped_buffer.pop(gid)
                await handle_combined(to_process)
        else:
            await handle_combined([event])

    await client.run_until_disconnected()

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
