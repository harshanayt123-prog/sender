"""Long-running Telethon group-announcement daemon for Vercel Daemons.

Runs as a *container worker*, not an HTTP function. Configure via environment.
Only use for Telegram groups that permit automated recurring announcements.
"""

import asyncio
import os
import signal
import time
from pathlib import Path

from dotenv import load_dotenv
from telethon import TelegramClient, errors
from telethon.sessions import StringSession

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR.parent / ".env", override=False)

# Country mapping preserved from the uploaded project.
COUNTRIES = {
    "Sri Lanka": ("SRI_LANKA_GROUP_IDS", "sri_lanka.txt"),
    "India": ("INDIA_GROUP_IDS", "india.txt"),
    "Romania": ("ROMANIA_GROUP_IDS", "romania.txt"),
    "Bangladesh": ("BANGLADESH_GROUP_IDS", "bangladesh.txt"),
    "Pakistan": ("PAKISTAN_GROUP_IDS", "pakistan.txt"),
    "Brazil": ("BRAZIL_GROUP_IDS", "brazil.txt"),
    "Indonesia": ("INDONESIA_GROUP_IDS", "indonesia.txt"),
    "Philippines": ("PHILIPPINES_GROUP_IDS", "philippines.txt"),
    "Malaysia": ("MALAYSIA_GROUP_IDS", "malaysia.txt"),
    "United Kingdom": ("UNITED_KINGDOM_GROUP_IDS", "united_kingdom.txt"),
    "United States": ("UNITED_STATES_GROUP_IDS", "united_states.txt"),
    "Australia": ("AUSTRALIA_GROUP_IDS", "australia.txt"),
    "Canada": ("CANADA_GROUP_IDS", "canada.txt"),
    "Unknown": ("UNKNOWN_GROUP_IDS", "unknown.txt"),
    "Link": ("LINK_IDS", "link.txt"),
    "Bangla": ("BANGLA_IDS", "bangla.txt"),
    "Hindi": ("HINDI_GROUP_IDS", "hindi.txt"),
    "Spanish": ("SPANISH_GROUP_IDS", "spanish.txt"),
}


