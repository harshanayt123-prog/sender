import asyncio
import os

from dotenv import load_dotenv
from telethon import TelegramClient

load_dotenv()

API_ID = int(os.environ["TELEGRAM_API_ID"])
API_HASH = os.environ["TELEGRAM_API_HASH"]

async def main():
    client = TelegramClient("group_list_session", API_ID, API_HASH)

    await client.start()

    me = await client.get_me()
    print(f"\nLogged in as: {me.first_name} ({me.id})")
    print("\n========== YOUR GROUPS ==========\n")

    count = 0

    async for dialog in client.iter_dialogs():
        if dialog.is_group:
            count += 1
            print(f"{count}. {dialog.name} | {dialog.id}")

    print(f"\nTotal groups: {count}")

    await client.disconnect()

if __name__ == "__main__":
    asyncio.run(main())