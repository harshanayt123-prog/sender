import os, asyncio
from dotenv import load_dotenv
from telethon import TelegramClient
from telethon.sessions import StringSession
load_dotenv()
async def main():
    c=TelegramClient(StringSession(),int(os.environ["TELEGRAM_API_ID"]),os.environ["TELEGRAM_API_HASH"])
    print("Use your PERSONAL Telegram phone number, not a bot token.")
    await c.start()
    me=await c.get_me()
    if me.bot: raise RuntimeError("Bot session detected")
    print("\nTELEGRAM_SESSION:\n"+c.session.save()+"\n")
    await c.disconnect()
asyncio.run(main())
