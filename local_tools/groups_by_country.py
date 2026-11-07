import os
import csv
import asyncio
from collections import defaultdict

from dotenv import load_dotenv
from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon.tl.functions.channels import GetFullChannelRequest


# ============================================================
# LOAD .ENV
# ============================================================

load_dotenv()

API_ID = os.getenv("TELEGRAM_API_ID")
API_HASH = os.getenv("TELEGRAM_API_HASH")
SESSION_STRING = os.getenv("TELEGRAM_SESSION")


# ============================================================
# CHECK ENVIRONMENT VARIABLES
# ============================================================

if not API_ID:
    raise RuntimeError(
        "TELEGRAM_API_ID is missing.\n"
        "Add TELEGRAM_API_ID to your .env file."
    )

if not API_HASH:
    raise RuntimeError(
        "TELEGRAM_API_HASH is missing.\n"
        "Add TELEGRAM_API_HASH to your .env file."
    )

if not SESSION_STRING:
    raise RuntimeError(
        "TELEGRAM_SESSION is missing.\n"
        "Add TELEGRAM_SESSION to your .env file."
    )

try:
    API_ID = int(API_ID)
except ValueError:
    raise RuntimeError(
        "TELEGRAM_API_ID must be a number."
    )


# ============================================================
# COUNTRY KEYWORDS
# ============================================================

COUNTRY_KEYWORDS = {

    "Sri Lanka": [
        "sri lanka",
        "srilanka",
        "sri lankan",
        "srilankan",
        "lanka",
        "ceylon",
        "sinhala",
        "sinhalese",
        "colombo",
        "kandy",
        "galle",
        "kurunegala",
        "jaffna",
        "matara",
        "negombo",
        "anuradhapura",
        "ratnapura",

        # Sinhala words/characters
        "සිංහල",
        "ලංකා",
        "කෙල්ල",
        "කොල්ල",
        "වැල",
        "සැප",
        "කාම",
        "අපේ",
        "මිතුර",
        "තරුණ",
        "සතුට",
        "යහන",
        "ලෝකය",
        "රාජදානිය",
        "අඩවිය",
        "ගබඩාව",
        "පන්තිය",
        "වාට්ටුව",

        # Common tags
        "sl ",
        " sl",
        "lk ",
        " lk",
        "🇱🇰"
    ],

    "India": [
        "india",
        "indian",
        "bharat",
        "भारत",
        "हिंदी",
        "hindi",
        "delhi",
        "mumbai",
        "chennai",
        "kerala",
        "tamil nadu",
        "kolkata",
        "bangalore",
        "bengaluru",
        "hyderabad",
        "tamil",
        "🇮🇳",


         # Tamil / Tamil Nadu
        "tamil",
        "தமிழ்",
        "தமிழ்நாடு",
        "தமிழ் நாடு",
        "தமிழன்",
        "தமிழச்சி",
        "தமிழர்கள்",
        "தமிழகம்",
        "சென்னை",
        "மதுரை",
        "கோயம்புத்தூர்",
        "திருச்சி",
        "திருச்சிராப்பள்ளி",
        "சேலம்",
        "திருநெல்வேலி",
        "வேலூர்",
        "தஞ்சாவூர்",
        "ஈரோடு",
        "திருப்பூர்",
        "கன்னியாகுமரி",
        "கோவை",
        "madurai",
        "coimbatore",
        "kovai",
        "trichy",
        "tiruchirappalli",
        "salem",
        "tirunelveli",
        "vellore",
        "thanjavur",
        "erode",
        "tiruppur",
        "kanyakumari",

    ],

        "Romania": [
        "romania",
        "romanian",
        "românia",
        "român",
        "română",
        "romani",
        "romania ",
        "bucuresti",
        "bucurești",
        "bucharest",
        "cluj",
        "cluj-napoca",
        "timisoara",
        "timișoara",
        "iasi",
        "iași",
        "constanta",
        "constanța",
        "brasov",
        "brașov",
        "craiova",
        "sibiu",
        "oradea",
        "arad",
        "ploiesti",
        "ploiești",
        "🇷🇴"
    ],

    "Bangladesh": [
        "bangladesh",
        "bangladeshi",
        "bangla",
        "বাংলাদেশ",
        "বাংলা",
        "dhaka",
        "🇧🇩"
    ],

    "Pakistan": [
        "pakistan",
        "pakistani",
        "پاکستان",
        "karachi",
        "lahore",
        "islamabad",
        "🇵🇰"
    ],

    "Nepal": [
        "nepal",
        "nepali",
        "नेपाल",
        "kathmandu",
        "🇳🇵"
    ],

    "Indonesia": [
        "indonesia",
        "indonesian",
        "jakarta",
        "bandung",
        "surabaya",
        "🇮🇩"
    ],

    "Philippines": [
        "philippines",
        "philippine",
        "filipino",
        "pinoy",
        "pinay",
        "manila",
        "cebu",
        "🇵🇭"
    ],

    "Malaysia": [
        "malaysia",
        "malaysian",
        "kuala lumpur",
        "🇲🇾"
    ],

    "Singapore": [
        "singapore",
        "singaporean",
        "🇸🇬"
    ],

    "Thailand": [
        "thailand",
        "thai",
        "bangkok",
        "🇹🇭"
    ],

    "Vietnam": [
        "vietnam",
        "vietnamese",
        "hanoi",
        "saigon",
        "ho chi minh",
        "🇻🇳"
    ],

    "Brazil": [
        "brazil",
        "brasil",
        "brasileiro",
        "brasileira",
        "são paulo",
        "sao paulo",
        "rio de janeiro",
        "🇧🇷"
    ],

    "United Kingdom": [
        "united kingdom",
        "british",
        "england",
        "scotland",
        "wales",
        "london",
        "🇬🇧"
    ],

    "United States": [
        "united states",
        "american",
        "new york",
        "los angeles",
        "california",
        "texas",
        "🇺🇸"
    ],

    "Australia": [
        "australia",
        "australian",
        "sydney",
        "melbourne",
        "🇦🇺"
    ],

    "Canada": [
        "canada",
        "canadian",
        "toronto",
        "vancouver",
        "🇨🇦"
    ]
}