def required_environment(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value or value.startswith("replace_with_") or value in {"12345678", "your_api_hash", "your_string_session"}:
        raise ValueError(f"Set a valid {name} in the deployment environment")
    return value


def positive_int(name: str, default: int, minimum: int) -> int:
    try:
        value = int(os.getenv(name, str(default)))
        if value < minimum:
            raise ValueError
        return value
    except ValueError:
        print(f"{name} must be at least {minimum}; using {default}.", flush=True)
        return default


def dry_run_enabled() -> bool:
    raw = os.getenv("DRY_RUN", "true").lower().strip()
    if raw not in {"true", "false", "1", "0", "yes", "no", "on", "off"}:
        raise ValueError("DRY_RUN must be true or false")
    return raw in {"true", "1", "yes", "on"}


def group_ids_from_env(name: str) -> list[int]:
    result = []
    seen = set()
    for item in os.getenv(name, "").split(","):
        value = item.strip()
        if not value:
            continue
        try:
            group_id = int(value)
        except ValueError:
            print(f"Ignoring invalid integer in {name}: {value!r}", flush=True)
            continue
        if group_id not in seen:
            seen.add(group_id)
            result.append(group_id)
    return result


def read_message(filename: str) -> str | None:
    path = BASE_DIR / "messages" / filename
    if not path.is_file():
        print(f"Skipping missing message file: {filename}", flush=True)
        return None
    content = path.read_text(encoding="utf-8").strip()
    if not content:
        print(f"Skipping empty message file: {filename}", flush=True)
        return None
    return content


async def interruptible_sleep(stop: asyncio.Event, seconds: int) -> None:
    try:
        await asyncio.wait_for(stop.wait(), timeout=seconds)
    except asyncio.TimeoutError:
        pass


async def load_joined_groups(client: TelegramClient) -> dict[int, object]:
    """Only target groups the signed-in account can actually see in its dialogs."""
    known = {}
    async for dialog in client.iter_dialogs():
        if dialog.is_group:
            known[dialog.id] = dialog.entity
    print(f"Loaded {len(known)} joined groups", flush=True)
    return known


async def send_one_cycle(client: TelegramClient, joined: dict[int, object],
                         stop: asyncio.Event, preview: bool, delay: int) -> int:
    """Returns Telegram's required FloodWait seconds, or 0."""
    processed = set()
    successes = 0
    for country, (env_var, filename) in COUNTRIES.items():
        if stop.is_set():
            break
        ids = group_ids_from_env(env_var)
        if not ids:
            continue
        message = read_message(filename)
        if not message:
            continue
        print(f"[{country}] {len(ids)} configured group(s)", flush=True)
        for group_id in ids:
            if stop.is_set():
                break
            if group_id in processed:
                print(f"SKIP {group_id}: already targeted this cycle", flush=True)
                continue
            processed.add(group_id)
            entity = joined.get(group_id)
            if entity is None:
                print(f"SKIP {country} -> {group_id}: not among joined groups", flush=True)
                continue
            if preview:
                print(f"DRY RUN {country} -> {group_id} ({len(message)} chars)", flush=True)
                continue
            try:
                await client.send_message(entity, message,
                                          parse_mode="html", link_preview=False)
                successes += 1
                print(f"SENT {country} -> {group_id}", flush=True)
            except errors.FloodWaitError as exc:
                print(f"FLOOD WAIT: Telegram requires {exc.seconds} seconds; stopping cycle", flush=True)
                return max(1, int(exc.seconds))
            except (errors.PeerFloodError, errors.UserRestrictedError) as exc:
                # Do not attempt to work around Telegram account restrictions.
                raise RuntimeError(f"Telegram account restricted: {type(exc).__name__}") from exc
            except (errors.ChatWriteForbiddenError,
                    errors.UserBannedInChannelError,
                    errors.ChatRestrictedError) as exc:
                print(f"SKIP {country} -> {group_id}: {type(exc).__name__}", flush=True)
            except errors.RPCError as exc:
                print(f"Telegram error {country} -> {group_id}: {type(exc).__name__}: {exc}", flush=True)
            except Exception as exc:
                print(f"Failed {country} -> {group_id}: {type(exc).__name__}: {exc}", flush=True)
            await interruptible_sleep(stop, delay)
    print(f"Cycle completed: {successes} message(s) sent (dry run: {preview})", flush=True)
    return 0


async def main() -> None:
    api_id_string = required_environment("TELEGRAM_API_ID")
    try:
        api_id = int(api_id_string)
    except ValueError as exc:
        raise RuntimeError("TELEGRAM_API_ID must be a valid integer") from exc
    api_hash = required_environment("TELEGRAM_API_HASH")
    session = required_environment("TELEGRAM_SESSION")
    preview = dry_run_enabled()

    stop = asyncio.Event()
    loop = asyncio.get_running_loop()
    for name in (signal.SIGTERM, signal.SIGINT):
        try:
            loop.add_signal_handler(name, stop.set)
        except NotImplementedError:
            # Windows: SIGTERM event handlers are not available.
            pass

    client = TelegramClient(StringSession(session), api_id, api_hash)
    await client.connect()
    try:
        if not await client.is_user_authorized():
            raise RuntimeError("TELEGRAM_SESSION is not authorized; generate a new session locally")
        me = await client.get_me()
        if getattr(me, "bot", False):
            raise RuntimeError("Bot session supplied; this project uses a user StringSession")
        print(f"Connected Telegram account ID {me.id}; DRY_RUN={preview}", flush=True)
        joined = await load_joined_groups(client)
        loaded_at = time.monotonic()
        while not stop.is_set():
            interval = positive_int("INTERVAL_SECONDS", default=120, minimum=60)
            delay = positive_int("DELAY_BETWEEN_GROUPS", default=10, minimum=0)
            if time.monotonic() - loaded_at > 6 * 3600:
                joined = await load_joined_groups(client)
                loaded_at = time.monotonic()
            print("Starting message cycle", flush=True)
            wait = await send_one_cycle(client, joined, stop, preview, delay)
            if stop.is_set():
                break
            pause = max(interval, wait)
            print(f"Next cycle in {pause} seconds", flush=True)
            await interruptible_sleep(stop, pause)
    finally:
        await client.disconnect()
    print("Telegram daemon stopped cleanly", flush=True)


if __name__ == "__main__":
    asyncio.run(main())
