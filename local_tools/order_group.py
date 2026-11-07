import asyncio
import os
from datetime import datetime

from dotenv import load_dotenv
from telethon import TelegramClient, functions, types
from telethon.errors import FloodWaitError

load_dotenv()

API_ID = int(os.environ["TELEGRAM_API_ID"])
API_HASH = os.environ["TELEGRAM_API_HASH"]


async def get_join_date(client, entity, my_id):
    try:
        # Supergroups / megagroups/
        if isinstance(entity, types.Channel):
            result = await client(
                functions.channels.GetParticipantRequest(
                    channel=entity,
                    participant="me"
                )
            )

            return getattr(result.participant, "date", None)

        # Old/basic Telegram groups
        elif isinstance(entity, types.Chat):
            result = await client(
                functions.messages.GetFullChatRequest(
                    chat_id=entity.id
                )
            )

            participants = getattr(
                result.full_chat.participants,
                "participants",
                []
            )

            for participant in participants:
                if getattr(participant, "user_id", None) == my_id:
                    return getattr(participant, "date", None)

    except FloodWaitError as e:
        print(f"FloodWait: waiting {e.seconds} seconds...")
        await asyncio.sleep(e.seconds + 1)

        # Try again
        return await get_join_date(client, entity, my_id)

    except Exception as e:
        print(f"Could not get join date: {entity.id} | {e}")

    return None


async def main():
    client = TelegramClient(
        "group_list_session",
        API_ID,
        API_HASH
    )

    await client.start()

    me = await client.get_me()

    print(f"\nLogged in as: {me.first_name} ({me.id})")
    print("\nReading groups and join dates...\n")

    groups = []

    async for dialog in client.iter_dialogs():

        if not dialog.is_group:
            continue

        joined_date = await get_join_date(
            client,
            dialog.entity,
            me.id
        )

        groups.append({
            "name": dialog.name,
            "id": dialog.id,
            "joined": joined_date
        })

        if joined_date:
            print(
                f"Found: {dialog.name} | "
                f"Joined: {joined_date.strftime('%Y-%m-%d %H:%M:%S')}"
            )
        else:
            print(
                f"Found: {dialog.name} | "
                f"Joined: Unknown"
            )

        # Small delay to reduce API rate-limit problems
        await asyncio.sleep(0.15)

    # Newest joined group first
    groups.sort(
        key=lambda x: (
            x["joined"].timestamp()
            if x["joined"]
            else float("-inf")
        ),
        reverse=True
    )

    print("\n")
    print("=" * 80)
    print("       GROUPS — RECENTLY JOINED FIRST")
    print("=" * 80)
    print()

    for number, group in enumerate(groups, 1):

        if group["joined"]:
            joined_text = group["joined"].strftime(
                "%Y-%m-%d %H:%M:%S"
            )
        else:
            joined_text = "Unknown"

        print(
            f"{number}. {group['name']}\n"
            f"   ID: {group['id']}\n"
            f"   Joined: {joined_text}\n"
        )

    print("=" * 80)
    print(f"Total groups: {len(groups)}")

    await client.disconnect()


if __name__ == "__main__":
    asyncio.run(main())