# -*- coding: utf-8 -*-
import sys
if len(sys.argv) > 1:
    print("Error: This script does not accept command-line arguments. Run as: python3 hoster_bot.py")
    sys.exit(1)

from telethon import TelegramClient, events, Button
from telethon.errors import SessionPasswordNeededError, PhoneCodeInvalidError, FloodWaitError
from telethon.tl.functions.messages import ReportRequest
from telethon.tl.types import (
    InputReportReasonSpam,
    InputReportReasonViolence,
    InputReportReasonPornography,
    InputReportReasonChildAbuse,
    InputReportReasonOther,
    DocumentAttributeVideo
)
import asyncio
import os
import time
import json
import random
import re
from datetime import datetime, timedelta
import subprocess
import psutil
import signal
import logging
from telethon.sessions import StringSession
broadcast_users = set()

SUPPORT_FILE = "support_accounts.json"
support_accounts = []  # → [{phone, user_id, first_name, username, session_string}]

def load_support_accounts():
    global support_accounts
    if os.path.exists(SUPPORT_FILE):
        try:
            with open(SUPPORT_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                support_accounts = data if isinstance(data, list) else []
            print(f"[SUPPORT] {len(support_accounts)} support accounts loaded.")
        except Exception as e:
            print(f"[SUPPORT] Load error: {e}")
            support_accounts = []
    else:                                                                                       support_accounts = []

def save_support_accounts():
    try:
        with open(SUPPORT_FILE, "w", encoding="utf-8") as f:
            json.dump(support_accounts, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"[SUPPORT] Save error: {e}")
                                                                                        # On startup load karo
load_support_accounts()

# Set up logging
logging.basicConfig(
    filename="hoster_bot.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# Lock for session access to prevent 'database is locked' errors
session_locks = {}

# Bot token for the hoster bot
bot_token = "7387414294:AAGbTNiTHVSsnCXj0slg--7RDe0ldnRjk3g"
api_id = 25770896
api_hash = "b3a85ada49f9eb19c7d9ab50527c131d"

# Define premium users (owners)
PREMIUM_USERS = {7661825494}

# Support group link and ID
SUPPORT_GROUP_LINK = "https://t.me/userbotsupportchat"
SUPPORT_GROUP_ID = -1003339101321

# Directories and files
DP_PHOTO_DIR = "dp_photos"
SUDO_FILE = "sudo_users.json"
BLOCKED_FILE = "blocked_users.json"

# Ensure directories exist
os.makedirs(DP_PHOTO_DIR, exist_ok=True)

# Dictionary to track hosting state
hosting_state = {}  # (chat_id, user_id) -> {"step": "phone"/"otp"/"password", ...}

# Bot start time for uptime calculation
BOT_START_TIME = time.time()

# Load sudo users
def load_sudo_users():
    if os.path.exists(SUDO_FILE):
        try:
            with open(SUDO_FILE, "r") as f:
                return set(json.load(f))
        except Exception as e:
            logging.error(f"Error loading sudo users: {str(e)}")
            return set()
    return set()

def save_sudo_users(sudo_users):
    try:
        with open(SUDO_FILE, "w") as f:
            json.dump(list(sudo_users), f)
    except Exception as e:
        logging.error(f"Error saving sudo users: {str(e)}")

sudo_users = load_sudo_users()

# Load blocked users
def load_blocked_users():
    if os.path.exists(BLOCKED_FILE):
        try:
            with open(BLOCKED_FILE, "r") as f:
                return set(json.load(f))
        except Exception as e:
            logging.error(f"Error loading blocked users: {str(e)}")
            return set()
    return set()

def save_blocked_users(blocked_users):
    try:
        with open(BLOCKED_FILE, "w") as f:
            json.dump(list(blocked_users), f)
    except Exception as e:
        logging.error(f"Error saving blocked users: {str(e)}")

blocked_users = load_blocked_users()

# Initialize the bot client with reduced resource usage
client = TelegramClient("hoster", api_id, api_hash, system_version="4.16.30-vxCUSTOM").start(bot_token=bot_token)

# Check for existing userbot processes and session files
def cleanup_existing_sessions(user_id):
    try:
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                if proc.info['cmdline'] and f'userbot_{user_id}' in ' '.join(proc.info['cmdline']):
                    proc.kill()
                    logging.info(f"Killed userbot process: PID {proc.pid}")
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
    except Exception as e:
        logging.error(f"Error killing processes: {e}")
    try:
        for file in os.listdir():
            if file.startswith(f'userbot_{user_id}') and file.endswith(('.session', '.session-journal', '.log')):
                os.remove(file)
                logging.info(f"Deleted file: {file}")
    except Exception as e:
        logging.error(f"Error deleting files: {e}")

# Check if userbot is hosted
def is_userbot_hosted(user_id):
    try:
        session_files = [f for f in os.listdir() if f.startswith(f'userbot_{user_id}') and f.endswith('.session')]
        if session_files:
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    if proc.info['cmdline'] and f'userbot_{user_id}' in ' '.join(proc.info['cmdline']):
                        return True, True  # Hosted and running
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
            return True, False  # Hosted but not running
        return False, False  # Not hosted
    except Exception as e:
        logging.error(f"Error checking userbot status for {user_id}: {e}")
        return False, False

# Get random display photo
def get_random_dp():
    try:
        photos = [f for f in os.listdir(DP_PHOTO_DIR) if f.endswith(('.jpg', '.png', '.jpeg'))]
        return os.path.join(DP_PHOTO_DIR, random.choice(photos)) if photos else None
    except Exception as e:
        logging.error(f"Error getting DP: {e}")
        return None

# Check if user is blocked before processing any command
async def check_blocked_user(event):
    user_id = event.sender_id
    if user_id in blocked_users:
        await event.reply(
            "You have been blocked from using this bot. For more information, please contact the owner - @ITZ_ME_ADITYA_02.",
            parse_mode='md'
        )
        logging.info(f"Blocked user {user_id} attempted to use a command")
        return True
    return False

# Log command function (reused from music feature)
async def log_command(event, command):
    logging.info(f"Command {command} executed by user {event.sender_id}")

import os
import json

ADDITIONAL_FILE = "additional_message.json"

# Load saved additional message on start
additional_msg = None
if os.path.exists(ADDITIONAL_FILE):
    try:
        with open(ADDITIONAL_FILE, "r") as f:
            data = json.load(f)
            additional_msg = data
    except:
        additional_msg = None

# /setadditional — reply to any message (only owner)
@client.on(events.NewMessage(pattern=r"^/setadditional$"))
async def set_additional(event):
    if event.sender_id != OWNER_ID:
        await event.reply("**Only owner can use /setadditional!** 🚫")
        return

    if not event.is_reply:
        await event.reply("**Reply to a message to set it as additional commands!**")
        return

    replied = await event.get_reply_message()

    global additional_msg
    additional_msg = {
        "chat_id": replied.chat_id,
        "message_id": replied.id
    }

    # Save to file
    with open(ADDITIONAL_FILE, "w") as f:
        json.dump(additional_msg, f)

    await event.reply("**Additional commands message set successfully!** ✅\nNow anyone can use /additionalcommands")

# /additionalcommands — anyone can use (FULL HIDE FORWARDING FIXED)
@client.on(events.NewMessage(pattern=r"^/additionalcommands$"))
async def additional_commands(event):
    if additional_msg is None:
        await event.reply("**No additional commands message set yet!**\nOwner needs to reply to a message with /setadditional")
        return

    try:
        await client.forward_messages(
            entity=event.chat_id,
            messages=additional_msg["message_id"],
            from_peer=additional_msg["chat_id"],
            drop_author=True,  # Ye forwarding tag fully hide karta hai
            silent=True        # No notification
        )
    except Exception as e:
        await event.reply(f"**Error: {str(e)}**")

# ===================== CLONE BOT MANAGEMENT (ENGLISH + FULL FEATURES) =====================

CLONE_DATA_FILE = "clone_bots.json"
active_clone_bots = {}  # token → {"owner_id": int, "bot_username": str, "bot_name": str, "client": client}

def load_clone_data():
    global active_clone_bots
    if os.path.exists(CLONE_DATA_FILE):
        try:
            with open(CLONE_DATA_FILE, "r") as f:
                data = json.load(f)
                for token, info in data.items():
                    active_clone_bots[token] = {
                        "owner_id": info["owner_id"],
                        "bot_username": info["bot_username"],
                        "bot_name": info["bot_name"],
                        "client": None
                    }
        except:
            active_clone_bots = {}

def save_clone_data():
    savable = {}
    for token, info in active_clone_bots.items():
        savable[token] = {
            "owner_id": info["owner_id"],
            "bot_username": info["bot_username"],
            "bot_name": info["bot_name"]
        }
    with open(CLONE_DATA_FILE, "w") as f:
        json.dump(savable, f)

load_clone_data()

# Start all saved clone bots on hoster bot start
async def start_all_clones():
    for token, info in active_clone_bots.items():
        try:
            clone_client = TelegramClient(StringSession(), api_id, api_hash)
            await clone_client.start(bot_token=token)
            from userbot_clone import add_userbot_commands
            add_userbot_commands(clone_client, owner_id=info["owner_id"])
            info["client"] = clone_client
        except Exception as e:
            print(f"Failed to start clone bot {token}: {e}")

client.loop.create_task(start_all_clones())

# /clone
@client.on(events.NewMessage(pattern=r"^/clone$"))
async def clone_userbot(event):
    if event.sender_id not in premium_raid_users:
        await event.reply("You are not authorized to use /clone")
        return

    await event.reply("**Cloning Bot**\n\nSend bot token:")

    async with client.conversation(event.sender_id) as conv:
        try:
            token_msg = await conv.wait_event(events.NewMessage(outgoing=False, from_users=event.sender_id))
            bot_token = token_msg.text.strip()

            if not bot_token or ":" not in bot_token:
                await conv.send_message("Invalid token! Try /clone again")
                return

            await conv.send_message("Token received! Starting clone bot...")

            clone_client = TelegramClient(StringSession(), api_id, api_hash)
            await clone_client.start(bot_token=bot_token)

            me = await clone_client.get_me()

            from userbot_clone import add_userbot_commands
            add_userbot_commands(clone_client, owner_id=event.sender_id)

            active_clone_bots[bot_token] = {
                "owner_id": event.sender_id,
                "bot_username": me.username or "NoUsername",
                "bot_name": me.first_name,
                "client": clone_client
            }
            save_clone_data()

            await conv.send_message(
                f"**CLONE BOT SUCCESSFULLY HOSTED**\n\n"
                f"Bot: @{me.username or 'No Username'}\n"
                f"Name: {me.first_name}\n"
                f"ID: `{me.id}`\n\n"
                f"The bot is now fully active with userbot features!"
            )

        except Exception as e:
            await conv.send_message(f"Error: {str(e)}")

# /rmclone
@client.on(events.NewMessage(pattern=r"^/rmclone$"))
async def remove_clone(event):
    if event.sender_id not in premium_raid_users:
        return

    await event.reply("**Removing Clone Bot**\n\nSend bot token to delete:")

    async with client.conversation(event.sender_id) as conv:
        try:
            token_msg = await conv.wait_event(events.NewMessage(outgoing=False, from_users=event.sender_id))
            bot_token = token_msg.text.strip()

            if bot_token not in active_clone_bots:
                await conv.send_message("No clone bot found with this token!")
                return

            if active_clone_bots[bot_token]["owner_id"] != event.sender_id and event.sender_id != OWNER_ID:
                await conv.send_message("This bot is not yours to delete!")
                return

            try:
                await active_clone_bots[bot_token]["client"].disconnect()
            except:
                pass

            del active_clone_bots[bot_token]
            save_clone_data()

            await conv.send_message("Clone bot successfully removed!")

        except Exception as e:
            await conv.send_message(f"Error: {str(e)}")

# /clonerestart — restart only own bots + send message
@client.on(events.NewMessage(pattern=r"^/clonerestart$"))
async def restart_my_clones(event):
    if event.sender_id not in premium_raid_users:
        return

    my_bots = [token for token, info in active_clone_bots.items() if info["owner_id"] == event.sender_id]

    if not my_bots:
        await event.reply("You have no active clone bots!")
        return

    await event.reply(f"Restarting your {len(my_bots)} clone bot(s)...")

    restarted = 0
    for token in my_bots:
        try:
            if active_clone_bots[token]["client"]:
                await active_clone_bots[token]["client"].disconnect()

            new_client = TelegramClient(StringSession(), api_id, api_hash)
            await new_client.start(bot_token=token)
            from userbot_clone import add_userbot_commands
            add_userbot_commands(new_client, owner_id=event.sender_id)
            active_clone_bots[token]["client"] = new_client

            # Send restart message from clone bot to owner
            await new_client.send_message(event.sender_id, "BOT RESTARTED ✅")

            restarted += 1
        except:
            pass

    await event.reply(f"Your clone bots restarted — {restarted} successful")

# /allclonerestart — only owner
@client.on(events.NewMessage(pattern=r"^/allclonerestart$"))
async def restart_all_clones(event):
    if event.sender_id != OWNER_ID:
        return

    if not active_clone_bots:
        await event.reply("No active clone bots!")
        return

    await event.reply(f"Restarting all {len(active_clone_bots)} clone bots...")

    restarted = 0
    for token, info in list(active_clone_bots.items()):
        try:
            if info["client"]:
                await info["client"].disconnect()

            new_client = TelegramClient(StringSession(), api_id, api_hash)
            await new_client.start(bot_token=token)
            from userbot_clone import add_userbot_commands
            add_userbot_commands(new_client, owner_id=info["owner_id"])
            info["client"] = new_client

            # Send message to respective owner
            await new_client.send_message(info["owner_id"], "BOT RESTARTED ✅ (Owner restarted all bots)")

            restarted += 1
        except:
            pass

    await event.reply(f"All clone bots restarted — {restarted} successful")

# /mybots — only own bots
@client.on(events.NewMessage(pattern=r"^/mybots$"))
async def my_bots(event):
    if event.sender_id not in premium_raid_users:
        return

    my_bots = {token: info for token, info in active_clone_bots.items() if info["owner_id"] == event.sender_id}

    if not my_bots:
        await event.reply("You have no active clone bots!")
        return

    list_text = "**Your Clone Bots**\n\n"
    for token, info in my_bots.items():
        list_text += f"• @{info['bot_username']} — {info['bot_name']}\n"

    await event.reply(list_text)

# /allclonebots — only owner
@client.on(events.NewMessage(pattern=r"^/allclonebots$"))
async def all_clone_bots(event):
    if event.sender_id != OWNER_ID:
        return

    if not active_clone_bots:
        await event.reply("No active clone bots!")
        return

    list_text = "**All Clone Bots**\n\n"
    for token, info in active_clone_bots.items():
        owner = "Owner" if info["owner_id"] == OWNER_ID else f"User `{info['owner_id']}`"
        list_text += f"• @{info['bot_username']} — {info['bot_name']} ({owner})\n"

    await event.reply(list_text)

# /rmpremium — remove premium user
@client.on(events.NewMessage(pattern=r"^/rmpremium(?:\s+(.+))?$"))
async def remove_premium(event):
    if event.sender_id != OWNER_ID:
        return

    target = event.pattern_match.group(1)

    if event.is_reply:
        replied = await event.get_reply_message()
        target_user = await replied.get_sender()
        user_id = target_user.id
    elif target:
        target = target.strip()
        if target.startswith("@"):
            try:
                user = await client.get_entity(target)
                user_id = user.id
            except:
                await event.reply("Invalid username or user not found!")
                return
        else:
            try:
                user_id = int(target)
            except:
                await event.reply("Invalid user ID!")
                return
    else:
        await event.reply("Reply to a user or provide username/ID!")
        return

    if user_id not in premium_raid_users:
        await event.reply(f"User `{user_id}` is not premium!")
        return

    if user_id == OWNER_ID:
        await event.reply("Cannot remove owner from premium!")
        return

    premium_raid_users.remove(user_id)
    save_premium_raid_users()
    await event.reply(f"Premium permission removed from user `{user_id}`!")

# /clonefeature — list of clone commands
@client.on(events.NewMessage(pattern=r"^/clonefeature$"))
async def clone_features(event):
    await event.reply(
        "Clone Bot Management Commands:\n\n"
        "/clone — Host new clone bot\n"
        "/rmclone — Delete a clone bot\n"
        "/clonerestart — Restart your clone bots\n"
        "/mybots — List your clone bots\n"
        "/allclonerestart — Restart all clone bots (owner only)\n"
        "/allclonebots — List all clone bots (owner only)\n"
        "/clonefeature — Show this list"
    )

# ===================== FORCE JOIN @ITZ_USERBOT (FINAL 100% WORKING) =====================

from telethon.errors import UserNotParticipantError
from telethon.tl.functions.channels import GetParticipantRequest

CHANNEL_USERNAME = "ZUDO_USERBOT"  # without @

joined_cache = set()  # fast cache — joined users ko yahan save karenge

@client.on(events.NewMessage(pattern=r"^/(start|host|restart|status|logout|supportraid|loginsupport|supportrestart|setsupport|clearsupport|premium|premiumusers|support|broadcast|help|commands)"))
async def force_join_check(event):
    user_id = event.sender_id

    # Cache me hai to direct allow
    if user_id in joined_cache:
        return

    try:
        # Channel entity get karo
        channel = await client.get_entity(CHANNEL_USERNAME)
        
        # Check karo user participant hai ya nahi
        await client(GetParticipantRequest(channel, user_id))
        
        # Joined hai — cache me daal do aur command chalao
        joined_cache.add(user_id)
        return

    except UserNotParticipantError:
        # Not joined
        pass
    except Exception as e:
        print(f"Force join check error: {e}")
        pass

    # Not joined — force join message bhej aur command stop kar do
    buttons = [
        [Button.url("𝐉𝐨𝐢𝐧 𝐂𝐡𝐚𝐧𝐧𝐞𝐥", f"https://t.me/{CHANNEL_USERNAME}")],
        [Button.inline("𝐈 𝐡𝐚𝐯𝐞 𝐉𝐨𝐢𝐧𝐞𝐝", data=f"verifyjoin_{user_id}")]
    ]

    await event.reply(
        "𝐏𝐥𝐞𝐚𝐬𝐞 𝐣𝐨𝐢𝐧 𝐨𝐮𝐫 𝐨𝐟𝐟𝐢𝐜𝐢𝐚𝐥 𝐜𝐡𝐚𝐧𝐧𝐞𝐥 𝐟𝐢𝐫𝐬𝐭 𝐭𝐨 𝐮𝐬𝐞 𝐭𝐡𝐞 𝐛𝐨𝐭!\n\n"
        "𝐀𝐟𝐭𝐞𝐫 𝐣𝐨𝐢𝐧𝐢𝐧𝐠, 𝐜𝐥𝐢𝐜𝐤 𝐭𝐡𝐞 𝐛𝐮𝐭𝐭𝐨𝐧 𝐛𝐞𝐥𝐨𝐰 𝐭𝐨 𝐜𝐨𝐧𝐭𝐢𝐧𝐮𝐞.",
        buttons=buttons
    )

    raise events.StopPropagation  # original command rok do

# Button handler — verify join
@client.on(events.CallbackQuery(data=re.compile(b"verifyjoin_")))
async def verify_joined(event):
    user_id = int(event.data.decode().split("_")[1])

    if event.sender_id != user_id:
        await event.answer("𝐓𝐡𝐢𝐬 𝐛𝐮𝐭𝐭𝐨𝐧 𝐢𝐬 𝐧𝐨𝐭 𝐟𝐨𝐫 𝐲𝐨𝐮!", alert=True)
        return

    try:
        channel = await client.get_entity(CHANNEL_USERNAME)
        await client(GetParticipantRequest(channel, user_id))
        
        # Joined hai — cache me daal do
        joined_cache.add(user_id)
        
        await event.edit("𝐓𝐡𝐚𝐧𝐤𝐬 𝐟𝐨𝐫 𝐣𝐨𝐢𝐧𝐢𝐧𝐠 𝐨𝐮𝐫 𝐜𝐡𝐚𝐧𝐧𝐞𝐥! 🔥\n𝐍𝐨𝐰 𝐲𝐨𝐮 𝐜𝐚𝐧 𝐮𝐬𝐞 𝐚𝐥𝐥 𝐜𝐨𝐦𝐦𝐚𝐧𝐝𝐬 𝐟𝐮𝐥𝐥𝐲...! 𝐂𝐡𝐞𝐜𝐤 ☑ 𝐛𝐲 - /help .")
        
    except UserNotParticipantError:
        await event.answer("𝐘𝐨𝐮 𝐡𝐚𝐯𝐞 𝐧𝐨𝐭 𝐣𝐨𝐢𝐧𝐞𝐝 𝐭𝐡𝐞 𝐜𝐡𝐚𝐧𝐧𝐞𝐥 𝐲𝐞𝐭! 𝐏𝐥𝐞𝐚𝐬𝐞 𝐣𝐨𝐢𝐧 𝐟𝐢𝐫𝐬𝐭.", alert=True)
    except Exception:
        await event.answer("𝐒𝐨𝐦𝐞𝐭𝐡𝐢𝐧𝐠 𝐰𝐞𝐧𝐭 𝐰𝐫𝐨𝐧𝐠. 𝐓𝐫𝐲 𝐚𝐠𝐚𝐢𝐧 𝐥𝐚𝐭𝐞𝐫.", alert=True)

# ===================== FULL SUPPORT SYSTEM FOR HOSTER BOT (LOGIN + RAID + RESTART + PREMIUM) =====================

import json
import os
import asyncio
import random
from telethon.tl.functions.messages import ImportChatInviteRequest
from telethon.tl.functions.channels import JoinChannelRequest

SUPPORT_FILE = "support_accounts.json"
support_sessions = []  # string sessions list

SUPPORT_MESSAGES_FILE = "support_messages.json"
support_messages = []  # list of {"type": "text/media", "content": str/id}

PREMIUM_USERS_FILE = "premium_raid_users.json"
premium_raid_users = []  # jo /supportraid use kar sakte hain

support_collect_mode = False
support_temp_messages = []

OWNER_ID = 7661825494  # ←← APNI ID DAAL DE

def load_support_accounts():
    global support_sessions
    if os.path.exists(SUPPORT_FILE):
        try:
            with open(SUPPORT_FILE, "r") as f:
                support_sessions = json.load(f)
        except:
            support_sessions = []
    else:
        support_sessions = []

def save_support_accounts():
    with open(SUPPORT_FILE, "w") as f:
        json.dump(support_sessions, f)

def load_support_messages():
    global support_messages
    if os.path.exists(SUPPORT_MESSAGES_FILE):
        try:
            with open(SUPPORT_MESSAGES_FILE, "r", encoding="utf-8") as f:
                support_messages = json.load(f)
        except:
            support_messages = []
    else:
        support_messages = []

def save_support_messages():
    with open(SUPPORT_MESSAGES_FILE, "w", encoding="utf-8") as f:
        json.dump(support_messages, f, ensure_ascii=False)

def load_premium_raid_users():
    global premium_raid_users
    if os.path.exists(PREMIUM_USERS_FILE):
        try:
            with open(PREMIUM_USERS_FILE, "r") as f:
                premium_raid_users = json.load(f)
        except:
            premium_raid_users = [OWNER_ID]
    else:
        premium_raid_users = [OWNER_ID]

def save_premium_raid_users():
    with open(PREMIUM_USERS_FILE, "w") as f:
        json.dump(premium_raid_users, f)

load_support_accounts()
load_support_messages()
load_premium_raid_users()

# /loginsupport — new support account login (FIXED + WORKING)
@client.on(events.NewMessage(pattern=r"^/loginsupport$"))
async def login_support(event):
    if event.sender_id != OWNER_ID:
        return

    await event.reply("**Support Account Login Shuru**\n\nPhone number daal (+91xxxxxxxxxx format me):")

    async with client.conversation(event.sender_id) as conv:
        try:
            phone_msg = await conv.wait_event(events.NewMessage(outgoing=False, from_users=event.sender_id))
            phone = phone_msg.text.strip()

            temp_client = TelegramClient(StringSession(), api_id, api_hash)
            await temp_client.connect()
            sent_code = await temp_client.send_code_request(phone)

            await conv.send_message("**OTP daal (12345 format me):**")
            otp_msg = await conv.wait_event(events.NewMessage(outgoing=False, from_users=event.sender_id))
            otp = otp_msg.text.strip().replace(" ", "")

            try:
                await temp_client.sign_in(phone, otp)
            except Exception as e:
                if "PASSWORD" in str(e):
                    await conv.send_message("**2FA password daal (agar laga ho):**")
                    pwd_msg = await conv.wait_event(events.NewMessage(outgoing=False, from_users=event.sender_id))
                    await temp_client.sign_in(password=pwd_msg.text.strip())
                else:
                    raise e

            me = await temp_client.get_me()
            session_str = temp_client.session.save()

            support_sessions.append(session_str)
            save_support_accounts()

            await conv.send_message(
                f"**SUPPORT ACCOUNT SUCCESSFULLY LOGGED IN**\n\n"
                f"Name: {me.first_name}\n"
                f"Username: @{me.username or 'None'}\n"
                f"ID: `{me.id}`\n\n"
                f"Total support accounts: `{len(support_sessions)}`\n\n"
                f"Ab /supportraid se raid kar sakta hai!"
            )

            await temp_client.disconnect()

        except Exception as e:
            await conv.send_message(f"**Login failed: {str(e)}**")

# /supportrestart — saare support accounts ko online/restart karo
@client.on(events.NewMessage(pattern=r"^/supportrestart$"))
async def restart_support_accounts(event):
    if event.sender_id != OWNER_ID:
        return

    if len(support_sessions) == 0:
        await event.reply("**Koi support account login nahi hai! Pehle /loginsupport kar**")
        return

    await event.reply(f"**Support accounts restart kar raha hu...** ({len(support_sessions)} accounts)")

    restarted = 0
    for session_str in support_sessions:
        try:
            s_client = TelegramClient(StringSession(session_str), api_id, api_hash)
            await s_client.connect()
            await s_client.start()
            await s_client.disconnect()
            restarted += 1
        except:
            pass

    await event.reply(f"**Support accounts restart complete**\nRestarted: `{restarted}` / `{len(support_sessions)}`")

# /setsupport — DM me bhej ke set karo
@client.on(events.NewMessage(pattern=r"^/setsupport$"))
async def start_support_collect(event):
    global support_collect_mode, support_temp_messages
    if event.sender_id != OWNER_ID:
        return

    support_collect_mode = True
    support_temp_messages = []

    await event.reply("**Support messages set kar raha hu**\n\n"
                      "Ab messages, stickers, photos, videos bhej do.\n"
                      "Last me **/done** likh dena.")

# /done — save kar do
@client.on(events.NewMessage(pattern=r"^/done$"))
async def done_support_collect(event):
    global support_collect_mode, support_temp_messages
    if event.sender_id != OWNER_ID or not support_collect_mode:
        return

    if len(support_temp_messages) == 0:
        await event.reply("**Koi message nahi bheja!**")
    else:
        support_messages.clear()
        for item in support_temp_messages:
            support_messages.append(item)
        save_support_messages()

        await event.reply(f"**SUPPORT MESSAGES SAVED**\nTotal: `{len(support_messages)}` items")

    support_collect_mode = False
    support_temp_messages = []

# Collect messages during setsupport
@client.on(events.NewMessage(from_users=OWNER_ID))
async def collect_support_messages(event):
    global support_temp_messages
    if not support_collect_mode:
        return

    if event.message and event.message.message and event.message.message.strip() in ["/done", "/setsupport", "/clearsupport"]:
        return

    if event.text:
        support_temp_messages.append({"type": "text", "content": event.text.strip()})
    elif event.media:
        support_temp_messages.append({"type": "media", "content": event.id})

    await event.reply(f"**Saved** — Total: `{len(support_temp_messages)}`")

# /clearsupport
@client.on(events.NewMessage(pattern=r"^/clearsupport$"))
async def clear_support(event):
    global support_messages
    if event.sender_id != OWNER_ID:
        return

    support_messages.clear()
    save_support_messages()
    await event.reply("**Support messages clear ho gaye**")

# /premium (reply / username / user id) — support raid permission
@client.on(events.NewMessage(pattern=r"^/premium(?:\s+(.+))?$"))
async def add_premium_user(event):
    if event.sender_id != OWNER_ID:
        return

    target = event.pattern_match.group(1)

    if event.is_reply:
        replied = await event.get_reply_message()
        target_user = await replied.get_sender()
        user_id = target_user.id
    elif target:
        target = target.strip()
        if target.startswith("@"):
            try:
                user = await client.get_entity(target)
                user_id = user.id
            except:
                await event.reply("**Username galat hai ya user nahi mila!**")
                return
        else:
            try:
                user_id = int(target)
            except:
                await event.reply("**Invalid user ID!**")
                return
    else:
        await event.reply("**Reply kar ya username/user ID daal bhai!**")
        return

    if user_id in premium_raid_users:
        await event.reply(f"**User** `{user_id}` **already premium hai**")
        return

    premium_raid_users.append(user_id)
    save_premium_raid_users()
    await event.reply(f"**User** `{user_id}` **ko support raid permission de diya gaya!**")

# /premiumusers — list dikhao
@client.on(events.NewMessage(pattern=r"^/premiumusers$"))
async def list_premium_users(event):
    if event.sender_id != OWNER_ID:
        return

    if len(premium_raid_users) == 0:
        await event.reply("**Koi premium user nahi hai abhi!**")
        return

    list_text = "**Premium Raid Users List**\n\n"
    for uid in premium_raid_users:
        try:
            user = await client.get_entity(uid)
            name = user.first_name or "Unknown"
            username = f"@{user.username}" if user.username else ""
            list_text += f"• `{uid}` — {name} {username}\n"
        except:
            list_text += f"• `{uid}` — Deleted Account\n"

    await event.reply(list_text)

# /supportraid — FULL FIX (NO "No message was sent previously" + INFINITE WAIT)
@client.on(events.NewMessage(pattern=r"^/supportraid$"))
async def support_raid(event):
    if event.sender_id not in premium_raid_users:
        await event.reply("**Tu allowed nahi hai /supportraid use karne ke liye**\nOwner se premium banwa")
        return

    if len(support_messages) == 0:
        await event.reply("**Pehle /setsupport se messages/media set kar bhai!**")
        return

    if len(support_sessions) == 0:
        await event.reply("**Koi support account login nahi hai! /loginsupport kar**")
        return

    # Pehla message bhej
    await event.reply("**Support Raid Shuru**\n\n**Group ka link bhej** (public/private):")

    group_link = None
    target_link = None
    count = None

    # Conversation start
    async with client.conversation(event.sender_id, timeout=None) as conv:  # infinite timeout
        # Group link ke liye loop
        while group_link is None:
            try:
                response = await conv.get_response()
                if response.text and response.text.strip():
                    group_link = response.text.strip()
                    await conv.send_message("**Group link mila!**\nAb **message link** bhej:")
                else:
                    await conv.send_message("**Group link daal bhai! Phir se bhej:**")
            except:
                await conv.send_message("**Group link bhej na bhai! Wait kar raha hu...**")

        # Message link ke liye loop
        while target_link is None:
            try:
                response = await conv.get_response()
                if response.text and response.text.startswith("https://t.me/"):
                    target_link = response.text.strip()
                    await conv.send_message("**Target mila!**\nAb **count** bhej (number me):")
                else:
                    await conv.send_message("**Sirf valid message link bhej bhai! (https://t.me/ se shuru)\nPhir se bhej:**")
            except:
                await conv.send_message("**Message link bhej na! Wait kar raha hu...**")

        # Count ke liye loop
        while count is None:
            try:
                response = await conv.get_response()
                count = int(response.text.strip())
                if count <= 0:
                    await conv.send_message("**Count 1 se zyada daal bhai! Phir se:**")
                    count = None
                else:
                    await conv.send_message(f"**SUPPORT RAID START**\n"
                                            f"Group: `{group_link}`\n"
                                            f"Target: `{target_link}`\n"
                                            f"Count: `{count}`\n"
                                            f"Accounts: `{len(support_sessions)}`\n\n"
                                            f"Sab ek saath join + raid kar rahe hain...")
            except ValueError:
                await conv.send_message("**Sirf number daal bhai! Phir se count bhej:**")
            except:
                await conv.send_message("**Count bhej na! Wait kar raha hu...**")

        # Parallel Join
        join_tasks = []
        for session_str in support_sessions:
            task = asyncio.create_task(join_group(session_str, group_link))
            join_tasks.append(task)
        await asyncio.gather(*join_tasks)

        # Parallel Raid
        raid_tasks = []
        per_account = count // len(support_sessions) + 10
        for session_str in support_sessions:
            task = asyncio.create_task(raid_account(session_str, target_link, per_account))
            raid_tasks.append(task)
        await asyncio.gather(*raid_tasks)

        await conv.send_message("**SUPPORT RAID KHATAM**\nFull tabahi mach gayi bhai! 🔥")

async def join_group(session_str, group_link):
    try:
        s_client = TelegramClient(StringSession(session_str), api_id, api_hash)
        await s_client.connect()
        await s_client.start()

        if "t.me/+" in group_link:
            hash_part = group_link.split("+")[1].split("/")[0]
            await s_client(ImportChatInviteRequest(hash_part))
        else:
            username = group_link.split("t.me/")[1].split("/")[0]
            await s_client(JoinChannelRequest(username))

        await s_client.disconnect()
    except:
        pass

async def raid_account(session_str, target_link, per_count):
    try:
        s_client = TelegramClient(StringSession(session_str), api_id, api_hash)
        await s_client.connect()
        await s_client.start()

        parts = target_link.split("/")[-2:]
        chat_id = int("-100" + parts[0]) if parts[0].isdigit() else parts[0]
        reply_to = int(parts[1])

        for _ in range(per_count):
            item = random.choice(support_messages)
            if item["type"] == "text":
                await s_client.send_message(chat_id, item["content"], reply_to=reply_to)
            else:
                original_msg = await client.get_messages("me", ids=item["content"])
                if original_msg:
                    await s_client.send_message(chat_id, original_msg, reply_to=reply_to)
            await asyncio.sleep(0.8)

        await s_client.disconnect()
    except:
        pass

# ===================== FULL PROFESSIONAL SUPPORT SYSTEM FOR HOSTER BOT =====================

from telethon.tl.functions.messages import ForwardMessagesRequest

active_support = {}  # user_id → {"owner_msg_id": int, "status": "pending/allowed"}

OWNER_ID = 7661825494  # ←← YAHAN APNI ID DAAL DE (tera ID)

# /support command
@client.on(events.NewMessage(pattern=r"^/support$"))
async def support_request(event):
    if await check_blocked_user(event):
        return

    user = await event.get_sender()
    user_id = user.id
    user_name = user.first_name or "User"
    username = f"@{user.username}" if user.username else "No Username"

    # Agar already active hai
    if user_id in active_support and active_support[user_id]["status"] == "allowed":
        await event.reply("Your support session is already active!\nYou can continue chatting with the admin.")
        return

    # User ko response
    await event.reply("**Support request sent!**\n"
                      "The admin has been notified. Please wait for approval.")

    # Owner ko message with persistent buttons
    buttons = [
        [Button.inline("Allow Support", data=f"allow_{user_id}"),
         Button.inline("End Support", data=f"end_{user_id}")]
    ]

    owner_msg = await client.send_message(
        OWNER_ID,
        f"**New Support Request**\n\n"
        f"User: {user_name}\n"
        f"Username: {username}\n"
        f"User ID: `{user_id}`\n"
        f"Time: {time.strftime('%H:%M - %d/%m/%Y')}\n\n"
        f"Status: Pending",
        buttons=buttons
    )

    active_support[user_id] = {
        "owner_msg_id": owner_msg.id,
        "status": "pending"
    }

# Button clicks
@client.on(events.CallbackQuery)
async def support_buttons(event):
    if event.sender_id != OWNER_ID:
        return

    data = event.data.decode("utf-8")

    if data.startswith("allow_"):
        user_id = int(data.split("_")[1])
        if user_id not in active_support:
            await event.answer("Request expired!", alert=True)
            return

        # User ka details fetch karo
        try:
            user = await client.get_entity(user_id)
            user_name = user.first_name or "Unknown"
            user_username = f"@{user.username}" if user.username else "No Username"
        except:
            user_name = "Unknown User"
            user_username = "No Username"

        active_support[user_id]["status"] = "allowed"

        await event.edit(
            f"**Support ALLOWED**\n\n"
            f"**Name:** {user_name}\n"
            f"**Username:** {user_username}\n"
            f"**User ID:** `{user_id}`\n\n"
            f"Messages will now be forwarded."
        )

        await client.send_message(user_id, "**Support Activated!**\n"
                                          "You can now chat with the admin.\n"
                                          "Please describe your issue.")

    elif data.startswith("end_"):
        user_id = int(data.split("_")[1])
        if user_id not in active_support:
            await event.answer("No active session!", alert=True)
            return

        # User details for end message
        try:
            user = await client.get_entity(user_id)
            user_name = user.first_name or "Unknown"
            user_username = f"@{user.username}" if user.username else "No Username"
        except:
            user_name = "Unknown User"
            user_username = "No Username"

        await event.edit(
            f"**Support ENDED**\n\n"
            f"**Name:** {user_name}\n"
            f"**Username:** {user_username}\n"
            f"**User ID:** `{user_id}`\n\n"
            f"Session closed."
        )

        await client.send_message(user_id, "**Support Deactivated**\n"
                                          "Thank you for contacting us!")

        if user_id in active_support:
            del active_support[user_id]

# Owner ka reply user ko forward
@client.on(events.NewMessage(chats=OWNER_ID))
async def forward_owner_to_user(event):
    if not event.is_reply:
        return

    replied = await event.get_reply_message()
    if not replied.fwd_from:
        return

    fwd_user_id = replied.fwd_from.from_id.user_id if replied.fwd_from.from_id else None
    if fwd_user_id not in active_support or active_support[fwd_user_id]["status"] != "allowed":
        return

    await client.forward_messages(fwd_user_id, event.message)

# Manual end command: /end <user_id>
@client.on(events.NewMessage(pattern=r"^/end(?:\s+(\d+))?$"))
async def manual_end_support(event):
    if event.sender_id != OWNER_ID:
        return

    user_id_str = event.pattern_match.group(1)
    if not user_id_str:
        await event.reply("**Usage:** `/end <user_id>`\nExample: `/end 123456789`")
        return

    try:
        user_id = int(user_id_str)
    except:
        await event.reply("**Invalid user ID!**")
        return

    if user_id not in active_support or active_support[user_id]["status"] != "allowed":
        await event.reply(f"**No active support session for user** `{user_id}`")
        return

    await client.send_message(user_id, "**Support Deactivated**\n"
                                      "Thank you for contacting us!")

    owner_msg_id = active_support[user_id]["owner_msg_id"]
    try:
        await client.edit_message(OWNER_ID, owner_msg_id, 
                                  f"**Support ENDED (Manual)**\nUser ID: `{user_id}`")
    except:
        pass

    del active_support[user_id]

    await event.reply(f"**Support manually ended for user** `{user_id}`")

# ===================== /reply <user_id> <message> – OWNER ONLY DIRECT MESSAGE =====================

@client.on(events.NewMessage(pattern=r"^/reply\s+(\d+)\s+([\s\S]*)$"))
async def reply_to_user(event):
    if event.sender_id != 7661825494:  # ←← APNI ID DAAL DE YAHAN
        return

    user_id = int(event.pattern_match.group(1))
    message = event.pattern_match.group(2).strip()

    if not message:
        await event.reply("**Use:** `/reply <user_id> <your message>`")
        return

    try:
        await client.send_message(user_id, message)
        await event.reply(f"**Message sent successfully to user** `{user_id}`\n"
                          f"Message: `{message}`")
    except Exception as e:
        await event.reply(f"**Failed to send message to user** `{user_id}`\n"
                          f"Error: `{str(e)}`\n"
                          f"Shayad usne privacy on kar rakhi hai (Nobody can message me)")

# ===================== /broadcast – OWNER ONLY (ALL USERS WHO EVER STARTED BOT) =====================

@client.on(events.NewMessage(pattern=r"^/broadcast(?:\s+([\s\S]*))?$"))
async def broadcast_cmd(event):
    if event.sender_id != 7661825494:  # ←← YAHAN APNI ID DAAL DE (tera ID)
        return

    text = event.pattern_match.group(1)
    if not text:
        await event.reply("**Use:** `/broadcast <your message>`\nExample: `/broadcast New update aa gaya!`")
        return

    if len(broadcast_users) == 0:
        await event.reply("**Koi user nahi hai broadcast list me abhi!**")
        return

    await event.reply(f"**Broadcast shuru ho gaya...**\n"
                      f"Total users: `{len(broadcast_users)}`\n"
                      f"Message bhej raha hu...")

    success = 0
    failed = 0

    for user_id in list(broadcast_users):  # list banao taaki remove kar sake
        try:
            await client.send_message(user_id, text)
            success += 1
            if success % 50 == 0:
                await event.edit(f"**Broadcast jaari...**\n"
                                 f"Sent: `{success}`\n"
                                 f"Failed: `{failed}`")
            await asyncio.sleep(0.4)  # safe delay
        except Exception as e:
            failed += 1
            if "blocked" in str(e).lower() or "privacy" in str(e).lower():
                broadcast_users.discard(user_id)  # block kiya to list se hata do
            continue

    await event.edit(f"**Broadcast Complete**\n\n"
                     f"Total users: `{len(broadcast_users)}`\n"
                     f"Successful: `{success}`\n"
                     f"Failed: `{failed}`\n\n"
                     f"Sabko message pahunch gaya bhai!")

# Reply Raid feature
raid_messages = [
    "Bhai, tu toh bilkul bekaar hai! 😝",
    "Ye kya bakwas kar raha hai? Chup kar! 😡",
    "Teri aukaat kya hai mujhe tag karne ki? 😂",
    "Abey chal na, time waste mat kar! 😜",
    "Tu toh ek number ka noob hai! 😎",
    "Bhaag yahan se, warna aur sunega! 😤",
    # Add more gaali messages as per your existing raid messages
]

# Track reply raid targets
reply_raid_targets = set()  # Stores user IDs for active reply raids
host_username = None  # Will be set to host user's username

# Patterns for reply raid commands
replyraid_pattern = re.compile(rf'^{re.escape(".")}replyraid(?:\s+(.+))?$')
dreplyraid_pattern = re.compile(rf'^{re.escape(".")}dreplyraid(?:\s+(.+))?$')

@client.on(events.NewMessage)
async def initialize_host_username(event):
    global host_username
    if host_username is None:
        host_user = await client.get_me()
        host_username = host_user.username.lower() if host_user.username else None
        logging.info(f"Host username set to: {host_username}")

@client.on(events.NewMessage(pattern=replyraid_pattern))
async def replyraid(event):
    global reply_raid_targets
    host_user_id = (await client.get_me()).id
    if event.sender_id != host_user_id:
        return
    await log_command(event, "replyraid")
    try:
        # Get target user (via reply or username/ID)
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
            except (ValueError, Exception) as e:
                await event.reply(f"**⚡ Invalid username or user ID: {str(e)} 🚫**", parse_mode='md')
                logging.error(f"Invalid target for replyraid by user {event.sender_id}: {str(e)}")
                return

        if not target_id:
            await event.reply("**⚡ Reply to a user or provide a username/user ID! 🚫**", parse_mode='md')
            return

        # Add target to reply raid list
        if target_id in reply_raid_targets:
            await event.reply("**⚡ Reply raid already active for this user! 🚫**", parse_mode='md')
            return
        reply_raid_targets.add(target_id)
        await event.reply(f"**⚡ Reply raid activated for user ID {target_id}! Will reply with gaali on their replies/tags. 🎯**", parse_mode='md')
        logging.info(f"Reply raid activated for user {target_id} by user {event.sender_id}")

    except Exception as e:
        await event.reply(f"**⚡ Replyraid mein error: {str(e)} 🚫**", parse_mode='md')
        logging.error(f"Error in replyraid for user {event.sender_id}: {str(e)}")
    await event.delete()

@client.on(events.NewMessage(pattern=dreplyraid_pattern))
async def dreplyraid(event):
    global reply_raid_targets
    host_user_id = (await client.get_me()).id
    if event.sender_id != host_user_id:
        return
    await log_command(event, "dreplyraid")
    try:
        # Get target user (via reply or username/ID)
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
            except (ValueError, Exception) as e:
                await event.reply(f"**⚡ Invalid username or user ID: {str(e)} 🚫**", parse_mode='md')
                logging.error(f"Invalid target for dreplyraid by user {event.sender_id}: {str(e)}")
                return

        if not target_id:
            await event.reply("**⚡ Reply to a user or provide a username/user ID! 🚫**", parse_mode='md')
            return

        # Remove target from reply raid list
        if target_id not in reply_raid_targets:
            await event.reply("**⚡ No reply raid active for this user! 🚫**", parse_mode='md')
            return
        reply_raid_targets.remove(target_id)
        await event.reply(f"**⚡ Reply raid deactivated for user ID {target_id}! 🛑**", parse_mode='md')
        logging.info(f"Reply raid deactivated for user {target_id} by user {event.sender_id}")

    except Exception as e:
        await event.reply(f"**⚡ Dreplyraid mein error: {str(e)} 🚫**", parse_mode='md')
        logging.error(f"Error in dreplyraid for user {event.sender_id}: {str(e)}")
    await event.delete()

@client.on(events.NewMessage)
async def auto_reply_raid(event):
    global reply_raid_targets, host_username
    host_user_id = (await client.get_me()).id
    sender_id = event.sender_id

    # Check if sender is a targeted user and message is a reply to host or contains host username
    if sender_id in reply_raid_targets:
        is_reply_to_host = False
        is_tag = False
        if event.reply_to_msg_id:
            reply_msg = await event.get_reply_message()
            if reply_msg and reply_msg.sender_id == host_user_id:
                is_reply_to_host = True
        if host_username and event.text and f"@{host_username}" in event.text.lower():
            is_tag = True

        if is_reply_to_host or is_tag:
            # Reply with a random raid message
            raid_msg = random.choice(raid_messages)
            await event.reply(raid_msg, parse_mode='md')
            logging.info(f"Auto-replied with raid message to user {sender_id} in chat {event.chat_id}")
            # Small delay to avoid flooding
            await asyncio.sleep(1)

# Welcome message handler
@client.on(events.NewMessage(pattern="/start"))
async def start(event):
    if await check_blocked_user(event):
        return

    broadcast_users.add(event.sender_id)

    logging.info(f"Received /start command from user {event.sender_id}")
    welcome_caption = (
        "🌟 𝐖ᴇʟᴄᴏᴍᴇ 𝐓ᴏ 𝐓ʜᴇ 𝐏ʀᴇᴍɪᴜᴍ 𝐔𝐬ᴇʀʙᴏᴛ 𝐇ᴏ𝐬ᴛᴇʀ 𝐁ᴏᴛ! 🌟\n\n\n"
        "🚀 𝐔ɴʟᴇᴀ𝐬ʜ 𝐓ʜᴇ 𝐏ᴏᴡᴇʀ 𝐎ғ 𝐀ᴜᴛᴏᴍᴀᴛɪᴏɴ 𝐖ɪᴛʜ 𝐒ᴛʏʟᴇ! 🚀 \n\n"
        "👑 𝐂ʀᴀғᴛᴇᴅ 𝐁ʏ: @ITZ_ME_ADITYA_02 👑 \n\n"
        "🔒 𝟏𝟎𝟎% 𝐒ᴇᴄᴜʀᴇ & 𝐋ɪɢʜᴛɴɪɴɢ 𝐅ᴀsᴛ! 🔒\n\n"
        "✨ 𝐄xᴘʟᴏʀᴇ 𝐂ᴏᴍᴍᴀɴᴅs ᴡɪᴛʜ /help 𝐎ʀ 𝐓ᴀᴘ 𝐁ᴇʟᴏᴡ! ✨"
    )
    buttons = [[Button.inline("📖 Help", data="show_help")]]
    dp_path = get_random_dp()
    if dp_path:
        await event.reply(file=dp_path, message=welcome_caption, parse_mode='md', buttons=buttons)
        logging.info(f"Sent welcome message with photo to user {event.sender_id}")
    else:
        await event.reply(welcome_caption, parse_mode='md', buttons=buttons)
        logging.info(f"Sent welcome message without photo to user {event.sender_id}")

# Help command handler
@client.on(events.NewMessage(pattern="/help"))
async def help(event):
    if await check_blocked_user(event):
        return
    help_list = (
        "🌟 𝐏ʀᴇᴍɪᴜᴍ 𝐇ᴏsᴛᴇʀ 𝐁ᴏᴛ 𝐂ᴏᴍᴍᴀɴᴅs 🌟\n\n"
        "🔹 /start -  𝐋ᴀᴜɴᴄʜ ᴛʜᴇ 𝐁ᴏᴛ ᴡɪᴛʜ ᴀ 𝐆ʀᴀɴᴅ 𝐖ᴇʟᴄᴏᴍᴇ\n"
        "🔹 /help - 𝐃ɪsᴄᴏᴠᴇʀ 𝐀ʟʟ 𝐂ᴏᴍᴍᴀɴᴅs\n"
        "🔹 /commands - 𝐄xᴘʟᴏʀᴇ 𝐔sᴇʀʙᴏᴛ 𝐅ᴇᴀᴛᴜʀᴇs\n"
        "🔹 /host - 𝐃ᴇᴘʟᴏʏ 𝐘ᴏᴜʀ 𝐎ᴡɴ 𝐔sᴇʀʙᴏᴛ\n"
        "🔹 /support - 𝐑ᴇǫᴜᴇsᴛ 𝐒ᴜᴘᴘᴏʀᴛ ғʀᴏᴍ 𝐀ᴅᴍɪɴ (𝐅ᴀsᴛ 𝐑ᴇsᴘᴏɴsᴇ)\n"
        "🔹 /restart - 𝐑ᴇᴠɪᴠᴇ 𝐘ᴏᴜʀ 𝐇ᴏsᴛᴇᴅ 𝐔sᴇʀʙᴏᴛ\n"
        "🔹 /supportraid - 𝐏ʀᴏ 𝐒ᴜᴘᴘᴏʀᴛ 𝐑ᴀɪᴅ 𝐂ᴏᴍᴍᴀɴᴅ  (𝐎ᴡɴᴇʀs / 𝐏ʀᴇᴍɪᴜᴍ 𝐔sᴇʀs 𝐎ɴʟʏ )\n"
        "🔹 /restartall -  𝐑ᴇsᴛᴀʀᴛ 𝐀ʟʟ 𝐔sᴇʀʙᴏᴛs (𝐎ᴡɴᴇʀs 𝐎ɴʟʏ)\n"
        "🔹 /refresh - 𝐑ᴇғʀᴇsʜ 𝐁ᴏᴛ 𝐒ᴛᴀᴛᴇ (𝐎ᴡɴᴇʀs 𝐎ɴʟʏ)\n"
        "🔹 /status - 𝐂ʜᴇᴄᴋ 𝐘ᴏᴜʀ 𝐔sᴇʀʙᴏᴛ’𝐬 𝐏ᴜʟsᴇ\n"
        "🔹 /logout -  𝐒ᴀғᴇʟʏ 𝐋ᴏɢ 𝐎ᴜᴛ 𝐘ᴏᴜʀ 𝐔sᴇʀʙᴏᴛ\n"
        "🔹 /sudolist - 𝐕ɪᴇᴡ 𝐒ᴜᴅᴏ 𝐔sᴇʀs (𝐎ᴡɴᴇʀs 𝐎ɴʟʏ)\n"
        "🔹 /setdp - 𝐒ᴇᴛ 𝐃ɪsᴘʟᴀʏ 𝐏ʜᴏᴛᴏ (𝐎ᴡɴᴇʀs 𝐎ɴʟʏ)\n"
        "🔹 /block - 𝐁ʟᴏᴄᴋ ᴀ 𝐔sᴇʀ (𝐎ᴡɴᴇʀs 𝐎ɴʟʏ)\n"
        "🔹 /unblock - 𝐔ɴʙʟᴏᴄᴋ ᴀ 𝐔sᴇʀ (𝐎ᴡɴᴇʀs 𝐎ɴʟʏ)\n"
        "🔹 /blockeduser - 𝐕ɪᴇᴡ 𝐁ʟᴏᴄᴋᴇᴅ 𝐔sᴇʀs (𝐎ᴡɴᴇʀs 𝐎ɴʟʏ)\n"
        "🔹 /stats -  𝐕ɪᴇᴡ 𝐁ᴏᴛ 𝐒ᴛᴀᴛɪsᴛɪᴄs (𝐎ᴡɴᴇʀs 𝐎ɴʟʏ)\n"
        "🔹 /secretfunction - 𝐕ɪᴇᴡ 𝐒ᴇᴄʀᴇᴛ 𝐂ᴏᴍᴍᴀɴᴅs (𝐎ᴡɴᴇʀs 𝐎ɴʟʏ)\n"
    )
    await event.reply(help_list, parse_mode='md')
    logging.info(f"Sent help menu to user {event.sender_id}")

# Callback query handler for help button
@client.on(events.CallbackQuery(data="show_help"))
async def show_help(event):
    if await check_blocked_user(event):
        return
    await help(event)

# Set display photo handler (owner-only)
@client.on(events.NewMessage(pattern="/setdp"))
async def set_dp(event):
    if await check_blocked_user(event):
        return
    if event.sender_id not in PREMIUM_USERS:
        await event.reply("🔐 **This Command is for Owners Only!** 🔐")
        logging.warning(f"Unauthorized /setdp attempt by user {event.sender_id}")
        return
    if not event.photo:
        await event.reply("📸 **Please Upload a Photo!**  📸")
        logging.info(f"User {event.sender_id} attempted /setdp without a photo")
        return
    try:
        photo_count = len([f for f in os.listdir(DP_PHOTO_DIR) if f.endswith(('.jpg', '.png', '.jpeg'))])
        if photo_count >= 5:
            await event.reply("⚠️ **Max 5 Photos Allowed! Delete Existing Ones.** ⚠️")
            logging.info(f"User {event.sender_id} reached max photo limit for /setdp")
            return
        photo_path = os.path.join(DP_PHOTO_DIR, f"dp_{event.sender_id}_{photo_count + 1}.jpg")
        await event.download_media(file=photo_path)
        await event.reply("Success **Display Photo Saved!**")
        logging.info(f"User {event.sender_id} saved a new display photo: {photo_path}")
    except Exception as e:
        await event.reply(f"Error Saving Photo: {e}")
        logging.error(f"Error saving photo for user {event.sender_id}: {e}")

import logging
import re
from html import escape

from telethon import Button, events
from telethon.errors import MessageNotModifiedError, RPCError


# ============================================================
# COMMAND HELP CONFIGURATION
# ============================================================
# Saari command information ek hi registry mein rakhi gayi hai.
# Menu aur detail pages isi registry ko use karte hain, isliye
# dono jagah commands alag-alag update karne ki zarurat nahi hai.
#
# IMPORTANT:
# Ye section sirf commands ka help menu display karta hai.
# Actual commands execute karne wale handlers alag se required hain.
# ============================================================

COMMANDS_LOGGER = logging.getLogger(__name__)

COMMANDS_PER_ROW = 3
COMMANDS_BACK_DATA = b"back_to_commands"
COMMANDS_TUTORIAL_URL = "https://t.me/USERBOTCOMMANDS/4"


def _help_command(usage, description, example, note=None):
    """Har command ke liye consistent help structure return kare."""
    return {
        "usage": usage,
        "description": description,
        "example": example,
        "note": note,
    }


COMMAND_HELP = {
    "spam": {
        "name": "Spam",
        "emoji": "📨",
        "commands": [
            _help_command(
                ".spam <count> [chatid] <message> [@username]",
                "Ek message ko specified count ke according repeat kare.",
                ".spam 5 @username Hello!",
                "Sirf permission wale chats mein use karein.",
            ),
            _help_command(
                ".stopspam [id]",
                "Running spam task ko stop kare.",
                ".stopspam 123",
            ),
        ],
    },
    "timed_spam": {
        "name": "Timed Spam",
        "emoji": "⏲️",
        "commands": [
            _help_command(
                ".tspam <time> [chatid/@username] <count> <message>",
                "Messages ke beech specified delay ke saath repeat kare.",
                ".tspam 1 @username 5 Test",
                "Delay ki unit actual .tspam handler ke according hogi.",
            ),
            _help_command(
                ".stopspam [id]",
                "Running timed-spam task ko stop kare.",
                ".stopspam 456",
            ),
        ],
    },
    "raid": {
        "name": "Raid",
        "emoji": "💥",
        "commands": [
            _help_command(
                ".raid <count> [chatid] [@username]",
                "Configured raid messages ka sequence start kare.",
                ".raid 10 @username",
                "Harassment ya bina permission targeting ke liye use na karein.",
            ),
            _help_command(
                ".stopraid [id]",
                "Running raid task ko stop kare.",
                ".stopraid 789",
            ),
        ],
    },
    "abusive_raid": {
        "name": "Abusive Raid",
        "emoji": "🔥",
        "commands": [
            _help_command(
                ".araid <count> [message_link]",
                "Reply kiye hue message ya message link par configured "
                "raid lines bheje.",
                ".araid 10 https://t.me/c/123456789/123",
                "Existing implementation ke mutabik stop karne ke liye "
                "/restart use hota hai. Harassment ke liye use na karein.",
            ),
        ],
    },
    "shayari_raid": {
        "name": "Shayari Raid",
        "emoji": "💌",
        "commands": [
            _help_command(
                ".sraid <count> [username/userid]",
                "Selected user ke liye shayari messages bheje. "
                "User ke message par reply karke bhi use kar sakte hain.",
                ".sraid 5 @username",
            ),
            _help_command(
                ".stopsraid",
                "Running shayari task ko stop kare.",
                ".stopsraid",
            ),
        ],
    },
    "reply_raid": {
        "name": "Reply Raid",
        "emoji": "🎯",
        "commands": [
            _help_command(
                ".replyraid [username/userid]",
                "Selected user ke reply ya mention par configured "
                "automatic raid response enable kare. "
                "Target ke message par reply karke bhi use kar sakte hain.",
                ".replyraid @username",
                "Harassment ya unwanted targeting ke liye use na karein.",
            ),
            _help_command(
                ".dreplyraid [username/userid]",
                "Selected user ke liye reply raid disable kare.",
                ".dreplyraid @username",
            ),
        ],
    },
    "tagging": {
        "name": "Tagging",
        "emoji": "🔔",
        "commands": [
            _help_command(
                ".tagall",
                "Group members ko mention karne ka task start kare.",
                ".tagall",
                "Group permission aur Telegram limits apply hoti hain.",
            ),
            _help_command(
                ".stoptagall [id]",
                "Running member-tagging task ko stop kare.",
                ".stoptagall 101",
            ),
        ],
    },
    "welcome": {
        "name": "Welcome",
        "emoji": "🎉",
        "commands": [
            _help_command(
                ".setwlcm <message>",
                "New members ke liye custom welcome message set kare.",
                ".setwlcm Welcome to our group!",
            ),
            _help_command(
                ".stopwlcm",
                "Welcome messages disable kare.",
                ".stopwlcm",
            ),
            _help_command(
                ".wlcmmssg",
                "Welcome configuration ko existing handler ke "
                "default/reset behaviour par restore kare.",
                ".wlcmmssg",
            ),
        ],
    },
    "moderation": {
        "name": "Moderation",
        "emoji": "🚫",
        "commands": [
            _help_command(
                ".ban @username [reason]",
                "User ko group se ban kare.",
                ".ban @username Spamming",
                "Required admin permissions honi chahiye.",
            ),
            _help_command(
                ".unban @username",
                "Previously banned user ka ban remove kare.",
                ".unban @username",
            ),
            _help_command(
                ".mute @username [time(s/m/h/d)] [reason]",
                "User ki messaging permission restrict kare. "
                "s = seconds, m = minutes, h = hours, d = days.",
                ".mute @username 1h Spamming",
            ),
            _help_command(
                ".unmute @username",
                "Muted user ki messaging permission restore kare.",
                ".unmute @username",
            ),
            _help_command(
                ".kick @username [reason]",
                "User ko current group se remove kare.",
                ".kick @username Disruptive behaviour",
            ),
            _help_command(
                ".clear <count>",
                "Specified number of messages delete kare.",
                ".clear 10",
                "Deletion permissions aur Telegram restrictions apply hoti hain.",
            ),
            _help_command(
                ".rmall",
                "Existing handler ke mutabik group members ko bulk remove kare.",
                ".rmall",
                "Destructive action: group owner ki explicit permission "
                "ke bina use na karein.",
            ),
            _help_command(
                "/invall <group_link/@username>",
                "Source group/channel ke members ko current chat mein "
                "add karne ka attempt kare.",
                "/invall @PublicGroup",
                "Admin permissions, user privacy, consent aur Telegram "
                "limits apply hoti hain; sab members add hona guaranteed nahi hai.",
            ),
            _help_command(
                ".add @username1 [@username2 ...]",
                "Ek ya multiple users ko current group mein add kare.",
                ".add @User1 @User2",
                "User privacy settings aur required permissions apply hoti hain.",
            ),
        ],
    },
    "fun": {
        "name": "Fun",
        "emoji": "😂",
        "commands": [
            _help_command(
                ".joke",
                "Random Hindi joke display kare.",
                ".joke",
            ),
            _help_command(
                ".flip",
                "Coin toss ka result display kare.",
                ".flip",
            ),
            _help_command(
                ".roll <number>",
                "Specified number ke according random roll generate kare.",
                ".roll 6",
            ),
            _help_command(
                ".rps rock|paper|scissors",
                "Rock, paper, scissors game play kare.",
                ".rps rock",
            ),
            _help_command(
                ".calc <expression>",
                "Mathematical expression calculate kare.",
                ".calc 2 + 3",
            ),
        ],
    },
    "customization": {
        "name": "Customization",
        "emoji": "✍️",
        "commands": [
            _help_command(
                ".stylish <name>",
                "Diye gaye text/name ke stylish variations generate kare.",
                ".stylish Aditya",
            ),
            _help_command(
                ".changeowner @username",
                "Ping message mein display hone wala owner username change kare.",
                ".changeowner @NewOwner",
                "Ye help entry sirf ping display customization describe "
                "karti hai; account ownership transfer nahi.",
            ),
            _help_command(
                ".setemoji <emoji>",
                "Ping message mein display hone wala custom emoji set kare.",
                ".setemoji ⚡",
                "Emoji command ke baad space dekar likhein.",
            ),
            _help_command(
                ".setemoji off",
                "Ping message se custom emoji remove kare.",
                ".setemoji off",
            ),
        ],
    },
    "cloning": {
        "name": "Profile Clone",
        "emoji": "👤",
        "commands": [
            _help_command(
                ".clone [username]",
                "Selected user's profile ko clone karne wala existing "
                "handler run kare. Username dein ya user ke message "
                "par reply karke command bhejein.",
                ".clone @username\n.clone  (user ke message par reply karke)",
                "Sirf apne ya permission wale profile par use karein. "
                "Kaunse profile fields copy honge, ye actual handler "
                "par depend karta hai.",
            ),
            _help_command(
                ".dclone",
                "Clone se pehle saved original profile restore kare.",
                ".dclone",
                "Restore tabhi possible hai jab actual clone handler "
                "ne original profile ka backup save kiya ho.",
            ),
        ],
    },
    "general": {
        "name": "General",
        "emoji": "ℹ️",
        "commands": [
            _help_command(
                ".ping",
                "Userbot ka response time check kare.",
                ".ping",
            ),
            _help_command(
                ".uptime",
                "Userbot ka running duration display kare.",
                ".uptime",
            ),
            _help_command(
                ".info [@username]",
                "User ya chat ki available information display kare.",
                ".info @username",
            ),
            _help_command(
                ".logout",
                "Userbot account/session se logout kare.",
                ".logout",
                "Logout ke baad dobara login ki zarurat ho sakti hai.",
            ),
        ],
    },
    "admin": {
        "name": "Admin",
        "emoji": "🔧",
        "commands": [
            _help_command(
                ".addsudo @username",
                "Trusted user ko sudo access de.",
                ".addsudo @username",
                "Owner-only command. Sirf trusted users ko access dein.",
            ),
            _help_command(
                ".rmsudo @username",
                "User ka sudo access remove kare.",
                ".rmsudo @username",
            ),
            _help_command(
                ".activeusers",
                "Active userbot users/sessions ki available list display kare.",
                ".activeusers",
            ),
        ],
    },
    "save_disappearing": {
        "name": "Save Disappearing",
        "emoji": "💾",
        "commands": [
            _help_command(
                ".sd",
                "Replied message/media ko Saved Messages mein save "
                "karne wala existing handler run kare.",
                ".sd  (supported message par reply karke)",
                "Sender ki permission aur privacy respect karein. "
                "Protected ya disappearing media save hona guaranteed nahi hai.",
            ),
        ],
    },
    "broadcast": {
        "name": "Broadcast",
        "emoji": "📢",
        "commands": [
            _help_command(
                ".broadcast <message>",
                "Configured groups mein announcement bheje, "
                "jahan messaging allowed ho.",
                ".broadcast Hello everyone!",
                "Sirf authorized groups mein use karein. Telegram "
                "rate limits aur chat permissions apply hoti hain.",
            ),
        ],
    },
    "antisafe": {
        "name": "AntiSafe",
        "emoji": "🛡️",
        "commands": [
            _help_command(
                ".antisafe on",
                "Unapproved incoming DMs ke liye automatic "
                "deletion/protection enable kare.",
                ".antisafe on",
                "Exact deletion behaviour existing AntiSafe handler "
                "par depend karta hai.",
            ),
            _help_command(
                ".antisafe off",
                "AntiSafe protection disable kare.",
                ".antisafe off",
            ),
        ],
    },
    "approve": {
        "name": "Approve",
        "emoji": "✅",
        "commands": [
            _help_command(
                ".approve",
                "Current DM ke user ko AntiSafe deletion se exempt kare.",
                ".approve  (user ke private chat mein)",
            ),
        ],
    },
    "craid": {
        "name": "CRAID",
        "emoji": "⚡",
        "commands": [
            _help_command(
                ".craid <count>",
                "Configured personal channel ke messages se "
                "reply-based raid task start kare.",
                ".craid 50  (target message par reply karke)",
                "Sirf permission wale chats mein use karein.",
            ),
            _help_command(
                ".setraid <channel_link>",
                "CRAID messages ke liye source channel set kare.",
                ".setraid https://t.me/+abc123",
                "Source channel ka access required hai.",
            ),
        ],
    },
    "autoreply": {
        "name": "AutoReply",
        "emoji": "🤖",
        "commands": [
            _help_command(
                ".autoreply <message>",
                "Username mention/@tag hone par custom automatic "
                "reply enable kare.",
                ".autoreply Abhi busy hoon, thodi der mein reply karunga.",
                "Is feature ka intended trigger @mention hai; "
                "normal replies aur PMs nahi.",
            ),
            _help_command(
                ".dautoreply",
                "Mention-based automatic replies disable kare.",
                ".dautoreply",
            ),
        ],
    },
    "nuclear_clear": {
        "name": "Nuclear Clear",
        "emoji": "☢️",
        "commands": [
            _help_command(
                ".clearall",
                "Bulk history-clearing operation ka confirmation "
                "flow start kare.",
                ".clearall",
                "Destructive operation. Actual scope account access, "
                "Telegram permissions aur existing handler par depend karta hai.",
            ),
            _help_command(
                ".clearall confirm",
                "Pending history-clearing operation confirm kare.",
                ".clearall confirm",
                "Deleted data recover na ho sake. Confirmation sirf "
                "help text mein nahi, actual handler mein enforce honi chahiye.",
            ),
        ],
    },
}


# ============================================================
# MENU / DETAIL RENDERERS
# ============================================================

def _build_commands_keyboard():
    """Stable callback IDs ke saath three-column keyboard banaye."""
    buttons = [
        Button.inline(
            f"{group['emoji']} {group['name']}",
            data=f"cmd_{group_id}".encode("utf-8"),
        )
        for group_id, group in COMMAND_HELP.items()
    ]

    return [
        buttons[index:index + COMMANDS_PER_ROW]
        for index in range(0, len(buttons), COMMANDS_PER_ROW)
    ]


def _build_commands_menu():
    """Initial menu aur Back button ke liye same content return kare."""
    command_count = sum(
        len(group["commands"])
        for group in COMMAND_HELP.values()
    )

    return (
        "✨ <b>𝐔sᴇʀʙᴏᴛ 𝐂ᴏᴍᴍᴀɴᴅs - 𝐏ʀᴇᴍɪᴜᴍ!<b> ✨\n\n"
        "💬 *𝐂ʟɪᴄᴋ ᴀ 𝐁ᴏx 𝐓ᴏ 𝐄xᴘʟᴏʀᴇ 𝐂ᴏᴍᴍᴀɴᴅs!* 💬\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"📂 <b>Categories:</b> {len(COMMAND_HELP)}\n"
        f"⌨️ <b>Command entries:</b> {command_count}\n\n"
        "📖 <b>Syntax guide</b>\n"
        "<code>&lt;value&gt;</code> — Required argument\n"
        "<code>[value]</code> — Optional argument\n"
        "<code>a|b</code> — Available options mein se ek\n\n"
        f'🎓 <a href="{escape(COMMANDS_TUTORIAL_URL, quote=True)}">'
        "Full Command Tutorial</a>\n\n"
        "🔹 <b>Select a category below</b>"
    )


def _build_command_details(group):
    """Har command ko same readable format mein render kare."""
    sections = [
        f"{group['emoji']} <b>{escape(group['name'])} — Commands</b>",
        "━━━━━━━━━━━━━━━━━━━━",
    ]

    for index, command in enumerate(group["commands"], start=1):
        section = (
            f"<b>{index}. Command</b>\n"
            f"<code>{escape(command['usage'])}</code>\n\n"
            f"📝 <b>Explanation</b>\n"
            f"{escape(command['description'])}\n\n"
            f"💡 <b>Example</b>\n"
            f"<pre>{escape(command['example'])}</pre>"
        )

        if command.get("note"):
            section += (
                "\n\n⚠️ <b>Note</b>\n"
                f"{escape(command['note'])}"
            )

        sections.append(section)

    sections.append(
        "↩️ Categories par wapas jaane ke liye Back button dabayein."
    )

    # HTML escaping ki wajah se <count>, &, usernames aur examples
    # Telegram formatting ko accidentally break nahi karenge.
    return "\n\n".join(sections)


# Sirf apne menu callbacks handle karein.
# Isse script ke doosre callback handlers unnecessarily match nahi honge.
_COMMAND_HELP_CALLBACK_PATTERN = re.compile(
    rb"^(?:back_to_commands|cmd_(?:"
    + b"|".join(
        re.escape(group_id.encode("utf-8"))
        for group_id in COMMAND_HELP
    )
    + rb"))$"
)


# ============================================================
# /commands HANDLER
# ============================================================

# /commands aur /commands@BotUsername support kare.
# /commandsXYZ jaise unrelated messages match nahi honge.
@client.on(
    events.NewMessage(
        pattern=r"(?i)^/commands(?:@[a-z0-9_]+)?\s*$"
    )
)
async def commands(event):
    if await check_blocked_user(event):
        return

    try:
        await event.reply(
            _build_commands_menu(),
            parse_mode="html",
            buttons=_build_commands_keyboard(),
            link_preview=False,
        )
    except RPCError:
        COMMANDS_LOGGER.exception(
            "Failed to send commands menu: sender_id=%s chat_id=%s",
            event.sender_id,
            event.chat_id,
        )
        return

    COMMANDS_LOGGER.info(
        "Commands menu sent: sender_id=%s chat_id=%s",
        event.sender_id,
        event.chat_id,
    )


# ============================================================
# COMMAND DETAILS / BACK BUTTON HANDLER
# ============================================================

@client.on(
    events.CallbackQuery(
        pattern=_COMMAND_HELP_CALLBACK_PATTERN
    )
)
async def handle_command_details(event):
    if await check_blocked_user(event):
        return

    callback_data = event.data

    if callback_data == COMMANDS_BACK_DATA:
        response = _build_commands_menu()
        buttons = _build_commands_keyboard()
        selected_group = "main_menu"
    else:
        # Pattern matched hone ke baad callback ID known ASCII bytes hai.
        group_id = callback_data[len(b"cmd_"):].decode("ascii")
        group = COMMAND_HELP.get(group_id)

        if group is None:
            await event.answer(
                "Category available nahi hai. /commands dobara open karein.",
                alert=True,
            )
            return

        response = _build_command_details(group)
        buttons = [[
            Button.inline(
                "↩️ Back to Commands",
                data=COMMANDS_BACK_DATA,
            )
        ]]
        selected_group = group_id

    try:
        # Callback acknowledge karne se Telegram ka loading spinner
        # message edit complete hone ka wait nahi karta.
        await event.answer()

        await event.edit(
            response,
            parse_mode="html",
            buttons=buttons,
            link_preview=False,
        )

    except MessageNotModifiedError:
        # Same category dobara tap karna normal hai; error log nahi karein.
        return

    except RPCError:
        COMMANDS_LOGGER.exception(
            "Failed to update command help: category=%s sender_id=%s",
            selected_group,
            event.sender_id,
        )
        return

    COMMANDS_LOGGER.info(
        "Command help displayed: category=%s sender_id=%s",
        selected_group,
        event.sender_id,
    )

#Sudo list handler
@client.on(events.NewMessage(pattern="/sudolist"))
async def sudolist(event):
    if await check_blocked_user(event):
        return
    if event.sender_id not in PREMIUM_USERS:
        await event.reply("🔐 **Owners Only!** 🔐")
        logging.warning(f"Unauthorized /sudolist attempt by user {event.sender_id}")
        return
    if not sudo_users:
        await event.reply("❌ **No Sudo Users.** ❌")
        return
    sudo_list = " 👥 **Sudo Users**:\n\n"
    for user_id in sudo_users:
        try:
            user = await client.get_entity(user_id)
            username = user.username if user.username else str(user_id)
            sudo_list += f"➤ @{username}\n"
        except:
            sudo_list += f"➤ User {user_id} (Not Found)\n"
    await event.reply(sudo_list, parse_mode='md')
    logging.info(f"Sent sudo list to user {event.sender_id}")

# Check group membership
async def is_group_member(user_id):
    try:
        participants = await client.get_participants(SUPPORT_GROUP_ID)
        return any(participant.id == user_id for participant in participants)
    except Exception as e:
        logging.error(f"Error checking group membership: {e}")
        return False

# Status command handler
@client.on(events.NewMessage(pattern="/status"))
async def status(event):
    if await check_blocked_user(event):
        return
    user_id = event.sender_id
    is_hosted, is_running = is_userbot_hosted(user_id)
    if is_hosted:
        if is_running:
            await event.reply("Success **Userbot Hosted & Running!**\nUse /commands.")
        else:
            await event.reply("Warning **Userbot Hosted but Not Running!**\nTry /restart or /logout.")
    else:
        await event.reply("Error **No Userbot Hosted!**\nUse /host.")
    logging.info(f"Sent status update to user {user_id}: Hosted={is_hosted}, Running={is_running}")

# Running bots command handler
@client.on(events.NewMessage(pattern="/runningbots"))
async def running_bots(event):
    if await check_blocked_user(event):
        return
    session_files = [f for f in os.listdir() if f.startswith('userbot_') and f.endswith('.session')]
    if not session_files:
        await event.reply("Error **No Userbots Found!**")
        logging.info(f"No userbots found for /runningbots by user {event.sender_id}")
        return

    running_bots_list = "🌟 **Running Userbots** 🌟\n\n"
    running_count = 0

    for session_file in session_files:
        try:
            user_id = int(session_file.split('_')[1])
            is_hosted, is_running = is_userbot_hosted(user_id)
            if is_hosted and is_running:
                userbot_client = TelegramClient(session_file.replace('.session', ''), api_id, api_hash)
                await userbot_client.connect()
                if await userbot_client.is_user_authorized():
                    user = await userbot_client.get_me()
                    username = user.username if user.username else str(user.id)
                    running_bots_list += f"➤ @{username}\n"
                    running_count += 1
                await userbot_client.disconnect()
        except Exception as e:
            logging.error(f"Error checking userbot {session_file}: {e}")
            continue

    if running_count == 0:
        running_bots_list += "❌ **No Userbots are currently running.** ❌"
    else:
        running_bots_list += f"\nTotal Running: {running_count}"

    await event.reply(running_bots_list, parse_mode='md')
    logging.info(f"Sent running bots list to user {event.sender_id}: {running_count} bots running")

# Refresh command handler (owners only)
@client.on(events.NewMessage(pattern="/refresh"))
async def refresh(event):
    if await check_blocked_user(event):
        return
    if event.sender_id not in PREMIUM_USERS:
        await event.reply("🔐 **Owners Only!** 🔐")
        logging.warning(f"Unauthorized /refresh attempt by user {event.sender_id}")
        return

    # Clear hosting state and session locks
    hosting_state.clear()
    session_locks.clear()
    logging.info("Cleared hosting state and session locks during refresh")

    # Reload sudo and blocked users to ensure latest data
    global sudo_users, blocked_users
    sudo_users = load_sudo_users()
    blocked_users = load_blocked_users()
    logging.info("Reloaded sudo and blocked users during refresh")

    await event.reply("Success **Bot Refreshed!**\nAll states and features have been updated.", parse_mode='md')
    logging.info(f"Bot refreshed by user {event.sender_id}")

# Secret function handler
@client.on(events.NewMessage(pattern="/secretfunction"))
async def secretfunction(event):
    if await check_blocked_user(event):
        return
    if event.sender_id not in PREMIUM_USERS:
        await event.reply("🔐 **Owners Only!** 🔐")
        logging.warning(f"Unauthorized /secretfunction attempt by user {event.sender_id}")
        return
    secret_commands = (
        "🔒 **Secret Commands** 🔪✩✩✩\n\n"
        "⚠️ **Owners Only - Use Carefully!** ⚠️\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━━\n"
        "🔹 **/reportall (number of reports per account) (message link) (spam, childabuse, violence, pornography, other) (reason)** 🔹\n"
        "Report a specific message using all userbots.\n"
        "Example: /reportall (2) (https://t.me/c/123456789/123) (childabuse) (Inappropriate content)\n"
        "━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "🔥 **Use Responsibly!** 🔥"
    )
    await event.reply(secret_commands, parse_mode='md')
    logging.info(f"Sent secret commands to user {event.sender_id}")

# Reportall command handler
@client.on(events.NewMessage(pattern=r'^/reportall\s+\((\d+)\)\s+\((https://t\.me/[^\s]+)\)\s+\((spam|childabuse|violence|pornography|other)\)\s+\((.+)\)$'))
async def reportall(event):
    if await check_blocked_user(event):
        return
    if event.sender_id not in PREMIUM_USERS:
        await event.reply("🔐 **Owners Only!** 🔐")
        logging.warning(f"Unauthorized /reportall attempt by user {event.sender_id}")
        return
    try:
        reports_per_account = int(event.pattern_match.group(1))
        message_link = event.pattern_match.group(2)
        reason_type = event.pattern_match.group(3).lower()
        reason_message = event.pattern_match.group(4).strip()

        # Validate reports per account
        if reports_per_account <= 0 or reports_per_account > 5:
            await event.reply("**⚡ Reports per account 1 se 5 ke beech hona chahiye! 🚫**", parse_mode='md')
            return

        # Parse message link
        chat_id, message_id = await parse_message_link(message_link)
        if not chat_id or not message_id:
            await event.reply("**⚡ Valid message link do! (e.g., https://t.me/c/123456789/123) 🚫**", parse_mode='md')
            return

        # Find valid userbots
        session_files = [f for f in os.listdir() if f.startswith('userbot_') and f.endswith('.session')]
        valid_sessions = []
        for session_file in session_files:
            session_name = session_file.replace('.session', '')
            try:
                userbot_client = TelegramClient(session_name, api_id, api_hash)
                await userbot_client.connect()
                if await userbot_client.is_user_authorized():
                    valid_sessions.append(session_file)
                await userbot_client.disconnect()
            except Exception as e:
                logging.info(f"Session {session_name} invalid: {str(e)}")
                continue

        if not valid_sessions:
            await event.reply("**⚡ No valid userbots found! 🚫**", parse_mode='md')
            logging.info(f"No valid userbots found for /reportall by user {event.sender_id}")
            return

        await event.reply(f"**🔥 Starting report from {len(valid_sessions)} userbots! 💥**", parse_mode='md')
        logging.info(f"Starting /reportall for user {event.sender_id}: {len(valid_sessions)} userbots")
        total_bots = len(valid_sessions)
        successful_reports = 0
        failed_reports = 0
        accounts_processed = 0

        # Get report reason
        report_reason = get_report_reason(reason_type)

        for session_file in valid_sessions:
            session_name = session_file.replace('.session', '')
            # Initialize lock for this session if not exists
            if session_name not in session_locks:
                session_locks[session_name] = asyncio.Lock()

            async with session_locks[session_name]:
                try:
                    userbot_client = TelegramClient(session_name, api_id, api_hash)
                    await userbot_client.connect()
                    bot_info = await userbot_client.get_me()
                    username = f"@{bot_info.username}" if bot_info.username else bot_info.first_name
                    await event.reply(f"**Reporting from {username} 📩**", parse_mode='md')

                    for i in range(reports_per_account):
                        try:
                            await userbot_client(ReportRequest(
                                peer=chat_id,
                                id=[message_id],
                                reason=report_reason,
                                message=reason_message
                            ))
                            successful_reports += 1
                            await event.reply(f"**{i+1} report sent from {username} 📩**", parse_mode='md')
                            await asyncio.sleep(random.uniform(1, 2))  # Increased delay to avoid rate limits
                        except FloodWaitError as e:
                            await event.reply(f"**⚡ FloodWait: Waiting {e.seconds} seconds for {username} 🚫**", parse_mode='md')
                            await asyncio.sleep(min(e.seconds, 120))
                            failed_reports += 1
                            break
                        except Exception as e:
                            await event.reply(f"**⚡ Report {i+1} mein error from {username}: {str(e)} 🚫**", parse_mode='md')
                            failed_reports += 1
                            break

                    await userbot_client.disconnect()
                    accounts_processed += 1
                    await event.reply(
                        f"**Success: {accounts_processed}/{total_bots} accounts processed!**\n"
                        f"Reports Sent: {successful_reports}\n"
                        f"Failed: {failed_reports}\n",
                        parse_mode='md'
                    )
                    logging.info(f"Processed report for {session_name}: {successful_reports} sent, {failed_reports} failed")
                    await asyncio.sleep(random.uniform(5, 10))  # Delay between accounts
                except Exception as e:
                    failed_reports += reports_per_account
                    await event.reply(f"**⚡ Error with {session_name}: {str(e)} 🚫**", parse_mode='md')
                    logging.error(f"Error reporting with session {session_name}: {str(e)}")
                    continue

        await event.reply(
            f"**Report Summary**\n\n"
            f"Total Bots: {total_bots}\n"
            f"Reports Sent: {successful_reports}\n"
            f"Failed: {failed_reports}\n",
            parse_mode='md'
        )
        logging.info(f"Completed /reportall for user {event.sender_id}: Total bots={total_bots}, Reports sent={successful_reports}, Failed={failed_reports}")
    except Exception as e:
        await event.reply(f"**⚡ Reportall mein error: {str(e)} 🚫**", parse_mode='md')
        logging.error(f"Error in /reportall for user {event.sender_id}: {str(e)}")
    await event.delete()

# Helper function to parse message link
async def parse_message_link(link):
    try:
        match = re.match(r'https://t\.me/(c/)?(\w+)/(\d+)', link)
        if not match:
            return None, None
        chat_identifier = match.group(2)
        message_id = int(match.group(3))
        if match.group(1):  # Private chat (c/)
            chat_id = f"-100{chat_identifier}"
        else:  # Public chat (@username or t.me/username)
            chat_id = f"@{chat_identifier}"
        return chat_id, message_id
    except Exception as e:
        logging.error(f"Error parsing message link: {e}")
        return None, None

# Helper function to map reason to Telegram report reason
def get_report_reason(reason):
    reason = reason.lower()
    reasons = {
        "spam": InputReportReasonSpam(),
        "violence": InputReportReasonViolence(),
        "pornography": InputReportReasonPornography(),
        "childabuse": InputReportReasonChildAbuse(),
        "other": InputReportReasonOther()
    }
    return reasons.get(reason, InputReportReasonOther())

# Helper function to get user ID from username, user ID, or reply
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
                user = await client.get_entity(username)
                return user.id
        else:
            return None
    except Exception as e:
        logging.error(f"Error getting user ID: {e}")
        return None

# Block command handler (owners only)
@client.on(events.NewMessage(pattern=r'^/block(?:\s+(.+))?$'))
async def block_user(event):
    if await check_blocked_user(event):
        return
    if event.sender_id not in PREMIUM_USERS:
        await event.reply("🔐 **Owners Only!** 🔐")
        logging.warning(f"Unauthorized /block attempt by user {event.sender_id}")
        return

    username_or_id = event.pattern_match.group(1)
    target_user_id = await get_user_id(event, username_or_id)

    if not target_user_id:
        await event.reply("Error **Please provide a valid username, user ID, or reply to a user!**", parse_mode='md')
        return

    if target_user_id in PREMIUM_USERS:
        await event.reply("Error **Cannot block an owner!**", parse_mode='md')
        return

    if target_user_id in blocked_users:
        await event.reply("Error **User is already blocked!**", parse_mode='md')
        return

    blocked_users.add(target_user_id)
    save_blocked_users(blocked_users)
    try:
        user = await client.get_entity(target_user_id)
        username = user.username if user.username else str(target_user_id)
        await event.reply(f"Success **User @{username} blocked!**", parse_mode='md')
        logging.info(f"User {target_user_id} blocked by owner {event.sender_id}")
    except:
        await event.reply(f"Success **User ID {target_user_id} blocked!**", parse_mode='md')
        logging.info(f"User {target_user_id} blocked by owner {event.sender_id}")

# Unblock command handler (owners only)
@client.on(events.NewMessage(pattern=r'^/unblock(?:\s+(.+))?$'))
async def unblock_user(event):
    if await check_blocked_user(event):
        return
    if event.sender_id not in PREMIUM_USERS:
        await event.reply("🔐 **Owners Only!** 🔐")
        logging.warning(f"Unauthorized /unblock attempt by user {event.sender_id}")
        return

    username_or_id = event.pattern_match.group(1)
    target_user_id = await get_user_id(event, username_or_id)

    if not target_user_id:
        await event.reply("Error **Please provide a valid username, user ID, or reply to a user!**", parse_mode='md')
        return

    if target_user_id not in blocked_users:
        await event.reply("Error **User is not blocked!**", parse_mode='md')
        return

    blocked_users.remove(target_user_id)
    save_blocked_users(blocked_users)
    try:
        user = await client.get_entity(target_user_id)
        username = user.username if user.username else str(target_user_id)
        await event.reply(f"Success **User @{username} unblocked!**", parse_mode='md')
        logging.info(f"User {target_user_id} unblocked by owner {event.sender_id}")
    except:
        await event.reply(f"Success **User ID {target_user_id} unblocked!**", parse_mode='md')
        logging.info(f"User {target_user_id} unblocked by owner {event.sender_id}")

# Blocked users list handler (owners only)
@client.on(events.NewMessage(pattern="/blockeduser"))
async def blocked_user_list(event):
    if await check_blocked_user(event):
        return
    if event.sender_id not in PREMIUM_USERS:
        await event.reply("🔐 **Owners Only!** 🔐")
        logging.warning(f"Unauthorized /blockeduser attempt by user {event.sender_id}")
        return

    if not blocked_users:
        await event.reply("No users are currently blocked.", parse_mode='md')
        return

    blocked_list = "🚫 **Blocked Users** 🚫\n\n"
    for user_id in blocked_users:
        try:
            user = await client.get_entity(user_id)
            username = user.username if user.username else str(user_id)
            blocked_list += f"➤ @{username}\n"
        except:
            blocked_list += f"➤ User {user_id} (Not Found)\n"

    await event.reply(blocked_list, parse_mode='md')
    logging.info(f"Sent blocked users list to user {event.sender_id}")

# Stats command handler (owners only)
@client.on(events.NewMessage(pattern="/stats"))
async def stats(event):
    
    # ✅ Owner ID hardcode — blocked list se bypass
    OWNER_IDS = [7661825494]
    
    # ✅ Pehle owner check karo, blocked check se pehle
    if event.sender_id not in OWNER_IDS and event.sender_id not in PREMIUM_USERS:
        await event.reply("🔐 **Owners Only!** 🔐")
        logging.warning(f"Unauthorized /stats attempt by user {event.sender_id}")
        return

    # ✅ Agar owner hai toh blocked check skip
    if event.sender_id not in OWNER_IDS:
        if await check_blocked_user(event):
            return

    # --- Total Hosted Userbots ---
    try:
        session_files = [f for f in os.listdir() if f.startswith('userbot_') and f.endswith('.session')]
        total_hosted = len(session_files)
    except Exception as e:
        logging.error(f"Error counting session files: {e}")
        total_hosted = "N/A"

    # --- Total Running Userbots ---
    try:
        total_running = 0
        if isinstance(total_hosted, int):
            for session_file in session_files:
                try:
                    user_id = int(session_file.split('_')[1])
                    is_hosted, is_running = is_userbot_hosted(user_id)
                    if is_hosted and is_running:
                        total_running += 1
                except Exception as inner_e:
                    logging.warning(f"Skipping session file {session_file}: {inner_e}")
                    continue
    except Exception as e:
        logging.error(f"Error counting running userbots: {e}")
        total_running = "N/A"

    # --- Total Sudo Users ---
    try:
        total_sudo = len(sudo_users)
    except Exception as e:
        logging.error(f"Error counting sudo users: {e}")
        total_sudo = "N/A"

    # --- Total Blocked Users ---
    try:
        total_blocked = len(blocked_users)
    except Exception as e:
        logging.error(f"Error counting blocked users: {e}")
        total_blocked = "N/A"

    # --- Bot Uptime ---
    try:
        uptime_seconds = int(time.time() - BOT_START_TIME)
        uptime = str(timedelta(seconds=uptime_seconds))
    except Exception as e:
        logging.error(f"Error calculating uptime: {e}")
        uptime = "N/A"

    # --- Final Message ---
    stats_message = (
        "📊 **Bot Statistics** 📊\n\n"
        f"🔹 **Total Hosted Userbots**: {total_hosted}\n"
        f"🔹 **Total Running Userbots**: {total_running}\n"
        f"🔹 **Total Sudo Users**: {total_sudo}\n"
        f"🔹 **Total Blocked Users**: {total_blocked}\n"
        f"🔹 **Bot Uptime**: {uptime}\n"
    )

    # ✅ Reply safely
    try:
        await event.reply(stats_message, parse_mode='md')
        logging.info(f"Sent bot stats to user {event.sender_id}")
    except Exception as e:
        logging.error(f"Failed to send stats message: {e}")
        try:
            await event.reply("⚠️ Stats fetch hua but message send nahi ho saka. Logs check karo.")
        except:
            pass

# Host command handler
@client.on(events.NewMessage(pattern="/host"))
async def host(event):
    if await check_blocked_user(event):
        return
    user_id = event.sender_id
    is_hosted, is_running = is_userbot_hosted(user_id)
    if is_hosted:
        msg = "Error **Userbot Already Hosted!**\n" + ("Try /restart or /logout." if is_running else "Use /restart or /logout.") + "\nCheck /commands."
        await event.reply(msg, parse_mode='md')
        logging.info(f"User {user_id} attempted to host but already has a userbot")
        return
    if not await is_group_member(user_id):
        await event.reply(
            "Warning **Join Our Support Group!**\n"
            f"Join: [Support Group]({SUPPORT_GROUP_LINK})\n"
            "You can still host.",
            parse_mode='md'
        )
    cleanup_existing_sessions(user_id)
    state_key = (event.chat_id, user_id)
    hosting_state[state_key] = {
        "step": "phone",
        "phone_number": None,
        "session_name": None,
        "userbot_client": None,
        "timeout_task": None,
        "password_attempts": 0
    }
    await event.reply("📱 **Enter Phone Number (+91xxxxxxxxxx):**")
    logging.info(f"Started hosting process for user {user_id}")

    async def timeout():
        await asyncio.sleep(120)
        if state_key in hosting_state and hosting_state[state_key].get("step") == "phone":
            await event.reply("Error **Timeout!** Try /host again.")
            hosting_state.pop(state_key, None)
            logging.info(f"Hosting timeout for user {user_id}")

    hosting_state[state_key]["timeout_task"] = asyncio.create_task(timeout())

#restart_target
@client.on(events.NewMessage(pattern=r'^/ubstart\s+(@?\w+|\d+)$'))
async def ubstart(event):
    user_id = event.sender_id
    logging.info(f"[/ubstart] Command received from user {user_id}")

    # Check if user is owner
    if user_id != OWNER_ID:
        await event.reply("**⚡ Error: Only the owner can use this command! 🚫**", parse_mode='md')
        logging.warning(f"[/ubstart] User {user_id} attempted to use owner-only command")
        return

    # Get target username or user ID
    target = event.pattern_match.group(1).strip()
    if target.startswith('@'):
        target_username = target.lstrip('@')
        target_user_id = None
    else:
        try:
            target_user_id = int(target)
            target_username = None
        except ValueError:
            await event.reply("**⚡ Error: Invalid username or user ID! 🚫**", parse_mode='md')
            logging.error(f"[/ubstart] Invalid target format: {target}")
            return

    # Resolve target user ID if username is provided
    if target_username:
        try:
            entity = await client.get_entity(target_username)
            target_user_id = entity.id
            target_username = entity.username.lstrip('@') if hasattr(entity, 'username') and entity.username else str(target_user_id)
        except Exception as e:
            await event.reply(f"**⚡ Error fetching user @{target_username}: {str(e)} 🚫**", parse_mode='md')
            logging.error(f"[/ubstart] Error fetching user @{target_username}: {str(e)}")
            return
    else:
        target_username = str(target_user_id)

    # Check if userbot is hosted
    is_hosted, is_running = is_userbot_hosted(target_user_id)
    if not is_hosted:
        await event.reply(f"**⚡ Error: No userbot hosted for @{target_username} or ID {target_user_id}! Use /host. 🚫**", parse_mode='md')
        logging.info(f"[/ubstart] No userbot hosted for user {target_user_id} (@{target_username})")
        return

    # Stop existing userbot process if running
    if is_running:
        try:
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    if proc.info['cmdline'] and f'userbot_{target_user_id}' in ' '.join(proc.info['cmdline']):
                        proc.kill()
                        logging.info(f"[/ubstart] Killed userbot process for user {target_user_id} (@{target_username}): PID {proc.pid}")
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
        except Exception as e:
            await event.reply(f"**⚡ Error stopping userbot for @{target_username}: {str(e)} 🚫**", parse_mode='md')
            logging.error(f"[/ubstart] Error stopping userbot for user {target_user_id} (@{target_username}): {str(e)}")
            return

    await event.reply(f"**🔄 Processing: Starting userbot for @{target_username}...**", parse_mode='md')
    logging.info(f"[/ubstart] Initiating start for user {target_user_id} (@{target_username})")

    # Find session file
    session_files = [f for f in os.listdir() if f.startswith(f'userbot_{target_user_id}') and f.endswith('.session')]
    if not session_files:
        await event.reply(f"**⚡ Error: No session file found for @{target_username}! Use /host. 🚫**", parse_mode='md')
        logging.info(f"[/ubstart] No session file found for user {target_user_id} (@{target_username})")
        return
    session_name = session_files[0].replace('.session', '')

    # Remove old log file
    log_file = f"userbot_{target_user_id}.log"
    if os.path.exists(log_file):
        try:
            os.remove(log_file)
            logging.info(f"[/ubstart] Removed old log file: {log_file}")
        except Exception as e:
            logging.error(f"[/ubstart] Error removing log file {log_file}: {str(e)}")

    # Start userbot
    max_retries = 3
    for attempt in range(max_retries):
        try:
            with open(log_file, "a") as f:
                process = subprocess.Popen(
                    ["nohup", "python3", "userbot.py", session_name],
                    stdin=subprocess.PIPE,
                    stdout=f,
                    stderr=f,
                    shell=False,
                    preexec_fn=os.setsid
                )
                process.stdin.close()
            await asyncio.sleep(10)
            if process.poll() is None:
                await event.reply(f"**✅ Success: Userbot for @{target_username} started!** Use .ping to verify.", parse_mode='md')
                logging.info(f"[/ubstart] Userbot started successfully for user {target_user_id} (@{target_username})")
                return
            else:
                with open(log_file, "r") as f:
                    log_output = f.read()[:3000]
                await event.reply(f"**⚡ Error (Attempt {attempt + 1}/{max_retries}) for @{target_username}:\n{log_output} 🚫**", parse_mode='md')
                logging.error(f"[/ubstart] Error starting userbot for user {target_user_id} (@{target_username}) (Attempt {attempt + 1}): {log_output}")
                await asyncio.sleep(10)
        except Exception as e:
            await event.reply(f"**⚡ Error (Attempt {attempt + 1}/{max_retries}) for @{target_username}: {str(e)} 🚫**", parse_mode='md')
            logging.error(f"[/ubstart] Exception while starting userbot for user {target_user_id} (@{target_username}) (Attempt {attempt + 1}): {str(e)}")
            await asyncio.sleep(10)
    await event.reply(f"**⚡ Error: Failed to start userbot for @{target_username}! Try /host. 🚫**", parse_mode='md')
    logging.warning(f"[/ubstart] Failed to start userbot for user {target_user_id} (@{target_username}) after {max_retries} attempts")

# Restart command handler
@client.on(events.NewMessage(pattern="/restart"))
async def restart(event):
    if await check_blocked_user(event):
        return
    user_id = event.sender_id
    is_hosted, is_running = is_userbot_hosted(user_id)
    if not is_hosted:
        await event.reply("Error **No Userbot Hosted!**\nUse /host.", parse_mode='md')
        logging.info(f"User {user_id} attempted /restart but no userbot hosted")
        return
    if is_running:
        try:
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    if proc.info['cmdline'] and f'userbot_{user_id}' in ' '.join(proc.info['cmdline']):
                        proc.kill()
                        logging.info(f"Killed userbot process: PID {proc.pid}")
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
        except Exception as e:
            await event.reply(f"Error Stopping Userbot: {e}", parse_mode='md')
            logging.error(f"Error stopping userbot for user {user_id}: {e}")
            return
    await event.reply("Processing **Restarting Userbot...**", parse_mode='md')
    session_files = [f for f in os.listdir() if f.startswith(f'userbot_{user_id}') and f.endswith('.session')]
    if not session_files:
        await event.reply("Error **No Session File!** Use /host.", parse_mode='md')
        logging.info(f"No session file found for user {user_id}")
        return
    session_name = session_files[0].replace('.session', '')
    log_file = f"userbot_{user_id}.log"
    if os.path.exists(log_file):
        os.remove(log_file)
        logging.info(f"Removed old log file: {log_file}")
    max_retries = 3
    for attempt in range(max_retries):
        try:
            with open(log_file, "a") as f:
                process = subprocess.Popen(
                    ["nohup", "python3", "userbot.py", session_name],
                    stdin=subprocess.PIPE,
                    stdout=f,
                    stderr=f,
                    shell=False,
                    preexec_fn=os.setsid
                )
                process.stdin.close()
            await asyncio.sleep(10)
            if process.poll() is None:
                await event.reply("Success **Userbot Restarted!**\nUse .ping.", parse_mode='md')
                logging.info(f"Userbot restarted successfully for user {user_id}")
                return
            else:
                with open(log_file, "r") as f:
                    log_output = f.read()[:3000]
                await event.reply(f"Error (Attempt {attempt + 1}/{max_retries}):\n{log_output}", parse_mode='md')
                logging.error(f"Error restarting userbot for user {user_id} (Attempt {attempt + 1}): {log_output}")
                await asyncio.sleep(10)
        except Exception as e:
            await event.reply(f"Error (Attempt {attempt + 1}/{max_retries}): {e}", parse_mode='md')
            logging.error(f"Exception while restarting userbot for user {user_id} (Attempt {attempt + 1}): {e}")
            await asyncio.sleep(10)
    await event.reply("Error **Failed to Restart!** Try /host.", parse_mode='md')
    logging.warning(f"Failed to restart userbot for user {user_id} after {max_retries} attempts")

# Restart all userbots handler
@client.on(events.NewMessage(pattern="/restartall"))
async def restart_all(event):
    if await check_blocked_user(event):
        return
    if event.sender_id not in PREMIUM_USERS:
        await event.reply("🔐 **Owners Only!** 🔐")
        logging.warning(f"Unauthorized /restartall attempt by user {event.sender_id}")
        return
    session_files = [f for f in os.listdir() if f.startswith('userbot_') and f.endswith('.session')]
    if not session_files:
        await event.reply("Error **No Userbots Found!**")
        logging.info(f"No userbots found for /restartall by user {event.sender_id}")
        return
    await event.reply("Processing **Restarting All Userbots...**", parse_mode='md')
    logging.info(f"Restarting all userbots for user {event.sender_id}")
    restarted_bots = 0
    failed_bots = 0
    for session_file in session_files:
        try:
            user_id = int(session_file.split('_')[1])
            if is_userbot_hosted(user_id)[1]:
                for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                    try:
                        if proc.info['cmdline'] and f'userbot_{user_id}' in ' '.join(proc.info['cmdline']):
                            proc.kill()
                            logging.info(f"Killed userbot process: PID {proc.pid}")
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        pass
            log_file = f"userbot_{user_id}.log"
            if os.path.exists(log_file):
                os.remove(log_file)
                logging.info(f"Removed old log file: {log_file}")
            session_name = session_file.replace('.session', '')
            with open(log_file, "a") as f:
                process = subprocess.Popen(
                    ["nohup", "python3", "userbot.py", session_name],
                    stdin=subprocess.PIPE,
                    stdout=f,
                    stderr=f,
                    shell=False,
                    preexec_fn=os.setsid
                )
                process.stdin.close()
            await asyncio.sleep(10)
            if process.poll() is None:
                restarted_bots += 1
                try:
                    await client.send_message(user_id, "Success **Userbot Restarted!**\nUse .ping.", parse_mode='md')
                    logging.info(f"Userbot restarted for user {user_id}")
                except:
                    pass
            else:
                failed_bots += 1
                logging.warning(f"Failed to restart userbot for user {user_id}")
        except Exception as e:
            failed_bots += 1
            logging.error(f"Exception while restarting userbot for user {user_id}: {e}")
    await event.reply(
        f"Restart Complete!\n"
        f"Total Bots: {len(session_files)}\n"
        f"Restarted: {restarted_bots}\n"
        f"Failed: {failed_bots}",
        parse_mode='md'
    )
    logging.info(f"Completed restart of all userbots for user {event.sender_id}: Restarted={restarted_bots}, Failed={failed_bots}")

# Logout command handler
@client.on(events.NewMessage(pattern="/logout"))
async def logout(event):
    if await check_blocked_user(event):
        return
    user_id = event.sender_id
    is_hosted, is_running = is_userbot_hosted(user_id)
    if not is_hosted:
        await event.reply("Error **No Userbot Hosted!**\nUse /host.", parse_mode='md')
        logging.info(f"User {user_id} attempted /logout but no userbot hosted")
        return
    if is_running:
        try:
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    if proc.info['cmdline'] and f"userbot_{user_id}" in ' '.join(proc.info['cmdline']):
                        proc.kill()
                        logging.info(f"Killed userbot process: PID {proc.pid}")
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
        except Exception as e:
            await event.reply(f"Error Stopping Userbot: {e}", parse_mode='md')
            logging.error(f"Error stopping userbot for user {user_id}: {e}")
            return
    cleanup_existing_sessions(user_id)
    await event.reply("Success **Userbot Logged Out!**\nUse /host to re-host.", parse_mode='md')
    logging.info(f"Userbot logged out for user {user_id}")

# ===================== SUPPORT RAID SYSTEM v3 (FULLY FIXED + LIFETIME) =====================

# /supporthost → ab 101% working
@client.on(events.NewMessage(pattern="^/supporthost$"))
async def supporthost(event):
    if event.sender_id not in PREMIUM_USERS:
        await event.reply("**Sirf Owner use kar sakta hai!**")
        return

    await event.reply("**Support Account Add Kar Rahe Hain**\n\nPhone number daal (+91xxxxxxxxxx):")

    async with client.conversation(event.chat_id, timeout=300) as conv:
        try:
            phone_msg = await conv.wait_event(events.NewMessage(from_users=event.sender_id))
            phone = phone_msg.message.message.strip()

            temp_client = TelegramClient(StringSession(), api_id, api_hash)
            await temp_client.connect()
            code = await temp_client.send_code_request(phone)

            await conv.send_message("OTP daal (12345 format me):")
            otp_msg = await conv.wait_event(events.NewMessage(from_users=event.sender_id))
            otp = otp_msg.message.message.strip().replace(" ", "")

            await temp_client.sign_in(phone, code=otp)
            me = await temp_client.get_me()

            session_string = temp_client.session.save()

            # Save in list + file
            new_acc = {
                "phone": phone,
                "user_id": me.id,
                "first_name": me.first_name,
                "username": me.username or "None",
                "session_string": session_string
            }

            # Duplicate check
            if any(acc["user_id"] == me.id for acc in support_accounts):
                await conv.send_message("**Ye account already add hai bhai!**")
                await temp_client.disconnect()
                return

            support_accounts.append(new_acc)
            save_support_accounts()

            await conv.send_message(
                f"**SUPPORT ACCOUNT SUCCESSFULLY ADDED**\n\n"
                f"Name: {me.first_name}\n"
                f"Username: @{me.username or 'None'}\n"
                f"ID: `{me.id}`\n"
                f"Total Accounts: `{len(support_accounts)}`\n\n"
                f"Ab `.supportraid` full power se chalega!"
            )
            await temp_client.disconnect()

        except Exception as e:
            await conv.send_message(f"**Error ho gaya:** `{str(e)}`")
            try:
                await temp_client.disconnect()
            except:
                pass

# /supportlist → ab sab show honge
@client.on(events.NewMessage(pattern="^/supportlist$"))
async def support_list(event):
    if event.sender_id not in PREMIUM_USERS:
        return

    if not support_accounts:
        await event.reply("**Abhi tak koi support account add nahi kiya!**")
        return

    text = "**LIFETIME SUPPORT ACCOUNTS**\n\n"
    for i, acc in enumerate(support_accounts, 1):
        text += f"{i}. {acc['first_name']} (@{acc['username']}) - `{acc['user_id']}`\n"

    text += f"\n**Total:** `{len(support_accounts)}` accounts"
    await event.reply(text)

# Sd (Save Disappearing) command handler
@client.on(events.NewMessage(pattern=r'^\.sd$'))
async def save_disappearing(event):
    user_id = event.sender_id
    # Check if user is a sudo user (only sudo users can use this command)
    if user_id not in sudo_users:
        await event.reply("🔐 **This Command is for Sudo Users Only!** 🔐", parse_mode='md')
        logging.warning(f"Unauthorized .sd attempt by user {user_id}")
        return
    logging.info(f"Sudo user {user_id} used .sd command")
    try:
        # Check if the command is a reply to a message
        if not event.reply_to_msg_id:
            await client.send_message('me', "**⚡ Disappearing message ko save karne ke liye uska reply do! 🚫**", parse_mode='md')
            await event.delete()
            return

        reply_msg = await event.get_reply_message()
        if not reply_msg:
            await client.send_message('me', "**⚡ Replied message invalid ya expired hai! 🚫**", parse_mode='md')
            await event.delete()
            return

        # Check if message has content to save
        if not reply_msg.text and not reply_msg.media:
            await client.send_message('me', "**⚡ Reply mein koi content nahi hai save karne ke liye! 🚫**", parse_mode='md')
            await event.delete()
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
                    media_path = f"disappearing_media_{user_id}_{int(time.time())}.jpg"
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
                        media_path = f"disappearing_media_{user_id}_{int(time.time())}.mp4"
                        await reply_msg.download_media(file=media_path)
                        video_attributes = {
                            "duration": video_attr.duration,
                            "w": video_attr.w,
                            "h": video_attr.h
                        }
                    else:
                        # Handle other documents if needed (e.g., GIFs, files)
                        media_type = "document"
                        media_path = f"disappearing_media_{user_id}_{int(time.time())}"
                        await reply_msg.download_media(file=media_path)
                else:
                    await client.send_message('me', "**⚡ Unsupported media type! Sirf photo, video ya document support karta hai. 🚫**", parse_mode='md')
                    await event.delete()
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

        # Delete the command message
        await event.delete()

    except Exception as e:
        await client.send_message('me', f"**⚡ Sd mein error: {str(e)} 🚫**", parse_mode='md')
        await event.delete()

# Handler for hosting responses
@client.on(events.NewMessage())
async def handle_hosting_response(event):
    state_key = (event.chat_id, event.sender_id)
    if state_key not in hosting_state:
        return
    if event.text.startswith(('.', '/', '!')):
        return
    state = hosting_state.get(state_key, {})
    if not state or "step" not in state:
        await event.reply("Error **Session Expired!** Use /host.", parse_mode='md')
        hosting_state.pop(state_key, None)
        logging.info(f"Hosting session expired for user {event.sender_id}")
        return

    if state.get("timeout_task"):
        state["timeout_task"].cancel()
        state["timeout_task"] = None

    if state["step"] == "phone":
        phone_number = event.text.strip()
        if not phone_number.startswith('+'):
            await event.reply("📱 **Use Country Code (+91xxxxxxxxxx)!** Try again.", parse_mode='md')
            hosting_state.pop(state_key, None)
            logging.info(f"Invalid phone number format by user {event.sender_id}")
            return
        timestamp = int(time.time())
        session_name = f"userbot_{event.sender_id}_{timestamp}"
        userbot_client = TelegramClient(session_name, api_id, api_hash)
        try:
            await userbot_client.connect()
            sent_code = await userbot_client.send_code_request(phone_number)
        except FloodWaitError as e:
            await event.reply(f"Rate Limit! Wait {e.seconds} seconds.", parse_mode='md')
            hosting_state.pop(state_key, None)
            logging.error(f"Flood wait error for user {event.sender_id}: {e}")
            return
        except Exception as e:
            await event.reply(f"Error Sending Code: {e}", parse_mode='md')
            hosting_state.pop(state_key, None)
            logging.error(f"Error sending code for user {event.sender_id}: {e}")
            return

        state["step"] = "otp"
        state["phone_number"] = phone_number
        state["session_name"] = session_name
        state["userbot_client"] = userbot_client
        await event.reply("🔑 **Enter OTP (e.g., 1 2 3 4 5):** Hurry, expires in 1-2 min!")
        logging.info(f"Sent OTP request for user {event.sender_id}")
        async def timeout():
            await asyncio.sleep(120)
            if state_key in hosting_state and hosting_state[state_key].get("step") == "otp":
                await event.reply("Error **Timeout!** Try /host again.")
                hosting_state.pop(state_key, None)
                logging.info(f"OTP timeout for user {event.sender_id}")

        state["timeout_task"] = asyncio.create_task(timeout())
    elif state["step"] == "otp":
        otp = event.text.strip()
        userbot_client = state["userbot_client"]
        phone_number = state["phone_number"]
        try:
            await userbot_client.sign_in(phone_number, code=otp.replace(" ", ""))
            await event.reply("🚀 **Hosting userbot, please wait...**", parse_mode='md')
        except PhoneCodeInvalidError:
            await event.reply("Error **Invalid OTP!** Try /host.", parse_mode='md')
            hosting_state.pop(state_key, None)
            logging.info(f"Invalid OTP provided by user {event.sender_id}")
            return
        except SessionPasswordNeededError:
            state["step"] = "password"
            state["password_attempts"] = 0
            await event.reply("🔒 **Enter 2FA Password:**")
            logging.info(f"2FA password required for user {event.sender_id}")

            async def timeout():
                await asyncio.sleep(120)
                if state_key in hosting_state and hosting_state[state_key].get("step") == "password":
                    await event.reply("Error **Timeout!** Try /host again.")
                    hosting_state.pop(state_key, None)
                    logging.info(f"2FA password timeout for user {event.sender_id}")
            state["timeout_task"] = asyncio.create_task(timeout())
            return
        except Exception as e:
            await event.reply(f"Error Signing In: {e}", parse_mode='md')
            hosting_state.pop(state_key, None)
            logging.error(f"Error signing in for user {event.sender_id}: {e}")
            return

        await complete_hosting(event, state_key)
    elif state["step"] == "password":
        password = event.text.strip()
        userbot_client = state["userbot_client"]
        state["password_attempts"] += 1
        max_attempts = 4

        try:
            await userbot_client.sign_in(password=password)
            await event.reply("🚖 **Hosting userbot, please wait...**", parse_mode='md')
        except Exception as e:
            remaining_attempts = max_attempts - state["password_attempts"]
            if remaining_attempts > 0:
                await event.reply(
                    f"Your 2FA password is incorrect. Please re-enter the password (only {remaining_attempts} tries left).",
                    parse_mode='md'
                )
                logging.info(f"Invalid 2FA password attempt {state['password_attempts']} by user {event.sender_id}")
                return
            else:
                await event.reply("Error **All 4 attempts failed!** Try /host again.", parse_mode='md')
                hosting_state.pop(state_key, None)
                logging.error(f"User {event.sender_id} failed all 2FA password attempts")
                return

        await complete_hosting(event, state_key)

async def complete_hosting(event, state_key):
    state = hosting_state.get(state_key, {})
    userbot_client = state["userbot_client"]
    session_name = state["session_name"]
    try:
        await userbot_client.disconnect()
    except Exception as e:
        await event.reply(f"Error Disconnecting: {e}", parse_mode='md')
        hosting_state.pop(state_key, None)
        logging.error(f"Error disconnecting userbot for user {event.sender_id}: {e}")
        return
    log_file = f"userbot_{event.sender_id}.log"
    if os.path.exists(log_file):
        os.remove(log_file)
        logging.info(f"Removed old log file: {log_file}")
    max_retries = 3
    for attempt in range(max_retries):
        try:
            with open(log_file, "a") as f:
                process = subprocess.Popen(
                    ["nohup", "python3", "userbot.py", session_name],
                    stdin=subprocess.PIPE,
                    stdout=f,
                    stderr=f,
                    shell=False,
                    preexec_fn=os.setsid
                )
                process.stdin.close()
            await asyncio.sleep(10)
            if process.poll() is None:
                await event.reply("Success **Userbot Hosted!**\nUse .ping to check.", parse_mode='md')
                logging.info(f"Userbot hosted successfully for user {event.sender_id}")
                hosting_state.pop(state_key, None)
                return
            else:
                with open(log_file, "r") as f:
                    log_output = f.read()[:3000]
                await event.reply(f"Error (Attempt {attempt + 1}/{max_retries}):\n{log_output}", parse_mode='md')
                logging.error(f"Error hosting userbot for user {event.sender_id} (Attempt {attempt + 1}): {log_output}")
                await asyncio.sleep(10)
        except Exception as e:
            await event.reply(f"Error (Attempt {attempt + 1}/{max_retries}): {e}", parse_mode='md')
            logging.error(f"Exception while hosting userbot for user {event.sender_id} (Attempt {attempt + 1}): {e}")
            await asyncio.sleep(10)
    await event.reply("Error **Failed to Host!** Try /host again.", parse_mode='md')
    logging.warning(f"Failed to host userbot for user {event.sender_id} after {max_retries} attempts")

# Start the client
if __name__ == '__main__':
    try:
        client.run_until_disconnected()
    except Exception as e:
        logging.error(f"Error running client: {e}")
        print(f"Error: {e}")
