import asyncio
import os

from dotenv import load_dotenv
from telethon import TelegramClient
from telethon.errors import (
    UserRestrictedError,
    FloodWaitError,
    RPCError,
)
from telethon.tl.functions.channels import CreateChannelRequest

load_dotenv()

API_ID = os.getenv("TELEGRAM_API_ID")
API_HASH = os.getenv("TELEGRAM_API_HASH")

if not API_ID:
    raise RuntimeError("TELEGRAM_API_ID is missing from .env")

if not API_HASH:
    raise RuntimeError("TELEGRAM_API_HASH is missing from .env")

API_ID = int(API_ID)


async def main():
    client = TelegramClient(
        "group_creator_session",
        API_ID,
        API_HASH
    )

    await client.start()

    me = await client.get_me()

    print("\n==============================")
    print("TELEGRAM ACCOUNT")
    print("==============================")
    print("Name:", me.first_name)
    print("Username:", f"@{me.username}" if me.username else "None")
    print("User ID:", me.id)
    print("Phone:", me.phone or "Hidden")
    print("Restricted flag:", getattr(me, "restricted", False))

    restriction_reason = getattr(me, "restriction_reason", None)

    if restriction_reason:
        print("\nRestriction information:")
        for reason in restriction_reason:
            print(
                f"- Platform: {getattr(reason, 'platform', '?')}"
            )
            print(
                f"  Reason: {getattr(reason, 'reason', '?')}"
            )
            print(
                f"  Text: {getattr(reason, 'text', '?')}"
            )

    print("\n==============================")
    print("GROUP CREATION TEST")
    print("==============================")

    choice = input(
        "Try to create the group now? (y/n): "
    ).strip().lower()

    if choice != "y":
        print("\nNo group creation attempted.")
        print("Check @SpamBot in Telegram for spam-limit status.")
        await client.disconnect()
        return

    try:
        result = await client(
            CreateChannelRequest(
                title="My Bot Community",
                about="Official community group for my Telegram bot",
                megagroup=True
            )
        )

        group = result.chats[0]

        print("\n✅ SUCCESS")
        print("Telegram currently allows this account to create groups.")
        print("Group name:", group.title)
        print("Group ID:", group.id)

    except UserRestrictedError:
        print("\n❌ ACCOUNT RESTRICTED")
        print(
            "Telegram is currently blocking this account "
            "from creating groups/channels."
        )
        print()
        print("Open Telegram and message:")
        print("@SpamBot")
        print()
        print(
            "If Telegram says the restriction was applied "
            "incorrectly, use the complaint/appeal option."
        )

    except FloodWaitError as e:
        print("\n⏳ FLOOD WAIT")
        print(
            f"Telegram requires you to wait approximately "
            f"{e.seconds} seconds."
        )

    except RPCError as e:
        print("\n❌ TELEGRAM API ERROR")
        print("Type:", type(e).__name__)
        print("Message:", str(e))

    except Exception as e:
        print("\n❌ UNEXPECTED ERROR")
        print("Type:", type(e).__name__)
        print("Message:", str(e))

    finally:
        await client.disconnect()


if __name__ == "__main__":
    asyncio.run(main())