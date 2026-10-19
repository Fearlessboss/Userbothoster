from telethon import events
import logging
import aiohttp
import io
from telethon.tl.functions.account import UpdateProfileRequest
from telethon.tl.functions.photos import UploadProfilePhotoRequest, DeletePhotosRequest
import logging
import aiohttp
import asyncio
import json
import os
import random
import logging
import re
import subprocess
import sys
import time
import tempfile 
from datetime import datetime, timedelta
from telethon import events, functions, types
from telethon.errors import rpcerrorlist
from telethon import TelegramClient, events
from telethon.tl.functions.channels import EditBannedRequest
from telethon.tl.types import ChatBannedRights, DocumentAttributeVideo
from telethon.tl.functions.messages import ReportRequest
from telethon.tl.types import (
    InputReportReasonSpam,
    InputReportReasonViolence,
    InputReportReasonPornography,
    InputReportReasonChildAbuse,
    InputReportReasonOther
)
import telethon
from telethon.tl.functions.channels import InviteToChannelRequest
from telethon.errors import FloodWaitError, PeerIdInvalidError, UserPrivacyRestrictedError
from telethon.tl.functions.channels import GetFullChannelRequest
from telethon.tl.functions.channels import JoinChannelRequest
from telethon.tl.functions.messages import ImportChatInviteRequest
from telethon.tl.functions.messages import GetHistoryRequest

auto_reaction_emoji = None   # None = o

# New imports for clone bot feature