# ============================================================
# DETECT COUNTRY
# ============================================================

def detect_country(name="", username="", description=""):

    text = (
        f"{name} {username} {description}"
    ).lower()

    scores = {}

    for country, keywords in COUNTRY_KEYWORDS.items():

        score = 0

        for keyword in keywords:

            if keyword.lower() in text:
                score += 1

        if score > 0:
            scores[country] = score

    if not scores:
        return "Unknown"

    # Country with highest number of keyword matches
    return max(
        scores,
        key=scores.get
    )


# ============================================================
# GET DESCRIPTION
# ============================================================

async def get_description(client, entity):

    try:

        full = await client(
            GetFullChannelRequest(entity)
        )

        return getattr(
            full.full_chat,
            "about",
            ""
        ) or ""

    except Exception:

        return ""


# ============================================================
# MAIN
# ============================================================

async def main():

    print("=" * 60)
    print("Telegram Groups By Country")
    print("=" * 60)

    print("\nConnecting to Telegram...")

    client = TelegramClient(
        StringSession(SESSION_STRING),
        API_ID,
        API_HASH
    )

    await client.connect()

    try:

        # ----------------------------------------------------
        # AUTH CHECK
        # ----------------------------------------------------

        if not await client.is_user_authorized():

            raise RuntimeError(
                "TELEGRAM_SESSION is not authorized."
            )

        me = await client.get_me()

        if me.bot:

            raise RuntimeError(
                "This is a bot session.\n"
                "Use a personal Telegram account StringSession."
            )

        print(
            f"Logged in as: {me.first_name} | ID: {me.id}"
        )

        # ----------------------------------------------------
        # GET DIALOGS
        # ----------------------------------------------------

        print("\nLoading Telegram groups...")

        dialogs = await client.get_dialogs()

        groups = []

        total_groups = sum(
            1 for d in dialogs
            if d.is_group
        )

        print(
            f"Found {total_groups} groups.\n"
        )

        current = 0

        # ----------------------------------------------------
        # PROCESS GROUPS
        # ----------------------------------------------------

        for dialog in dialogs:

            if not dialog.is_group:
                continue

            current += 1

            entity = dialog.entity

            group_id = dialog.id

            name = dialog.name or "Unknown Group"

            username = (
                getattr(
                    entity,
                    "username",
                    ""
                ) or ""
            )

            print(
                f"[{current}/{total_groups}] "
                f"{name}"
            )

            # Try getting description
            description = await get_description(
                client,
                entity
            )

            country = detect_country(
                name,
                username,
                description
            )

            groups.append({

                "country": country,

                "name": name,

                "id": group_id,

                "username": username,

                "description": description

            })

            print(
                f"    ID: {group_id}"
            )

            print(
                f"    Country: {country}"
            )

            if username:

                print(
                    f"    Username: @{username}"
                )

            print()

            # Be gentle with Telegram requests
            await asyncio.sleep(0.5)

        # ----------------------------------------------------
        # SORT
        # ----------------------------------------------------

        groups.sort(
            key=lambda x: (
                x["country"],
                x["name"].lower()
            )
        )

        # ----------------------------------------------------
        # CSV EXPORT
        # ----------------------------------------------------

        csv_file = "groups_by_country.csv"

        with open(
            csv_file,
            "w",
            newline="",
            encoding="utf-8-sig"
        ) as f:

            writer = csv.DictWriter(

                f,

                fieldnames=[
                    "country",
                    "name",
                    "id",
                    "username",
                    "description"
                ]
            )

            writer.writeheader()

            writer.writerows(groups)

        # ----------------------------------------------------
        # GROUP BY COUNTRY
        # ----------------------------------------------------

        grouped = defaultdict(list)

        for group in groups:

            grouped[
                group["country"]
            ].append(group)

        # ----------------------------------------------------
        # TXT EXPORT
        # ----------------------------------------------------

        txt_file = "groups_by_country.txt"

        with open(
            txt_file,
            "w",
            encoding="utf-8"
        ) as f:

            for country in sorted(grouped.keys()):

                country_groups = grouped[country]

                f.write(
                    "\n"
                    + "=" * 70
                    + "\n"
                )

                f.write(
                    f"{country} "
                    f"({len(country_groups)} groups)\n"
                )

                f.write(
                    "=" * 70
                    + "\n\n"
                )

                # Group name + ID
                for index, group in enumerate(
                    country_groups,
                    start=1
                ):

                    f.write(
                        f"{index}. "
                        f"{group['name']} | "
                        f"{group['id']}\n"
                    )

                # --------------------------------------------
                # GROUP_IDS format
                # --------------------------------------------

                ids = ",".join(
                    str(group["id"])
                    for group in country_groups
                )

                f.write(
                    "\nGROUP_IDS=\n"
                )

                f.write(
                    ids
                )

                f.write(
                    "\n\n"
                )

        # ----------------------------------------------------
        # SEPARATE COUNTRY FILES
        # ----------------------------------------------------

        for country, country_groups in grouped.items():

            safe_country = (
                country
                .lower()
                .replace(" ", "_")
            )

            filename = (
                f"groups_{safe_country}.txt"
            )

            with open(
                filename,
                "w",
                encoding="utf-8"
            ) as f:

                f.write(
                    f"{country}\n"
                )

                f.write(
                    "=" * 50
                    + "\n\n"
                )

                for group in country_groups:

                    f.write(
                        f"{group['name']} | "
                        f"{group['id']}\n"
                    )

                ids = ",".join(
                    str(group["id"])
                    for group in country_groups
                )

                f.write(
                    "\nGROUP_IDS=\n"
                )

                f.write(ids)

                f.write("\n")

        # ----------------------------------------------------
        # SUMMARY
        # ----------------------------------------------------

        print("\n")
        print("=" * 60)
        print("COUNTRY SUMMARY")
        print("=" * 60)

        for country in sorted(grouped.keys()):

            print(
                f"{country}: "
                f"{len(grouped[country])}"
            )

        print("\n")
        print("=" * 60)
        print("DONE")
        print("=" * 60)

        print(
            f"\nTotal groups: {len(groups)}"
        )

        print(
            f"CSV: {csv_file}"
        )

        print(
            f"TXT: {txt_file}"
        )

        print(
            "\nSeparate country TXT files "
            "were also created."
        )

    finally:

        await client.disconnect()


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":

    asyncio.run(main())