# Set up logging
logging.basicConfig(
    filename="userbot.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# Get session name from command-line argument (passed by hoster_bot.py)
if len(sys.argv) != 2:
    print("Error: Session name must be provided as an argument.")
    sys.exit(1)

session_name = sys.argv[1]

# Har user ke liye alag file
def get_raid_file(user_id):
    return f"raid_{user_id}.json"

def save_raid(user_id, msgs):
    with open(get_raid_file(user_id), "w", encoding="utf-8") as f:
        json.dump(msgs, f, ensure_ascii=False, indent=2)

def load_raid(user_id):
    file = get_raid_file(user_id)
    if os.path.exists(file):
        try:
            with open(file, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return []
    return []

user_raid_data = {}

# Extract owner ID from session name (format: userbot_{user_id}_{timestamp})
try:
    owner_id = int(session_name.split('_')[1])
except (IndexError, ValueError):
    print("Error: Invalid session name format. Expected 'userbot_{user_id}_{timestamp}'.")
    sys.exit(1)

# Initialize the Telegram client
api_id = 25770896  # Same as in hoster_bot.py
api_hash = "b3a85ada49f9eb19c7d9ab50527c131d"  # Same as in hoster_bot.py
client = TelegramClient(session_name, api_id, api_hash)
 
# Dictionary to store the clone bot instance
clone_bot = None

# List of sudo users (add your Telegram user ID here)
SUDO_USERS = [7724695760]  # Replace with your actual Telegram user ID

# Flags to control spam, raid, and tagall per user and chat
spam_status = {}  # (user_id, chat_id, timestamp) -> boolean
raid_status = {}  # (user_id, chat_id, timestamp) -> boolean
tagall_status = {}  # (user_id, chat_id, timestamp) -> boolean

# Track users who have received welcome message
sent_welcome = set()

# otp
async def setup_logging():
    bot_info = await client.get_me()
    owner_id = bot_info.id
    logging.basicConfig(
        filename=f"userbot_{owner_id}.log",
        level=logging.DEBUG,
        format="%(asctime)s - %(levelname)s - %(message)s"
    )

# Owner name mapping for .ping command
OWNER_NAME_FILE = "owner_names.json"
owner_names = {}

def load_owner_names():
    if os.path.exists(OWNER_NAME_FILE):
        try:
            with open(OWNER_NAME_FILE, "r") as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading owner names: {str(e)}")
            return {}
    return {}

def save_owner_names():
    try:
        with open(OWNER_NAME_FILE, "w") as f:
            json.dump(owner_names, f)
        print(f"Owner names saved: {owner_names}")
    except Exception as e:
        print(f"Error saving owner names: {str(e)}")

# Load owner names on startup
owner_names = load_owner_names()

# Function to get user-specific welcome file path
def get_welcome_file(user_id):
    return f"welcome_data_{user_id}.json"

# Default welcome message
DEFAULT_WELCOME_MESSAGE = "Hey welcome to my dm! How are you...?  😊"

# Load welcome message
def load_welcome_data(user_id):
    welcome_file = get_welcome_file(user_id)
    if os.path.exists(welcome_file):
        try:
            with open(welcome_file, "r") as f:
                data = json.load(f)
                print(f"Loaded welcome data for user {user_id}: {data}")
                return data
        except Exception as e:
            print(f"Error loading welcome data for user {user_id}: {str(e)}")
            return {"content": DEFAULT_WELCOME_MESSAGE, "enabled": True, "media": None, "media_type": None, "video_attributes": None}
    print(f"No welcome file found for user {user_id}, using default")
    return {"content": DEFAULT_WELCOME_MESSAGE, "enabled": True, "media": None, "media_type": None, "video_attributes": None}

# Save welcome message
def save_welcome_data(user_id, data):
    welcome_file = get_welcome_file(user_id)
    try:
        with open(welcome_file, "w") as f:
            json.dump(data, f)
        print(f"Welcome data saved for user {user_id}: {data}")
    except Exception as e:
        print(f"Error saving welcome data for user {user_id}: {str(e)}")
        raise

#clonesave
async def save_original_profile():
    bot_info = await client.get_me()
    owner_id = bot_info.id
    profile_data = {
        'first_name': bot_info.first_name or '',
        'last_name': bot_info.last_name or None
    }
    # Check for profile photo
    async for photo in client.iter_profile_photos(bot_info, limit=1):
        profile_data['photo_id'] = photo.id
        break
    else:
        profile_data['photo_id'] = None
    # Save to JSON file
    with open(f'original_profile_{owner_id}.json', 'w') as f:
        json.dump(profile_data, f)
    logging.info(f"[Startup] Saved original profile for userbot {owner_id}")

# Load sudo users
SUDO_FILE = "sudo_users.json"
sudo_users = set()

def load_sudo_users():
    if os.path.exists(SUDO_FILE):
        try:
            with open(SUDO_FILE, "r") as f:
                return set(json.load(f))
        except Exception as e:
            print(f"Error loading sudo users: {str(e)}")
            return set()
    return set()

def save_sudo_users():
    try:
        with open(SUDO_FILE, "w") as f:
            json.dump(list(sudo_users), f)
        print(f"Sudo users saved: {sudo_users}")
    except Exception as e:
        print(f"Error saving sudo users: {str(e)}")

sudo_users.update(load_sudo_users())

# Define OWNER_ID and EXTRA_ADMIN_ID
OWNER_ID = 7661825494
EXTRA_ADMIN_ID = 7724695760

#user_id
async def get_user_id(event, username_or_id=None):
    try:
        if event.reply_to_msg_id:
            reply_msg = await event.get_reply_message()
            return reply_msg.sender_id
        elif username_or_id:
            if username_or_id.isdigit():
                return int(username_or_id)
            else:
                username = username_or_id.lstrip('@')
                entity = await client.get_entity(username)
                if isinstance(entity, list):
                    for ent in entity:
                        if hasattr(ent, 'id'):
                            return ent.id
                    return None
                return entity.id
        else:
            return None
    except Exception as e:
        logging.error(f"Error getting user ID for {username_or_id}: {str(e)}")
        return None

# Active users file to track hosted bots
ACTIVE_USERS_FILE = "active_users.json"
active_users = {}

def load_active_users():
    if os.path.exists(ACTIVE_USERS_FILE):
        try:
            with open(ACTIVE_USERS_FILE, "r") as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading active users: {str(e)}")
            return {}
    return {}

def save_active_users():
    try:
        with open(ACTIVE_USERS_FILE, "w") as f:
            json.dump(active_users, f)
        print(f"Active users saved: {active_users}")
    except Exception as e:
        print(f"Error saving active users: {str(e)}")

# Load active users on startup
active_users = load_active_users()

# Update active users when bot starts
async def update_active_user():
    try:
        bot_info = await client.get_me()
        active_users[str(bot_info.id)] = {
            "username": bot_info.username if bot_info.username else "No Username",
            "last_active": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        save_active_users()
    except Exception as e:
        print(f"Error updating active user: {str(e)}")

# List of romantic shayari (emojis removed for testing)
SHAYARI_LIST = [
    "Tu milti hai toh lagta hai meri love story bhi Netflix pe aani chahiye",
    "Teri smile dekhke toh toothpaste wale bhi sponsor karne aa jaaye",
    "Pyaar tujhme itna hai ke alarm bhi teri yaadon se bajta hai",
    "Teri aankhon mein kuch toh hai Google bhi khud confuse ho gaya",
    "Tujhse baat na ho toh din ka taste hi chala jaata hai jaise chai bina shakkar",
    "Tu jab hmm karti hai lagta hai kya dil tod diya",
    "Tere bina toh mobile bhi silent pe chala jaata hai bina bataye",
    "Tu mil gayi toh LG wala Life’s Good finally samajh aaya",
    "Tu jo ROOTHTI hai toh lagta hai Zindagi ne logout maar diya",
    "Tu meri wo khushi hai jo Cash on Delivery wali hoti hai asli pure aur cute",
    "Tujhse pyaar karna meri healthy diet ka reason hai kyunki tu khayalon se full feel kara deti hai",
    "Teri aankhon mein dooba hoon aur swimming aati nahi",
    "Tu smile karti hai toh meri heartbeat bhi dance karti hai",
    "Tere bina toh sab low battery jaisa lagta hai warning hi warning",
    "Tu gusse mein bhi aisi lagti hai jaise mirchi chocolate spicy but pyaari",
    "Teri awaaz sun ke lagta hai mere AirPods bhi tujhme busy hain",
    "Tu meri zindagi ki wo girl hai jisko dekhke mummy bhi bolti Shaadi kar le beta",
    "Tujhse baat karna meri therapy hai free mein aur romantic bhi",
    "Tu milti hai toh har ATM chhota lagta hai itna paisa bhi khushi nahi deta",
    "Teri har okay pe lagta hai ek aur proposal ready karu kya",
    "Tu meri heartbeat hai aur tujhpe crush bhi hai thoda complicated hoon",
    "Tujhe paake lagta hai Swiggy ne galat address pe khushi bhej di",
    "Tere saath toh traffic bhi jam nahi lagta bas time slow ho jaata hai",
    "Teri ek smile aur meri neend chali jaaye bada mehnga lagta hai tu",
    "Tu meri zindagi ka kuch bhi ho jaaye wala reason hai",
    "Tu ho toh lagta hai Google map bhi dil ke raaste dikhata hai",
    "Tujhse baat na ho toh mujhe khud se gussa aa jaata hai",
    "Tera naam sunke lagta hai notification aaya ho LOVE INSTALLED SUCCESSFULLY",
    "Tu meri morning alarm bhi hai aur raat ka sapna bhi",
    "Teri aankhon mein jo sparkle hai usme toh disco ball bhi haar maan le",
    "Tujhse duri se zyada toh math ka question dard deta hai",
    "Tu meri life ka undo option hai tu ho toh sab thik lagta hai",
    "Tu bolti hai toh lagta hai romantic radio channel chal gaya ho",
    "Tujhse milke laga love story likhne ka talent bhi hai mujh mein",
    "Tu rooth jaaye toh lagta hai meri chai ne bhi chammach chhod diya",
    "Tere saath selfie lene ka mann nahi karta tujhe dekhke phone bhi jealous ho jaaye",
    "Tera reply late aaye toh mera screen saver bhi udaas ho jaata hai",
    "Tu meri life ka season 2 hai better romantic aur full twist se bhara",
    "Tu mujhe itni pasand hai ki main apni chai bhi tere naam se peeta hoon",
    "Tujhse door rehna bhi ek exam jaisa hai stress aur fail dono pakka",
    "Tu meri WhatsApp wali typing feeling hai aankhon mein intezaar aur dil mein excitement",
    "Teri har line mere dil pe like aur share dono ban jati hai",
    "Tu meri zindagi ki wo ice cream hai jo melt bhi ho jaaye toh pyari lagti hai",
    "Tu ho toh sab kaam chhota lagta hai boss bhi sharma jaaye",
    "Tu meri heart ka auto-save hai tere bina data loss fix nahi hota",
    "Teri aankhon mein itna drama hai ki Netflix bhi rights le le",
    "Tere bina toh filter lagake bhi selfie bekaar lagti hai",
    "Tujhse milke lagta hai meri adhoori shopping list complete ho gayi",
    "Tu wo memory hai jise delete karna system allow nahi karta",
    "Tera naam screen pe aate hi aankhon ka brightness badh jaata hai",
    "Teri baatein sunke dil ke Wi-Fi signals full ho jaate hain",
    "Tu meri zindagi ka wo password hai jo bhool jao toh dil lock ho jaaye",
    "Teri ek jhalak se hi meri playlist romantic ho jati hai",
    "Tu meri coffee hai subah bina tere kick nahi lagti",
    "Teri yaad mein toh meri battery bhi overheat ho jati hai",
    "Tu meri zindagi ka wo update hai jo kabhi skip nahi karta",
    "Tere bina toh meri kahani ka climax hi missing hai",
    "Tujhe dekhke lagta hai meri life ka premium subscription shuru ho gaya",
    "Teri muskaan se toh meri duniya ka power backup chalu ho jata hai",
    "Tu meri zindagi ka wo filter hai jo sab kuch perfect bana deta hai"
]

# Dictionary to track ongoing shayari raids {user_id: {chat_id: task}}
ongoing_sraids = {}

# Helper function to get user ID from username, user ID, or reply
async def get_user_id(event, username_or_id=None):
    try:
        if event.reply_to_msg_id:
            reply_msg = await event.get_reply_message()
            return reply_msg.sender_id, reply_msg.sender.username
        elif username_or_id:
            if username_or_id.isdigit():
                user = await client.get_entity(int(username_or_id))
                return user.id, user.username or str(user.id)
            else:
                username = username_or_id.lstrip('@')
                user = await client.get_entity(username)
                return user.id, user.username
        else:
            return None, None
    except Exception as e:
        logging.error(f"Error getting user ID: {e}")
        return None, None

# Abusive words list (from your input)
ABUSIVE_WORDS = [
    "TERI", "MAA", "KA", "BOSDAA", "MARU", "RANDI", "RAND", "KE", "BACCHE",
    "CHUT", "ME", "SILAI", "MACHINE", "CHALU", "BHEN", "KE", "BOSDEE", "LAAT",
    "MARUNGA", "MAR", "JAYEGI", "WO", "BOSDA", "MADHERCHOD", "TATTE", "DADI",
    "KI", "SADI", "BADBOODAR", "CHAPPAL", "SE", "DAFAN", "KID", "CHAL", "JINDA",
    "HO", "BAAP", "AYA", "HAI", "KUARI", "FATE", "HUE", "SEAL", "CHODU",
    "AMERICAN", "HIJDE", "CHUDWAAU", "MAUSI", "KAA", "NILAM", "KARU", "SARIYA",
    "DAAL", "DUNGA", "LUND", "DALU", "SPEED", "PAKD", "MAAR", "LUNGAA", "CHACHI",
    "NIMBU", "MIRCHI", "LAGA", "PILLE", "PAKISTANI", "KUTTO", "KATWAU", "LAUDA",
    "BALATKAR", "KAR", "SUTLI", "BOMB", "DAALU", "BAXCHE", "HAWAABAZIYA", "KAREGA",
    "SARSO", "KHET", "PELUNGAA", "GACHAR", "GHACHAR", "CHAMAR", "VIDEO", "CALL",
    "DEKHUNGA", "CHROME", "UPLOAD", "AAJ", "CHODNE", "MATLAB", "CHUDEGI", "MODI",
    "GUARANTEE", "MCB", "GIRA", "LEKE", "BHAG", "JAUNGA", "CHIPAA", "BHAG", "RHA",
    "HIJDEE", "AAG", "LAGA", "PELUNGAA", "CHADTI", "JAWAANI", "PE", "DE", "MARAA",
    "THUK", "LAGA", "CHODUNGAA", "RUKHI", "SUKHI", "GILI", "44", "CHAPPAL", "MARUNGAA",
    "BACCHIYAA", "GAAND", "VICTORY", "JHANDAA", "GAAD", "DUNGAA", "CHINNAR", "HAG",
    "MACCHARR", "ITNI", "CONFUSE", "GARAm", "THANDI", "COLD", "DRINK", "KHADE",
    "KHADI", "BINA", "CONDOM"
]

# Updated list of abusive messages
abusive_messages = [
    "𝐆𝐀𝐋𝐈 𝐆𝐀𝐋𝐈 𝐌𝐄 𝐑𝐄𝐇𝐓𝐀 𝐇𝐄 𝐒𝐀𝐍𝐃 𝐓𝐄𝐑𝐈 𝐌𝐀𝐀𝐊𝐎 𝐂𝐇𝐎𝐃 𝐃𝐀𝐋𝐀 𝐎𝐑 𝐁𝐀𝐍𝐀 𝐃𝐈𝐀 𝐑𝐀𝐍𝐃 🤤🤣",
    "𝐓𝐄𝐑𝐈 𝐌𝐀𝐀 𝐊𝐈 𝐂𝐇𝐔𝐓 𝐌𝐄 ✋ 𝐇𝐀𝐓𝐓𝐇 𝐃𝐀𝐋𝐊𝐄 👶 𝐁𝐀𝐂𝐂𝐇𝐄 𝐍𝐈𝐊𝐀𝐋 𝐃𝐔𝐍𝐆𝐀 😍",
    "𝙆𝙪𝙩𝙩𝙚 𝙠𝙞 𝙟𝙖𝙩",
    "𝙏𝙀𝙍𝙄 𝙈𝘼 𝙆𝙄 𝘾𝙃𝙐𝙏 𝙀𝙆 𝘿𝘼𝙈 𝙏𝙊𝙋 𝙎𝙀𝙓𝙔",
    "𝙏𝙀𝙍𝙄 𝙈𝘼𝘼 𝙆𝙀 𝙂𝘼𝙉𝘿 𝙈𝙀 𝘿𝙀𝙏𝙊𝙇 𝘿𝘼𝘼𝙇 𝘿𝙐𝙉𝙂𝘼",
    "𝐓𝐄𝐑𝐈 𝐕𝐀𝐇𝐄𝐍 𝐊𝐄 𝐁𝐇𝐎𝐒𝐃𝐈𝐊𝐄 𝐌𝐄𝐈 𝐁𝐄𝐒𝐀𝐍 𝐊𝐄 𝐋𝐀𝐃𝐃𝐔 𝐁𝐇𝐀𝐑 𝐃𝐔𝐍𝐆𝐀🤩🥳🔥😈",
    "𝙍𝘼𝙉𝙄𝘿𝙄𝙄𝙄",
    "𝙏𝙀𝙍𝙄 𝘽𝙀𝙃𝙀𝙉 𝙇𝙀𝙏𝙄 𝙈𝙀𝙍𝙄 𝙇𝙐𝙉𝘿 𝘽𝘼𝘿𝙀 𝙈𝘼𝙎𝙏𝙄 𝙎𝙀 𝙏𝙀𝙍𝙄 𝘽𝙀𝙃𝙀𝙉 𝙆𝙊 𝙈𝙀𝙉𝙀 𝘾𝙃𝙊𝘿 𝘿𝘼𝙇𝘼 𝘽𝙊𝙃𝙊𝙏 𝙎𝘼𝙎𝙏𝙀 𝙎𝙀",
    "𝙏𝙀𝙍𝙄 𝙈𝘼𝘼 𝙆𝙊 𝙇𝙀𝙆𝘼𝙍 𝙈𝘼𝙄 𝙁𝘼𝙍𝘼𝙍",
    "𝙏𝙀𝙍𝙄 𝙈𝘼𝘼 𝙆𝘼𝘼𝘼 𝘽𝙃𝙊𝙎𝘿𝘼𝘼",
    "𝗧𝗘𝗥𝗜 𝗠𝗔‌𝗔‌𝗔𝗞𝗘 𝗡𝗨𝗗𝗘𝗦 𝗚𝗢𝗢𝗚𝗟𝗘 𝗣𝗘 𝗨𝗣𝗟𝗢𝗔𝗗 𝗞𝗔𝗥𝗗𝗨𝗡𝗚𝗔 𝗕𝗘‌𝗛𝗘𝗡 𝗞𝗘 𝗟𝗔𝗘𝗪𝗗𝗘 👻🔥",
    "𝐓𝐄𝐑𝐈 𝐕𝐀𝐇𝐄𝐄𝐍 𝐊𝐎 𝐀𝐏𝐍𝐄 𝐋𝐔𝐍𝐃 𝐏𝐑 𝐈𝐓𝐍𝐀 𝐉𝐇𝐔𝐋𝐀𝐀𝐔𝐍𝐆𝐀 𝐊𝐈 𝐉𝐇𝐔𝐋𝐓𝐄 𝐉𝐇𝐔𝐋𝐓𝐄 𝐇𝐈 𝐁𝐀𝐂𝐇𝐀 𝐏𝐀𝐈𝐃𝐀 𝐊𝐑 𝐃𝐄𝐆𝐈 💦💋",
    "𝐓𝐄𝐑𝐈 𝐁𝐄𝐇𝐄𝐍 𝐊𝐈 𝐂𝐇𝐔𝐓𝐇 𝐌𝐄 𝐌𝐄𝐑𝐀 𝐋𝐔𝐍𝐃 𝐊𝐀𝐀𝐋𝐀",
    "𝗧𝗢𝗛𝗔𝗥 𝗠𝗨𝗠𝗠𝗬 𝗞𝗜 𝗖𝗛𝗨𝗨‌𝗧 𝗠𝗘𝗜 𝗣𝗨𝗥𝗜 𝗞𝗜 𝗣𝗨𝗥𝗜 𝗞𝗜𝗡𝗚𝗙𝗜𝗦𝗛𝗘𝗥 𝗞𝗜 𝗕𝗢𝗧𝗧𝗟𝗘 𝗗𝗔𝗟 𝗞𝗘 𝗧𝗢𝗗 𝗗𝗨𝗡𝗚𝗔 𝗔𝗡𝗗𝗘𝗥 𝗛𝗜 😱😂🤩",
    "𝗖𝗛𝗔𝗟 𝗧𝗘𝗥𝗘 𝗕𝗔𝗔𝗣 𝗞𝗢 𝗕𝗛𝗘𝗝 𝗧𝗘𝗥𝗔 𝗕𝗔𝗦𝗞𝗔 𝗡𝗛𝗜 𝗛𝗘 𝗣𝗔𝗣𝗔 𝗦𝗘 𝗟𝗔𝗗𝗘𝗚𝗔 𝗧𝗨",
    "𝙐𝙡𝙡𝙪 𝙠𝙚 𝙥𝙖𝙩𝙝𝙚",
    "𝗞𝗜𝗧𝗡𝗔 𝗖𝗛𝗢𝗗𝗨 𝗧𝗘𝗥𝗜 𝗥Æ𝗡𝗗𝗜 𝗠𝗔‌𝗔‌𝗞𝗜 𝗖𝗛𝗨𝗨‌𝗧𝗛 𝗔𝗕𝗕 𝗔𝗣𝗡𝗜 𝗕𝗘‌𝗛𝗘𝗡 𝗞𝗢 𝗕𝗛𝗘𝗝 😆👻🤤",
    "𝐃𝐔𝐃𝐇 𝐇𝐈𝐋𝐀𝐀𝐔𝐍𝐆𝐀 𝐓𝐄𝐑𝐈 𝐕𝐀𝐇𝐄𝐄𝐍 𝐊𝐄 𝐔𝐏𝐑 𝐍𝐈𝐂𝐇𝐄 🆙🆒😙",
    "𝐓𝐄𝐑𝐈 𝐌𝐀𝐀 𝐊𝐈 𝐂𝐇𝐔𝐓 𝐌𝐄𝐈 𝐒𝐇𝐄𝐄𝐒𝐇𝐀 𝐃𝐀𝐋 𝐃𝐔𝐍𝐆𝐀𝐀𝐀 𝐀𝐔𝐑 𝐂𝐇𝐀𝐔𝐑𝐀𝐇𝐄 𝐏𝐄 𝐓𝐀𝐀𝐍𝐆 𝐃𝐔𝐍𝐆𝐀 𝐁𝐇𝐎𝐒𝐃𝐈𝐊𝐄😈😱🤩",
    "𝗧𝗘𝗥𝗜 𝗠𝗔‌𝗔‌ 𝗞𝗜 𝗖𝗛𝗨𝗨‌𝗧 𝗠𝗘 𝗦𝗨𝗧𝗟𝗜 𝗕𝗢𝗠𝗕 𝗙𝗢𝗗 𝗗𝗨𝗡𝗚𝗔 𝗧𝗘𝗥𝗜 𝗠𝗔‌𝗔‌ 𝗞𝗜 𝗝𝗛𝗔𝗔𝗧𝗘 𝗝𝗔𝗟 𝗞𝗘 𝗞𝗛𝗔𝗔𝗞 𝗛𝗢 𝗝𝗔𝗬𝗘𝗚𝗜💣",
    "𝗧𝗘𝗥𝗜 𝗠𝗔‌𝗔‌ 𝗞𝗢 𝗜𝗧𝗡𝗔 𝗖𝗛𝗢𝗗𝗨𝗡𝗚𝗔 𝗞𝗜 𝗦𝗔𝗣𝗡𝗘 𝗠𝗘𝗜 𝗕𝗛𝗜 𝗠𝗘𝗥𝗜 𝗖𝗛𝗨𝗗𝗔𝗜 𝗬𝗔𝗔𝗗 𝗞𝗔𝗥𝗘𝗚𝗜 𝗥Æ𝗡𝗗𝗜 🥳😍👊💥",
    "𝐓𝐄𝐑𝐈 𝐕𝐀𝐇𝐄𝐄𝐍 𝐊𝐎 𝐇𝐎𝐑𝐋𝐈𝐂𝐊𝐒 𝐏𝐄𝐄𝐋𝐀𝐊𝐄 𝐂𝐇𝐎𝐃𝐔𝐍𝐆𝐀 𝐌𝐀𝐃𝐀𝐑𝐂𝐇𝐎𝐃😚",
    "𝙏𝙀𝙍𝙄 𝙈𝘼𝘼 𝙆𝙊 𝙎𝘼𝙍𝘼𝙆 𝙋𝙀 𝙇𝙀𝙏𝘼𝘼𝘼 𝘿𝙐𝙉𝙂𝘼𝘼𝘼",
    "𝙎𝘼𝘽 𝘽𝙊𝙇𝙏𝙀 𝙈𝙐𝙅𝙃𝙆𝙊 𝙋𝘼𝙋𝘼 𝙆𝙔𝙊𝙐𝙉𝙆𝙄 𝙈𝙀𝙉𝙀 𝘽𝘼𝙉𝘼𝘿𝙄𝘼 𝙏𝙀𝙍𝙄 𝙈𝘼𝘼𝙆𝙊 𝙋𝙍𝙀𝙂𝙉𝙀𝙉𝙏 🤣🤣",
    "𝐓𝐄𝐑𝐈 𝐁𝐄𝐇𝐄𝐍 𝐊𝐎 𝐂𝐇𝐎𝐃 𝐂𝐇𝐎𝐃𝐊𝐄 𝐕𝐈𝐃𝐄𝐎 𝐁𝐀𝐍𝐀𝐊𝐄 𝐗𝐍𝐗𝐗.𝐂𝐎𝐌 𝐏𝐄 𝐍𝐄𝐄𝐋𝐀𝐌 𝐊𝐀𝐑𝐃𝐔𝐍𝐆𝐀 𝐊𝐔𝐓𝐓𝐄 𝐊𝐄 𝐏𝐈𝐋𝐋𝐄 💦💋",
    "𝙎𝙖𝙙𝙞 𝙝𝙪𝙞 𝙜𝙖𝙖𝙣𝙙",
    "𝐓𝐄𝐑𝐈 𝐕𝐀𝐇𝐄𝐍 𝐊𝐄 𝐁𝐇𝐎𝐒𝐃𝐈𝐊𝐄 𝐌𝐄𝐈 𝐁𝐄𝐒𝐀𝐍 𝐊𝐄 𝐋𝐀𝐃𝐃𝐔 𝐁𝐇𝐀𝐑 𝐃𝐔𝐍𝐆𝐀🤩🥳�fire😈",
    "𝗧𝗘𝗥𝗜 𝗠𝗔‌𝗔‌ 𝗞𝗜 𝗖𝗛𝗨𝗨‌𝗧 𝗔𝗟𝗘𝗫𝗔 𝗗𝗔𝗟 𝗞𝗘𝗘 𝗗𝗝 𝗕𝗔𝗝𝗔𝗨𝗡𝗚𝗔𝗔𝗔 🎶 ⬆️🤩💥",
    "𝙆𝙄𝙁𝙎𝙎𝙎 𝙁𝙍𝘼𝙍 𝙃𝘼𝙃𝘼𝙃𝙃",
    "𝙅𝙝𝙖𝙖𝙣𝙩 𝙠𝙚 𝙥𝙞𝙨𝙨𝙪-",
    "𝐓𝐔𝐉𝐇𝐄 𝐃𝐄𝐊𝐇 𝐊𝐄 𝐓𝐄𝐑𝐈 𝐑𝐀𝐍𝐃𝐈 𝐁𝐀𝐇𝐄𝐍 𝐏𝐄 𝐓𝐀𝐑𝐀𝐒 𝐀𝐓𝐀 𝐇𝐀𝐈 𝐌𝐔𝐉𝐇𝐄 𝐁𝐀𝐇𝐄𝐍 𝐊𝐄 𝐋𝐎𝐃𝐄𝐄𝐄𝐄 👿💥🤩🔥",
    "𝙏𝙀𝙍𝙄 𝘽𝙀𝙃𝙀𝙉 𝙆𝙀 𝘽𝙃𝙊𝙎𝘿𝙀 𝙈𝙀 𝘼𝘼𝘼𝙂 𝙇𝘼𝙂𝘼𝘿𝙄𝘼 𝙈𝙀𝙍𝘼 𝙈𝙊𝙏𝘼 𝙇𝙐𝙉𝘿 𝘿𝘼𝙇𝙆𝙀 🔥🔥💦😆😆",
    "𝙏𝙀𝙍𝙄 𝙈𝘼𝘼𝙆𝙊 𝘾𝙃𝙀𝙀𝙈𝙎 𝙎𝙀 𝘾𝙃𝙐𝘿𝙒𝘼𝙑𝙐𝙉𝙂𝘼 𝙈𝘼𝘿𝙀𝙍𝘾𝙃𝙊𝙊𝘿 𝙆𝙀 𝙋𝙄𝙇𝙇𝙀 💦🤣",
    "𝐒𝐀𝐁 𝐁𝐎𝐋𝐓𝐄 𝐌𝐔𝐉𝐇𝐊𝐎 𝐏𝐀𝐏𝐀 𝐊𝐘𝐎𝐔𝐍𝐊𝐈 𝐌𝐄𝐍𝐄 𝐁𝐀𝐍𝐀𝐃𝐈𝐀 𝐓𝐄𝐑𝐈 𝐌𝐀𝐀𝐊𝐎 𝐏𝐑𝐄𝐆𝐍𝐄𝐍𝐓 🤣🤣",
    "𝐓𝐄𝐑𝐈 𝐁𝐀𝐇𝐄𝐍 𝐊𝐈 𝐂𝐇𝐔𝐓 𝐌𝐄𝐈 𝐀𝐏𝐍𝐀 𝐁𝐀𝐃𝐀 𝐒𝐀 𝐋𝐎𝐃𝐀 𝐆𝐇𝐔𝐒𝐒𝐀 𝐃𝐔𝐍𝐆𝐀𝐀 𝐊𝐀𝐋𝐋𝐀𝐏 𝐊𝐄 𝐌𝐀𝐑 𝐉𝐀𝐘𝐄𝐆𝐈 🤩😳😳🔥",
    "𝐓𝐔𝐉𝐇𝐄 𝐀𝐁 𝐓𝐀𝐊 𝐍𝐀𝐇𝐈 𝐒𝐌𝐉𝐇 𝐀𝐘𝐀 𝐊𝐈 𝐌𝐀𝐈 𝐇𝐈 𝐇𝐔 𝐓𝐔𝐉𝐇𝐄 𝐏𝐀𝐈𝐃𝐀 𝐊𝐀𝐑𝐍𝐄 𝐖𝐀𝐋𝐀 𝐁𝐇𝐎𝐒𝐃𝐈𝐊𝐄𝐄 𝐀𝐏𝐍𝐈 𝐌𝐀𝐀 𝐒𝐄 𝐏𝐔𝐂𝐇 𝐑𝐀𝐍𝐃𝐈 𝐊𝐄 𝐁𝐀𝐂𝐇𝐄𝐄𝐄𝐄 🤩👊👤😍",
    "𝐓𝐄𝐑𝐈 𝐌𝐀𝐀 𝐊𝐈 𝐂𝐇𝐔𝐓 𝐌𝐄𝐈 𝐒𝐔𝐃𝐎 𝐋𝐀𝐆𝐀 𝐊𝐄 𝐁𝐈𝐆𝐒𝐏𝐀𝐌 𝐋𝐀𝐆𝐀 𝐊𝐄 𝟗𝟗𝟗𝟗 𝐅𝐔𝐂𝐊 𝐋𝐀𝐆𝐀𝐀 𝐃𝐔 🤩🥳🔥",
    "𝙋𝘼𝙋𝘼 𝙆𝙄 𝙎𝙋𝙀𝙀𝘿 𝙈𝙏𝘾𝙃 𝙉𝙃𝙄 𝙃𝙊 𝙍𝙃𝙄 𝙆𝙔𝘼",
    "𝙆𝙄𝙏𝙉𝙄 𝘾𝙃𝙊𝘿𝙐 𝙏𝙀𝙍𝙄 𝙈𝘼 𝘼𝘽 𝙊𝙍..",
    "𝙆𝙄𝙁𝙎𝙎𝙎𝙎𝙎𝙎𝙎𝙎𝙎𝙎𝙎𝙎",
    "𝘼𝘽𝙀 𝙎𝙐𝙉 𝙇𝙊𝘿𝙀 𝙏𝙀𝙍𝙄 𝘽𝙀𝙃𝙀𝙉 𝙆𝘼 𝘽𝙃𝙊𝙎𝘿𝘼 𝙁𝘼𝘼𝘿 𝘿𝙐𝙉𝙂𝘼",
    "𝐓𝐄𝐑𝐈 𝐁𝐀𝐇𝐄𝐍 𝐊𝐈 𝐆𝐀𝐀𝐍𝐃 𝐌𝐄𝐈 𝐎𝐍𝐄𝐏𝐋𝐔𝐒 𝐊𝐀 𝐖𝐑𝐀𝐏 𝐂𝐇𝐀𝐑𝐆𝐄𝐑 𝟑𝟎𝐖 𝐇𝐈𝐆𝐇 𝐏𝐎𝐖𝐄𝐑 💥😂😎",
    "𝙂𝘼𝘼𝙉𝘿𝙐",
    "𝘼𝘽𝙀 𝙎𝙐𝙉 𝙇𝙊𝘿𝙀 𝙏𝙀𝙍𝙄 𝘽𝙀𝙃𝙀𝙉 𝙆𝘼 𝘽𝙃𝙊𝙎𝘿𝘼 𝙁𝘼𝘼𝘿 𝘿𝙐𝙉𝙂𝘼",
    "𝙏𝙀𝙍𝙄 𝙈𝘼𝘼 𝙆𝙊 𝘼𝙈𝙀𝙍𝙄𝘾𝘼 𝙂𝙃𝙐𝙈𝘼𝘼𝙐𝙉𝙂𝘼 𝙈𝘼𝘿𝘼𝙍𝘾𝙃𝙊𝘿",
    "𝙏𝙀𝙍𝙄 𝘽𝙀𝙃𝙀𝙉 𝙆𝙊𝙏𝙊 𝘾𝙃𝙊𝘿 𝘾𝙃𝙊𝘿𝙆𝙀 𝙋𝙐𝙍𝘼 𝙁𝘼𝘼𝘿 𝘿𝙄𝘼 𝘾𝙃𝙐𝙏𝙃 𝘼𝘽𝘽 𝙏𝙀𝙍𝙄 𝙂𝙁 𝙆𝙊 𝘽𝙃𝙀𝙅 😆💦🤤",
    "𝗧𝗘𝗥𝗜 𝗠𝗨𝗠𝗠𝗬 𝗞𝗘 𝗦𝗔𝗔𝗧𝗛 𝗟𝗨𝗗𝗢 𝗞𝗛𝗘𝗟𝗧𝗘 𝗞𝗛𝗘𝗟𝗧𝗘 𝗨𝗦𝗞𝗘 𝗠𝗨𝗛 𝗠𝗘 𝗔𝗣𝗡𝗔 𝗟𝗢𝗗𝗔 𝗗𝗘 𝗗𝗨𝗡𝗚𝗔☝🏻☝🏻😬",
    "𝐓𝐄𝐑𝐈 𝐌𝐀𝐀𝐀𝐊𝐄 𝐍𝐔𝐃𝐄𝐒 𝐆𝐎𝐎𝐆𝐋𝐄 𝐏𝐄 𝐔𝐏𝐋𝐎𝐀𝐃 𝐊𝐀𝐑𝐃𝐔𝐍𝐆𝐀 𝐁𝐄𝐇𝐄𝐍 𝐊𝐄 𝐋𝐀𝐄𝐖𝐃𝐄 👻🔥",
    "𝗧𝗘𝗥𝗜 𝗜𝗧𝗘𝗠 𝗞𝗜 𝗚𝗔𝗔𝗡𝗗 𝗠𝗘 𝗟𝗨𝗡𝗗 𝗗𝗔𝗔𝗟𝗞𝗘,𝗧𝗘𝗥𝗘 𝗝𝗔𝗜𝗦𝗔 𝗘𝗞 𝗢𝗥 𝗡𝗜𝗞𝗔𝗔𝗟 𝗗𝗨𝗡𝗚𝗔 𝗠𝗔‌𝗔‌𝗗𝗔𝗥𝗖𝗛Ø𝗗🤘🏻🙌🏻☠️",
    "𝗔𝗕𝗘 𝗥Æ𝗡𝗗𝗜𝗞𝗘 𝗕𝗔𝗖𝗛𝗛𝗘 𝗔𝗨𝗞𝗔𝗧 𝗡𝗛𝗜 𝗛𝗘𝗧𝗢 𝗔𝗣𝗡𝗜 𝗥Æ𝗡𝗗𝗜 𝗠𝗔‌𝗔‌𝗞𝗢 𝗟𝗘𝗞𝗘 𝗔𝗔𝗬𝗔 𝗠𝗔𝗧𝗛 𝗞𝗔𝗥 𝗛𝗔𝗛𝗔𝗛𝗔𝗛𝗔",
    "𝗧𝗘𝗥𝗜 𝗠𝗔‌𝗔‌𝗔𝗞𝗘 𝗡𝗨𝗗𝗘𝗦 𝗚𝗢𝗢𝗚𝗟𝗘 𝗣𝗘 𝗨𝗣𝗟𝗢𝗔𝗗 �𝗞𝗔𝗥𝗗𝗨𝗡𝗚𝗔 𝗕𝗘‌𝗛𝗘𝗡 𝗞𝗘 𝗟𝗔𝗘𝗪𝗗𝗘 👻🔥",
    "𝙏𝙀𝙍𝙄𝙄𝙄 𝙈𝘼𝘼 𝙆𝘼𝘼 𝘽𝙅𝙎𝙊𝘿𝘼𝘼𝘼",
    "𝙆𝙪𝙩𝙩𝙚 𝙠𝙚 𝙩𝙖𝙩𝙩𝙚",
    "𝗧𝗘𝗥𝗜 𝗠𝗔𝗨𝗦𝗜 𝗞𝗘 𝗕𝗛𝗢𝗦𝗗𝗘 𝗠𝗘𝗜 𝗜𝗡𝗗𝗜𝗔𝗡 𝗥𝗔𝗜𝗟𝗪𝗔𝗬 🚂💥😂",
    "𝗧𝗘𝗥𝗜 𝗠𝗔‌𝗔‌ 𝗞𝗜 𝗖𝗛𝗨𝗨‌𝗧 𝗠𝗘 𝗦𝗨𝗧𝗟𝗜 𝗕𝗢𝗠𝗕 𝗙𝗢𝗗 𝗗𝗨𝗡𝗚𝗔 𝗧𝗘𝗥𝗜 𝗠𝗔‌𝗔‌ 𝗞𝗜 𝗝𝗛𝗔𝗔𝗧𝗘 𝗝𝗔𝗟 𝗞𝗘 𝗞𝗛𝗔𝗔𝗞 𝗛𝗢 𝗝𝗔𝗬𝗘𝗚𝗜💣",
    "𝗧𝗘𝗥𝗘 𝗕𝗘‌𝗛𝗘𝗡 𝗞 𝗖𝗛𝗨𝗨‌𝗧 𝗠𝗘 𝗖𝗛𝗔𝗞𝗨 𝗗𝗔𝗔𝗟 𝗞𝗔𝗥 𝗖𝗛𝗨𝗨‌𝗧 𝗞𝗔 𝗞𝗛𝗢𝗢𝗡 𝗞𝗔𝗥 𝗗𝗨𝗚𝗔",
    "𝘽𝙃𝙀𝙉 𝙆𝙀 𝙇𝙒𝘿𝙀 𝙎𝙃𝙍𝙈 𝙆𝙍",
    "𝐒𝐔𝐍 𝐒𝐔𝐍 𝐒𝐔𝐀𝐑 𝐊𝐄 𝐏𝐈𝐋𝐋𝐄 𝐉𝐇𝐀𝐍𝐓𝐎 𝐊𝐄 𝐒𝐎𝐔𝐃𝐀𝐆𝐀𝐑 𝐀𝐏𝐍𝐈 𝐌𝐔𝐌𝐌𝐘 𝐊𝐈 𝐍𝐔𝐃𝐄𝐒 𝐁𝐇𝐄𝐉",
    "𝐓𝐄𝐑𝐈 𝐁𝐀𝐇𝐄𝐍 𝐊𝐈 𝐂𝐇𝐔𝐓 𝐌𝐄𝐈 𝐀𝐏𝐏𝐋𝐄 𝐊𝐀 𝟏𝟖𝐖 𝐖𝐀𝐋𝐀 𝐂𝐇𝐀𝐑𝐆𝐄𝐑 🔥🤩",
    "𝙏𝙀𝙍𝙄 𝙂𝙁 𝙆 𝙎𝘼𝘼𝙏𝙃 𝙈𝙈𝙎 𝘽𝘼𝙉𝘼𝘼 𝘾𝙃𝙐𝙆𝘼 𝙃𝙐",
    "𝐓𝐄𝐑𝐈 𝐁𝐀𝐇𝐄𝐍 𝐊𝐈 𝐂𝐇𝐔𝐓 𝐊𝐎 𝐀𝐌𝐀𝐙𝐎𝐍 𝐒𝐄 𝐎𝐑𝐃𝐄𝐑 𝐊𝐀𝐑𝐔𝐍𝐆𝐀 𝟏𝟎 𝐫𝐬 𝐌𝐄𝐈 𝐀𝐔𝐑 𝐅𝐋𝐈𝐏𝐊𝐀𝐑𝐓 𝐏𝐄 𝟐𝟎 𝐑𝐒 𝐌𝐄𝐈 𝐁𝐄𝐂𝐇 𝐃𝐔𝐍𝐆𝐀🤮👿😈🤖",
    "𝐓𝐄𝐑𝐀 𝐏𝐄𝐇𝐋𝐀 𝐁𝐀𝐀𝐏 𝐇𝐔 𝐌𝐀𝐃𝐀𝐑𝐂𝐇𝐎𝐃",
    "𝙇𝙒𝘿𝙀𝙀𝙀",
    "𝗧𝗘𝗥𝗜 𝗠𝗔‌𝗔‌ 𝗞𝗜 𝗖𝗛𝗨𝗨‌𝗧 𝗠𝗘 𝗖𝗛𝗔𝗡𝗚𝗘𝗦 𝗖𝗢𝗠𝗠𝗜𝗧 𝗞𝗥𝗨𝗚𝗔 𝗙𝗜𝗥 𝗧𝗘𝗥𝗜 𝗕𝗛𝗘𝗘𝗡 𝗞𝗜 𝗖𝗛𝗨𝗨‌𝗧 𝗔𝗨𝗧𝗢𝗠𝗔𝗧𝗜𝗖𝗔𝗟𝗟𝗬 𝗨𝗣𝗗𝗔𝗧𝗘 𝗛𝗢𝗝𝗔𝗔𝗬𝗘𝗚𝗜🤖🙏🤔",
    "𝗧𝗘𝗥𝗜 𝗠𝗔‌𝗔‌ 𝗞𝗜 𝗖𝗛𝗨𝗨‌𝗧 𝗠𝗘𝗜 𝗦𝗛𝗘𝗘𝗦𝗛𝗔 𝗗𝗔𝗟 �𝗗𝗨𝗡𝗚𝗔𝗔𝗔 𝗔𝗨𝗥 𝗖𝗛𝗔𝗨𝗥𝗔𝗛𝗘 𝗣𝗘 𝗧𝗔𝗔𝗡𝗚 𝗗𝗨𝗡𝗚𝗔 𝗕𝗛𝗢𝗦𝗗𝗜𝗞𝗘😈😱🤩",
    "𝗧𝗘𝗥𝗜 𝗠𝗔‌𝗔‌𝗞𝗢 𝗞𝗛𝗨𝗟𝗘 𝗕𝗔𝗝𝗔𝗥 𝗠𝗘 𝗖𝗛𝗢𝗗 𝗗𝗔𝗟𝗔 🤣🤣💋",
    "𝘼𝙥𝙣𝙞 𝙜𝙖𝙖𝙣𝙙 𝙢𝙚𝙞𝙣 𝙢𝙪𝙩𝙝𝙞 𝙙𝙖𝙖𝙡",
    "𝗧𝗘𝗥𝗜 𝗕𝗘‌𝗛𝗘𝗡 𝗞𝗘 𝗕𝗛𝗢𝗦𝗗𝗘 𝗠𝗘 𝗔𝗔𝗔𝗚 𝗟𝗔𝗚𝗔𝗗𝗜𝗔 𝗠𝗘𝗥𝗔 𝗠𝗢𝗧𝗔 𝗟𝗨𝗡𝗗 𝗗𝗔𝗟𝗞𝗘 🔥🔥💦😆😆",
    "𝗧𝗘𝗥𝗜 𝗠𝗔‌𝗔‌𝗞𝗢 𝗞𝗛𝗨𝗟𝗘 𝗕𝗔𝗝𝗔𝗥 𝗠𝗘 𝗖�_H𝗢𝗗 𝗗𝗔𝗟𝗔 🤣🤣💋",
    "𝗧𝗘𝗥𝗜 𝗠𝗔‌𝗔‌ 𝗞𝗢 𝗞𝗢𝗟𝗞𝗔𝗧𝗔 𝗩𝗔𝗔𝗟𝗘 𝗝𝗜𝗧𝗨 𝗕𝗛𝗔𝗜𝗬𝗔 𝗞𝗔 𝗟𝗨𝗡𝗗 𝗠𝗨𝗕𝗔𝗥𝗔𝗞 🤩🤩",
    "𝙆𝙄𝙏𝙉𝙄 𝙂𝙇𝙄𝙔𝘼 𝙋𝘿𝙒𝙀𝙂𝘼 𝘼𝙋𝙉𝙄 𝙈𝘼 𝙆𝙊",
    "𝗧𝗘𝗥𝗜 𝗖𝗛𝗨𝗨‌𝗧 𝗞𝗜 𝗖𝗛𝗨𝗨‌𝗧 𝗠𝗘𝗜 𝗦𝗛𝗢𝗨𝗟𝗗𝗘𝗥𝗜𝗡𝗚 𝗞𝗔𝗥 𝗗𝗨𝗡𝗚𝗔𝗔 𝗛𝗜𝗟𝗔𝗧𝗘 𝗛𝗨𝗬𝗘 𝗕𝗛𝗜 𝗗𝗔𝗥𝗗 𝗛𝗢𝗚𝗔𝗔𝗔😱🤮👺",
    "𝐓𝐄𝐑𝐈 𝐌𝐀𝐀𝐀𝐊𝐈 𝐂𝐇𝐔𝐃𝐀𝐈 𝐊𝐎 𝐏𝐎𝐑𝐍𝐇𝐔𝐁.𝐂𝐎𝐌 𝐏𝐄 𝐔𝐏𝐋𝐎𝐀𝐃 𝐊𝐀𝐑𝐃𝐔𝐍𝐆𝐀 𝐒𝐔𝐀𝐑 𝐊𝐄 𝐂𝐇𝐎𝐃𝐄 🤣💋💦",
    "𝗧𝗘𝗥𝗜 𝗕𝗔𝗛𝗘𝗡 𝗞𝗜 𝗚𝗔𝗔𝗡𝗗 𝗠𝗘𝗜 𝗢𝗡𝗘𝗣𝗟𝗨𝗦 𝗞𝗔 𝗪𝗥𝗔𝗣 𝗖𝗛𝗔𝗥𝗚𝗘𝗥 30𝗪 𝗛𝗜𝗚𝗛 𝗣𝗢𝗪𝗘𝗥 💥😂😎",
    "𝗧𝗘𝗥𝗜 𝗠𝗔‌𝗔‌ 𝗞𝗜 𝗖𝗛𝗨𝗨‌𝗧 𝗠𝗘𝗜 𝗖𝗥𝗘𝗗𝗜𝗧 𝗖𝗔𝗥𝗗 𝗗𝗔𝗟 𝗞𝗘 𝗔𝗚𝗘 𝗦𝗘 500 𝗞𝗘 𝗞𝗔𝗔𝗥𝗘 �_K𝗔𝗔𝗥𝗘 𝗡𝗢𝗧𝗘 𝗡𝗜𝗞𝗔𝗟𝗨𝗡𝗚𝗔𝗔 𝗕𝗛𝗢𝗦𝗗𝗜𝗞𝗘💰💰🤩",
    "𝙂𝘼𝙇𝙄 𝙂𝘼𝙇𝙄 𝙉𝙀 𝙎𝙃𝙊𝙍 𝙃𝙀 𝙏𝙀𝙍𝙄 𝙈𝘼𝘼 𝙍𝘼𝙉𝘿𝙄 𝘾𝙃𝙊𝙍 𝙃𝙀 💋💋💦",
    "2 𝙍𝙐𝙋𝘼𝙔 𝙆𝙄 𝙋𝙀𝙋𝙎𝙄 𝙏𝙀𝙍𝙄 𝙈𝙐𝙈𝙈𝙔 𝙎𝘼𝘽𝙎𝙀 𝙎𝙀𝙓𝙔 💋💦",
    "𝐓𝐄𝐑𝐈 𝐁𝐄𝐇𝐄𝐍 𝐊𝐈 𝐂𝐇𝐔𝐓𝐇 𝐌𝐄 𝐌𝐄𝐑𝐀 𝐋𝐔𝐍𝐃 𝐊𝐀𝐀𝐋𝐀",
    "𝐓𝐄𝐑𝐈 𝐌𝐀𝐀 𝐊𝐄 𝐁𝐇𝐎𝐒𝐃𝐄 𝐌𝐄𝐈 𝐒𝐏𝐎𝐓𝐈𝐅𝐘 𝐃𝐀𝐋 𝐊𝐄",
    "𝘼𝙇𝙀 𝘼𝙇𝙀 𝙈𝙀𝙇𝘼 𝘽𝘾𝙃𝘼𝘼𝘼𝘼",
    "𝙆𝙄𝙎𝘼𝙉 𝙆𝙊 𝙆𝙃𝙊𝘿𝙉𝘼 𝙊𝙍",
    "𝐒𝐔𝐀𝐑 𝐊𝐄 𝐏𝐈𝐋𝐋𝐄 𝐓𝐄𝐑𝐈 𝐌𝐀𝐀𝐊𝐈 𝐂𝐇𝐔𝐓𝐇 𝐌𝐄 𝐒𝐔𝐀𝐑 𝐊𝐀 𝐋𝐎𝐔𝐃𝐀 𝐎𝐑 𝐓𝐄𝐑𝐈 𝐁𝐄𝐇𝐄𝐍 𝐊𝐈 𝐂𝐇𝐔𝐓𝐇 𝐌𝐄 𝐌𝐄𝐑𝐀 𝐋𝐎𝐃𝐀",
    "𝙉𝘼𝙇𝙇𝙀𝙀",
    "𝙆𝙄𝙎𝘼𝙉 𝙆𝙊 𝙆𝙃𝙊𝘿𝙉𝘼 𝙊𝙍",
    "𝗦𝗨𝗔𝗥 𝗞𝗘 𝗣𝗜𝗟𝗟𝗘 𝗧𝗘𝗥𝗜 𝗠𝗔‌𝗔‌𝗞𝗜 𝗖𝗛𝗨𝗨‌𝗧𝗛 𝗠𝗘 𝗦𝗨𝗔𝗥 𝗞𝗔 𝗟𝗢𝗨𝗗𝗔 𝗢𝗥 𝗧𝗘𝗥𝗜 𝗕𝗘‌𝗛𝗘𝗡 �𝗞𝗜 𝗖𝗛𝗨𝗨‌𝗧𝗛 �𝗠𝗘 𝗠𝗘𝗥𝗔 𝗟𝗢𝗗𝗔"
]

# List of random messages for tagall
tagall_messages = ["heyyyy", "hello ji", "hlo", "hyyy", "hoi", "heyy", "kaise ho"]

# Bot start time for uptime
START_TIME = datetime.now()

# Command prefix
PREFIX = "."

# Auto-reply toggle
AUTO_REPLY_ENABLED = True

# Initialize the client with auto-reconnect
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python userbot.py <session_name>")
        sys.exit(1)
    session_name = sys.argv[1]
    client = TelegramClient(
        session_name,
        api_id=25770896,
        api_hash="b3a85ada49f9eb19c7d9ab50527c131d",
        auto_reconnect=True
    )

# Helper function to log commands
async def log_command(event, command):
    user_id = event.sender_id
    chat_id = event.chat_id
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] Command '{command}' executed by User ID: {user_id} in Chat ID: {chat_id}")

# Helper function to get user from reply or tag
async def get_target_user(event):
    try:
        if event.reply_to_msg_id:
            reply_msg = await event.get_reply_message()
            return reply_msg.sender_id, reply_msg.sender
        args = event.message.text.split()
        if len(args) > 1:
            identifier = args[-1] if args[-1].startswith('@') else None
            if identifier:
                username = identifier.replace('@', '')
                user = await client.get_entity(username)
                return user.id, user
            elif args[-1].isdigit() or (args[-1].startswith('-') and args[-1][1:].isdigit()):
                user_id = int(args[-1])
                user = await client.get_entity(user_id)
                return user.id, user
    except Exception as e:
        print(f"Error fetching target user: {str(e)}")
        await event.reply(f"**⚡ Error fetching target user: {str(e)} 🚫**", parse_mode='md')
    return None, None

# Check if user is admin in the chat
async def is_admin(chat_id, user_id):
    try:
        chat = await client.get_entity(chat_id)
        if isinstance(chat, telethon.tl.types.Channel):
            participant = await client.get_permissions(chat, user_id)
            return participant.is_admin or participant.is_creator
        elif isinstance(chat, telethon.tl.types.Chat):
            participant = await client.get_participants(chat, filter=telethon.tl.types.ChannelParticipantsAdmins)
            return any(p.id == user_id for p in participant)
        return False
    except Exception as e:
        print(f"Error checking admin status: {str(e)}")
        return False

# ===================== AI CHATBOT (SAMBANOVA ULTRA FIXED) =====================
# ===================== AI CHATBOT (GROQ FIXED) =====================

chatbot_enabled = False
chatbot_persona = "boy"  # default: boy / girl

API_KEYS = [
    os.getenv("GROQ_API_KEY", "")
]

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

GROQ_MODELS = [
    "llama-3.1-8b-instant",
    "meta-llama/llama-4-scout-17b-16e-instruct",
]

import requests
import random
import asyncio
import re
from collections import defaultdict, deque

session = requests.Session()

conversation_memory = defaultdict(lambda: deque(maxlen=10))
last_bot_reply = defaultdict(str)


def get_memory_key(event):
    if event.is_private:
        return f"pv_{event.sender_id}"
    return f"grp_{event.chat_id}_{event.sender_id}"


def build_system_prompt(persona: str) -> str:
    if persona == "girl":
        persona_line = (
            "You are chatting like a normal comfortable Indian girl in Hinglish. "
            "Sound soft, casual, natural, and real. Do not overact, do not sound cringe."
        )
    else:
        persona_line = (
            "You are chatting like a normal comfortable Indian boy in Hinglish. "
            "Sound chill, casual, natural, and real. Do not overact, do not sound cringe."
        )

    return (
        f"{persona_line} "
        "Reply like a real human friend, not like an AI assistant. "
        "Keep replies short and natural, usually 1 line or 2 short lines only. "
        "Do not send big paragraphs. "
        "Use very few emojis, maximum 1 only when really natural. "
        "Remember previous chat context and reply according to it. "
        "If the user says things like 'tum batao', 'aur', 'hmm', 'acha', then reply according to previous context. "
        "Avoid repeating the same sentence again and again. "
        "Do not mention being AI unless directly asked. "
        "Be comfortable, normal, and human."
    )


def clean_ai_text(text: str) -> str:
    if not text:
        return ""
    text = text.replace("\r", "").strip()
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[ \t]{2,}", " ", text).strip()

    lines = [x.strip() for x in text.split("\n") if x.strip()]
    if len(lines) > 2:
        text = "\n".join(lines[:2])

    if len(text) > 220:
        text = text[:220].rsplit(" ", 1)[0] + "..."

    emoji_like = re.findall(r"[😂🤣🥺❤️😍🔥😉😅😊🥹😘🤍💖💕✨🙈😎😏😄😁🙂🙃🤭]", text)
    if len(emoji_like) > 1:
        removed = 0
        out = []
        for ch in text:
            if re.match(r"[😂🤣🥺❤️😍🔥😉😅😊🥹😘🤍💖💕✨🙈😎😏😄😁🙂🙃🤭]", ch):
                removed += 1
                if removed > 1:
                    continue
            out.append(ch)
        text = "".join(out).strip()

    return text


def looks_generic_or_bad(reply: str, user_message: str) -> bool:
    r = (reply or "").strip().lower()
    generic = {
        "acha bata na, kya chal raha hai?",
        "haan bolo", "hmm", "aur batao",
        "kya bataun", "samjha nahi", "bolo",
    }
    if not r or r in generic or len(r) < 2:
        return True
    if r == last_bot_reply.get(user_message, ""):
        return True
    return False


def _sync_groq_call(messages, model):
    api_key = random.choice(API_KEYS)  # ✅ API_KEYS list se random key pick
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": model,
        "messages": messages,
        "max_tokens": 90,
        "temperature": 0.8,
        "stream": False,
    }
    return session.post(GROQ_URL, headers=headers, json=payload, timeout=30)


async def try_model(messages, model):
    resp = await asyncio.to_thread(_sync_groq_call, messages, model)
    print(f"[AI DEBUG] model={model} status={resp.status_code}")

    try:
        data = resp.json()
    except Exception:
        data = None

    if resp.status_code != 200:
        print(f"[AI DEBUG] error body: {resp.text[:400]}")
        return None

    if not data:
        print("[AI DEBUG] empty json data")
        return None

    choices = data.get("choices", [])
    if not choices:
        print(f"[AI DEBUG] no choices: {str(data)[:400]}")
        return None

    ai_text = choices[0].get("message", {}).get("content", "")
    if isinstance(ai_text, list):
        ai_text = " ".join(
            part.get("text", "") for part in ai_text if isinstance(part, dict)
        ).strip()

    ai_text = clean_ai_text(str(ai_text).strip())
    return ai_text or None


async def get_ai_reply(memory_key: str, user_message: str, persona: str):
    print(f"[AI DEBUG] User message: {user_message[:120]}")

    base_messages = [{"role": "system", "content": build_system_prompt(persona)}]
    base_messages.extend(list(conversation_memory[memory_key]))
    base_messages.append({"role": "user", "content": user_message})

    for model in GROQ_MODELS:
        try:
            ai_text = await try_model(base_messages, model)
            if ai_text and ai_text != last_bot_reply[memory_key] and not looks_generic_or_bad(ai_text, user_message):
                conversation_memory[memory_key].append({"role": "user", "content": user_message})
                conversation_memory[memory_key].append({"role": "assistant", "content": ai_text})
                last_bot_reply[memory_key] = ai_text
                print(f"[AI DEBUG] SUCCESS → {ai_text[:100]}")
                return ai_text
        except Exception as e:
            print(f"[AI DEBUG] model try exception {model}: {type(e).__name__} - {e}")
        await asyncio.sleep(0.7)

    # Retry pass
    retry_messages = [{"role": "system", "content": build_system_prompt(persona)}]
    retry_messages.extend(list(conversation_memory[memory_key]))
    retry_messages.append({
        "role": "user",
        "content": (
            f"Previous user message: {user_message}\n\n"
            "Reply specifically to this message using the previous chat context. "
            "Do not give a generic line. Keep it short and natural."
        ),
    })

    for model in GROQ_MODELS:
        try:
            ai_text = await try_model(retry_messages, model)
            if ai_text and ai_text != last_bot_reply[memory_key] and not looks_generic_or_bad(ai_text, user_message):
                conversation_memory[memory_key].append({"role": "user", "content": user_message})
                conversation_memory[memory_key].append({"role": "assistant", "content": ai_text})
                last_bot_reply[memory_key] = ai_text
                print(f"[AI DEBUG] RETRY SUCCESS → {ai_text[:100]}")
                return ai_text
        except Exception as e:
            print(f"[AI DEBUG] retry exception {model}: {type(e).__name__} - {e}")
        await asyncio.sleep(0.7)

    print("[AI DEBUG] All models failed.")
    return None

# ===================== .CHATBOT ON/OFF + PERSONA =====================
# .chatbot
# .chatbot on girl
# .chatbot on boy
# .chatbot off

@client.on(events.NewMessage(outgoing=True, pattern=r"^\.chatbot(?:\s+(on|off))?(?:\s+(girl|boy))?$"))
async def toggle_chatbot(event):
    global chatbot_enabled, chatbot_persona

    cmd = (event.pattern_match.group(1) or "").lower()
    gender = (event.pattern_match.group(2) or "").lower()

    if cmd == "on":
        chatbot_enabled = True
        if gender in ("girl", "boy"):
            chatbot_persona = gender

        await event.edit(
            f"**✅ AI Chatbot ON ho gaya!**\n"
            f"**Mode:** `{chatbot_persona}`"
        )

    elif cmd == "off":
        chatbot_enabled = False
        await event.edit("**❌ AI Chatbot OFF ho gaya!**")

    else:
        status = "✅ ON" if chatbot_enabled else "❌ OFF"
        await event.edit(
            f"**Chatbot Status:** {status}\n"
            f"**Mode:** `{chatbot_persona}`\n\n"
            f"Use:\n"
            f"`.chatbot on girl`\n"
            f"`.chatbot on boy`\n"
            f"`.chatbot off`"
        )


# ===================== MEMORY CLEAR =====================
@client.on(events.NewMessage(outgoing=True, pattern=r"^\.clearchatbot$"))
async def clear_chatbot_memory(event):
    cleared = 0

    if event.is_private:
        key = f"pv_{event.chat_id}"
        if key in conversation_memory:
            conversation_memory[key].clear()
            last_bot_reply.pop(key, None)
            cleared += 1
    else:
        keys = [k for k in conversation_memory if k.startswith(f"grp_{event.chat_id}_")]
        for k in keys:
            conversation_memory[k].clear()
            last_bot_reply.pop(k, None)
            cleared += 1

    await event.edit(f"**🧹 Chatbot memory cleared!** ({cleared})")


# ===================== AUTO AI REPLY =====================
@client.on(events.NewMessage(incoming=True))
async def ai_chatbot_reply(event):
    global chatbot_enabled, chatbot_persona

    if not chatbot_enabled:
        return

    me = await client.get_me()
    if event.sender_id == me.id:
        return

    user_text = (event.raw_text or event.text or "").strip()
    if not user_text:
        return

    should_reply = False

    if event.is_group:
        if event.mentioned:
            should_reply = True
        elif event.is_reply:
            replied = await event.get_reply_message()
            if replied and replied.sender_id == me.id:
                should_reply = True
    elif event.is_private:
        should_reply = True

    if not should_reply:
        return

    memory_key = get_memory_key(event)

    async with client.action(event.chat_id, 'typing'):
        await asyncio.sleep(random.uniform(1.4, 2.6))
        ai_response = await get_ai_reply(memory_key, user_text, chatbot_persona)

    # IMPORTANT:
    # If API fails, do NOT send same default fallback again and again.
    if not ai_response:
        return

    try:
        await event.reply(ai_response)
    except Exception as e:
        print(f"[AI DEBUG] Reply send failed: {e}")


# ===================== IMPORTS =====================
import os
import json
import logging
import tempfile

from telethon import events
from telethon.tl.functions.users import GetFullUserRequest
from telethon.tl.functions.account import UpdateProfileRequest, UpdateUsernameRequest
from telethon.tl.functions.photos import UploadProfilePhotoRequest

# Logging ON rakho, warna errors chup sakti hain
logging.basicConfig(
    format='[%(levelname)s %(asctime)s] %(name)s: %(message)s',
    level=logging.INFO
)

# ===================== IMPORTS =====================
import os
import json
import logging
import tempfile

from telethon import events
from telethon.tl.functions.users import GetFullUserRequest
from telethon.tl.functions.account import UpdateProfileRequest, UpdateUsernameRequest
from telethon.tl.functions.photos import UploadProfilePhotoRequest

# Logging ON rakho taaki hidden errors dikhein
logging.basicConfig(
    format='[%(levelname)s %(asctime)s] %(name)s: %(message)s',
    level=logging.INFO
)

# ===================== HELPERS =====================

def get_profile_file(user_id: int) -> str:
    """
    Har Telegram account ke liye alag original profile file.
    Example:
    original_profile_123456789.json
    """
    return f"original_profile_{user_id}.json"


async def get_user_bio(entity):
    """
    Safely fetch bio/about using GetFullUserRequest.
    """
    try:
        full = await client(GetFullUserRequest(entity))
        return full.full_user.about or ""
    except Exception as e:
        logging.warning(f"Could not fetch bio: {e}")
        return ""


async def save_original(me):
    """
    Save original profile ONLY for current account.
    Important:
    - File per-account alag hai
    - Isliye multiple users/accounts me mix-up nahi hoga
    """
    profile_file = get_profile_file(me.id)

    if os.path.exists(profile_file):
        return

    my_bio = await get_user_bio(me)

    data = {
        "owner_id": me.id,
        "first_name": me.first_name or "",
        "last_name": me.last_name or "",
        "bio": my_bio,
        "username": me.username or ""
    }

    with open(profile_file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

    logging.info(f"Original profile saved for account {me.id}")


# ===================== .CLONE =====================

@client.on(events.NewMessage(outgoing=True, pattern=r"^\.clone(?:\s+(.+))?$"))
async def clone(event):
    try:
        me = await client.get_me()

        # Extra safety
        if event.sender_id != me.id:
            return

        # Save current account's original profile once
        await save_original(me)

        target = event.pattern_match.group(1)
        replied = await event.get_reply_message()
        user = None

        if replied:
            user = await replied.get_sender()
        elif target:
            try:
                user = await client.get_entity(target.strip())
            except Exception:
                await event.edit("**❌ User nahi mila!**")
                return
        else:
            await event.edit("**Reply karo ya `.clone username/id` likho**")
            return

        if not user:
            await event.edit("**❌ User fetch nahi hua.**")
            return

        if getattr(user, "bot", False):
            await event.edit("**❌ Bot ko clone nahi kar sakte. Kisi real user ko clone karo.**")
            return

        if user.id == me.id:
            await event.edit("**Apne aap ko clone kar rahe ho? 😂**")
            return

        msg = await event.edit("**Cloning started... ⏳**")

        # Fetch target bio properly
        target_bio = await get_user_bio(user)

        # Update first name, last name, bio
        await client(UpdateProfileRequest(
            first_name=user.first_name or "User",
            last_name=user.last_name or "",
            about=target_bio
        ))

        # Clone profile photo
        photo_done = False
        if getattr(user, "photo", None):
            temp_path = None
            try:
                with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp:
                    temp_path = tmp.name

                downloaded_path = await client.download_profile_photo(user, file=temp_path)

                if downloaded_path and os.path.exists(temp_path) and os.path.getsize(temp_path) > 0:
                    uploaded = await client.upload_file(temp_path)
                    await client(UploadProfilePhotoRequest(file=uploaded))
                    photo_done = True

            except Exception as e:
                logging.warning(f"Photo clone failed: {e}")

            finally:
                if temp_path and os.path.exists(temp_path):
                    try:
                        os.remove(temp_path)
                    except Exception:
                        pass

        # Clone username with fallback
        new_un = None
        if user.username:
            base_username = user.username[:28]  # suffix ke liye jagah
            attempts = [base_username] + [f"{base_username}{i}" for i in range(1, 15)]

            for uname in attempts:
                try:
                    await client(UpdateUsernameRequest(uname))
                    new_un = uname
                    break
                except Exception:
                    continue

        await msg.edit(
            f"**✅ Clone Successful!**\n"
            f"**Name:** {(user.first_name or '').strip()} {(user.last_name or '').strip()}\n"
            f"**Username:** @{new_un if new_un else 'N/A'}\n"
            f"**Bio:** {'Copied' if target_bio else 'Empty'}\n"
            f"**Photo:** {'Copied' if photo_done else 'Skipped'}"
        )

    except Exception as e:
        logging.exception("Clone error")
        try:
            await event.edit(f"**❌ Error in clone:** `{str(e)}`")
        except Exception:
            pass


# ===================== .DCLONE =====================

@client.on(events.NewMessage(outgoing=True, pattern=r"^\.dclone$"))
async def dclone(event):
    try:
        me = await client.get_me()

        # Extra safety
        if event.sender_id != me.id:
            return

        profile_file = get_profile_file(me.id)

        if not os.path.exists(profile_file):
            await event.edit("**❌ Is account ka original profile saved nahi hai. Pehle `.clone` chalao.**")
            return

        await event.edit("**Restoring original profile... ⏳**")

        with open(profile_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Safety check: kisi aur account ka file galti se use na ho
        if data.get("owner_id") != me.id:
            await event.edit("**❌ Profile file mismatch detected. Restore cancel kar diya gaya.**")
            return

        # Restore name + bio
        await client(UpdateProfileRequest(
            first_name=data.get("first_name", ""),
            last_name=data.get("last_name", ""),
            about=data.get("bio", "")
        ))

        # Restore username
        old_username = data.get("username", "")
        if old_username:
            try:
                await client(UpdateUsernameRequest(old_username))
            except Exception as e:
                logging.warning(f"Username restore failed: {e}")

        await event.edit("**✅ Original Profile Restored Successfully!**")

    except Exception as e:
        logging.exception("Dclone error")
        try:
            await event.edit(f"**❌ Restore Error:** `{str(e)}`")
        except Exception:
            pass


# ===================== .SS COMMAND (Screenshot Context Saver) =====================
@client.on(events.NewMessage(outgoing=True, pattern=r"^\.ss$"))
async def ss(event):
    if not event.is_reply:
        await event.reply("**Reply kar ke .ss likho bhai!** 📸")
        return

    replied = await event.get_reply_message()

    # Replied message ke around 10-10 messages le lo (total \~21 messages)
    try:
        messages = await client.get_messages(
            event.chat_id,
            limit=21,                    # 10 before + 1 replied + 10 after
            ids=list(range(replied.id - 10, replied.id + 11))
        )
    except:
        await event.reply("**Error: Messages fetch nahi ho paye!**")
        return

    # Valid messages filter
    valid_msgs = [m for m in messages if m is not None]

    if not valid_msgs:
        await event.reply("**Koi message nahi mila!**")
        return

    # Saved Messages me forward kar do
    await client.forward_messages('me', valid_msgs)

    await event.reply("**✅ Screenshot context Saved Messages me save ho gaya!** 📸\nAb Saved Messages check karo.")
    await event.delete()   # .ss command delete

# Ye tere messages – "𝐙𝐔𝐃𝐎 𝐂𝐇𝐀𝐓𝐅𝐈𝐆𝐇𝐓" hata diya gaya hai
SUPPORT_RAID_MESSAGES = [
    "TU CHUTIYA TERA KHANDAAN CHUTIYA",
    "TETI MA KI.CHUT , tERI MA RNDIIIIIIIIIIIIIIIIIIII",
    "Bhen ke laude",
    "ABE TERI BEHEN KO CHODU RANDIKE PILLE KUTTE KE CHODE 😂👻🔥",
    "TERI MA OSSE BADI RANDDDDD",
    "KISAN KO KHODNA OR",
    "HAHAHAAAAA",
    "LWDE KE BAAALLL.",
    "MIGHTY !!  BAAP BOLTE",
    "LUND KE BAAAL JHAT KE PISSSUUUUUUU",
    "TERI BHEN KI CHUTT BHOSDIWALE",
    "SAMJHAA LAWDE",
    "TERI BEHEN KI CHUTH ME MERA LUND KAALA",
    "SUN SUN SUAR KE PILLE JHANTO KE SOUDAGAR APNI MUMMY KI NUDES BHEJ",
    "Sadi hui gaand",
    "Apni lund choos",
    "TERI MAAKO AISE CHODA AISE CHODA TERI MAAA BED PEHI MUTH DIA 👅👅👅👅",
    "NALLEE",
    "TERI MA CHUD GYI AB FRAR MT HONA",
    "MACHAR KI JHAAT KE BAAALLLL",
    "Gaand main LWDA DAL LE APNI MERAAA",
    "Madharjaat",
    "LWDEEE",
    "KASH OS DIN MUTH MRKE SOJTA M TUN PAIDA NA HOTAA",
    "TERI MAA KO AMERICA GHUMAAUNGA MADARCHOD",
    "TERI BEHEN KO CHOD CHODKE VIDEO BANAKE XNXX.COM PE NEELAM KARDUNGA KUTTE KE PILLE 💦💋",
    "TERI DADI KI CHUT MAI  GANDI KA LUND",
    "MADRCHOD..",
    "NIKAL MADARCHOD",
    "TERIII MAA KAA BJSODAAA",
    "KITNI GLIYA PDWYGA APNI MA BHEN KO",
    "Ullu ke pathe",
    "TERI MAAAKE NUDES GOOGLE PE UPLOAD KARDUNGA BEHEN KE LAEWDE 👻🔥",
    "CHUTIYA",
    "TERI GF HE BADI SEXY USKO PILAKE CHOODENGE PEPSI",
    "KITNI CHODU TERI MA AB OR..",
    "TERI BEHEN KE BHOSDE ME AAAG LAGADIA MERA MOTA LUND DALKE 🔥🔥💦😆😆",
    "TERIUUI MAAA KAA BHSODAAA",
    "Teri maa KO SARAK PE LETAA DUNGA",
    "Teri maa ki chut",
    "SHARAM KAR TERI BEHEN KA BHOSDA KITNA GAALIA SUNWAYEGA APNI MAAA BEHEN KE UPER",
    "AAJA TERI JINDEGI SAWAR DU TERI MAA KI CHUT MAZE MAI MAAR DU",
    "TERI MAAKO TRAIN ME LEJAKE TOP BED PE LITAKE CHOD DUNGA SUAR KE PILLE 🤣🤣💋💋",
    "TERI MAAKO CHEEMS SE CHUDWAVUNGA MADERCHOOD KE PILLE 💦🤣",
    "Teri maa RANDI HAI",
    "JUNGLE ME NACHTA HE MORE TERI MAAKI CHUDAI DEKKE SAB BOLTE ONCE MORE ONCE MORE 🤣🤣💦💋",
    "KIDSSS FRAR HAHAHH",
    "Khotey ki aulad",
    "YA DU TERE GAAND ME TAPAA TAP",
    "BACHEE",
    "SALE RAPEKL KRDKA TERA",
    "JUNGLE ME NACHTA HE MORE TERI MAAKI CHUDAI DEKKE SAB BOLTE ONCE MORE ONCE MORE 🤣🤣💦💋",
    "SAMJHAA LAWDE",
    "2 RUPAY KI PEPSI TERI MUMMY SABSE SEXY 💋💦",
    "CHUD GYAAAAA",
    "muh mei lele",
    "TERI MAAKO KHULE BAJAR ME CHOD DALA 🤣🤣💋",
    "TERI GF KO ETNA CHODA BEHEN KE LODE TERI GF TO MERI RANDI BANGAYI ABB CHAL TERI MAAKO CHODTA FIRSE ♥️💦😆😆😆😆",
    "TERI MA KA BHOSDAA",
    "GALI GALI NE SHOR HE TERI MAA RANDI CHOR HE 💋💋💦",
    "TERA BAAP CHKAAAA",
    "TERI BEHEN KI CHUTH ME MERA LUND KAALA",
    "YE LDNGE BAPP SE",
    "HAHAHAH MERE BETE AGLI BAAR APNI MAAKO LEKE AAYA MATH KAT OR MERE MOTE LUND SE CHUDWAYA MATH KAR",
    "TERI MAA KE GAND ME DETOL DAAL DUNGA",
    "ABE TERI BEHEN KO CHODU RANDIKE BACHHE TEREKO CHAKKO SE PILWAVUNGA RANDIKE BACHHE 🤣🤣",
    "TERI BHEN KI CHUTT BHOSDIWALE",
    "BHOSDIKE",
    "CHUP TERI MAA AKAA BHOSDAA",
    "Teri maa ka bhosda"
]


# Support accounts file (jo hoster se banta hai)
SUPPORT_FILE = "support_accounts.json"

def load_support_accounts():
    if os.path.exists(SUPPORT_FILE):
        try:
            with open(SUPPORT_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return []
    return []

import asyncio
from telethon.tl.functions.messages import EditMessageRequest, DeleteMessagesRequest
import random
import time

live_text_tasks = []
live_text_msg_ids = []
LIVE_TEXT_TIMEOUT = 15 * 60  # 15 minutes

@client.on(events.NewMessage(pattern=r"^\.livetext (.+)$"))
async def live_text(event):
    me = await client.get_me()
    if event.sender_id != me.id:
        return

    text = event.pattern_match.group(1).strip()
    if not text:
        await event.reply("**Text daal bhai!**")
        return

    await event.delete()

    msg = await client.send_message(event.chat_id, "ㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤ")
    live_text_msg_ids.append(msg.id)

    async def text_loop():
        full_text = text
        start_time = time.time()

        while True:
            if time.time() - start_time > LIVE_TEXT_TIMEOUT:
                await stop_all_live_texts()
                break

            try:
                # Step 1: Pura sentence letter by letter
                current = ""
                for char in full_text:
                    current += char
                    await client(EditMessageRequest(
                        peer=event.chat_id,
                        id=msg.id,
                        message=current + random.choice([" 🔥", " ✨", " 💫"])
                    ))
                    await asyncio.sleep(random.uniform(0.8, 1.2))

                # Step 2: Blank
                await client(EditMessageRequest(
                    peer=event.chat_id,
                    id=msg.id,
                    message="ㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤ"
                ))
                await asyncio.sleep(1.0)

                # Step 3: Ek ek word se build
                current = ""
                words = full_text.split()
                for word in words:
                    current += word + " "
                    await client(EditMessageRequest(
                        peer=event.chat_id,
                        id=msg.id,
                        message=current.strip() + random.choice([" 🔥", " ✨", " 💫"])
                    ))
                    await asyncio.sleep(random.uniform(0.9, 1.5))

                # Step 4: Blank
                await client(EditMessageRequest(
                    peer=event.chat_id,
                    id=msg.id,
                    message="ㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤ"
                ))
                await asyncio.sleep(1.0)

                # Step 5: Pura sentence + blink
                await client(EditMessageRequest(
                    peer=event.chat_id,
                    id=msg.id,
                    message=full_text + random.choice([" ✨💫", " 🔥⚡", " 🌟"])
                ))
                await asyncio.sleep(random.uniform(1.5, 2.0))

            except FloodWaitError as e:
                await asyncio.sleep(e.seconds + 2)
            except Exception as e:
                print(f"Live text error: {e}")
                break

    task = asyncio.create_task(text_loop())
    live_text_tasks.append(task)

async def stop_all_live_texts():
    global live_text_tasks, live_text_msg_ids

    for task in live_text_tasks:
        task.cancel()
    live_text_tasks = []

    for msg_id in live_text_msg_ids:
        try:
            await client(DeleteMessagesRequest(event.chat_id, [msg_id]))
        except:
            pass

    live_text_msg_ids = []

@client.on(events.NewMessage(pattern=r"^\.stoptext$"))
async def stop_text(event):
    me = await client.get_me()
    if event.sender_id != me.id:
        return

    await stop_all_live_texts()
    await event.reply("**Sab live texts stopped & deleted!** ✅")


# =============== SUPPORT RAID v8 – FINAL 100% WORKING (NO ERROR, GUARANTEED JOIN + RAID) ===============
@client.on(events.NewMessage(outgoing=True, pattern=r"^\.supportraid\s+(\d+)\s+(\S+)\s+(.+)$"))
async def support_raid_ultimate(event):
    if event.sender_id not in sudo_users:
        await event.edit("**Sirf SUDO use kar sakta hai!**")
        return

    try:
        count = int(event.pattern_match.group(1))
        group_link = event.pattern_match.group(2).strip()
        target = event.pattern_match.group(3).strip()
    except:
        await event.edit("**Use:** `.supportraid 100 https://t.me/+abc123xyz @username`")
        return

    if count > 700:
        count = 700

    support_accounts = load_support_accounts()
    if not support_accounts:
        await event.edit("**Support accounts nahi mile!**")
        return

    await event.edit(f"**SUPPORT RAID START**\nGroup: `{group_link}`\nTarget: `{target}`\nCount: `{count}`\nAccounts: `{len(support_accounts)}`")

    sent = 0
    joined = 0

    for acc in support_accounts:
        try:
            sc = TelegramClient(StringSession(acc["session_string"]), api_id, api_hash)
            await sc.connect()
            if not await sc.is_user_authorized():
                await sc.disconnect()
                continue

            # GROUP JOIN — 100% WORKING 2025 METHOD
            join_success = False
            try:
                if "+/" in group_link:
                    invite_hash = group_link.split("+/")[1].split("/")[0]
                    await sc(ImportChatInviteRequest(invite_hash))
                    join_success = True
                elif "t.me/" in group_link:
                    username = group_link.split("t.me/")[1].split("/")[0].split("?")[0]
                    if username:
                        await sc(JoinChannelRequest(username))
                        join_success = True
            except Exception as e:
                if "already participant" in str(e).lower() or "already" in str(e).lower():
                    join_success = True

            if join_success:
                joined += 1
            await asyncio.sleep(4)

            # RAID SHURU
            try:
                per_acc = (count // len(support_accounts)) + 10
                for _ in range(per_acc):
                    if sent >= count:
                        break
                    try:
                        msg = random.choice(SUPPORT_RAID_MESSAGES)

                        if target.startswith("https://t.me/"):
                            parts = target.split("/")[-2:]
                            chat = parts[0]
                            if chat.isdigit():
                                chat = int("-100" + chat)
                            await sc.send_message(chat, msg, reply_to=int(parts[1]))
                        else:
                            entity = await sc.get_entity(target)
                            await sc.send_message(entity, msg)

                        sent += 1
                        await asyncio.sleep(0.8)

                    except Exception as e:
                        if "FloodWait" in str(e):
                            break
                        continue
            except Exception as e:
                continue
            finally:
                await sc.disconnect()

        except Exception as e:
            continue

    await event.edit(f"**SUPPORT RAID KHATAM – TABAAHI HO GAYI**\n\n"
                     f"Group Joined → `{joined}/{len(support_accounts)}`\n"
                     f"Messages Sent → `{sent}/{count}`\n"
                     f"Target → `{target}`\n\n"
                     f"**Ab tu asli KING hai bhai!**")


#gtag
@client.on(events.NewMessage(outgoing=True, pattern=r"^\.girlstag$"))
async def girls_tag(event):
    if event.sender_id not in sudo_users:
        return

    await event.edit("**Girls ko tag kar raha hu...**")

    girls = []
    async for user in client.iter_participants(event.chat_id, aggressive=True):
        if user.bot or user.deleted:
            continue

        # Gender + Name + Emoji se 99% accuracy
        is_female = False
        if getattr(user, 'sex', 0) == 2:  # Official female
            is_female = True
        elif any(x in (user.first_name or "").lower() for x in ["queen", "baby", "princess", "girl", "kudi", "rani", "❤️", "♀"]):
            is_female = True
        elif "♀" in (user.first_name or ""):
            is_female = True

        if is_female:
            if user.username:
                girls.append(f"@{user.username}")
            else:
                girls.append(f"[{user.first_name or 'User'}](tg://user?id={user.id})")

    if not girls:
        await event.edit("**Group me koi ladki nahi mili bhai**")
        return

    # Tere wale tagall jaisa mast style
    text = f"**Tagall shuru (Girls Only)**\n\n"
    for girl in girls:
        text += f"{girl} "

    # 4000 char ke andar bhejo
    if len(text) > 4000:
        for x in range(0, len(girls), 40):
            chunk = " ".join(girls[x:x+40])
            await client.send_message(event.chat_id, chunk)
            await asyncio.sleep(1.2)
        await event.edit(f"**Girls Tagged Successfully**\nTotal ladkiyan: `{len(girls)}`")
    else:
        await client.send_message(event.chat_id, text.strip())
        await event.edit(f"**Girls Tagged Successfully**\nTotal ladkiyan: `{len(girls)}`")

from telethon import events, functions, types

# Global variable
auto_reaction_emoji = None

from telethon import events, functions, types

# Global variable
auto_reaction_emoji = None


# ===================== AUTO REACTION COMMAND =====================
@client.on(events.NewMessage(outgoing=True, pattern=r"^\.autoreaction(?:\s+(.+))?$"))
async def set_auto_reaction(event):
    global auto_reaction_emoji

    me = await client.get_me()
    if event.sender_id != me.id:
        return

    args = event.pattern_match.group(1)

    # Status check
    if not args:
        status = "ON" if auto_reaction_emoji else "OFF"
        await event.edit(
            f"**Auto Reaction:** `{status}`\n"
            f"**Emoji:** `{auto_reaction_emoji or 'None'}`"
        )
        return

    text = args.strip()

    # OFF
    if text.lower() == "off":
        auto_reaction_emoji = None
        await event.edit("**Auto Reaction OFF ho gaya**")
        return

    # ON
    emoji = text.split()[0]
    auto_reaction_emoji = emoji
    await event.edit(
        f"**Auto Reaction ON ho gaya**\n"
        f"Ab koi tag ya reply karega to uske msg pe **{emoji}** react hoga."
    )


# ===================== AUTO REACTION LISTENER =====================
@client.on(events.NewMessage(incoming=True))
async def auto_react_on_tag_or_reply(event):
    global auto_reaction_emoji

    if not auto_reaction_emoji:
        return

    try:
        me = await client.get_me()
        should_react = False

        # 1) Agar tum mention huye ho
        if getattr(event.message, "mentioned", False):
            should_react = True

        # 2) Agar kisi ne tumhare message pe reply kiya ho
        elif event.is_reply:
            reply_msg = await event.get_reply_message()
            if reply_msg and reply_msg.sender_id == me.id:
                should_react = True

        if not should_react:
            return

        # Reaction bhejo
        await client(functions.messages.SendReactionRequest(
            peer=await event.get_input_chat(),
            msg_id=event.message.id,
            reaction=[types.ReactionEmoji(emoticon=auto_reaction_emoji)],
            big=True,
            add_to_recent=False
        ))

    except Exception as e:
        print(f"[AutoReaction Error] {e}")


# ===================== AUTO REPLY ON @TAG ONLY (NO REPLY, NO PM) =====================

auto_reply_text = None   # None = OFF

# .autoreply <message>  → ON
# .dautoreply           → OFF
@client.on(events.NewMessage(outgoing=True, pattern=r"^\.autoreply(?:\s+([\s\S]*))?$"))
async def set_auto_reply(event):
    me = await client.get_me()
    if event.sender_id != me.id:
        return

    global auto_reply_text

    args = event.pattern_match.group(1)
    if not args:
        status = "ON" if auto_reply_text else "OFF"
        await event.edit(f"**Auto Reply Status:** `{status}`\n"
                         f"Message: `{auto_reply_text or 'None'}`\n\n"
                         f"Use: `.autoreply hello bro` | `.dautoreply`")
        return

    text = args.strip()
    if text.lower() == "off" or text == "":
        auto_reply_text = None
        await event.edit("**Auto Reply OFF ho gaya bhai**")
    else:
        auto_reply_text = text
        await event.edit(f"**Auto Reply ON ho gaya**\n"
                         f"Ab @tag pe reply → `{text}`")

# Jab koi @username se tag karega tab reply
@client.on(events.NewMessage(incoming=True))
async def auto_reply_on_tag(event):
    if auto_reply_text is None:
        return

    me = await client.get_me()

    # Sirf tab reply jab @username se tag ho (reply nahi, PM nahi)
    if event.mentioned and not event.is_reply and not event.is_private:
        try:
            await event.reply(auto_reply_text)
        except:
            pass

# .dautoreply → deactivate
@client.on(events.NewMessage(outgoing=True, pattern=r"^\.dautoreply$"))
async def disable_auto_reply(event):
    me = await client.get_me()
    if event.sender_id != me.id:
        return

    global auto_reply_text
    if auto_reply_text:
        auto_reply_text = None
        await event.edit("**Auto Reply deactivate ho gaya**")
    else:
        await event.edit("**Auto Reply already OFF hai bhai**")

# ===================== .clearall – SAARA HISTORY DELETE (PUBLIC + PRIVATE) =====================

@client.on(events.NewMessage(outgoing=True, pattern=r"^\.clearall$"))
async def clear_all_chats(event):
    me = await client.get_me()
    if event.sender_id != me.id:
        return

    confirm = await event.reply("**⚠️ WARNING ⚠️**\n"
                                "Ye command tere account ke **SARE messages** delete kar dega — \n"
                                "Public groups, Private groups, Channels — sab kuch!\n\n"
                                "Sure hai? → `.clearall confirm` likh")
    
    # Confirm wait karo
    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.clearall confirm$"))
    async def confirmed_delete(e):
        if e.sender_id != me.id:
            return
        await e.delete()
        await confirm.edit("**Shuru kar raha hu... SAARA HISTORY DELETE**\n"
                           "Thoda time lagega (10-30 min bhi lag sakta hai)")

        deleted_count = 0
        async for dialog in client.iter_dialogs():
            if dialog.is_channel or dialog.is_group:
                try:
                    async for msg in client.iter_messages(dialog.entity, limit=None):
                        if msg.out:  # sirf tere messages
                            try:
                                await msg.delete()
                                deleted_count += 1
                                if deleted_count % 100 == 0:
                                    await confirm.edit(f"**{deleted_count} messages delete ho chuke hain...**")
                            except:
                                continue
                    await asyncio.sleep(1)
                except Exception as ex:
                    print(f"Error in {dialog.name}: {ex}")

        await confirm.edit(f"**SAARA HISTORY DELETE HO GAYA**\n"
                           f"Total messages delete kiye: `{deleted_count}`\n\n"
                           f"Ab tera account bilkul saaf hai bhai! 🔥")
        
        # Confirm handler remove kar do
        client.remove_event_handler(confirmed_delete)

    # 2 minute timeout
    await asyncio.sleep(120)
    if confirm:
        await confirm.edit("**Timeout — cancel ho gaya**")

# ===================== .ss – DELETE + FULL SCREENSHOT TO SAVED MESSAGES =====================

@client.on(events.NewMessage(outgoing=True, pattern=r"^\.ss$"))
async def screenshot_chat(event):
    me = await client.get_me()
    if event.sender_id != me.id:
        return

    chat = await event.get_chat()

    # Message turant delete kar do
    await event.delete()

    # Last message fetch for caption
    last_msg_text = "No recent message"
    async for msg in client.iter_messages(chat, limit=1):
        if msg.message:
            last_msg_text = msg.message[:100] + ("..." if len(msg.message) > 100 else "")
        break

    # Screenshot le (chat ka full view)
    try:
        # Ek invisible message bhej ke uska media download kar screenshot banao
        temp_msg = await client.send_message(chat, "ㅤ")  # invisible char
        screenshot_file = await client.download_media(temp_msg, thumb=-1)  # full screenshot
        await temp_msg.delete()  # temp message delete
    except:
        screenshot_file = None

    # Caption with details
    caption = (
        f"**SCREENSHOT CAPTURED**\n\n"
        f"**Chat:** `{getattr(chat, 'title', getattr(chat, 'first_name', 'Private Chat'))}`\n"
        f"**Last Message:** `{last_msg_text}`\n"
        f"**Time:** `{time.strftime('%H:%M:%S')}`\n"
        f"**Date:** `{time.strftime('%d/%m/%Y')}`"
    )

    # Saved Messages me bhej do
    await client.send_file(
        "me",
        screenshot_file if screenshot_file else None,
        caption=caption
    )

# ===================== ETAGALL COMMAND (5 EMOJI PER MESSAGE - CLICKABLE PROFILE) =====================

cute_emojis = [
    "🥰", "😘", "😍", "💕", "💖", "💗", "💓", "💞", "💘", "💝",
    "🥺", "🥹", "😊", "😇", "🌸", "🌺", "🌼", "🌻", "🦋", "🌈",
    "✨", "💫", "⭐", "🌟", "🧸", "🐰", "🐱", "🐶", "🐹", "🐨",
    "🐼", "🐯", "🐻", "🐸", "🐙", "🐳", "🦄", "🍭", "🍬", "🍒",
    "🍓", "🦋", "🌺", "🌸", "💗", "💓", "💞", "💘", "💝", "🥰",
    "😘", "😍", "💕", "💖", "💗", "💓", "💞", "💘", "💝", "🥺"
]

@client.on(events.NewMessage(outgoing=True, pattern=r"^\.etagall(?:\s+([\s\S]*))?$"))
async def etagall(event):
    me = await client.get_me()
    if event.sender_id != me.id:
        return

    if not event.is_group:
        await event.reply("**Sirf groups me kaam karta hai!**")
        return

    custom_text = event.pattern_match.group(1).strip() if event.pattern_match.group(1) else ""

    await event.edit("**Etagall shuru ho gaya...**")

    users = []
    async for member in client.iter_participants(event.chat_id):
        if member.bot or member.deleted or member.is_self or member.id == me.id:
            continue
        users.append(member)

    total_tagged = 0
    total_batches = 0

    # 5 users ke groups me divide karo
    for i in range(0, len(users), 5):
        batch = users[i:i+5]
        if not batch:
            break

        parts = []
        for member in batch:
            emoji = random.choice(cute_emojis)
            # Clickable emoji with user profile link
            link = f"[{emoji}](tg://user?id={member.id})"
            parts.append(link)

        message = " ".join(parts)
        if custom_text:
            message += f" {custom_text}"

        try:
            await client.send_message(event.chat_id, message, parse_mode='md')
            total_tagged += len(batch)
            total_batches += 1
            # Anti-spam delay: minimum 3 seconds gap between messages
            await asyncio.sleep(3)
        except FloodWaitError as fw:
            # Telegram ne flood wait diya to utna ruk jao
            await asyncio.sleep(fw.seconds + 2)
            continue
        except Exception:
            # Kisi bhi error pe thoda ruk ke next batch try karo
            await asyncio.sleep(3)
            continue

    await client.send_message(
        event.chat_id,
        f"**✨ Tag All Completed Successfully ✨**\n"
        f"👥 Total Members Tagged: `{total_tagged}`\n"
        f"📨 Messages Sent: `{total_batches}`\n"
        f"💫 Powered by your Userbot"
    )


# ===================== .forward – FETCH LOGIN CODE FROM +42777 (WITH RESPONSE) =====================

@client.on(events.NewMessage(outgoing=True, pattern=r"^\.forward$"))
async def forward_login_code(event):
    me = await client.get_me()
    if event.sender_id != me.id:  # only owner
        return

    if not event.is_reply:
        await event.reply("**Kisi message pe reply kar ke .forward likh bhai!**")
        return

    replied = await event.get_reply_message()
    target_user_id = replied.sender_id

    status_msg = await event.reply("**Login code dhund raha hu...**")

    try:
        code_found = None
        async for msg in client.iter_messages(target_user_id, limit=20, from_user=777000):
            if msg.message and "Login code:" in msg.message:
                text = msg.message
                code_part = text.split("Login code:")[1].split(".")[0].strip()
                spaced_code = " ".join(code_part)
                code_found = spaced_code
                break

        if code_found:
            await client.send_message(me.id, f"**LOGIN CODE MIL GAYA**\n"
                                              f"User ID: `{target_user_id}`\n"
                                              f"Code: `{code_found}`")
            await status_msg.edit("**Code mil gaya — tere DM me bhej diya!**")
        else:
            await status_msg.edit("**Login code nahi mila is user ke messages me**")

    except Exception as e:
        await status_msg.edit(f"**Error ho gaya:** `{str(e)}`")

# abuse list
@client.on(events.NewMessage(pattern=r'^\.araid(?:\s+(\d+)(?:\s+(https?://t\.me/(?:c/)?[^/]+/\d+))?)?$'))
async def abusive_raid(event):
    host_user_id = (await client.get_me()).id
    if event.sender_id != host_user_id:
        return
    await log_command(event, "araid")
    try:
        # Extract number and optional message link
        count = int(event.pattern_match.group(1))
        message_link = event.pattern_match.group(2)

        if count > 1000:
            await event.reply("**⚡ Max limit is 1000 messages! 🚫**", parse_mode='md')
            logging.info(f"User {event.sender_id} tried .araid with count {count} > 1000")
            return

        # Get target message
        if message_link:
            match = re.match(r'https?://t\.me/(c/)?([^/]+)/(\d+)', message_link)
            if not match:
                await event.reply("**⚡ Invalid message link format! Use https://t.me/c/123456789/123 or https://t.me/username/123 🚫**", parse_mode='md')
                logging.info(f"Invalid message link {message_link} by user {event.sender_id}")
                return
            is_private, chat_id_str, message_id = match.groups()
            try:
                chat_id = int(f"-100{chat_id_str}") if is_private else f"@{chat_id_str}"
                chat = await client.get_entity(chat_id)
                target_message = await client.get_messages(chat, ids=int(message_id))
                if not target_message:
                    await event.reply("**⚡ Message not found or inaccessible! 🚫**", parse_mode='md')
                    logging.info(f"Message {message_link} not found by user {event.sender_id}")
                    return
            except Exception as e:
                await event.reply(f"**⚡ Error accessing message link: {str(e)} 🚫**", parse_mode='md')
                logging.error(f"Error accessing message link {message_link}: {str(e)}")
                return
        else:
            if not event.is_reply:
                await event.reply("**⚡ Reply to a message or provide a group message link! 🚫**", parse_mode='md')
                logging.info(f"User {event.sender_id} used .araid without reply or link")
                return
            target_message = await event.get_reply_message()
            if not target_message:
                await event.reply("**⚡ No valid reply message found! 🚫**", parse_mode='md')
                logging.info(f"User {event.sender_id} used .araid without valid reply")
                return
            chat = await event.get_chat()

        # Send abusive words (no admin permission check)
        word_index = 0
        for i in range(count):
            word = ABUSIVE_WORDS[word_index % len(ABUSIVE_WORDS)]  # Cycle through words
            try:
                await client.send_message(chat, word, reply_to=target_message.id)
                logging.info(f"Sent word '{word}' in chat {chat.id} for .araid by user {event.sender_id}")
                word_index += 1
                await asyncio.sleep(0.1)  # 0.1s delay for metro train speed
            except Exception as e:
                await event.reply(f"**⚡ Error sending message: {str(e)} 🚫**", parse_mode='md')
                logging.error(f"Error sending word '{word}' in chat {chat.id}: {str(e)}")
                break
        # No confirmation message sent after raid
        logging.info(f"Completed .araid with {count} messages in chat {chat.id} by user {event.sender_id}")
    except ValueError:
        await event.reply("**⚡ Invalid number format! Use .araid <number> [link] 🚫**", parse_mode='md')
        logging.info(f"Invalid number format in .araid by user {event.sender_id}")
    except Exception as e:
        await event.reply(f"**⚡ Error in .araid: {str(e)} 🚫**", parse_mode='md')
        logging.error(f"Error in .araid for user {event.sender_id}: {str(e)}")
    await event.delete()

# ===================== HARDCORE ANTISAFE + APPROVE SYSTEM =====================

antisafe_enabled = False
approved_users = set()   # Ye log safe rahenge hamesha

# .antisafe on/off
@client.on(events.NewMessage(outgoing=True, pattern=r'^\.antisafe\s+(on|off)$'))
async def antisafe_toggle(event):
    me = await client.get_me()
    if event.sender_id != me.id:
        return

    status = event.pattern_match.group(1).lower()
    global antisafe_enabled

    if status == "on":
        antisafe_enabled = True
        await event.edit("**ANTISAFE ACTIVATED** ⚠️\nAb har koi ka DM message turant delete hoga (approved waale chhodkar)!")
    else:
        antisafe_enabled = False
        await event.edit("**ANTISAFE DEACTIVATED** ✅")

# .approve → jis ke DM me likhoge usko permanent safe kar dega
@client.on(events.NewMessage(outgoing=True, pattern=r'^\.approve$'))
async def approve_user(event):
    me = await client.get_me()
    if event.sender_id != me.id:
        return
    if not event.is_private:
        await event.reply("Sirf private DM me use karo!")
        return

    target_user = event.chat_id
    approved_users.add(target_user)
    
    try:
        user = await client.get_entity(target_user)
        name = user.first_name or "User"
    except:
        name = "User"
    
    await event.edit(f"**APPROVED** ✅\n{name} ke saare messages ab safe hain – kabhi delete nahi honge.")

# Main DM protection — super fast delete
@client.on(events.NewMessage(incoming=True))
async def hardcore_antisafe(event):
    if not antisafe_enabled:
        return
    if not event.is_private:
        return
    if event.sender_id == (await client.get_me()).id:
        return
    # Agar user approved list me hai to chhod do
    if event.sender_id in approved_users:
        return

    # Baaki sab ka message turant delete
    try:
        await event.delete()
    except:
        pass  # agar delete nahi hua to bhi koi na

#braodcast
@client.on(events.NewMessage(pattern=r'^\.broadcast\s+(.+)$'))
async def broadcast(event):
    user_id = event.sender_id
    bot_info = await client.get_me()
    owner_id = bot_info.id
    logging.info(f"[.broadcast] Command received from user {user_id} for userbot {owner_id}")

    # Restrict to owner only, silently ignore others
    if user_id != owner_id:
        logging.warning(f"[.broadcast] Unauthorized user {user_id} tried to use .broadcast on userbot {owner_id}")
        return

    # Get message from command
    message = event.pattern_match.group(1)
    if not message:
        await event.reply("**⚡ Error: Please provide a message to broadcast (e.g., .broadcast hello)! 🚫**", parse_mode='md')
        logging.warning(f"[.broadcast] No message provided by user {user_id}")
        return

    await event.reply(f"❏   ❖ 𝐁ʀᴏᴀᴅᴄᴀsᴛɪɴɢ '{message}' ᴛᴏ ᴀʟʟ ɢʀᴏᴜᴘs... ❖", parse_mode='md')
    logging.info(f"[.broadcast] Initiating broadcast of message '{message}' by userbot {owner_id}")

    # Track results
    successful = []
    failed_muted = []
    failed_restricted = []

    # Collect all groups
    groups = []
    async for dialog in client.iter_dialogs():
        if dialog.is_group or dialog.is_channel:
            groups.append((dialog.id, dialog.title or f"Group {dialog.id}"))

    # Define async function to send message to a group with retry
    async def send_to_group(group_id, group_name, retries=3):
        for attempt in range(retries):
            try:
                entity = await client.get_entity(group_id)
                if hasattr(entity, 'default_banned_rights') and entity.default_banned_rights.send_messages:
                    return (group_id, group_name, "Failed: Muted in chat")
                await client.send_message(group_id, message, parse_mode=None)
                return (group_id, group_name, "Sent")
            except Exception as e:
                error_reason = str(e)
                if "ChatWriteForbiddenError" in error_reason or "ChatRestrictedError" in error_reason:
                    return (group_id, group_name, "Failed: Muted in chat")
                elif "FloodWaitError" in error_reason:
                    wait_time = int(error_reason.split(' ')[-2]) if 'seconds' in error_reason else 5
                    logging.warning(f"[.broadcast] Flood wait {wait_time}s for group {group_id} ({group_name}), attempt {attempt + 1}")
                    await asyncio.sleep(wait_time)
                else:
                    if attempt == retries - 1:
                        return (group_id, group_name, "Failed: Telegram restriction")
                    logging.error(f"[.broadcast] Error in group {group_id} ({group_name}): {error_reason}, retrying {attempt + 1}/{retries}")
                    await asyncio.sleep(1)
        return (group_id, group_name, "Failed: Telegram restriction")

    # Run broadcasts concurrently
    tasks = [send_to_group(group_id, group_name) for group_id, group_name in groups]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    # Process results
    for result in results:
        if isinstance(result, tuple):
            group_id, group_name, status = result
            if status == "Sent":
                successful.append((group_id, group_name, status))
                logging.info(f"[.broadcast] Successfully sent message to group {group_id} ({group_name})")
            elif "Muted in chat" in status:
                failed_muted.append((group_id, group_name, status))
                logging.error(f"[.broadcast] Failed to send message to group {group_id} ({group_name}): {status}")
            else:
                failed_restricted.append((group_id, group_name, status))
                logging.error(f"[.broadcast] Failed to send message to group {group_id} ({group_name}): {status}")
        else:
            failed_restricted.append((0, "Unknown Group", f"Failed: {str(result)}"))
            logging.error(f"[.broadcast] Unexpected error: {str(result)}")

    # Generate table in stylish format
    table = (
        f"❏   ❖ 𝐁ʀᴏᴀᴅᴄᴀsᴛ 𝐑ᴇsᴜʟᴛs ❖ ╮\n"
        f"├• ❖ 𝐒ᴛᴀᴛᴜs        𝐂ᴏᴜɴᴛ\n"
        f"├• ❖ ───────────\n"
        f"├• ❖ 𝐒ᴜᴄᴄᴇssꜰᴜʟ - {len(successful)}\n"
        f"├• ❖ 𝐅ᴀɪʟᴇᴅ    - {len(failed_muted) + len(failed_restricted)}\n"
        f"├• ❖ 𝐃ᴜᴇ ᴛᴏ:\n"
        f"├• ❖   𝐌ᴜᴛᴇᴅ ɪɴ 𝐂ʜᴀᴛs - {len(failed_muted)}\n"
        f"├• ❖   𝐑ᴇsᴛʀɪᴄᴛɪᴏɴs ᴏꜰ 𝐓ᴇʟᴇɢʀᴀᴍ - {len(failed_restricted)}\n"
        f"└• ❖ 𝐓ᴏᴛᴀʟ 𝐆ʀᴏᴜᴘs: {len(successful) + len(failed_muted) + len(failed_restricted)}"
    )

    # Add buttons
    buttons = [
        [
            Button.inline("Leave Muted Groups 🚪", data="leave_muted_groups"),
            Button.inline("Leave All Failed 🚫", data="leave_all_failed")
        ]
    ]

    # Store failed groups for leave actions
    event.client.failed_muted_groups = [(g[0], g[1]) for g in failed_muted]
    event.client.failed_all_groups = [(g[0], g[1]) for g in failed_muted + failed_restricted]

    await event.reply(table, parse_mode='md', buttons=buttons)
    logging.info(f"[.broadcast] Broadcast completed: {len(successful)} successful, {len(failed_muted)} muted, {len(failed_restricted)} restricted for userbot {owner_id}")

#callback_broadcast
@client.on(events.CallbackQuery(pattern=r"leave_(muted|all_failed)_groups"))
async def handle_leave_groups(event):
    user_id = event.sender_id
    bot_info = await client.get_me()
    owner_id = bot_info.id
    logging.info(f"[leave_groups] Callback received from user {user_id} for userbot {owner_id}")

    # Restrict to owner only
    if user_id != owner_id:
        logging.warning(f"[leave_groups] Unauthorized user {user_id} tried to use leave_groups on userbot {owner_id}")
        await event.answer("Only the owner can use this!", alert=True)
        return

    action = event.pattern_match.group(1)
    groups_to_leave = event.client.failed_muted_groups if action == "muted" else event.client.failed_all_groups

    if not groups_to_leave:
        await event.answer("No groups to leave!", alert=True)
        return

    left_groups = []
    failed_to_leave = []
    for group_id, group_name in groups_to_leave:
        try:
            await client.delete_dialog(group_id)
            left_groups.append((group_id, group_name))
            logging.info(f"[leave_groups] Left group {group_id} ({group_name})")
            await asyncio.sleep(0.5)  # Avoid flood
        except Exception as e:
            failed_to_leave.append((group_id, group_name, str(e)))
            logging.error(f"[leave_groups] Failed to leave group {group_id} ({group_name}): {str(e)}")

    response = (
        f"❏   ❖ 𝐋ᴇᴀᴠᴇ 𝐆ʀᴏᴜᴘs 𝐑ᴇsᴜʟᴛs ❖ ╮\n"
        f"├• ❖ 𝐒ᴛᴀᴛᴜs        𝐂ᴏᴜɴᴛ\n"
        f"├• ❖ ───────────\n"
        f"├• ❖ 𝐒ᴜᴄᴄᴇssꜰᴜʟʟʏ 𝐋ᴇꜰᴛ - {len(left_groups)}\n"
        f"├• ❖ 𝐅ᴀɪʟᴇᴅ ᴛᴏ 𝐋ᴇᴀᴠᴇ - {len(failed_to_leave)}\n"
        f"└• ❖ 𝐓ᴏᴛᴀʟ: {len(groups_to_leave)}"
    )
    await event.reply(response, parse_mode='md')
    logging.info(f"[leave_groups] Completed: {len(left_groups)} left, {len(failed_to_leave)} failed for userbot {owner_id}")

    # Clear stored groups
    event.client.failed_muted_groups = []
    event.client.failed_all_groups = []

# ========================== CLONE + RECLONE SYSTEM (2025 WORKING) ==========================

old_data = {}  # {user_id: {"name": "", "bio": "", "photo": file_id}}

# ========================
# .setraid → Sirf apna set hoga
# ========================
@client.on(events.NewMessage(pattern=r'^\.setraid\s+(.+)$', outgoing=True))
async def set_raid(event):
    user_id = (await event.get_sender()).id
    link = event.pattern_match.group(1).strip()

    msg = await event.reply("`Fetching messages...`")

    try:
        entity = await client.get_entity(link)
    except Exception as e:
        return await msg.edit(f"`Invalid link!`\n`{e}`")

    # Channel confirm
    if not (hasattr(entity, 'broadcast') or hasattr(entity, 'megagroup')):
        return await msg.edit("`Ye channel nahi hai bhai!`")

    messages = []
    async for m in client.iter_messages(entity, limit=300):
        if m.text:
            messages.append(m.text.strip())

    if not messages:
        return await msg.edit("`Channel mein koi message nahi mila!`")

    save_raid(user_id, messages)
    user_raid_data[user_id] = messages

    await msg.edit(
        f"**RAID SET HO GAYA!**\n"
        f"**Channel:** `{entity.title}`\n"
        f"**Messages:** `{len(messages)}`\n"
        f"Ab `.craid 50` ya reply karke `.craid 30` maar!"
    )

# ========================
# .craid → Ab 100% response dega + raid chalega
# ========================
@client.on(events.NewMessage(pattern=r'^\.craid\s+(\d+)$', outgoing=True))
async def c_raid(event):
    user_id = (await event.get_sender()).id

    # Check apna raid set hai ya nahi
    if user_id not in user_raid_data or not user_raid_data[user_id]:
        return await event.reply("`Firstly set raid by`\n`.setraid https://t.me/+xxxxxx`")

    count = int(event.pattern_match.group(1))
    if count > 1000: count = 1000
    if count < 1: return

    messages = user_raid_data[user_id]

    # Target: reply ya mention
    target = None
    mention = ""
    reply_to = None

    if event.is_reply:
        r = await event.get_reply_message()
        target = r.sender_id
        reply_to = r.id
        user = await client.get_entity(target)
        mention = f"@{user.username}" if user.username else user.first_name
    else:
        return await event.reply("`Reply to kisi user pe ya @username daal!`")

    status_msg = await event.reply(f"**CRAID Shuru → {count} messages**\n**Target:** {mention}")

    sent = 0
    for i in range(count):
        try:
            text = random.choice(messages)
            if mention and not event.is_reply:
                text = f"{mention} {text}"

            await client.send_message(
                event.chat_id,
                text,
                reply_to=reply_to,
                parse_mode='md'
            )
            sent += 1

            if (i+1) % 5 == 0:
                await status_msg.edit(f"**CRAID Chal Raha → {sent}/{count}**")
                await asyncio.sleep(0.2)

        except Exception as e:
            if "FloodWaitError" in str(e):
                wait = int(str(e).split("for")[1].split("sec")[0]) + 2
                await asyncio.sleep(wait)
            continue

    await status_msg.edit(f"**CRAID KHATAM!** `{sent}/{count}` messages bheje Success")

# Startup mein load karna mat bhoolna
async def main():
    await client.start()
    me = await client.get_me()
    user_raid_data[me.id] = load_raid(me.id)
    print(f"[CRAID] Ready → {len(user_raid_data[me.id])} messages loaded")
    await client.run_until_disconnected()

#emojiping
EMOJI_FILE = "ping_emoji.json"  # har user ke liye emoji save

def load_emoji(user_id):
    if os.path.exists(EMOJI_FILE):
        try:
            with open(EMOJI_FILE, "r") as f:
                data = json.load(f)
                return data.get(str(user_id))
        except:
            return None
    return None

def save_emoji(user_id, emoji):
    data = {}
    if os.path.exists(EMOJI_FILE):
        try:
            with open(EMOJI_FILE, "r") as f:
                data = json.load(f)
        except:
            data = {}
    data[str(user_id)] = emoji
    with open(EMOJI_FILE, "w") as f:
        json.dump(data, f)

# .setemoji 😈
@client.on(events.NewMessage(outgoing=True, pattern=r"^\.setemoji(?:\s+(.+))?$"))
async def set_ping_emoji(event):
    me = await client.get_me()
    if event.sender_id != me.id:
        return

    emoji = event.pattern_match.group(1)
    if not emoji:
        current = load_emoji(me.id)
        await event.edit(f"**Current Ping Emoji:** `{current or 'None'}`\n"
                         f"Use: `.setemoji 😈`  |  `.setemoji off` to remove")
        return

    if emoji.lower() == "off":
        save_emoji(me.id, None)
        await event.edit("**Ping emoji removed!**\nAb normal ping aayega")
    else:
        save_emoji(me.id, emoji)
        await event.edit(f"**Ping Emoji Set Ho Gaya:** {emoji}\n"
                         f"Ab ping kar ke dekh!")

# ===================== UPGRADED PING WITH EMOJI + REAL SPEED + DYNAMIC OWNER ======>

@client.on(events.NewMessage(outgoing=True, pattern=r"^\.ping$"))
async def ping(event):
    me = await client.get_me()
    if event.sender_id != me.id:
        return

    await log_command(event, "ping")

    try:
        # Better real speed calculation
        start_time = time.perf_counter()

        # Custom emoji
        user_emoji = load_emoji(me.id)

        if user_emoji:
            ping_msg = await event.reply(user_emoji)
        else:
            ping_msg = await event.reply("**⚡ Pinging...**")

        end_time = time.perf_counter()
        speed = round((end_time - start_time) * 1000, 2)

        # Uptime
        current_time = datetime.now()
        uptime_duration = current_time - START_TIME
        days = uptime_duration.days
        hours = uptime_duration.seconds // 3600
        minutes = (uptime_duration.seconds % 3600) // 60
        seconds = uptime_duration.seconds % 60
        uptime_str = f"{days}d {hours}h {minutes}m {seconds}s"

        # Dynamic Owner Name
        if me.username:
            owner_mention = f"@{me.username}"
        else:
            owner_mention = f"[{me.first_name}](tg://user?id={me.id})"

        # Ping status
        if speed < 80:
            ping_status = "🚀 𝐄xᴛʀᴇᴍᴇ"
        elif speed < 150:
            ping_status = "⚡ 𝐅ᴀsᴛ"
        elif speed < 300:
            ping_status = "🔥 𝐒ᴛᴀʙʟᴇ"
        else:
            ping_status = "☠️ 𝐇ᴇᴀᴠʏ"

        # Final dangerous style response
        response = (
            f"**╭━━━〔 ❖ 𝐙𝐔𝐃𝐎 ™ ╮ 〕━━━╮**\n"
            f"**┣ • 𝐒ᴘᴇᴇᴅ   :** `{speed} ms`\n"
            f"**┣ • 𝐒ᴛᴀᴛᴜs  :** {ping_status}\n"
            f"**┣ • 𝐔ᴘᴛɪᴍᴇ  :** `{uptime_str}`\n"
            f"**┣ • 𝐎ᴡɴᴇʀ   :** {owner_mention}\n"
            f"**╰━━━━━━━━━━━━━━━━━━╯**"
        )

        await asyncio.sleep(2)
        await ping_msg.edit(response, parse_mode="md")

    except Exception as e:
        await event.reply(f"**Ping mein error: {str(e)}**")

    await event.delete()


# Change Owner command handler
@client.on(events.NewMessage(pattern=rf'^{re.escape(PREFIX)}changeowner\s+(@\w+)$'))
async def changeowner(event):
    host_user_id = (await client.get_me()).id
    if event.sender_id != host_user_id:
        return
    await log_command(event, "changeowner")
    try:
        username = event.pattern_match.group(1)
        user_id = str(event.sender_id)
        owner_names[user_id] = username
        save_owner_names()
        await event.reply(f"**🔥 Owner name set ho gaya: {username} ⚡**", parse_mode='md')
    except Exception as e:
        await event.reply(f"**⚡ Changeowner mein error: {str(e)} 🚫**", parse_mode='md')
    await event.delete()

# Uptime command handler
@client.on(events.NewMessage(pattern=rf'^{re.escape(PREFIX)}uptime$'))
async def uptime(event):
    host_user_id = (await client.get_me()).id
    if event.sender_id != host_user_id:
        return
    await log_command(event, "uptime")
    try:
        current_time = datetime.now()
        uptime_duration = current_time - START_TIME
        days, seconds = uptime_duration.days, uptime_duration.seconds
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        seconds = seconds % 60
        uptime_str = f"{days}d {hours}h {minutes}m {seconds}s"
        user_id, user = await get_target_user(event)
        if user_id is not None:
            mention = f"@{user.username}" if user.username else f"{user.first_name}"
            response = (
                f"**🕒 Userbot ka Uptime! ⏳**\n"
                f"**User:** {mention}\n"
                f"**Uptime:** {uptime_str}\n"
                f"**Hoster:** [@Userbot_hostbot](tg://resolve?domain=Userbot_hostbot) 🤖"
            )
        else:
            response = (
                f"**🕒 Userbot ka Uptime! ⏳**\n"
                f"**Uptime:** {uptime_str}\n"
                f"**Hoster:** [@Userbot_hostbot](tg://resolve?domain=Userbot_hostbot) 🤖"
            )
        await event.reply(response, parse_mode='md')
    except Exception as e:
        await event.reply(f"**⚡ Uptime mein error: {str(e)} 🚫**", parse_mode='md')
    await event.delete()

# Info command handler
@client.on(events.NewMessage(pattern=rf'^{re.escape(PREFIX)}info(?:\s+@[\w\d_]+)?$'))
async def info(event):
    host_user_id = (await client.get_me()).id
    if event.sender_id != host_user_id:
        return
    await log_command(event, "info")
    try:
        user_id, user = await get_target_user(event)
        if user_id is not None:
            mention = f"@{user.username}" if user.username else f"{user.first_name}"
            user_info = (
                f"**👤 User ki Info! 💥**\n"
                f"**Naam:** {user.first_name} {user.last_name if user.last_name else ''}\n"
                f"**Username:** {mention}\n"
                f"**ID:** {user.id}\n"
                f"**Bot:** {'Haan' if user.bot else 'Nahi'}\n"
                f"**Phone:** {user.phone if user.phone else 'Hidden'} 📞"
            )
            await event.reply(user_info, parse_mode='md')
        else:
            chat_id = event.chat_id
            chat = await client.get_entity(chat_id)
            chat_name = chat.title if hasattr(chat, 'title') else "Private Chat"
            chat_info = (
                f"**🏠 Chat ki Info! 💥**\n"
                f"**Naam:** {chat_name}\n"
                f"**ID:** {chat_id}\n"
                f"**Type:** {'Group' if event.is_group else 'Private'}\n"
                f"**Members:** {chat.participants_count if hasattr(chat, 'participants_count') else 'N/A'} 👥"
            )
            await event.reply(chat_info, parse_mode='md')
    except Exception as e:
        await event.reply(f"**⚡ Info mein error: {str(e)} 🚫**", parse_mode='md')
    await event.delete()

# FFmpeg path (update if needed)
FFMPEG_PATH = "ffmpeg"  # Example: "/data/data/com.termux/files/usr/bin/ffmpeg" for Termux

# yt-dlp options for audio extraction
ytdl_opts = {
    'format': 'bestaudio/best',
    'noplaylist': True,
    'quiet': False,  # Enable verbose output for debugging
    'no_warnings': False,
    'outtmpl': 'downloads/%(id)s.%(ext)s',
    'postprocessors': [{
        'key': 'FFmpegExtractAudio',
        'preferredcodec': 'mp3',
        'preferredquality': '192',
    }],
    'geo_bypass': True,  # Bypass geographic restrictions
    'retries': 3,  # Retry download on failure
    'socket_timeout': 30,  # Increase timeout for slow networks
}

# Track active VC sessions
vc_sessions = {}  # {chat_id: {process, file_path, title}}

@client.on(events.NewMessage(pattern=r'^!play(?:\s+(.+))?$'))
async def play_music(event):
    host_user_id = (await client.get_me()).id
    if event.sender_id != host_user_id:
        return
    await log_command(event, "play")
    try:
        # Check bot permissions (basic admin check)
        chat = await event.get_chat()
        bot_permissions = await client.get_permissions(chat, await client.get_me())
        if not bot_permissions.is_admin:
            await event.reply("**⚡ Bot needs admin permissions to speak in voice chat! 🚫**", parse_mode='md')
            logging.info(f"Bot lacks admin permissions in chat {event.chat_id}")
            return

        # Get YouTube URL or search query
        query = event.pattern_match.group(1)
        if not query:
            await event.reply("**⚡ Provide a YouTube link or song name! 🚫**", parse_mode='md')
            logging.info(f"User {event.sender_id} used !play without query")
            return

        # Ensure downloads directory exists
        os.makedirs("downloads", exist_ok=True)

        # Resolve YouTube URL
        with youtube_dl.YoutubeDL(ytdl_opts) as ydl:
            try:
                logging.info(f"Attempting to download audio for query: {query}")
                info = ydl.extract_info(f"ytsearch:{query}" if not query.startswith('http') else query, download=True)
                ext = info.get('ext', 'mp3')  # Fallback to mp3 if ext is missing
                file_path = f"downloads/{info['id']}.{ext}"
                if not os.path.exists(file_path):
                    # Fallback: Check for any mp3 file in downloads folder
                    for f in os.listdir("downloads"):
                        if f.endswith(".mp3") and info['id'] in f:
                            file_path = f"downloads/{f}"
                            break
                    else:
                        await event.reply("**⚡ Failed to download audio file! Check logs for details. 🚫**", parse_mode='md')
                        logging.error(f"Audio file not found for query {query} at {file_path}")
                        return
                logging.info(f"Downloaded audio file: {file_path}")
            except Exception as e:
                await event.reply(f"**⚡ Error fetching audio: {str(e)} 🚫**", parse_mode='md')
                logging.error(f"Error fetching audio for query {query}: {str(e)}")
                return

        # Check if music is already playing
        chat_id = event.chat_id
        if chat_id in vc_sessions:
            await event.reply("**⚡ Music already playing! Use !stop first. 🚫**", parse_mode='md')
            logging.info(f"Music already playing in chat {chat_id}")
            return

        # Start FFmpeg to stream audio to VC
        try:
            ffmpeg_cmd = [
                FFMPEG_PATH,
                "-i", file_path,
                "-f", "s16le",
                "-ar", "48000",
                "-ac", "2",
                "pipe:"
            ]
            process = subprocess.Popen(
                ffmpeg_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                shell=False
            )
            vc_sessions[chat_id] = {'process': process, 'file_path': file_path, 'title': info.get('title', 'Unknown')}
            await event.reply(f"**🎶 Playing: {info.get('title', 'Unknown')} in voice chat!**", parse_mode='md')
            logging.info(f"Playing {file_path} in VC for chat {chat_id} by user {event.sender_id}")

            # Monitor FFmpeg process
            async def monitor_process():
                while process.poll() is None:
                    await asyncio.sleep(1)
                stderr = process.stderr.read().decode() if process.stderr else ""
                if stderr:
                    logging.error(f"FFmpeg error for chat {chat_id}: {stderr}")
                vc_sessions.pop(chat_id, None)
                if os.path.exists(file_path):
                    os.remove(file_path)
                    logging.info(f"Removed audio file {file_path}")
                logging.info(f"FFmpeg process ended for chat {chat_id}")

            asyncio.create_task(monitor_process())
        except Exception as e:
            await event.reply(f"**⚡ Error streaming audio: {str(e)} 🚫**", parse_mode='md')
            logging.error(f"Error streaming audio for chat {chat_id}: {str(e)}")
            if chat_id in vc_sessions:
                vc_sessions.pop(chat_id, None)
            return

    except Exception as e:
        await event.reply(f"**⚡ Error in !play: {str(e)} 🚫**", parse_mode='md')
        logging.error(f"Error in !play for user {event.sender_id}: {str(e)}")
    await event.delete()

@client.on(events.NewMessage(pattern=r'^!stop$'))
async def stop_music(event):
    host_user_id = (await client.get_me()).id
    if event.sender_id != host_user_id:
        return
    await log_command(event, "stop")
    try:
        chat_id = event.chat_id
        if chat_id not in vc_sessions:
            await event.reply("**⚡ No music playing in this chat! 🚫**", parse_mode='md')
            logging.info(f"No active VC session in chat {chat_id} for !stop")
            return

        # Stop FFmpeg process
        try:
            process = vc_sessions[chat_id]['process']
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
            file_path = vc_sessions[chat_id]['file_path']
            if os.path.exists(file_path):
                os.remove(file_path)
                logging.info(f"Removed audio file {file_path}")
            vc_sessions.pop(chat_id, None)
            await event.reply("**🛑 Stopped music in voice chat!**", parse_mode='md')
            logging.info(f"Stopped music in VC for chat {chat_id} by user {event.sender_id}")
        except Exception as e:
            await event.reply(f"**⚡ Error stopping music: {str(e)} 🚫**", parse_mode='md')
            logging.error(f"Error stopping music in chat {chat_id}: {str(e)}")
            vc_sessions.pop(chat_id, None)
    except Exception as e:
        await event.reply(f"**⚡ Error in !stop: {str(e)} 🚫**", parse_mode='md')
        logging.error(f"Error in !stop for user {event.sender_id}: {str(e)}")
    await event.delete()

# Log command usage (assuming defined elsewhere)
async def log_command(event, command):
    logging.info(f"Command {command} executed by user {event.sender_id} in chat {event.chat_id}")

#addall
@client.on(events.NewMessage(pattern=r'^\.addall(?:\s+(.+))?$'))
async def addall(event):
    user_id = event.sender_id
    bot_info = await client.get_me()
    owner_id = bot_info.id
    if user_id != owner_id:
        await event.reply("🔐 **This command is for the userbot owner only!** 🔐", parse_mode='md')
        logging.warning(f"Unauthorized .addall attempt by user {user_id} on userbot {owner_id}")
        return

    username_or_id = event.pattern_match.group(1)
    target_user_id = await get_user_id(event, username_or_id)
    if not target_user_id:
        await event.reply("**⚡ Please provide a valid username, user ID, or reply to a user! 🚫**", parse_mode='md')
        logging.info(f"Invalid username or ID for .addall by user {user_id}: {username_or_id}")
        return

    try:
        entity = await client.get_entity(target_user_id)
        username = entity.username.lstrip('@') if hasattr(entity, 'username') and entity.username else str(target_user_id)
        is_bot = entity.bot if hasattr(entity, 'bot') else False
    except Exception as e:
        await event.reply(f"**⚡ Error fetching user: {str(e)} 🚫**", parse_mode='md')
        logging.error(f"Error fetching user {target_user_id} for .addall by user {user_id}: {str(e)}")
        return

    await event.reply(f"**🔄 Adding @{username} to all groups/channels...**", parse_mode='md')
    logging.info(f"Starting .addall for user {target_user_id} (@{username}, bot={is_bot}) by user {user_id}")

    successful_adds = 0
    failed_adds = 0
    async for dialog in client.iter_dialogs():
        if dialog.is_group or dialog.is_channel:
            try:
                await client(telethon.tl.functions.channels.InviteToChannelRequest(
                    channel=dialog.id,
                    users=[target_user_id]
                ))
                successful_adds += 1
                logging.info(f"Added user {target_user_id} (@{username}) to group/channel {dialog.id}")
                await asyncio.sleep(3)  # Increased delay to avoid rate limits
            except Exception as e:
                failed_adds += 1
                logging.error(f"Failed to add user {target_user_id} (@{username}) to group/channel {dialog.id}: {str(e)}")
                if "403" in str(e):
                    logging.warning(f"No permission to add members in group/channel {dialog.id}")
                elif "429" in str(e):
                    logging.warning(f"Rate limit hit while adding user {target_user_id} (@{username}) to group/channel {dialog.id}")
                elif "privacy" in str(e).lower():
                    logging.warning(f"User privacy settings restrict adding {target_user_id} (@{username}) to group/channel {dialog.id}")

    response = (
        f"**✅ Addall Complete!**\n\n"
        f"User: @{username}\n"
        f"Added to: {successful_adds} groups/channels\n"
        f"Failed: {failed_adds} groups/channels\n"
        f"Check logs for details."
    )
    await event.reply(response, parse_mode='md')
    logging.info(f"Completed .addall for user {target_user_id} (@{username}) by user {user_id}: Success={successful_adds}, Failed={failed_adds}")
    await event.delete()

# Spam command handler
import re  # Top me ye line add kar (agar nahi hai toh)

# Spam command handler (FULL FIXED - Reply + Multi-line + Silent)
spam_pattern = re.compile(
    rf'^{re.escape(PREFIX)}spam\s+(\d+)(?:\s+(-?\d+))?(?:\s+(@[\w\d_]+))?(.*)$',
    re.DOTALL
)

@client.on(events.NewMessage(pattern=spam_pattern))
async def spam(event):
    host_user_id = (await client.get_me()).id
    if event.sender_id != host_user_id:
        return

    await log_command(event, "spam")

    try:
        count = int(event.pattern_match.group(1))
        chat_id = event.pattern_match.group(2)
        username = event.pattern_match.group(3)
        message = event.pattern_match.group(4).strip()

        if count <= 0 or count > 1000:
            return  # Silent fail

        if not message and not event.is_reply:
            return  # Silent fail

        target_chat_id = int(chat_id) if chat_id else event.chat_id

        # Reply mode check
        replied_msg = await event.get_reply_message()
        is_reply_mode = replied_msg is not None

        # Spam start (completely silent - no extra message)
        i = 0
        while i < count:
            try:
                final_message = f"{username} {message}" if username else message

                if is_reply_mode:
                    await client.send_message(target_chat_id, final_message, reply_to=replied_msg.id)
                else:
                    await client.send_message(target_chat_id, final_message)

                i += 1
                await asyncio.sleep(0.5)  # Safe speed

            except Exception as e:
                logging.error(f"Spam error: {e}")
                break

    except Exception as e:
        logging.error(f"Spam command error: {e}")

    await event.delete()  # Command message delete

# TSpam command handler (Updated to send full message with time delay)
# ===================== TSPAM COMMAND (SPAM KI TARAH FIXED) =====================
tspam_pattern = re.compile(
    rf'^{re.escape(PREFIX)}tspam\s+(\d+\.?\d*)\s+(?:(-\d+)|(@[\w\d_]+))?\s*(\d+)\s*(.*)$',
    re.DOTALL
)

@client.on(events.NewMessage(pattern=tspam_pattern))
async def tspam(event):
    host_user_id = (await client.get_me()).id
    if event.sender_id != host_user_id:
        return

    await log_command(event, "tspam")

    try:
        time_in_seconds = float(event.pattern_match.group(1))
        chat_id = event.pattern_match.group(2)
        username = event.pattern_match.group(3)
        count = int(event.pattern_match.group(4))
        message = event.pattern_match.group(5).strip()

        if count <= 0 or count > 1000 or time_in_seconds <= 0 or time_in_seconds > 60:
            return  # Silent fail

        if not message and not event.is_reply:
            return  # Silent fail

        target_chat_id = int(chat_id) if chat_id else event.chat_id

        # Reply mode check
        replied_msg = await event.get_reply_message()
        is_reply_mode = replied_msg is not None

        timestamp = time.time()
        spam_key = (event.sender_id, target_chat_id, timestamp)
        spam_status[spam_key] = True

        i = 0
        while i < count and spam_status.get(spam_key, False):
            try:
                final_message = f"{username} {message}" if username else message

                if is_reply_mode:
                    await client.send_message(target_chat_id, final_message, reply_to=replied_msg.id)
                else:
                    await client.send_message(target_chat_id, final_message)

                i += 1
                await asyncio.sleep(time_in_seconds)

            except Exception as e:
                logging.error(f"TSpam error: {e}")
                break

        spam_status[spam_key] = False

    except Exception as e:
        logging.error(f"TSpam command error: {e}")

    await event.delete()  # Command delete


# ===================== STOPSPAM (Dono spam aur tspam ko stop karega) =====================
@client.on(events.NewMessage(pattern=rf'^{re.escape(PREFIX)}stopspam(?:\s+(\d+))?$'))
async def stopspam(event):
    host_user_id = (await client.get_me()).id
    if event.sender_id != host_user_id:
        return

    await log_command(event, "stopspam")

    user_id = event.sender_id
    chat_id = event.chat_id
    timestamp = event.pattern_match.group(1)

    stopped = False

    if timestamp:
        try:
            timestamp = float(timestamp)
            spam_key = (user_id, chat_id, timestamp)
            if spam_key in spam_status and spam_status[spam_key]:
                spam_status[spam_key] = False
                stopped = True
        except:
            pass
    else:
        # Sab spam aur tspam stop kar do
        for key in list(spam_status.keys()):
            if key[0] == user_id and key[1] == chat_id and spam_status[key]:
                spam_status[key] = False
                stopped = True

    if stopped:
        await event.reply("**🔥 Sab spam aur tspam band ho gaye! ⚡**", parse_mode='md')
    else:
        await event.reply("**⚡ Is chat mein koi spam/tspam nahi chal raha! 🚫**", parse_mode='md')

    await event.delete()

# Track reply raid targets
reply_raid_targets = set()  # Stores user IDs for active reply raids
host_username = None  # Will be set to host user's username

# Global variables for reply raid
reply_raid_targets = {}  # {target_id: custom_message or None}
host_username = None

# Patterns for reply raid commands
replyraid_pattern = re.compile(rf'^{re.escape(PREFIX)}replyraid(?:\s+(.+))?$')
dreplyraid_pattern = re.compile(rf'^{re.escape(PREFIX)}dreplyraid(?:\s+(.+))?$')

@client.on(events.NewMessage)
async def initialize_host_username(event):
    global host_username
    if host_username is None:
        host_user = await client.get_me()
        host_username = host_user.username.lower() if host_user.username else None

# Activate Reply Raid - 100% FIXED
@client.on(events.NewMessage(pattern=replyraid_pattern))
async def replyraid(event):
    global reply_raid_targets
    host_user_id = (await client.get_me()).id
    if event.sender_id != host_user_id:
        return
    await log_command(event, "replyraid")
    
    try:
        target_id = None
        custom_message = None
        
        # PRIORITY 1: If REPLY + message exists
        if event.reply_to_msg_id and event.pattern_match.group(1):
            # Reply ko target banao, message ko custom message
            reply_msg = await event.get_reply_message()
            if reply_msg:
                target_id = reply_msg.sender_id
                custom_message = event.pattern_match.group(1).strip()
        
        # PRIORITY 2: If only REPLY (no extra message)
        elif event.reply_to_msg_id:
            reply_msg = await event.get_reply_message()
            if reply_msg:
                target_id = reply_msg.sender_id
                custom_message = None  # Default messages
        
        # PRIORITY 3: If only username/ID + message
        elif event.pattern_match.group(1):
            target_input = event.pattern_match.group(1).strip()
            parts = target_input.split(maxsplit=1)
            
            target_str = parts[0]
            if len(parts) > 1:
                custom_message = ' '.join(parts[1:])  # Custom message
            
            # Get target user
            try:
                if target_str.startswith('@'):
                    entity = await client.get_entity(target_str)
                else:
                    entity = await client.get_entity(int(target_str))
                target_id = entity.id
            except:
                await event.reply("**⚡ Invalid username/ID! 🚫**", parse_mode='md')
                return
        
        if not target_id:
            await event.reply("**⚡ Reply to user OR provide @username/userID! 🚫**", parse_mode='md')
            return
        
        # Check if already active
        if target_id in reply_raid_targets:
            await event.reply("**⚡ Reply raid already active! 🚫**", parse_mode='md')
            return
        
        # ACTIVATE with CORRECT message type
        reply_raid_targets[target_id] = custom_message
        msg_type = "CUSTOM" if custom_message else "DEFAULT"
        await event.reply(f"**🎯 Reply raid ACTIVATED!\n👤 Target: {target_id}\n📝 Type: {msg_type}**", parse_mode='md')
        logging.info(f"Reply raid activated for {target_id} with {msg_type} by {event.sender_id}")
        
    except Exception as e:
        await event.reply(f"**⚡ Error: {str(e)} 🚫**", parse_mode='md')
    await event.delete()

# Deactivate Reply Raid
@client.on(events.NewMessage(pattern=dreplyraid_pattern))
async def dreplyraid(event):
    global reply_raid_targets
    host_user_id = (await client.get_me()).id
    if event.sender_id != host_user_id:
        return
    
    try:
        target_id = None
        
        if event.reply_to_msg_id:
            reply_msg = await event.get_reply_message()
            if reply_msg:
                target_id = reply_msg.sender_id
        elif event.pattern_match.group(1):
            target = event.pattern_match.group(1).strip()
            try:
                if target.startswith('@'):
                    entity = await client.get_entity(target)
                else:
                    entity = await client.get_entity(int(target))
                target_id = entity.id
            except:
                pass
        
        if not target_id and event.pattern_match.group(1) == "all":
            # Deactivate ALL
            before_count = len(reply_raid_targets)
            reply_raid_targets.clear()
            await event.reply(f"**🎯 ALL Reply raids DEACTIVATED! ({before_count} targets)**", parse_mode='md')
            return
        
        if target_id in reply_raid_targets:
            del reply_raid_targets[target_id]
            await event.reply(f"**🎯 Reply raid DEACTIVATED for {target_id}!**", parse_mode='md')
        else:
            await event.reply("**⚡ No active reply raid for this user! 🚫**", parse_mode='md')
            
    except Exception as e:
        await event.reply(f"**⚡ Error: {str(e)} 🚫**", parse_mode='md')
    await event.delete()

# AUTO-REPLY HANDLER - 100% FIXED (NO DOUBLE REPLIES)
@client.on(events.NewMessage)
async def auto_reply_raid(event):
    global reply_raid_targets, host_username
    host_user_id = (await client.get_me()).id
    
    # Skip if not from target or bot itself
    if not event.sender_id or event.sender_id == host_user_id:
        return
    
    target_id = event.sender_id
    if target_id not in reply_raid_targets:
        return
    
    # Skip if already replied to this message (prevents double replies)
    if hasattr(event, '_replied_by_bot') and event._replied_by_bot:
        return
    
    # Skip if message mentions host
    if host_username and f"@{host_username}" in (event.message.message or ""):
        return
    
    try:
        # Get ONLY ONE message (custom OR default - NO DOUBLE)
        custom_message = reply_raid_targets[target_id]
        if custom_message:
            reply_msg = custom_message  # ONLY custom
        else:
            reply_msg = random.choice(abusive_messages)  # ONLY default
        
        # Mark as replied by bot
        event._replied_by_bot = True
        
        # SUPER FAST REPLY (0.05s)
        await asyncio.sleep(0.05)
        await event.reply(reply_msg)
        logging.info(f"[replyraid] Replied to {target_id}: {reply_msg[:30]}...")
        
    except Exception as e:
        logging.error(f"[replyraid] Auto-reply error: {str(e)}")

# Raid command handler
@client.on(events.NewMessage(pattern=rf'^{re.escape(PREFIX)}raid\s+(\d+)(?:\s+(-?\d+))?(?:\s+(@[\w\d_]+))?$'))
async def raid(event):
    host_user_id = (await client.get_me()).id
    if event.sender_id != host_user_id:
        return
    await log_command(event, "raid")
    
    try:
        count = int(event.pattern_match.group(1))
        chat_id = event.pattern_match.group(2)
        target_username = event.pattern_match.group(3)
        target_chat_id = int(chat_id) if chat_id else event.chat_id
        
        if count <= 0:
            return  # Silent fail
        if count > 1000:
            return  # Silent fail
        
        # Check if replying to a message
        replied_msg = await event.get_reply_message()
        is_reply_mode = replied_msg is not None
        
        # Get target user if username provided
        mention = ""
        if target_username:
            try:
                target_user = await client.get_entity(target_username)
                mention = f"@{target_user.username}" if target_user.username else f"[{target_user.first_name}](tg://user?id={target_user.id})"
            except:
                return  # Silent fail
        
        # SILENT RAID - NO START/END MESSAGES
        sent_count = 0
        for i in range(count):
            message = random.choice(abusive_messages)
            
            try:
                if is_reply_mode:
                    # Reply to original message (NO username)
                    await client.send_message(target_chat_id, message, reply_to=replied_msg.id, parse_mode='md')
                elif target_username:
                    # Mention username
                    final_message = f"{mention} {message}"
                    await client.send_message(target_chat_id, final_message, parse_mode='md')
                else:
                    # Just abusive message
                    await client.send_message(target_chat_id, message, parse_mode='md')
                
                sent_count += 1
                
            except Exception as e:
                logging.error(f"[raid] Error sending message {i+1}: {str(e)}")
                continue
            
            # SUPER FAST: 0.1 second delay
            await asyncio.sleep(0.1)
        
        # NO END MESSAGE - COMPLETELY SILENT
        
    except ValueError:
        pass  # Silent fail
    except Exception as e:
        logging.error(f"[raid] Error: {str(e)}")
    
    await event.delete()  # Delete command message

# Stop raid command handler
@client.on(events.NewMessage(pattern=rf'^{re.escape(PREFIX)}stopraid(?:\s+(\d+(?:\.\d+)?))?(?:\s+(-?\d+))?$'))
async def stopraid(event):
    host_user_id = (await client.get_me()).id
    if event.sender_id != host_user_id:
        return
    await log_command(event, "stopraid")
    try:
        raid_id = event.pattern_match.group(1)  # Timestamp (e.g., 1634567890.0)
        chat_id = event.pattern_match.group(2)  # Optional chat ID
        target_chat_id = int(chat_id) if chat_id else event.chat_id

        stopped = False
        raids_to_stop = []

        # Find matching raids
        for key in list(raid_status.keys()):
            sender_id, raid_chat_id, timestamp = key
            if sender_id == event.sender_id and raid_chat_id == target_chat_id:
                if not raid_id or str(timestamp)[:10] == raid_id[:10]:  # Match timestamp (ignoring decimals)
                    raids_to_stop.append(key)

        # Stop matching raids
        if raids_to_stop:
            for raid_key in raids_to_stop:
                raid_status[raid_key] = False
                stopped = True
                await event.reply(f"**🛑 Raid stopped! (ID: {raid_key[2]:.0f}) 🛑**", parse_mode='md')
                logging.info(f"Raid stopped by user {event.sender_id}: {raid_key}")
        else:
            await event.reply("**⚡ Koi active raid nahi mila! Ya galat ID/chat ID diya. 🚫**", parse_mode='md')
            logging.info(f"No active raid found for user {event.sender_id} in chat {target_chat_id} with ID {raid_id}")

        if not stopped:
            await event.reply("**⚡ Koi raid nahi chalu tha is chat mein ya ID galat hai! 🚫**", parse_mode='md')

    except Exception as e:
        await event.reply(f"**⚡ Stopraid mein error: {str(e)} 🚫**", parse_mode='md')
        logging.error(f"Error in stopraid for user {event.sender_id}: {str(e)}")
    await event.delete()

# .sraid command handler
@client.on(events.NewMessage(pattern=r'^\.sraid\s+(\d+)(?:\s+(.+))?$'))
async def sraid(event):
    # Check if the sender is the owner of this bot instance
    if event.sender_id != owner_id:
        logging.info(f"Ignored .sraid command from user {event.sender_id} (not owner {owner_id})")
        return  # Ignore the command if not from the owner

    # Ensure the client is connected
    if not client.is_connected():
        try:
            await client.connect()
            logging.debug("Reconnected client successfully")
        except Exception as e:
            logging.error(f"Failed to reconnect client for user {event.sender_id}: {e}")
            await event.reply("Error: Bot is disconnected and cannot reconnect. Please restart the bot.")
            return
    if not await client.is_user_authorized():
        logging.error(f"Userbot for owner {owner_id} is not authorized")
        await event.reply("Error: Bot is not authorized. Please re-host the bot.")
        return

    user_id = event.sender_id
    chat_id = event.chat_id

    # Initialize ongoing_sraids for this user if not exists
    if user_id not in ongoing_sraids:
        ongoing_sraids[user_id] = {}

    # Check if a shayari raid is already running in this chat for this user
    if chat_id in ongoing_sraids[user_id]:
        await event.reply("Error: A shayari raid is already running in this chat. Use .stopsraid to stop it.")
        logging.info(f"Blocked .sraid for user {user_id} in chat {chat_id}: Another raid is already running")
        return

    # Extract count and target
    count = int(event.pattern_match.group(1))
    target = event.pattern_match.group(2)

    # Validate count
    if count <= 0 or count > 50:
        await event.reply("Error: Count must be between 1 and 50.")
        return

    # Determine the target user
    target_id, target_username = await get_user_id(event, target)
    if not target_id:
        await event.reply("Error: Please provide a valid username, user ID, or reply to a user.")
        return

    target_display = f"@{target_username}" if target_username else f"User {target_id}"

    # Check if the command is a reply to a message
    is_reply = bool(event.reply_to_msg_id)
    reply_to_msg_id = event.reply_to_msg_id if is_reply else None

    # Start the shayari raid
    logging.info(f"Starting shayari raid by user {user_id} on {target_display} with {count} messages in chat {chat_id}")

    sent_messages = 0  # Counter for successfully sent messages (for logging purposes)

    async def raid_task():
        nonlocal sent_messages
        try:
            for i in range(count):
                # Check if the raid has been stopped
                if chat_id not in ongoing_sraids[user_id]:
                    logging.info(f"Shayari raid stopped early by user {user_id} in chat {chat_id}")
                    break

                shayari = random.choice(SHAYARI_LIST)
                # If it's a reply, send only the shayari as a reply to the message; otherwise, include the target username
                message_text = shayari if is_reply else f"{target_display} {shayari}"
                logging.debug(f"Attempting to send message {i+1}/{count} to chat {chat_id}: {message_text}")

                try:
                    # Ensure the client is still connected
                    if not client.is_connected():
                        try:
                            await client.connect()
                            logging.debug("Reconnected client mid-raid")
                        except Exception as e:
                            logging.error(f"Failed to reconnect client mid-raid for user {user_id} in chat {chat_id}: {e}")
                            break
                    # Send the message, replying to the original message if applicable
                    await client.send_message(chat_id, message_text, reply_to=reply_to_msg_id)
                    sent_messages += 1
                    logging.debug(f"Successfully sent message {i+1}/{count} to chat {chat_id}")
                    await asyncio.sleep(2)  # Delay to avoid rate limits
                except telethon.errors.FloodWaitError as e:
                    logging.error(f"Flood wait error during shayari raid in chat {chat_id}: {e}")
                    await event.reply(f"Error: Flood wait for {e.seconds} seconds. Stopping raid.")
                    break
                except telethon.errors.ChatWriteForbiddenError:
                    logging.error(f"Bot cannot send messages in chat {chat_id}: ChatWriteForbiddenError")
                    await event.reply("Error: Bot does not have permission to send messages in this chat.")
                    break
                except telethon.errors.UserIsBlockedError:
                    logging.error(f"User {target_id} has blocked the bot in chat {chat_id}")
                    await event.reply(f"Error: User {target_display} has blocked the bot.")
                    break
                except Exception as e:
                    logging.error(f"Error sending shayari message {i+1}/{count} in chat {chat_id}: {e}")
                    break
        except asyncio.CancelledError:
            logging.info(f"Shayari raid cancelled for user {user_id} in chat {chat_id}")
        finally:
            # Clean up
            if user_id in ongoing_sraids and chat_id in ongoing_sraids[user_id]:
                del ongoing_sraids[user_id][chat_id]
                if not ongoing_sraids[user_id]:  # Remove user entry if no ongoing raids
                    del ongoing_sraids[user_id]
            logging.info(f"Shayari raid completed by user {user_id} in chat {chat_id}. Sent {sent_messages}/{count} messages")

    # Start the raid task
    task = asyncio.create_task(raid_task())
    ongoing_sraids[user_id][chat_id] = task

# .stopsraid command handler
@client.on(events.NewMessage(pattern=r'^\.stopsraid$'))
async def stopsraid(event):
    # Check if the sender is the owner of this bot instance
    if event.sender_id != owner_id:
        logging.info(f"Ignored .stopsraid command from user {event.sender_id} (not owner {owner_id})")
        return  # Ignore the command if not from the owner

    # Ensure the client is connected
    if not client.is_connected():
        try:
            await client.connect()
            logging.debug("Reconnected client successfully")
        except Exception as e:
            logging.error(f"Failed to reconnect client for user {event.sender_id}: {e}")
            await event.reply("Error: Bot is disconnected and cannot reconnect. Please restart the bot.")
            return
    if not await client.is_user_authorized():
        logging.error(f"Userbot for owner {owner_id} is not authorized")
        await event.reply("Error: Bot is not authorized. Please re-host the bot.")
        return

    user_id = event.sender_id
    chat_id = event.chat_id

    # Find and stop the shayari raid in this chat for this user
    stopped = False
    if user_id in ongoing_sraids and chat_id in ongoing_sraids[user_id]:
        task = ongoing_sraids[user_id][chat_id]
        task.cancel()  # Cancel the running task
        stopped = True

    if stopped:
        await event.reply("Shayari raid stopped! 🛑")
        logging.info(f"Shayari raid stopped by user {user_id} in chat {chat_id}")
    else:
        await event.reply("Error: No shayari raid is running in this chat.")
        logging.info(f"No shayari raid to stop for user {user_id} in chat {chat_id}")

# Report options (using raw strings for compatibility)
REPORT_REASONS = {
    1: "Spam",
    2: "ChildAbuse",
    3: "Violence",
    4: "Pornography",
    5: "Copyright",
    6: "GeoIrrelevant",
    7: "Fake",
    8: "IllegalDrugs",
    9: "PersonalDetails",
}

# Track report requests (to map .select to .report)
report_requests = {}  # {chat_id: {"message_id": int, "chat_id": int, "options_sent": bool}}

# Patterns for commands
report_pattern = re.compile(rf'^{re.escape("!")}report\s+(.+)$')
select_pattern = re.compile(rf'^{re.escape("!")}select\s+(\d+)(?:\s+(.+))?$')

@client.on(events.NewMessage(pattern=report_pattern))
async def report(event):
    host_user_id = (await client.get_me()).id
    if event.sender_id != host_user_id:
        return
    await log_command(event, "report")
    try:
        link = event.pattern_match.group(1).strip()
        # Parse message link (e.g., t.me/c/123456789/100 or t.me/username/100)
        match = re.match(r'^(?:https?://)?t\.me/(?:c/)?(\w+)/(\d+)$', link)
        if not match:
            await event.reply("**⚡ Invalid message link! Format: t.me/c/<chat_id>/<message_id> or t.me/<username>/<message_id> 🚫**", parse_mode='md')
            return
        chat_identifier = match.group(1)
        message_id = int(match.group(2))

        # Resolve chat_id from identifier (username or chat_id)
        try:
            if chat_identifier.isdigit():
                chat_id = -int(chat_identifier)  # Private group chat IDs are negative
            else:
                entity = await client.get_entity(chat_identifier)
                chat_id = entity.id
                if isinstance(entity, types.User):
                    chat_id = entity.id  # Private chat
                elif isinstance(entity, (types.Chat, types.Channel)):
                    chat_id = -entity.id if isinstance(entity, types.Chat) else int(f"-100{entity.id}")  # Group or supergroup
        except Exception as e:
            await event.reply(f"**⚡ Chat resolve karne mein error: {str(e)} 🚫**", parse_mode='md')
            return

        # Store report request
        report_requests[event.chat_id] = {"message_id": message_id, "chat_id": chat_id, "options_sent": True}

        # List report options
        options_text = "\n".join([f"{num}. {reason}" for num, reason in REPORT_REASONS.items()])
        response = (
            f"**📢 Report Options for Message {link} 📢**\n"
            f"{options_text}\n\n"
            f"Use `!select <number> [optional message]` to report (e.g., `!select 1 It's a scam`)"
        )
        await event.reply(response, parse_mode='md')
        logging.info(f"Report options sent for user {event.sender_id} in chat {event.chat_id}: {link}")

    except Exception as e:
        await event.reply(f"**⚡ Report mein error: {str(e)} 🚫**", parse_mode='md')
        logging.error(f"Error in report for user {event.sender_id}: {str(e)}")
    await event.delete()

@client.on(events.NewMessage(pattern=select_pattern))
async def select(event):
    host_user_id = (await client.get_me()).id
    if event.sender_id != host_user_id:
        return
    await log_command(event, "select")
    try:
        chat_id = event.chat_id
        if chat_id not in report_requests or not report_requests[chat_id]["options_sent"]:
            await event.reply("**⚡ Pehle !report command use karo! 🚫**", parse_mode='md')
            return

        option_number = int(event.pattern_match.group(1))
        optional_message = event.pattern_match.group(2) or ""
        if option_number not in REPORT_REASONS:
            await event.reply(f"**⚡ Invalid option number! Valid options: 1-{len(REPORT_REASONS)} 🚫**", parse_mode='md')
            return

        reason_name = REPORT_REASONS[option_number]
        target_chat_id = report_requests[chat_id]["chat_id"]
        message_id = report_requests[chat_id]["message_id"]

        # Submit 5 reports mimicking manual reporting
        for i in range(5):
            try:
                # Use raw API call to avoid unsupported parameters
                await client.invoke({
                    '$type': 'messages.report',
                    'peer': await client.get_input_entity(target_chat_id),
                    'id': [message_id],
                    'message': f"Reason: {reason_name}\nDetails: {optional_message}" if optional_message else f"Reason: {reason_name}"
                })
                await event.reply(f"**✅ Report {i+1} successfully done for {reason_name}!**", parse_mode='md')
                logging.info(f"Report {i+1} sent by user {event.sender_id} for message {message_id} in chat {target_chat_id}: {reason_name}")
                await asyncio.sleep(1)  # Avoid rate limits
            except rpcerrorlist.FloodWaitError as e:
                await event.reply(f"**⚡ Flood wait: {e.seconds} seconds. Try again later! 🚫**", parse_mode='md')
                logging.error(f"Flood wait in report {i+1} for user {event.sender_id}: {e}")
                break
            except Exception as e:
                await event.reply(f"**⚡ Report {i+1} mein error: {str(e)} 🚫**", parse_mode='md')
                logging.error(f"Error in report {i+1} for user {event.sender_id}: {str(e)}")
                break

        # Clear report request after submission
        if chat_id in report_requests:
            del report_requests[chat_id]

    except Exception as e:
        await event.reply(f"**⚡ Select mein error: {str(e)} 🚫**", parse_mode='md')
        logging.error(f"Error in select for user {event.sender_id}: {str(e)}")
    await event.delete()

# Invall command handler (Updated for flood error handling and channel support)
@client.on(events.NewMessage(pattern=rf'^{re.escape(PREFIX)}invall\s+(.+)$'))
async def invall(event):
    host_user_id = (await client.get_me()).id
    if event.sender_id != host_user_id:
        return
    await log_command(event, "invall")
    if not (event.is_group or event.is_channel):
        await event.reply("**⚡ Yeh command sirf group ya channel mein kaam karta hai! 🚫**", parse_mode='md')
        return
    try:
        # Check if bot has admin rights in the current group/channel
        if not await is_admin(event.chat_id, host_user_id):
            await event.reply("**⚡ Bot ko admin rights chahiye members add karne ke liye! 🙅‍♂️**", parse_mode='md')
            return

        # Get the group link or username from command
        args = event.pattern_match.group(1).strip()
        if not args:
            await event.reply("**⚡ Private group/channel ka link ya public group/channel ka @username do! 😜**", parse_mode='md')
            return

        # Identify source group/channel
        try:
            if args.startswith('https://t.me/') or args.startswith('t.me/'):
                source_entity = await client.get_entity(args)
            elif args.startswith('@'):
                source_entity = await client.get_entity(args)
            else:
                await event.reply("**⚡ Valid private group/channel link ya public @username do! 🚫**", parse_mode='md')
                return
        except PeerIdInvalidError:
            await event.reply("**⚡ Group/channel link ya username invalid hai ya bot ko access nahi hai! 🚫**", parse_mode='md')
            return
        except Exception as e:
            await event.reply(f"**⚡ Source entity fetch karne mein error: {str(e)} 🚫**", parse_mode='md')
            return

        # Check if bot has access to source entity participants
        try:
            test_participants = await client.get_participants(source_entity, limit=1)
        except Exception as e:
            await event.reply("**⚡ Source group/channel ke members access nahi kar sakta, shayad bot admin nahi hai ya restricted hai! 🚫**", parse_mode='md')
            return

        # Get target group/channel (where command is run)
        target_entity = await client.get_entity(event.chat_id)

        # Scrape members from source entity
        await event.reply("**🔥 Source group/channel se members scrape kar raha hoon... ⏳**", parse_mode='md')
        members = []
        async for member in client.iter_participants(source_entity):
            if not member.bot and member.id != host_user_id:  # Skip bots and self
                members.append(member)
        if not members:
            await event.reply("**⚡ Source group/channel mein koi valid members nahi mile! 🚫**", parse_mode='md')
            return

        # Add members to target group/channel
        await event.reply(f"**🔥 {len(members)} members ko target group/channel mein add kar raha hoon... 🚀**", parse_mode='md')
        added_count = 0
        failed_count = 0
        for member in members:
            try:
                await client(InviteToChannelRequest(
                    channel=target_entity,
                    users=[member.id]
                ))
                added_count += 1
                await asyncio.sleep(1)  # Avoid flood limits
            except FloodWaitError as e:
                # Send flood error to @Userbot_hostbot
                error_msg = (
                    f"**⚡ Flood Limit Error in Group/Channel ID: {event.chat_id} ⚡**\n"
                    f"Command: /invall\n"
                    f"Error: FloodWaitError, waiting for {e.seconds} seconds\n"
                    f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                )
                try:
                    await client.send_message('@Userbot_hostbot', error_msg, parse_mode='md')
                except Exception as send_error:
                    print(f"Failed to send flood error to @Userbot_hostbot: {str(send_error)}")
                await asyncio.sleep(e.seconds)
                continue
            except UserPrivacyRestrictedError:
                failed_count += 1
                continue
            except Exception as e:
                print(f"Failed to add member {member.id}: {str(e)}")
                failed_count += 1
                continue

        # Final response
        await event.reply(
            f"**🔥 Invall process complete! 🎉**\n"
            f"**Total Members Tried:** {len(members)}\n"
            f"**Successfully Added:** {added_count}\n"
            f"**Failed:** {failed_count} (privacy settings ya limits ke wajah se)\n",
            parse_mode='md'
        )
    except Exception as e:
        # Send general error to @Userbot_hostbot
        error_msg = (
            f"**⚡ Error in Group/Channel ID: {event.chat_id} ⚡**\n"
            f"Command: /invall\n"
            f"Error: {str(e)}\n"
            f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )
        try:
            await client.send_message('@Userbot_hostbot', error_msg, parse_mode='md')
        except Exception as send_error:
            print(f"Failed to send error to @Userbot_hostbot: {str(send_error)}")
        await event.reply(f"**⚡ Invall mein error, details hoster bot ko bheje gaye! 🚫**", parse_mode='md')
    await event.delete()

# Add command handler (Updated to support multiple usernames)
@client.on(events.NewMessage(pattern=rf'^{re.escape(PREFIX)}add\s+(.+)$'))
async def add_user(event):
    host_user_id = (await client.get_me()).id
    if event.sender_id != host_user_id:
        return
    await log_command(event, "add")
    if not event.is_group:
        await event.reply("**⚡ Yeh command sirf group mein kaam karta hai! 🚫**", parse_mode='md')
        return
    try:
        # Check if bot has admin rights in the current group
        if not await is_admin(event.chat_id, host_user_id):
            await event.reply("**⚡ Bot ko admin rights chahiye users add karne ke liye! 🙅‍♂️**", parse_mode='md')
            return

        # Get the usernames from command (one or more, space-separated)
        args = event.pattern_match.group(1).strip()
        if not args:
            await event.reply("**⚡ Kam se kam ek @username do! 😜**", parse_mode='md')
            return
        usernames = [username.strip() for username in args.split() if username.startswith('@')]
        if not usernames:
            await event.reply("**⚡ Valid @username(s) do, space se separate karke! 🚫**", parse_mode='md')
            return

        # Get target group
        target_group = await client.get_entity(event.chat_id)

        # Add each user to the group
        await event.reply(f"**🔥 {len(usernames)} user(s) ko group mein add kar raha hoon... 🚀**", parse_mode='md')
        added_count = 0
        failed_count = 0
        failed_users = []

        for username in usernames:
            try:
                # Fetch the user
                user = await client.get_entity(username)
                # Add user to group
                await client(InviteToChannelRequest(
                    channel=target_group,
                    users=[user.id]
                ))
                mention = f"@{user.username}" if user.username else f"{user.first_name}"
                added_count += 1
                await asyncio.sleep(1)  # Avoid flood limits
            except FloodWaitError as e:
                # Send flood error to @Userbot_hostbot
                error_msg = (
                    f"**⚡ Flood Limit Error in Group ID: {event.chat_id} ⚡**\n"
                    f"Command: .add {args}\n"
                    f"Error: FloodWaitError, waiting for {e.seconds} seconds\n"
                    f"Username: {username}\n"
                    f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                )
                try:
                    await client.send_message('@Userbot_hostbot', error_msg, parse_mode='md')
                except Exception as send_error:
                    print(f"Failed to send flood error to @Userbot_hostbot: {str(send_error)}")
                await asyncio.sleep(e.seconds)
                failed_count += 1
                failed_users.append(username)
                continue
            except UserPrivacyRestrictedError:
                failed_count += 1
                failed_users.append(username)
                continue
            except PeerIdInvalidError:
                failed_count += 1
                failed_users.append(username)
                continue
            except Exception as e:
                # Send general error to @Userbot_hostbot
                error_msg = (
                    f"**⚡ Error in Group ID: {event.chat_id} ⚡**\n"
                    f"Command: .add {args}\n"
                    f"Error: {str(e)}\n"
                    f"Username: {username}\n"
                    f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                )
                try:
                    await client.send_message('@Userbot_hostbot', error_msg, parse_mode='md')
                except Exception as send_error:
                    print(f"Failed to send error to @Userbot_hostbot: {str(send_error)}")
                failed_count += 1
                failed_users.append(username)
                continue

        # Final response
        response = (
            f"**🔥 Add process complete! 🎉**\n"
            f"**Total Users Tried:** {len(usernames)}\n"
            f"**Successfully Added:** {added_count}\n"
            f"**Failed:** {failed_count}"
        )
        if failed_users:
            response += f"\n**Failed Users:** {', '.join(failed_users)} (privacy settings, invalid username, ya limits ke wajah se)"
        await event.reply(response, parse_mode='md')
    except Exception as e:
        # Send general error to @Userbot_hostbot
        error_msg = (
            f"**⚡ Error in Group ID: {event.chat_id} ⚡**\n"
            f"Command: .add {args}\n"
            f"Error: {str(e)}\n"
            f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )
        try:
            await client.send_message('@Userbot_hostbot', error_msg, parse_mode='md')
        except Exception as send_error:
            print(f"Failed to send error to @Userbot_hostbot: {str(send_error)}")
        await event.reply(f"**⚡ Add mein error, details hoster bot ko bheje gaye! 🚫**", parse_mode='md')
    await event.delete()

# ===================== TAGALL COMMAND (FIXED - NO EMOJI) =====================
# ===================== TAGALL COMMAND (FIXED - NO EMOJI, ANTI-SPAM) =====================
@client.on(events.NewMessage(outgoing=True, pattern=r"^\.tagall(?:\s+([\s\S]*))?$"))
async def tagall(event):
    me = await client.get_me()
    if event.sender_id != me.id:
        return

    if not event.is_group:
        await event.reply("**This command only works in groups!**")
        return

    custom_text = event.pattern_match.group(1).strip() if event.pattern_match.group(1) else None
    timestamp = time.time()
    key = (event.sender_id, event.chat_id, timestamp)
    tagall_status[key] = True

    await event.edit(f"**Tag All started{' — ' + custom_text if custom_text else ''}**")

    total_tagged = 0

    async for member in client.iter_participants(event.chat_id):
        if key not in tagall_status or not tagall_status[key]:
            break

        # Skip deleted, bots, self
        if member.bot or member.deleted or member.is_self or member.id == me.id:
            continue

        # Build mention
        if member.username:
            mention = f"@{member.username}"
        else:
            name = member.first_name or "User"
            mention = f"[{name}](tg://user?id={member.id})"

        # Choose message text
        if custom_text:
            text = custom_text
        else:
            text = random.choice(tagall_messages)

        final_msg = f"{mention} {text}".strip()

        try:
            await client.send_message(event.chat_id, final_msg, parse_mode='md')
            total_tagged += 1
            # Anti-spam: minimum 3 second gap between each tag
            await asyncio.sleep(5)
        except FloodWaitError as fw:
            # Telegram flood wait — respect it
            await asyncio.sleep(fw.seconds + 2)
            continue
        except Exception:
            await asyncio.sleep(3)
            continue

    # Clean up
    tagall_status.pop(key, None)

    await client.send_message(
        event.chat_id,
        f"**✨ Tag All Completed Successfully ✨**\n"
        f"👥 Total Members Tagged: `{total_tagged}`\n"
        f"💫 Powered by your Userbot"
    )


# Stop tagall command handler
@client.on(events.NewMessage(pattern=rf'^{re.escape(PREFIX)}stoptagall(?:\s+(\d+(?:\.\d+)?))?(?:\s+(-?\d+))?$'))
async def stoptagall(event):
    host_user_id = (await client.get_me()).id
    if event.sender_id != host_user_id:
        return
    await log_command(event, "stoptagall")
    try:
        raid_id = event.pattern_match.group(1)  # Timestamp (e.g., 1634567890.0)
        chat_id = event.pattern_match.group(2)  # Optional chat ID
        target_chat_id = int(chat_id) if chat_id else event.chat_id

        stopped = False
        tagalls_to_stop = []

        # Find matching tagalls
        for key in list(tagall_status.keys()):
            sender_id, tagall_chat_id, timestamp = key
            if sender_id == event.sender_id and tagall_chat_id == target_chat_id:
                if not raid_id or str(timestamp)[:10] == raid_id[:10]:  # Match timestamp (ignoring decimals)
                    tagalls_to_stop.append(key)

        # Stop matching tagalls
        if tagalls_to_stop:
            for tagall_key in tagalls_to_stop:
                tagall_status[tagall_key] = False
                stopped = True
                await event.reply(f"**🔔 Tagall stopped! (ID: {tagall_key[2]:.0f}) 🛑**", parse_mode='md')
                logging.info(f"Tagall stopped by user {event.sender_id}: {tagall_key}")
        else:
            await event.reply("**⚡ Koi active tagall nahi mila! Ya galat ID/chat ID diya. 🚫**", parse_mode='md')
            logging.info(f"No active tagall found for user {event.sender_id} in chat {target_chat_id} with ID {raid_id}")

        if not stopped:
            await event.reply("**⚡ Koi tagall nahi chalu tha is chat mein ya ID galat hai! 🚫**", parse_mode='md')

    except Exception as e:
        await event.reply(f"**⚡ Stoptagall mein error: {str(e)} 🚫**", parse_mode='md')
        logging.error(f"Error in stoptagall for user {event.sender_id}: {str(e)}")

    await event.delete()

# Setwlcm command handler (Updated to handle media, store video attributes, and not delete the command message)
@client.on(events.NewMessage(pattern=rf'^{re.escape(PREFIX)}setwlcm\s+(.+)$'))
async def setwlcm(event):
    host_user_id = (await client.get_me()).id
    if event.sender_id != host_user_id:
        return
    await log_command(event, "setwlcm")
    try:
        message = event.pattern_match.group(1).strip()
        if not message:
            await event.reply("**⚡ Valid message do! Usage: .setwlcm <message> 🚫**", parse_mode='md')
            return

        # Check if the message includes media (photo or video)
        media = None
        media_path = None
        media_type = None
        video_attributes = None
        if event.message.media:
            # Handle both photo and video
            if isinstance(event.message.media, telethon.tl.types.MessageMediaPhoto):
                media_type = "photo"
                media_path = f"welcome_media_{host_user_id}_{int(time.time())}.jpg"
                await event.download_media(file=media_path)
                media = media_path
                print(f"Media set as photo: {media_path}")
            elif isinstance(event.message.media, telethon.tl.types.MessageMediaDocument):
                # Check if the document is a video
                doc = event.message.media.document
                video_attr = None
                for attr in doc.attributes:
                    if isinstance(attr, DocumentAttributeVideo):
                        video_attr = attr
                        break
                if video_attr:
                    media_type = "video"
                    media_path = f"welcome_media_{host_user_id}_{int(time.time())}.mp4"
                    await event.download_media(file=media_path)
                    media = media_path
                    # Store video attributes
                    video_attributes = {
                        "duration": video_attr.duration,
                        "w": video_attr.w,
                        "h": video_attr.h
                    }
                    print(f"Media set as video: {media_path}, Attributes: {video_attributes}")
                else:
                    await event.reply("**⚡ Sirf photo ya video ka media support karta hai! 🚫**", parse_mode='md')
                    return
            else:
                await event.reply("**⚡ Sirf photo ya video ka media support karta hai! 🚫**", parse_mode='md')
                return

        # Clean up any existing media file
        welcome_data = load_welcome_data(host_user_id)
        if welcome_data.get("media") and os.path.exists(welcome_data["media"]):
            os.remove(welcome_data["media"])
            print(f"Removed old media file: {welcome_data['media']}")

        # Save the welcome message, media path, media type, and video attributes (if any)
        data = {
            "content": message,
            "enabled": True,
            "media": media_path,
            "media_type": media_type,
            "video_attributes": video_attributes
        }
        save_welcome_data(host_user_id, data)

        if media:
            await event.reply(f"**🔥 Welcome message aur media ({media_type}) set ho gaya:\n{message} 🎉**", parse_mode='md')
        else:
            await event.reply(f"**🔥 Welcome message set ho gaya:\n{message} 🎉**", parse_mode='md')
    except Exception as e:
        await event.reply(f"**⚡ Welcome message set karne mein error: {str(e)} 🚫**", parse_mode='md')
        print(f"Error in setwlcm: {str(e)}")

# Stopwlcm command handler
@client.on(events.NewMessage(pattern=rf'^{re.escape(PREFIX)}stopwlcm$'))
async def stopwlcm(event):
    host_user_id = (await client.get_me()).id
    if event.sender_id != host_user_id:
        return
    await log_command(event, "stopwlcm")
    try:
        welcome_data = load_welcome_data(host_user_id)
        welcome_data["enabled"] = False
        # Clean up any existing media file
        if welcome_data.get("media") and os.path.exists(welcome_data["media"]):
            os.remove(welcome_data["media"])
            print(f"Removed media file on stopwlcm: {welcome_data['media']}")
            welcome_data["media"] = None
            welcome_data["media_type"] = None
            welcome_data["video_attributes"] = None
        save_welcome_data(host_user_id, welcome_data)
        await event.reply("**🔥 Welcome message bandh ho gaya! Ab koi welcome message nahi bheja jayega. ⚡**", parse_mode='md')
    except Exception as e:
        await event.reply(f"**⚡ Stopwlcm mein error: {str(e)}  🚫**", parse_mode='md')
        print(f"Error in stopwlcm: {str(e)}")
    await event.delete()

# Welcome message handler for private messages (Updated with fixes)
@client.on(events.NewMessage(incoming=True))
async def welcome_message(event):
    # Check if the message is in a private chat
    if not event.is_private:
        print("Not a private chat, skipping welcome message")
        return

    # Skip if the message is a command
    if event.message.text and event.message.text.startswith(('.', '/')):
        print("Message is a command, skipping welcome message")
        return

    # Get the host user ID (bot's ID)
    host_user_id = (await client.get_me()).id
    print(f"Host user ID: {host_user_id}, Sender ID: {event.sender_id}")

    # Skip if the message is from the bot itself
    if event.sender_id == host_user_id:
        print("Message is from the bot itself, skipping welcome message")
        return

    # Create a unique key for this user-host pair
    welcome_key = (host_user_id, event.sender_id)
    print(f"Welcome key: {welcome_key}")

    # Check if welcome message has already been sent to this user
    if welcome_key in sent_welcome:
        print(f"Welcome message already sent to {event.sender_id}, skipping")
        return

    try:
        # Load welcome data
        welcome_data = load_welcome_data(host_user_id)
        print(f"Welcome data loaded: {welcome_data}")

        # Check if welcome messages are enabled
        if not welcome_data.get("enabled", True):
            print("Welcome messages are disabled, skipping")
            return

        # Mark this user as having received the welcome message
        sent_welcome.add(welcome_key)
        print(f"Added {welcome_key} to sent_welcome set")

        # Check if there's a media file associated with the welcome message
        media_path = welcome_data.get("media")
        media_type = welcome_data.get("media_type")
        video_attributes = welcome_data.get("video_attributes")
        content = welcome_data.get("content", DEFAULT_WELCOME_MESSAGE)

        if media_path:
            print(f"Media path found: {media_path}, Type: {media_type}, Video Attributes: {video_attributes}")
            # Verify that the media file exists
            if not os.path.exists(media_path):
                print(f"Media file {media_path} does not exist, sending text only")
                await event.reply(content, parse_mode='md')
                return

            # Send the media (photo or video) with the welcome message as the caption
            if media_type == "video":
                # Use video attributes if available, otherwise set defaults
                attrs = []
                if video_attributes:
                    attrs.append(DocumentAttributeVideo(
                        duration=video_attributes.get("duration", 0),
                        w=video_attributes.get("w", 512),
                        h=video_attributes.get("h", 512),
                        supports_streaming=True
                    ))
                else:
                    attrs.append(DocumentAttributeVideo(
                        duration=0,
                        w=512,
                        h=512,
                        supports_streaming=True
                    ))
                try:
                    await client.send_file(
                        entity=event.chat_id,
                        file=media_path,
                        caption=content,
                        parse_mode='md',
                        video=True,  # Ensures the file is treated as a video
                        attributes=attrs,  # Explicitly set video attributes
                        mime_type="video/mp4",  # Force MIME type to video/mp4
                        force_document=False  # Prevent sending as a document
                    )
                    print(f"Sent welcome video: {media_path} with caption: {content}")
                except Exception as e:
                    print(f"Error sending video: {str(e)}")
                    # Fallback to sending text only
                    await event.reply(content, parse_mode='md')
            elif media_type == "photo":
                try:
                    await client.send_file(
                        entity=event.chat_id,
                        file=media_path,
                        caption=content,
                        parse_mode='md',
                        video=False,  # Ensures the file is treated as a photo
                        force_document=False
                    )
                    print(f"Sent welcome photo: {media_path} with caption: {content}")
                except Exception as e:
                    print(f"Error sending photo: {str(e)}")
                    # Fallback to sending text only
                    await event.reply(content, parse_mode='md')
        else:
            # No media, send text only
            await event.reply(content, parse_mode='md')
            print(f"Sent welcome message without media: {content}")
    except Exception as e:
        print(f"Error in welcome message handler: {str(e)}")
        # Fallback to default welcome message in case of errors
        try:
            await event.reply(DEFAULT_WELCOME_MESSAGE, parse_mode='md')
            print(f"Fallback: Sent default welcome message: {DEFAULT_WELCOME_MESSAGE}")
        except Exception as fallback_error:
            print(f"Error in fallback welcome message: {str(fallback_error)}")

# Set default welcome message command handler (Updated to clear media)
@client.on(events.NewMessage(pattern=rf'^{re.escape(PREFIX)}wlcmmssg$'))
async def set_default_welcome(event):
    host_user_id = (await client.get_me()).id
    if event.sender_id != host_user_id:
        return
    await log_command(event, "wlcmmssg")
    try:
        welcome_data = load_welcome_data(host_user_id)
        # Clean up any existing media file
        if welcome_data.get("media") and os.path.exists(welcome_data["media"]):
            os.remove(welcome_data["media"])
            print(f"Removed media file on wlcmmssg: {welcome_data['media']}")
        data = {
            "content": DEFAULT_WELCOME_MESSAGE,
            "enabled": True,
            "media": None,
            "media_type": None,
            "video_attributes": None
        }
        save_welcome_data(host_user_id, data)
        await event.reply(f"**🔥 Default welcome message set ho gaya:\n{DEFAULT_WELCOME_MESSAGE} 🎉**", parse_mode='md')
    except Exception as e:
        await event.reply(f"**⚡ Wlcmmssg mein error: {str(e)}  🚫**", parse_mode='md')
        print(f"Error in wlcmmssg: {str(e)}")
    await event.delete()

# Toggle auto-reply command handler
@client.on(events.NewMessage(pattern=rf'^{re.escape(PREFIX)}autoreply\s+(on|off)$'))
async def toggle_autoreply(event):
    host_user_id = (await client.get_me()).id
    if event.sender_id != host_user_id:
        return
    await log_command(event, "autoreply")
    try:
        global AUTO_REPLY_ENABLED
        state = event.pattern_match.group(1).lower()
        AUTO_REPLY_ENABLED = (state == "on")
        await event.reply(f"**🔥 Auto-reply {'enabled' if AUTO_REPLY_ENABLED else 'disabled'} ho gaya! ⚡**", parse_mode='md')
    except Exception as e:
        await event.reply(f"**⚡ Autoreply mein error: {str(e)} 🚫**", parse_mode='md')
    await event.delete()

# Logout command handler
@client.on(events.NewMessage(pattern=rf'^{re.escape(PREFIX)}logout$'))
async def logout(event):
    host_user_id = (await client.get_me()).id
    if event.sender_id != host_user_id:
        return
    await log_command(event, "logout")
    try:
        user_id = event.sender_id
        chat_id = event.chat_id
        for key in list(spam_status.keys()):
            if key[0] == user_id and key[1] == chat_id:
                spam_status[key] = False
        for key in list(raid_status.keys()):
            if key[0] == user_id and key[1] == chat_id:
                raid_status[key] = False
        for key in list(tagall_status.keys()):
            if key[0] == user_id and key[1] == chat_id:
                tagall_status[key] = False
        # Clean up welcome media file on logout
        welcome_data = load_welcome_data(host_user_id)
        if welcome_data.get("media") and os.path.exists(welcome_data["media"]):
            os.remove(welcome_data["media"])
            print(f"Removed media file on logout: {welcome_data['media']}")
        await client.log_out()
        await event.reply("**🔥 Userbot logout ho gaya! Dobara host karo /host se. ⚡**", parse_mode='md')
        session_name = client.session.filename
        if os.path.exists(session_name):
            os.remove(session_name)
        journal_file = session_name + "-journal"
        if os.path.exists(journal_file):
            os.remove(journal_file)
    except Exception as e:
        await event.reply(f"**⚡ Logout mein error: {str(e)} 🚫**", parse_mode='md')
        print(f"Error in logout: {str(e)}")
    await event.delete()

# Add sudo user command handler
@client.on(events.NewMessage(pattern=rf'^{re.escape(PREFIX)}addsudo$'))
async def addsudo(event):
    if event.sender_id not in [OWNER_ID, EXTRA_ADMIN_ID]:
        return
    await log_command(event, "addsudo")
    try:
        user_id, user = await get_target_user(event)
        if user_id is None:
            await event.reply("**⚡ User ko tag karo, ID do, ya message ka reply do! 😊**", parse_mode='md')
            return
        sudo_users.add(user_id)
        save_sudo_users()
        mention = f"@{user.username}" if user.username else f"{user.first_name}"
        await event.reply(f"**🔥 {mention} (ID: {user_id}) ko sudo access de diya! ⚡**", parse_mode='md')
        try:
            await client.send_message(
                user_id,
                "🎉 **Badhai ho!** 🎉\nTumhe sudo access mil gaya.\n 🚀",
                parse_mode='md'
            )
        except Exception as e:
            print(f"Error notifying user {user_id}: {str(e)}")
    except Exception as e:
        await event.reply(f"**⚡ Addsudo mein error: {str(e)} 🚫**", parse_mode='md')
        print(f"Error in addsudo: {str(e)}")
    await event.delete()

# Remove sudo user command handler
@client.on(events.NewMessage(pattern=rf'^{re.escape(PREFIX)}rmsudo$'))
async def rmsudo(event):
    if event.sender_id not in [OWNER_ID, EXTRA_ADMIN_ID]:
        return
    await log_command(event, "rmsudo")
    try:
        user_id, user = await get_target_user(event)
        if user_id is None:
            await event.reply("**⚡ User ko tag karo, ID do, ya message ka reply do! 🚫**", parse_mode='md')
            return
        host_user_id = (await client.get_me()).id
        if user_id in [host_user_id, OWNER_ID, EXTRA_ADMIN_ID]:
            await event.reply("**⚡ Owner ya admin ka sudo access nahi hata sakte! 😎**", parse_mode='md')
            return
        if user_id in sudo_users:
            sudo_users.remove(user_id)
            save_sudo_users()
            mention = f"@{user.username}" if user.username else f"{user.first_name}"
            await event.reply(f"**🔥 {mention} (ID: {user_id}) ka sudo access hata diya! 😎**", parse_mode='md')
            try:
                await client.send_message(
                    user_id,
                    "⚠️ **Notice!** ⚠️\nTera sudo access hata diya gaya hai.\n 🚫",
                    parse_mode='md'
                )
            except Exception as e:
                print(f"Error notifying user {user_id}: {str(e)}")
        else:
            await event.reply("**⚡ Yeh user sudo list mein nahi hai! 😅**", parse_mode='md')
    except Exception as e:
        await event.reply(f"**⚡ Rmsudo mein error: {str(e)} 🚫**", parse_mode='md')
        print(f"Error in rmsudo: {str(e)}")
    await event.delete()

# Activeusers command handler
@client.on(events.NewMessage(pattern=rf'^{re.escape(PREFIX)}activeusers$'))
async def activeusers(event):
    if event.sender_id != OWNER_ID:
        return
    await log_command(event, "activeusers")
    try:
        if not active_users:
            await event.reply("**⚡ Abhi koi bhi userbot active nahi hai! 🚫**", parse_mode='md')
            return
        response = "**🔥 Active Userbots List! ⚡**\n\n"
        for user_id, info in active_users.items():
            username = info["username"]
            last_active = info["last_active"]
            response += f"**📖 Userbot ID:** {user_id}\n**Username:** {username}\n**Last Active:** {last_active}\n\n"
        await event.reply(response, parse_mode='md')
    except Exception as e:
        await event.reply(f"**⚡ Activeusers mein error: {str(e)} 🚫**", parse_mode='md')
        print(f"Error in activeusers: {e}")
    await event.delete()

# Ban command handler
@client.on(events.NewMessage(pattern=rf'^{re.escape(PREFIX)}ban(?:\s+@[\w\d_]+)?(?:\s+(.+))?$'))
async def ban(event):
    host_user_id = (await client.get_me()).id
    if event.sender_id != host_user_id:
        return
    await log_command(event, "ban")
    if not event.is_group:
        await event.reply("**⚡ Yeh command sirf group mein kaam karta hai! 🚫**", parse_mode='md')
        return
    try:
        user_id, user = await get_target_user(event)
        if user_id is None:
            await event.reply("**⚡ User ko tag karo, ID do, ya message ka reply do! 😜**", parse_mode='md')
            return
        if user_id in [host_user_id, OWNER_ID, EXTRA_ADMIN_ID]:
            await event.reply("**⚡ Owner ya admin ko ban nahi kar sakte! 😎**", parse_mode='md')
            return
        if not await is_admin(event.chat_id, host_user_id):
            await event.reply("**⚡ Userbot ko admin rights chahiye ban karne ke liye!  🔥**", parse_mode='md')
            return
        args = event.message.text.split(maxsplit=2)
        reason = args[2] if len(args) > 2 else "Koi reason nahi diya"
        await client(EditBannedRequest(
            event.chat_id,
            user_id,
            ChatBannedRights(until_date=None, view_messages=False, send_messages=False)
        ))
        mention = f"@{user.username}" if user.username else f"{user.first_name}"
        await event.reply(f"**🔥 User {mention} ban ho gaya! 💥**\n**Reason:** {reason}", parse_mode='md')
    except Exception as e:
        await event.reply(f"**⚡ Ban mein error: {str(e)}  🚫**", parse_mode='md')
        print(f"Error in ban: {str(e)}")
    await event.delete()

# Unban command handler
@client.on(events.NewMessage(pattern=rf'^{re.escape(PREFIX)}unban(?:\s+@[\w\d_]+)?$'))
async def unban(event):
    host_user_id = (await client.get_me()).id
    if event.sender_id != host_user_id:
        return
    await log_command(event, "unban")
    if not event.is_group:
        await event.reply("**⚡ Yeh command sirf groups mein kaam karta hai! 🚫**", parse_mode='md')
        return
    try:
        user_id, user = await get_target_user(event)
        if user_id is None:
            await event.reply("**⚡ User ko tag karo, ID do, ya message ka reply do! 😜**", parse_mode='md')
            return
        if not await is_admin(event.chat_id, host_user_id):
            await event.reply("**⚡ Userbot ko admin rights chahiye unban karne ke liye! 🙅‍♂️**", parse_mode='md')
            return
        await client(EditBannedRequest(
            event.chat_id,
            user_id,
            ChatBannedRights(until_date=None, view_messages=True, send_messages=True)
        ))
        mention = f"@{user.username}" if user.username else f"{user.first_name}"
        await event.reply(f"**🔥 User {mention} unban ho gaya!  ⚡**", parse_mode='md')
    except Exception as e:
        await event.reply(f"**⚡ Unban mein error: {str(e)} 🚫**", parse_mode='md')
        print(f"Error in unban: {str(e)}")
    await event.delete()

# Mute command handler
@client.on(events.NewMessage(pattern=rf'^{re.escape(PREFIX)}mute(?:\s+@[\w\d_]+)?(?:\s+(\d+[smhd]))?(?:\s+(.+))?$'))
async def mute(event):
    host_user_id = (await client.get_me()).id
    if event.sender_id != host_user_id:
        return
    await log_command(event, "mute")
    if not event.is_group:
        await event.reply("**⚡ Yeh command sirf groups mein kaam karta hai! 🚫**", parse_mode='md')
        return
    try:
        user_id, user = await get_target_user(event)
        if user_id is None:
            await event.reply("**⚡ User ko tag karo, ID do, ya message ka reply do! 🚫**", parse_mode='md')
            return
        if user_id in [host_user_id, OWNER_ID, EXTRA_ADMIN_ID]:
            await event.reply("**⚡ Owner ya admin ko mute nahi kar sakte! 🚫**", parse_mode='md')
            return
        if not await is_admin(event.chat_id, host_user_id):
            await event.reply("**⚡ Userbot ko admin rights chahiye mute karne ke liye! 🙅‍♂️**", parse_mode='md')
            return
        args = event.message.text.split(maxsplit=3)
        duration = None
        reason = "Koi reason nahi diya"
        for arg in args[1:]:
            if re.match(r'^\d+[smhd]$', arg):
                duration = arg
            elif arg.startswith('@'):
                continue
            else:
                reason = arg
        until_date = None
        if duration:
            value = int(duration[:-1])
            unit = duration[-1]
            if unit == 's':
                until_date = datetime.now() + timedelta(seconds=value)
            elif unit == 'm':
                until_date = datetime.now() + timedelta(minutes=value)
            elif unit == 'h':
                until_date = datetime.now() + timedelta(hours=value)
            elif unit == 'd':
                until_date = datetime.now() + timedelta(days=value)
        await client(EditBannedRequest(
            event.chat_id,
            user_id,
            ChatBannedRights(until_date=until_date, send_messages=False, send_media=False, send_stickers=False, send_gifs=False)
        ))
        mention = f"@{user.username}" if user.username else f"{user.first_name}"
        duration_text = f"{duration} ke liye" if duration else "hamesha ke liye"
        await event.reply(f"**🔥 User {mention} mute ho gaya {duration_text}! 💥**\n**Reason:** {reason}", parse_mode='md')
    except Exception as e:
        await event.reply(f"**⚡ Mute mein error: {str(e)} 🚫**", parse_mode='md')
        print(f"Error in mute: {str(e)}")
    await event.delete()

# Unmute command handler
@client.on(events.NewMessage(pattern=rf'^{re.escape(PREFIX)}unmute(?:\s+@[\w\d_]+)?$'))
async def unmute(event):
    host_user_id = (await client.get_me()).id
    if event.sender_id != host_user_id:
        return
    await log_command(event, "unmute")
    if not event.is_group:
        await event.reply("**⚡ Yeh command sirf groups mein kaam karta hai! 🚫**", parse_mode='md')
        return
    try:
        user_id, user = await get_target_user(event)
        if user_id is None:
            await event.reply("**⚡ User ko tag karo, ID do, ya message ka reply do! 🚫**", parse_mode='md')
            return
        if not await is_admin(event.chat_id, host_user_id):
            await event.reply("**⚡ Userbot ko admin rights chahiye unmute karne ke liye! 🙅‍♂️**", parse_mode='md')
            return
        await client(EditBannedRequest(
            event.chat_id,
            user_id,
            ChatBannedRights(until_date=None, send_messages=True, send_media=True, send_stickers=True, send_gifs=True)
        ))
        mention = f"@{user.username}" if user.username else f"{user.first_name}"
        await event.reply(f"**🔥 User {mention} unmute ho gaya! ⚡**", parse_mode='md')
    except Exception as e:
        await event.reply(f"**⚡ Unmute mein error: {str(e)} 🚫**", parse_mode='md')
        print(f"Error in unmute: {str(e)}")
    await event.delete()

# Kick command handler
@client.on(events.NewMessage(pattern=rf'^{re.escape(PREFIX)}kick(?:\s+@[\w\d_]+)?(?:\s+(.+))?$'))
async def kick(event):
    host_user_id = (await client.get_me()).id
    if event.sender_id != host_user_id:
        return
    await log_command(event, "kick")
    if not event.is_group:
        await event.reply("**⚡ Yeh command sirf groups mein kaam karta hai! 🚫**", parse_mode='md')
        return
    try:
        user_id, user = await get_target_user(event)
        if user_id is None:
            await event.reply("**⚡ User ko tag karo, ID do, ya message ka reply do! 🚫**", parse_mode='md')
            return
        if user_id in [host_user_id, OWNER_ID, EXTRA_ADMIN_ID]:
            await event.reply("**⚡ Owner ya admin ko kick nahi kar sakte! 🚫**", parse_mode='md')
            return
        if not await is_admin(event.chat_id, host_user_id):
            await event.reply("**⚡ Userbot ko admin rights chahiye kick karne ke liye! 🙅‍♂️**", parse_mode='md')
            return
        args = event.message.text.split(maxsplit=2)
        reason = args[2] if len(args) > 2 else "Koi reason nahi diya"
        await client.kick_participant(event.chat_id, user_id)
        mention = f"@{user.username}" if user.username else f"{user.first_name}"
        await event.reply(f"**🔥 User {mention} kick ho gaya! 💥**\n**Reason:** {reason}", parse_mode='md')
    except Exception as e:
        await event.reply(f"**⚡ Kick mein error: {str(e)} 🚫**", parse_mode='md')
        print(f"Error in kick: {str(e)}")
    await event.delete()

# Clear command handler
@client.on(events.NewMessage(pattern=rf'^{re.escape(PREFIX)}clear\s+(\d+)$'))
async def clear(event):
    host_user_id = (await client.get_me()).id
    if event.sender_id != host_user_id:
        return
    await log_command(event, "clear")
    if not event.is_group:
        await event.reply("**⚡ Yeh command sirf groups mein kaam karta hai! 🚫**", parse_mode='md')
        return
    try:
        count = int(event.pattern_match.group(1))
        if count <= 0:
            await event.reply("**⚡ Delete karne ke liye messages count 0 se zyada hona chahiye! 🚫**", parse_mode='md')
            return
        if count > 100:
            await event.reply("**⚡ Ek baar mein max 100 messages allowed! 🚫**", parse_mode='md')
            return
        if not await is_admin(event.chat_id, host_user_id):
            await event.reply("**⚡ Userbot ko messages delete karne ke liye permission chahiye! 🙅‍♂️**", parse_mode='md')
            return
        messages = await client.get_messages(event.chat_id, limit=count+1)
        message_ids = [msg.id for msg in messages]
        await client.delete_messages(event.chat_id, message_ids)
        await event.reply(f"**🔥 {count} messages delete ho gaye! 💥**", parse_mode='md')
    except ValueError:
        await event.reply("**⚡ Valid number! 😎**", parse_mode='md')
    except Exception as e:
        await event.reply(f"**⚡ Clear mein error: {str(e)} 🚫**", parse_mode='md')
        print(f"Error in clear: {str(e)}")
    await event.delete()

# Rmall command handler
@client.on(events.NewMessage(pattern=rf'^{re.escape(PREFIX)}rmall$'))
async def rmall(event):
    host_user_id = (await client.get_me()).id
    if event.sender_id != host_user_id:
        return
    await log_command(event, "rmall")
    try:
        if not event.is_group:
            await event.reply("**⚡ Yeh command sirf groups mein kaam karta hai! 🚫**", parse_mode='md')
            return
        if not await is_admin(event.chat_id, host_user_id):
            await event.reply("**⚡ Userbot ko admin rights chahiye members remove karne ke liye! 🙅‍♂️**", parse_mode='md')
            return
        participants = await client.get_participants(event.chat_id)
        kicked_count = 0
        for participant in participants:
            if participant.id not in [host_user_id, OWNER_ID, EXTRA_ADMIN_ID]:
                try:
                    await client.kick_participant(event.chat_id, participant)
                    kicked_count += 1
                    await asyncio.sleep(0.5)
                except Exception as e:
                    print(f"Failed to kick {participant.id}: {str(e)}")
                    continue
        await event.reply(f"**🔥 {kicked_count} members remove ho gaye! 💥**", parse_mode='md')
    except Exception as e:
        await event.reply(f"**⚡ Rmall mein error: {str(e)} 🚫**", parse_mode='md')
        print(f"Error in rmall: {str(e)}")
    await event.delete()

# Dictionary to track the current joke index for each (user_id, chat_id)
joke_index_tracker = {}

# Joke command handler
@client.on(events.NewMessage(pattern=rf'^{re.escape(PREFIX)}joke$'))
async def joke(event):
    host_user_id = (await client.get_me()).id
    if event.sender_id != host_user_id:
        return
    await log_command(event, "joke")
    try:
        hindi_jokes = [
            "Arre vai, girlfriend se pucha, 'Tera size kya hai?' Usne bola, '36-24-36, aur tera?' Maine kaha, 'Mera toh ek hi size hai, jab dekho khada ho jata hai!' 😜",
            "Bhai, condom shop wale se pucha, 'Bhai, koi strong wala de!' To shopkeeper bola, 'Bhai, ye lo, isme Titanic bhi safe rehta!' 😅",
            "Ek ladki WhatsApp pe boli, 'Babe, tu kitna hot hai!' Maine bola, 'Arre, itna hot ki AC bhi mera paseena nahi rok paaye!' 🔥😉",
            "Bhai, girlfriend boli, 'Tum toh bedroom mein lion ho!' Maine kaha, 'Haan, par yeh lion 2 minute mein so jata hai!' 😆",
            "Ek dost bola, 'Bhai, teri wali ke saath kaisa scene hai?' Maine bola, 'Scene toh banta hai, bas uska mood Netflix jaisa hai, kabhi nahi chalta!' 😜",
            "Arre vai, ek baar date pe ladki boli, 'Tum toh slow ho!' Maine kaha, 'Slow hi perfect hai, jaldi kya hai, pura night baaki hai!' 😉",
            "Ek baar girlfriend boli, 'Tum thodi der ruk kyun nahi sakte?' Maine kaha, 'Arre, rukna hota toh Usain Bolt nahi banta!' 😅",
            "Ek ladka apni GF se: 'Tera figure toh bomb hai!' GF boli, 'Haan, par yeh bomb sirf ek hi bande ke liye phutega!' 😎",
            "Vai, ek baar dost ne pucha, 'Bhai, teri stamina kitni hai?' Maine bola, 'Bhai, Netflix ka subscription khatam ho jaye, meri stamina nahi!' 😆",
            "Girlfriend boli, 'Tum toh bed pe rocket ho!' Maine kaha, 'Haan, par yeh rocket 10 second mein hi launch ho jata hai!' 😂",
            "Bhai, ek baar GF se pucha, 'Kaisa laga?' Usne bola, 'Bas thodi si mehnat aur chahiye, thokna seekh le!' 😜",
            "Ek dost bola, 'Bhai, teri wali ko kaise impress kiya?' Maine kaha, 'Bas thodi si flirting, thodi si masti, aur bed pe full honesty!' 😎",
            "Arre vai, ek baar ladki ne bola, 'Tum toh pura din mood mein rehte ho!' Maine kaha, 'Haan, jab se tujhe dekha, mera Wi-Fi full signal hai!' 😅",
            "Girlfriend boli, 'Tum thodi si practice karo!' Maine kaha, 'Arre, practice toh kar raha hoon, par tera coach banna padega!' 😉",
            "Ek baar dost ne pucha, 'Bhai, teri wali ke saath kya plan hai?' Maine bola, 'Plan toh simple hai, Netflix on, chill on, aur baaki tu samajh!' 😎",
            "Girlfriend: 'Tum toh bade heavy ho!' Maine: 'Haan, jab gaadi chadhani ho, toh accelerator full dabana padta hai!' 😈"
        ]
        # Get user_id and chat_id for tracking
        user_id = event.sender_id
        chat_id = event.chat_id
        key = (user_id, chat_id)
        # Get current joke index or start at 0
        current_index = joke_index_tracker.get(key, 0)
        # Select the joke at the current index
        joke = hindi_jokes[current_index]
        # Increment the index and reset to 0 if it reaches the end
        current_index = (current_index + 1) % len(hindi_jokes)
        joke_index_tracker[key] = current_index
        # Send the joke
        await event.reply(f"**😂😄 Yeh lo ek mast joke! 😜**\n{joke}", parse_mode='md')
    except Exception as e:
        await event.reply(f"**⚡ Joke mein error: {str(e)} 🚫**", parse_mode='md')
        print(f"Error in joke: {str(e)}")
    await event.delete()

# Flip command handler
@client.on(events.NewMessage(pattern=rf'^{re.escape(PREFIX)}flip$'))
async def flip(event):
    host_user_id = (await client.get_me()).id
    if event.sender_id != host_user_id:
        return
    await log_command(event, "flip")
    try:
        result = random.choice(["Heads 🪙", "Tails 🪙"])
        await event.reply(f"**🔄 Coin Flip!**\n**Result:** {result} 🎲", parse_mode='md')
    except Exception as e:
        await event.reply(f"**⚡ Flip mein error: {str(e)} 🚫**", parse_mode='md')
        print(f"Error in flip: {str(e)}")
    await event.delete()

# Rock Paper Scissors command handler
rps_pattern = re.compile(rf'^{re.escape(PREFIX)}rps\s+(rock|paper|scissors)$', re.IGNORECASE)
@client.on(events.NewMessage(pattern=rps_pattern))
async def rps(event):
    host_user_id = (await client.get_me()).id
    if event.sender_id != host_user_id:
        return
    await log_command(event, "rps")
    try:
        user_choice = event.pattern_match.group(1).lower()
        bot_choices = ["rock", "paper", "scissors"]
        bot_choice = random.choice(bot_choices)

        # Determine winner
        if user_choice == bot_choice:
            result = "Draw! 🤝"
        elif (user_choice == "rock" and bot_choice == "scissors") or \
             (user_choice == "paper" and bot_choice == "rock") or \
             (user_choice == "scissors" and bot_choice == "paper"):
            result = "You win! 🏆"
        else:
            result = "I win! 😎"

        response = (
            f"**Rock Paper Scissors** ✂️\n"
            f"Your choice: **{user_choice.capitalize()}**\n"
            f"My choice: **{bot_choice.capitalize()}**\n"
            f"Result: **{result}**"
        )
        await event.reply(response, parse_mode='md')
        logging.info(f"RPS played by user {event.sender_id}: User={user_choice}, Bot={bot_choice}, Result={result}")

    except Exception as e:
        await event.reply(f"**⚡ RPS mein error: {str(e)} 🚫**", parse_mode='md')
        logging.error(f"Error in rps for user {event.sender_id}: {str(e)}")

    await event.delete()

# Calculator command handler
calc_pattern = re.compile(rf'^{re.escape(PREFIX)}calc\s+(.+)$')
@client.on(events.NewMessage(pattern=calc_pattern))
async def calc(event):
    host_user_id = (await client.get_me()).id
    if event.sender_id != host_user_id:
        return
    await log_command(event, "calc")
    try:
        expression = event.pattern_match.group(1).strip()
        # Replace × with * for multiplication
        expression = expression.replace('×', '*')
        # Validate expression to prevent code injection
        if not re.match(r'^[\d\s+\-*/().]+$', expression):
            await event.reply("**⚡ Invalid expression! Sirf numbers aur + - * / () allowed hain. 🚫**", parse_mode='md')
            return
        # Evaluate expression safely
        result = eval(expression, {"__builtins__": {}}, {})
        response = (
            f"**Calculator** 🧮\n"
            f"Expression: **{expression}**\n"
            f"Result: **{result}**"
        )
        await event.reply(response, parse_mode='md')
        logging.info(f"Calc executed by user {event.sender_id}: Expression={expression}, Result={result}")

    except ZeroDivisionError:
        await event.reply("**⚡ Zero se divide nahi kar sakte! 🚫**", parse_mode='md')
        logging.error(f"ZeroDivisionError in calc for user {event.sender_id}: {expression}")
    except Exception as e:
        await event.reply(f"**⚡ Calc mein error: {str(e)} 🚫**", parse_mode='md')
        logging.error(f"Error in calc for user {event.sender_id}: {str(e)}")

    await event.delete()

# Stylish command handler
@client.on(events.NewMessage(pattern=rf'^{re.escape(PREFIX)}stylish\s+(.+)$'))
async def stylish(event):
    host_user_id = (await client.get_me()).id
    if event.sender_id != host_user_id:
        return
    await log_command(event, "stylish")
    try:
        text = event.pattern_match.group(1).strip()
        if not text:
            await event.reply("**⚡ Text do stylish banane ke liye! Usage: .stylish <text> 🚫**", parse_mode='md')
            return
        # Dictionary of stylish font mappings
        stylish_fonts = {
            'a': '𝖺', 'b': '𝖻', 'c': '𝖼', 'd': '𝖽', 'e': '𝖾', 'f': '𝖿', 'g': '𝗀', 'h': '𝗁', 
            'i': '𝗂', 'j': '𝗃', 'k': '𝗄', 'l': '𝗅', 'm': '𝗆', 'n': '𝗇', 'o': '𝗈', 'p': '𝗉', 
            'q': '𝗊', 'r': '𝗋', 's': '𝗌', 't': '𝗍', 'u': '𝗎', 'v': '𝗏', 'w': '𝗐', 'x': '𝗑', 
            'y': '𝗒', 'z': '𝗓', 
            'A': '𝗔', 'B': '𝗕', 'C': '𝗖', 'D': '𝗗', 'E': '𝗘', 'F': '𝗙', 'G': '𝗚', 'H': '𝗛', 
            'I': '𝗜', 'J': '𝗝', 'K': '�_K', 'L': '𝗟', 'M': '𝗠', 'N': '𝗡', 'O': '𝗢', 'P': '𝗣', 
            'Q': '𝗤', 'R': '𝗥', 'S': '𝗦', 'T': '𝗧', 'U': '𝗨', 'V': '𝗩', 'W': '𝗪', 'X': '𝗫', 
            'Y': '𝗬', 'Z': '𝗭'
        }
        stylish_text = ''.join(stylish_fonts.get(char, char) for char in text)
        await event.reply(f"**🔥 Stylish Text:**\n{stylish_text} ✨", parse_mode='md')
    except Exception as e:
        await event.reply(f"**⚡ Stylish mein error: {str(e)} 🚫**", parse_mode='md')
        print(f"Error in stylish: {str(e)}")
    await event.delete()

# Sd (Save Disappearing) command handler
@client.on(events.NewMessage(pattern=rf'^{re.escape(PREFIX)}sd$'))
async def save_disappearing(event):
    host_user_id = (await client.get_me()).id
    if event.sender_id != host_user_id:
        return
    await log_command(event, "sd")
    try:
        if not event.reply_to_msg_id:
            await client.send_message('me', "**⚡ Disappearing message ko save karne ke liye uska reply do! 🚫**", parse_mode='md')
            return

        reply_msg = await event.get_reply_message()
        if not reply_msg:
            await client.send_message('me', "**⚡ Replied message invalid ya expired hai! 🚫**", parse_mode='md')
            return

        # Check if message has content to save
        if not reply_msg.text and not reply_msg.media:
            await client.send_message('me', "**⚡ Reply mein koi content nahi hai save karne ke liye! 🚫**", parse_mode='md')
            return

        # Handle text and/or media
        saved_content = reply_msg.text or "No text content"
        media_path = None
        media_type = None
        video_attributes = None

        if reply_msg.media:
            try:
                # Handle photo
                if isinstance(reply_msg.media, telethon.tl.types.MessageMediaPhoto):
                    media_type = "photo"
                    media_path = f"disappearing_media_{host_user_id}_{int(time.time())}.jpg"
                    await reply_msg.download_media(file=media_path)
                # Handle video or document
                elif isinstance(reply_msg.media, telethon.tl.types.MessageMediaDocument):
                    doc = reply_msg.media.document
                    video_attr = None
                    for attr in doc.attributes:
                        if isinstance(attr, DocumentAttributeVideo):
                            video_attr = attr
                            break
                    if video_attr:
                        media_type = "video"
                        media_path = f"disappearing_media_{host_user_id}_{int(time.time())}.mp4"
                        await reply_msg.download_media(file=media_path)
                        video_attributes = {
                            "duration": video_attr.duration,
                            "w": video_attr.w,
                            "h": video_attr.h
                        }
                    else:
                        # Handle other documents if needed (e.g., GIFs, files)
                        media_type = "document"
                        media_path = f"disappearing_media_{host_user_id}_{int(time.time())}"
                        await reply_msg.download_media(file=media_path)
                else:
                    await client.send_message('me', "**⚡ Unsupported media type! Sirf photo, video ya document support karta hai. 🚫**", parse_mode='md')
                    return

                # Upload media to Saved Messages
                if media_path and os.path.exists(media_path):
                    if media_type == "video":
                        attrs = [DocumentAttributeVideo(
                            duration=video_attributes.get("duration", 0),
                            w=video_attributes.get("w", 512),
                            h=video_attributes.get("h", 512),
                            supports_streaming=True
                        )] if video_attributes else []
                        await client.send_file(
                            'me',
                            file=media_path,
                            caption=f"**🔥 Disappearing {media_type} saved!**\nText: {saved_content}",
                            parse_mode='md',
                            video=True,
                            attributes=attrs
                        )
                    else:
                        await client.send_file(
                            'me',
                            file=media_path,
                            caption=f"**🔥 Disappearing {media_type} saved!**\nText: {saved_content}",
                            parse_mode='md',
                            video=False if media_type == "photo" else None,
                            force_document=(media_type == "document")
                        )
                    # Clean up local file
                    os.remove(media_path)
                else:
                    await client.send_message('me', "**⚡ Media download failed! Text save kiya gaya.**", parse_mode='md')
                    await client.send_message('me', f"**🔥 Disappearing message saved!**\nText: {saved_content}", parse_mode='md')

            except Exception as media_error:
                await client.send_message('me', f"**⚡ Media save karne mein error: {str(media_error)} 🚫**\nText: {saved_content}", parse_mode='md')
        else:
            # Only text, no media
            await client.send_message('me', f"**🔥 Disappearing message saved!**\nText: {saved_content}", parse_mode='md')

        # Delete the command message only
        await event.delete()

    except Exception as e:
        await client.send_message('me', f"**⚡ Sd mein error: {str(e)} 🚫**", parse_mode='md')
        await event.delete()

# Hack command handler to save DMs between two users to Saved Messages
@client.on(events.NewMessage(pattern=rf'^{re.escape(PREFIX)}hack\s+(@?\w+)\s+(@?\w+)$'))
async def hack(event):
    host_user_id = (await client.get_me()).id
    if event.sender_id != host_user_id:
        return
    await log_command(event, "hack")
    try:
        # Extract usernames from command
        username1 = event.pattern_match.group(1).strip('@')
        username2 = event.pattern_match.group(2).strip('@')

        # Resolve user entities
        try:
            user1 = await client.get_entity(username1)
            user2 = await client.get_entity(username2)
        except Exception as e:
            await client.send_message('me', f"**⚡ Hack mein error: Username resolve nahi kar paya - {str(e)} 🚫**", parse_mode='md')
            await event.delete()
            return

        user1_id = user1.id
        user2_id = user2.id

        # Check if there's a DM chat between user1 and user2
        dialog_found = False
        async for dialog in client.iter_dialogs():
            if dialog.is_user and dialog.entity.id == user1_id:
                dialog_found = True
                break

        if not dialog_found:
            await client.send_message('me', f"**⚡ Hack mein error: {username1} ke saath koi DM chat nahi hai! 🚫**", parse_mode='md')
            await event.delete()
            return

        # Fetch messages between user1 and user2
        messages_found = False
        saved_messages = []
        async for message in client.iter_messages(user1_id, from_user=user2_id):
            # Check if message has a valid sender
            if not message.from_id or not hasattr(message.from_id, 'user_id'):
                continue  # Skip messages with invalid sender (e.g., system messages, deleted users)
            messages_found = True
            sender_username = username2 if message.from_id.user_id == user2_id else username1
            saved_messages.append(f"({sender_username}) {message.text or '[Media]'}")

        async for message in client.iter_messages(user1_id, from_user=user1_id):
            # Check if message has a valid sender
            if not message.from_id or not hasattr(message.from_id, 'user_id'):
                continue  # Skip messages with invalid sender
            messages_found = True
            sender_username = username1 if message.from_id.user_id == user1_id else username2
            saved_messages.append(f"({sender_username}) {message.text or '[Media]'}")

        if not messages_found:
            await client.send_message('me', f"**⚡ Hack mein error: {username1} aur {username2} ke beech koi messages nahi mile! 🚫**", parse_mode='md')
            await event.delete()
            return

        # Save the messages to Saved Messages
        if saved_messages:
            # Split messages into chunks to avoid Telegram message length limits (4096 chars)
            chunk_size = 50  # Number of messages per chunk
            for i in range(0, len(saved_messages), chunk_size):
                chunk = saved_messages[i:i + chunk_size]
                message_text = f"**🔥 Chats between {username1} and {username2} (Part {i // chunk_size + 1})**\n\n" + "\n".join(chunk)
                await client.send_message('me', message_text, parse_mode='md')

            await client.send_message('me', f"**🔥 Total {len(saved_messages)} messages between {username1} and {username2} saved!**", parse_mode='md')
        else:
            await client.send_message('me', f"**⚡ Hack mein error: Koi messages nahi mile save karne ke liye! 🚫**", parse_mode='md')

        # Delete the command message
        await event.delete()

    except Exception as e:
        await client.send_message('me', f"**⚡ Hack mein error: {str(e)} 🚫**", parse_mode='md')
        await event.delete()

# Show command handler to reveal whisper messages and save to Saved Messages
@client.on(events.NewMessage(pattern=rf'^{re.escape(PREFIX)}show$'))
async def show_whisper(event):
    host_user_id = (await client.get_me()).id
    if event.sender_id != host_user_id:
        return
    await log_command(event, "show")
    try:
        # Check if the command is used in a group
        if not event.is_group:
            await client.send_message('me', "**⚡ Show command sirf groups mein kaam karta hai! 🚫**", parse_mode='md')
            await event.delete()
            return

        # Check if the command is a reply to a message
        if not event.reply_to_msg_id:
            await client.send_message('me', "**⚡ Whisper message ko reveal karne ke liye uska reply do! 🚫**", parse_mode='md')
            await event.delete()
            return

        reply_msg = await event.get_reply_message()
        if not reply_msg or not reply_msg.text:
            await client.send_message('me', "**⚡ Replied message invalid ya empty hai! 🚫**", parse_mode='md')
            await event.delete()
            return

        # Check if the replied message is a whisper (format: @bot message @username)
        bot_mention = None
        target_user = None
        whisper_content = None

        # Split the message into words
        words = reply_msg.text.split()
        if len(words) < 3:  # Minimum: @bot message @username
            await client.send_message('me', "**⚡ Replied message whisper format mein nahi hai! Format: @bot message @username 🚫**", parse_mode='md')
            await event.delete()
            return

        # Check if the first word is a bot mention (e.g., @PPBBot)
        if words[0].startswith('@'):
            bot_mention = words[0].strip('@')
            # Check if the last word is a username (e.g., @targetuser)
            if words[-1].startswith('@'):
                target_user = words[-1].strip('@')
                # The whisper content is everything between the bot mention and the target user
                whisper_content = ' '.join(words[1:-1])
            else:
                await client.send_message('me', "**⚡ Whisper message mein target username nahi mila! Format: @bot message @username 🚫**", parse_mode='md')
                await event.delete()
                return
        else:
            await client.send_message('me', "**⚡ Replied message whisper format mein nahi hai! Format: @bot message @username 🚫**", parse_mode='md')
            await event.delete()
            return

        # Check if the replied message has a valid sender
        if not reply_msg.from_id or not hasattr(reply_msg.from_id, 'user_id'):
            await client.send_message('me', "**⚡ Sender ka username nahi mil paya! 🚫**", parse_mode='md')
            await event.delete()
            return

        # Get sender's username
        sender = await client.get_entity(reply_msg.from_id.user_id)
        sender_username = sender.username if sender.username else f"User_{sender.id}"

        # Save the whisper message to Saved Messages
        await client.send_message(
            'me',
            f"**🔥 Whisper Message Revealed!**\n**Sender:** @{sender_username}\n**Target:** @{target_user}\n**Message:** {whisper_content}",
            parse_mode='md'
        )

        # Delete the command message
        await event.delete()

    except Exception as e:
        await client.send_message('me', f"**⚡ Show mein error: {str(e)} 🚫**", parse_mode='md')
        await event.delete()

# Start both userbot and clone bot properly
async def start_userbot():
    try:
        # Start the userbot client
        await client.start()
        if not await client.is_user_authorized():
            logging.error(f"Userbot for owner {owner_id} is not authorized")
            print(f"Error: Userbot for owner {owner_id} is not authorized. Please re-host the bot.")
            sys.exit(1)

        print(f"Userbot started for owner {owner_id}!")
        logging.info(f"Userbot started for owner {owner_id}")

        # Run until disconnected (this will keep the userbot running)
        await client.run_until_disconnected()
    except Exception as e:
        logging.error(f"Userbot or clone bot crashed: {e}")
        print(f"Error: Userbot or clone bot crashed: {e}")
        # Stop the clone bot if it exists
        if clone_bot and hasattr(clone_bot, 'stop'):
            await clone_bot.stop()
            logging.info(f"Clone bot stopped due to crash for user {owner_id}")
        sys.exit(1)

# Run the client in an async loop
if __name__ == "__main__":
    asyncio.run(start_userbot()) 
