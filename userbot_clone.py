# userbot_clone.py — Full English + All Commands

from telethon import events, Button
from telethon.tl.functions.channels import EditBannedRequest, EditAdminRequest
from telethon.tl.functions.messages import UpdatePinnedMessageRequest
from telethon.tl.types import ChatBannedRights, ChatAdminRights
import asyncio
import time
import random
from datetime import datetime, timedelta
import json
import os

AUTHORIZED_FILE = "authorized_users.json"
WELCOME_FILE = "clone_welcomes.json"
CHATS_FILE = "broadcast_chats.json"
WARNS_FILE = "warns_data.json"
GBAN_FILE = "gban_list.json"

RAID_MESSAGES = [
    "𝐓𝐄𝐑𝐈 𝐌𝐀𝐀 𝐊𝐈 𝐂𝐇𝐔𝐓 𝐌𝐄 ✋ 𝐇𝐀𝐓𝐓𝐇 𝐃𝐀𝐋𝐊𝐄 👶 𝐁𝐀𝐂𝐂𝐇𝐄 𝐍𝐈𝐊𝐀𝐋 𝐃𝐔𝐍𝐆𝐀 😍",
    "𝐆𝐀𝐋𝐈 𝐆𝐀𝐋𝐈 𝐌𝐄 𝐑𝐄𝐇𝐓𝐀 𝐇𝐄 𝐒𝐀𝐍𝐃 𝐓𝐄𝐑𝐈 𝐌𝐀𝐀𝐊𝐎 𝐂𝐇𝐎𝐃 𝐃𝐀𝐋𝐀 𝐎𝐑 𝐁𝐀𝐍𝐀 𝐃𝐈𝐀 𝐑𝐀𝐍𝐃 🤤🤣",
    "𝐓𝐄𝐑𝐈 𝐌𝐀𝐀 𝐊𝐀 𝐁𝐇𝐎𝐒𝐃𝐀 𝐌𝐄 𝐋𝐔𝐍𝐃 𝐃𝐀𝐀𝐋 𝐊𝐄 𝐂𝐇𝐎𝐃𝐔𝐍𝐆𝐀 𝐑𝐀𝐍𝐃𝐈 𝐊𝐄 𝐁𝐀𝐂𝐇𝐇𝐄",
    "𝐁𝐄𝐇𝐄𝐍 𝐊𝐄 𝐋𝐀𝐔𝐃𝐄 𝐓𝐄𝐑𝐈 𝐌𝐀𝐀 𝐊𝐈 𝐂𝐇𝐔𝐓 𝐌𝐄 𝐒𝐔𝐓𝐋𝐈 𝐁𝐎𝐌𝐁 𝐃𝐀𝐀𝐋 𝐃𝐔𝐍𝐆𝐀",
    "𝐓𝐄𝐑𝐈 𝐌𝐀𝐀 𝐊𝐈 𝐂𝐇𝐔𝐓 𝐌𝐄 𝐃𝐄𝐓𝐎𝐋 𝐃𝐀𝐀𝐋 𝐊𝐄 𝐂𝐇𝐎𝐃𝐔𝐍𝐆𝐀 𝐌𝐀𝐃𝐀𝐑𝐂𝐇𝐎𝐃",
    "𝐑𝐀𝐍𝐃𝐈 𝐊𝐄 𝐁𝐀𝐂𝐇𝐇𝐄 𝐓𝐄𝐑𝐈 𝐁𝐄𝐇𝐄𝐍 𝐊𝐈 𝐂𝐇𝐔𝐓 𝐌𝐀𝐀𝐑𝐔𝐍𝐆𝐀",
    "𝐓𝐄𝐑𝐈 𝐌𝐀𝐀 𝐊𝐎 𝐂𝐇𝐎𝐃 𝐂𝐇𝐎𝐃 𝐊𝐄 𝐑𝐀𝐍𝐃 𝐁𝐀𝐍𝐀 𝐃𝐈𝐘𝐀",
    "𝐋𝐔𝐍𝐃 𝐊𝐄 𝐁𝐀𝐀𝐋 𝐓𝐄𝐑𝐈 𝐌𝐀𝐀 𝐊𝐈 𝐂𝐇𝐔𝐓 𝐌𝐄 𝐌𝐔𝐓𝐇 𝐌𝐀𝐀𝐑𝐔𝐍𝐆𝐀",
    "𝐓𝐄𝐑𝐈 𝐁𝐄𝐇𝐄𝐍 𝐊𝐈 𝐂𝐇𝐔𝐓 𝐌𝐄 𝐋𝐔𝐍𝐃 𝐃𝐀𝐀𝐋 𝐊𝐄 𝐇𝐈𝐋𝐀𝐔𝐍𝐆𝐀",
    "𝐌𝐀𝐃𝐀𝐑𝐂𝐇𝐎𝐃 𝐓𝐄𝐑𝐈 𝐌𝐀𝐀 𝐊𝐀 𝐁𝐇𝐎𝐒𝐃𝐀 𝐅𝐀𝐀𝐃 𝐃𝐔𝐍𝐆𝐀",
    "𝐓𝐄𝐑𝐈 𝐌𝐀𝐀 𝐊𝐈 𝐂𝐇𝐔𝐓 𝐌𝐄 𝐇𝐀𝐀𝐓𝐇 𝐃𝐀𝐀𝐋 𝐊𝐄 𝐁𝐀𝐂𝐂𝐇𝐄 𝐍𝐈𝐊𝐀𝐀𝐋𝐔𝐍𝐆𝐀",
    "𝐑𝐀𝐍𝐃𝐈 𝐊𝐄 𝐏𝐈𝐋𝐋𝐄 𝐓𝐄𝐑𝐈 𝐌𝐀𝐀 𝐊𝐎 𝐂𝐇𝐎𝐃𝐔𝐍𝐆𝐀",
    "𝐁𝐇𝐎𝐒𝐃𝐈𝐊𝐄 𝐓𝐄𝐑𝐈 𝐁𝐄𝐇𝐄𝐍 𝐊𝐈 𝐂𝐇𝐔𝐓 𝐌𝐀𝐀𝐑 𝐊𝐄 𝐑𝐀𝐊𝐇𝐔𝐍𝐆𝐀",
    "𝐓𝐄𝐑𝐈 𝐌𝐀𝐀 𝐊𝐀 𝐁𝐇𝐎𝐒𝐃𝐀 𝐂𝐇𝐎𝐃 𝐊𝐄 𝐋𝐀𝐀𝐋 𝐊𝐀𝐑 𝐃𝐔𝐍𝐆𝐀",
    "𝐂𝐇𝐔𝐓𝐈𝐘𝐄 𝐓𝐄𝐑𝐈 𝐌𝐀𝐀 𝐊𝐈 𝐂𝐇𝐔𝐓 𝐌𝐄 𝐋𝐔𝐍𝐃 𝐃𝐀𝐀𝐋𝐔𝐍𝐆𝐀",
    "𝐓𝐄𝐑𝐈 𝐌𝐀𝐀 𝐊𝐈 𝐂𝐇𝐔𝐓 𝐌𝐄 𝐇𝐀𝐓𝐇𝐎𝐃𝐀 𝐌𝐀𝐀𝐑𝐔𝐍𝐆𝐀 𝐑𝐀𝐍𝐃𝐈 𝐊𝐄 𝐁𝐀𝐂𝐇𝐇𝐄",
    "𝐁𝐄𝐇𝐄𝐍𝐂𝐇𝐎𝐃 𝐓𝐄𝐑𝐈 𝐌𝐀𝐀 𝐊𝐎 𝐊𝐇𝐔𝐋𝐄 𝐁𝐀𝐉𝐀𝐀𝐑 𝐌𝐄 𝐂𝐇𝐎𝐃𝐔𝐍𝐆𝐀",
    "𝐓𝐄𝐑𝐈 𝐁𝐄𝐇𝐄𝐍 𝐊𝐀 𝐁𝐇𝐎𝐒𝐃𝐀 𝐅𝐀𝐀𝐃 𝐊𝐄 𝐑𝐀𝐊𝐇 𝐃𝐔𝐍𝐆𝐀",
    "𝐌𝐀𝐃𝐀𝐑𝐂𝐇𝐎𝐃 𝐓𝐄𝐑𝐈 𝐆𝐀𝐀𝐍𝐃 𝐌𝐄 𝐋𝐔𝐍𝐃 𝐃𝐀𝐀𝐋 𝐊𝐄 𝐂𝐇𝐎𝐃𝐔𝐍𝐆𝐀",
    "𝐑𝐀𝐍𝐃𝐈 𝐊𝐄 𝐀𝐔𝐋𝐀𝐃 𝐓𝐄𝐑𝐈 𝐌𝐀𝐀 𝐊𝐈 𝐂𝐇𝐔𝐓 𝐌𝐀𝐀𝐑𝐔𝐍𝐆𝐀",
]

SHAYARI_MESSAGES = [
    "💕 **𝐓𝐞𝐫𝐢 𝐚𝐚𝐧𝐤𝐡𝐨𝐧 𝐦𝐞 𝐝𝐮𝐛 𝐣𝐚𝐧𝐚 𝐜𝐡𝐚𝐡𝐭𝐚 𝐡𝐮𝐧,**\n**𝐉𝐚𝐢𝐬𝐞 𝐬𝐚𝐦𝐮𝐧𝐝𝐚𝐫 𝐦𝐞 𝐥𝐞𝐡𝐫𝐞𝐧 𝐝𝐮𝐛𝐭𝐢 𝐡𝐚𝐢𝐧.** 🌸",
    "❤️ **𝐓𝐮𝐦𝐡𝐚𝐫𝐢 𝐦𝐮𝐬𝐤𝐚𝐧 𝐦𝐞𝐫𝐞 𝐝𝐢𝐥 𝐤𝐚 𝐬𝐮𝐤𝐨𝐨𝐧 𝐡𝐚𝐢,**\n**𝐁𝐢𝐧𝐚 𝐭𝐮𝐦𝐡𝐚𝐫𝐞 𝐲𝐞 𝐝𝐢𝐥 𝐚𝐝𝐡𝐮𝐫𝐚 𝐥𝐚𝐠𝐭𝐚 𝐡𝐚𝐢.** ✨",
    "🌹 **𝐂𝐡𝐚𝐧𝐝 𝐛𝐡𝐢 𝐬𝐡𝐚𝐫𝐦𝐚 𝐣𝐚𝐲𝐞 𝐭𝐞𝐫𝐢 𝐚𝐝𝐚𝐨𝐧 𝐬𝐞,**\n**𝐓𝐮 𝐡𝐚𝐢 𝐰𝐨 𝐧𝐨𝐨𝐫 𝐣𝐨 𝐫𝐚𝐚𝐭𝐨𝐧 𝐤𝐨 𝐫𝐨𝐬𝐡𝐚𝐧 𝐤𝐚𝐫 𝐝𝐞.** 🌙",
    "💖 **𝐓𝐞𝐫𝐞 𝐛𝐢𝐧𝐚 𝐲𝐞 𝐝𝐮𝐧𝐢𝐲𝐚 𝐬𝐮𝐧𝐢 𝐥𝐚𝐠𝐭𝐢 𝐡𝐚𝐢,**\n**𝐓𝐮 𝐚𝐚 𝐣𝐚 𝐭𝐨 𝐡𝐚𝐫 𝐥𝐚𝐦𝐡𝐚 𝐤𝐡𝐮𝐬𝐡𝐢𝐲𝐨𝐧 𝐬𝐞 𝐛𝐡𝐚𝐫 𝐣𝐚𝐲𝐞.** 🦋",
    "🥰 **𝐌𝐨𝐡𝐚𝐛𝐛𝐚𝐭 𝐤𝐢 𝐢𝐧𝐭𝐞𝐡𝐚 𝐭𝐮 𝐡𝐚𝐢 𝐦𝐞𝐫𝐞 𝐥𝐢𝐲𝐞,**\n**𝐓𝐞𝐫𝐞 𝐛𝐚𝐚𝐝 𝐤𝐨𝐢 𝐚𝐮𝐫 𝐧𝐚𝐡𝐢 𝐜𝐡𝐚𝐡𝐢𝐲𝐞.** 💗",
    "💞 **𝐓𝐞𝐫𝐢 𝐲𝐚𝐝𝐨𝐧 𝐦𝐞 𝐤𝐡𝐨𝐲𝐚 𝐫𝐞𝐡𝐭𝐚 𝐡𝐮𝐧 𝐦𝐚𝐢𝐧,**\n**𝐇𝐚𝐫 𝐬𝐚𝐚𝐧𝐬 𝐦𝐞 𝐭𝐞𝐫𝐚 𝐧𝐚𝐦 𝐥𝐞𝐭𝐚 𝐡𝐮𝐧 𝐦𝐚𝐢𝐧.** 🌺",
    "💘 **𝐓𝐮𝐦 𝐦𝐞𝐫𝐞 𝐝𝐢𝐥 𝐤𝐢 𝐝𝐡𝐚𝐝𝐤𝐚𝐧 𝐛𝐚𝐧 𝐠𝐚𝐲𝐞 𝐡𝐨,**\n**𝐀𝐛 𝐛𝐢𝐧𝐚 𝐭𝐮𝐦𝐡𝐚𝐫𝐞 𝐣𝐞𝐞𝐧𝐚 𝐦𝐮𝐬𝐡𝐤𝐢𝐥 𝐡𝐨 𝐠𝐚𝐲𝐚.** 💫",
    "🌷 **𝐀𝐚𝐧𝐤𝐡𝐨𝐧 𝐬𝐞 𝐚𝐚𝐧𝐤𝐡𝐞𝐧 𝐦𝐢𝐥𝐚𝐤𝐞 𝐝𝐞𝐤𝐡𝐨,**\n**𝐊𝐢𝐭𝐧𝐚 𝐩𝐲𝐚𝐫 𝐜𝐡𝐡𝐮𝐩𝐚 𝐡𝐚𝐢 𝐢𝐧𝐦𝐞 𝐭𝐮𝐦𝐡𝐚𝐫𝐞 𝐥𝐢𝐲𝐞.** 🌸",
    "💓 **𝐓𝐞𝐫𝐞 𝐥𝐢𝐲𝐞 𝐝𝐢𝐥 𝐬𝐞 𝐝𝐮𝐚 𝐤𝐚𝐫𝐭𝐚 𝐡𝐮𝐧,**\n**𝐇𝐚𝐫 𝐤𝐡𝐮𝐬𝐡𝐢 𝐭𝐞𝐫𝐞 𝐧𝐚𝐬𝐞𝐞𝐛 𝐦𝐞 𝐚𝐚𝐲𝐞.** 🌈",
    "💗 **𝐓𝐮𝐦𝐡𝐚𝐫𝐚 𝐧𝐚𝐚𝐦 𝐥𝐞𝐭𝐞 𝐡𝐢 𝐦𝐮𝐬𝐤𝐮𝐫𝐚𝐡𝐚𝐭 𝐚𝐚 𝐣𝐚𝐭𝐢 𝐡𝐚𝐢,**\n**𝐘𝐞 𝐦𝐨𝐡𝐚𝐛𝐛𝐚𝐭 𝐤𝐚 𝐚𝐬𝐚𝐫 𝐡𝐚𝐢 𝐦𝐞𝐫𝐞 𝐝𝐢𝐥 𝐩𝐞.** ✨",
    "🌹 **𝐓𝐞𝐫𝐞 𝐢𝐬𝐡𝐪 𝐦𝐞 𝐝𝐢𝐰𝐚𝐧𝐚 𝐡𝐨 𝐠𝐚𝐲𝐚 𝐡𝐮𝐧 𝐦𝐚𝐢𝐧,**\n**𝐀𝐛 𝐤𝐨𝐢 𝐚𝐮𝐫 𝐧𝐚𝐳𝐚𝐫 𝐧𝐚𝐡𝐢 𝐚𝐚𝐭𝐚.** 💕",
    "💖 **𝐉𝐚𝐛 𝐬𝐞 𝐭𝐮𝐦𝐡𝐞 𝐝𝐞𝐤𝐡𝐚 𝐡𝐚𝐢,**\n**𝐓𝐚𝐛 𝐬𝐞 𝐝𝐢𝐥 𝐛𝐬 𝐭𝐮𝐦𝐡𝐞 𝐡𝐢 𝐜𝐡𝐚𝐡𝐭𝐚 𝐡𝐚𝐢.** 🦋",
    "🥰 **𝐓𝐮𝐦𝐡𝐚𝐫𝐢 𝐛𝐚𝐚𝐭𝐞𝐧 𝐲𝐚𝐝 𝐚𝐚𝐭𝐢 𝐡𝐚𝐢𝐧 𝐫𝐚𝐚𝐭 𝐛𝐡𝐚𝐫,**\n**𝐍𝐞𝐞𝐧𝐝 𝐮𝐝 𝐣𝐚𝐭𝐢 𝐡𝐚𝐢 𝐭𝐞𝐫𝐞 𝐤𝐡𝐚𝐲𝐚𝐥𝐨𝐧 𝐦𝐞.** 🌙",
    "💗 **𝐌𝐞𝐫𝐚 𝐝𝐢𝐥 𝐭𝐞𝐫𝐞 𝐧𝐚𝐚𝐦 𝐬𝐞 𝐝𝐡𝐚𝐝𝐤𝐭𝐚 𝐡𝐚𝐢,**\n**𝐘𝐞 𝐩𝐲𝐚𝐫 𝐤𝐚𝐛𝐡𝐢 𝐤𝐡𝐚𝐭𝐚𝐦 𝐧𝐚𝐡𝐢 𝐡𝐨𝐠𝐚.** ✨",
    "💞 **𝐓𝐮 𝐡𝐚𝐢 𝐦𝐞𝐫𝐢 𝐳𝐢𝐧𝐝𝐚𝐠𝐢 𝐤𝐚 𝐬𝐚𝐛𝐬𝐞 𝐡𝐚𝐬𝐞𝐞𝐧 𝐡𝐢𝐬𝐬𝐚,**\n**𝐁𝐢𝐧𝐚 𝐭𝐞𝐫𝐞 𝐤𝐮𝐜𝐡 𝐛𝐡𝐢 𝐚𝐝𝐡𝐮𝐫𝐚 𝐥𝐚𝐠𝐭𝐚 𝐡𝐚𝐢.** 🌸",
]

# Paste your long braid messages here
BRAID_MESSAGES = [
    "**𝐓𝐄𝐑𝐈 𝐌𝐀𝐀 𝐊𝐈 𝐂𝐇𝐔𝐓 𝐌𝐄 𝐈𝐓𝐍𝐀 𝐁𝐀𝐃𝐀 𝐋𝐔𝐍𝐃 𝐃𝐀𝐀𝐋𝐔𝐍𝐆𝐀 𝐊𝐈 𝐖𝐎 𝐂𝐇𝐈𝐋𝐋𝐀𝐓𝐄 𝐂𝐇𝐈𝐋𝐋𝐀𝐓𝐄 𝐇𝐎𝐒𝐇 𝐊𝐇𝐎 𝐃𝐄𝐆𝐈** 😂😂\n"
    "**𝐔𝐒𝐊𝐄 𝐁𝐀𝐀𝐃 𝐔𝐒𝐊𝐈 𝐆𝐀𝐀𝐍𝐃 𝐌𝐄 𝐁𝐇𝐈 𝐒𝐀𝐌𝐀𝐀𝐍 𝐃𝐀𝐀𝐋 𝐊𝐄 𝐃𝐎𝐍𝐎 𝐂𝐇𝐇𝐄𝐃 𝐄𝐊 𝐒𝐀𝐀𝐓𝐇 𝐂𝐇𝐎𝐃𝐔𝐍𝐆𝐀** 🤣🤣\n"
    "**𝐓𝐄𝐑𝐈 𝐁𝐄𝐇𝐄𝐍 𝐊𝐎 𝐁𝐇𝐈 𝐏𝐀𝐀𝐒 𝐁𝐈𝐓𝐇𝐀 𝐊𝐄 𝐃𝐄𝐊𝐇𝐍𝐄 𝐃𝐔𝐍𝐆𝐀 𝐊𝐈 𝐔𝐒𝐊𝐈 𝐌𝐀𝐀 𝐊𝐀𝐈𝐒𝐄 𝐂𝐇𝐔𝐃 𝐑𝐀𝐇𝐈 𝐇𝐀𝐈** 😈\n"
    "**𝐏𝐇𝐈𝐑 𝐓𝐄𝐑𝐈 𝐁𝐄𝐇𝐄𝐍 𝐊𝐈 𝐁𝐇𝐈 𝐁𝐀𝐀𝐑𝐈 𝐀𝐀𝐘𝐄𝐆𝐈 𝐀𝐔𝐑 𝐃𝐎𝐍𝐎 𝐌𝐀𝐀-𝐁𝐄𝐓𝐈 𝐄𝐊 𝐒𝐀𝐀𝐓𝐇 𝐑𝐀𝐍𝐃𝐈 𝐁𝐀𝐍 𝐉𝐀𝐘𝐄𝐍𝐆𝐈** 💀\n"
    "**𝐓𝐄𝐑𝐀 𝐏𝐔𝐑𝐀 𝐊𝐇𝐀𝐍𝐃𝐀𝐀𝐍 𝐌𝐄𝐑𝐄 𝐋𝐔𝐍𝐃 𝐊𝐀 𝐆𝐔𝐋𝐀𝐀𝐌 𝐁𝐀𝐍 𝐉𝐀𝐘𝐄𝐆𝐀** 🔥🔥\n"
    "**𝐀𝐁 𝐁𝐎𝐋 𝐌𝐀𝐃𝐀𝐑𝐂𝐇𝐎𝐃 𝐊𝐈𝐓𝐍𝐀 𝐌𝐀𝐙𝐀 𝐀𝐀𝐘𝐀** 😂🤣",

    "**𝐒𝐔𝐍 𝐑𝐀𝐍𝐃𝐈 𝐊𝐄 𝐁𝐀𝐂𝐇𝐇𝐄 𝐓𝐄𝐑𝐈 𝐌𝐀𝐀 𝐊𝐈 𝐂𝐇𝐔𝐓 𝐊𝐀 𝐌𝐄𝐑𝐀 𝐏𝐔𝐑𝐀𝐍𝐀 𝐊𝐇𝐀𝐓𝐀 𝐇𝐀𝐈** 😈\n"
    "**𝐌𝐀𝐈𝐍𝐄 𝐔𝐒𝐊𝐎 𝐈𝐓𝐍𝐀 𝐂𝐇𝐎𝐃𝐀 𝐊𝐈 𝐔𝐒𝐊𝐈 𝐂𝐇𝐔𝐓 𝐊𝐀 𝐒𝐊𝐈𝐍 𝐋𝐀𝐀𝐋 𝐇𝐎 𝐆𝐀𝐘𝐀 𝐓𝐇𝐀** 😂\n"
    "**𝐀𝐀𝐉 𝐏𝐇𝐈𝐑 𝐒𝐄 𝐔𝐒𝐈 𝐂𝐇𝐔𝐓 𝐌𝐄 𝐋𝐔𝐍𝐃 𝐃𝐀𝐀𝐋 𝐊𝐄 𝐔𝐒𝐄 𝐘𝐀𝐀𝐃 𝐃𝐈𝐋𝐀𝐔𝐍𝐆𝐀** 🤣🤣\n"
    "**𝐓𝐄𝐑𝐈 𝐁𝐄𝐇𝐄𝐍 𝐊𝐈 𝐆𝐀𝐀𝐍𝐃 𝐁𝐇𝐈 𝐔𝐓𝐍𝐈 𝐇𝐈 𝐓𝐈𝐆𝐇𝐓 𝐇𝐀𝐈 𝐉𝐈𝐓𝐍𝐈 𝐓𝐄𝐑𝐈 𝐌𝐀𝐀 𝐊𝐈 𝐂𝐇𝐔𝐓 𝐓𝐇𝐈** 💀\n"
    "**𝐃𝐎𝐍𝐎 𝐊𝐎 𝐄𝐊 𝐒𝐀𝐀𝐓𝐇 𝐍𝐀𝐍𝐆𝐀 𝐊𝐀𝐑 𝐊𝐄 𝐂𝐇𝐎𝐃𝐔𝐍𝐆𝐀 𝐀𝐔𝐑 𝐓𝐔𝐉𝐇𝐄 𝐕𝐈𝐃𝐄𝐎 𝐁𝐇𝐄𝐉𝐔𝐍𝐆𝐀** 🔥\n"
    "**𝐏𝐇𝐈𝐑 𝐃𝐄𝐊𝐇𝐍𝐀 𝐊𝐀𝐈𝐒𝐄 𝐑𝐎𝐓𝐀 𝐇𝐀𝐈 𝐓𝐔 𝐌𝐀𝐃𝐀𝐑𝐂𝐇𝐎𝐃** 😂😂",

    "**𝐓𝐄𝐑𝐈 𝐌𝐀𝐀 𝐊𝐎 𝐊𝐇𝐔𝐋𝐄 𝐁𝐀𝐉𝐀𝐀𝐑 𝐌𝐄 𝐍𝐀𝐍𝐆𝐀 𝐊𝐀𝐑 𝐊𝐄 𝐂𝐇𝐎𝐃𝐔𝐍𝐆𝐀** 😈💀\n"
    "**𝐋𝐎𝐆 𝐃𝐄𝐊𝐇𝐓𝐄 𝐑𝐀𝐇𝐄𝐍𝐆𝐄 𝐀𝐔𝐑 𝐓𝐄𝐑𝐈 𝐌𝐀𝐀 𝐌𝐄𝐑𝐄 𝐋𝐔𝐍𝐃 𝐏𝐄 𝐔𝐂𝐇𝐀𝐋𝐓𝐈 𝐑𝐀𝐇𝐄𝐆𝐈** 😂🤣\n"
    "**𝐔𝐒𝐊𝐄 𝐌𝐔𝐇 𝐌𝐄 𝐋𝐔𝐍𝐃 𝐃𝐀𝐀𝐋 𝐊𝐄 𝐔𝐒𝐞 𝐂𝐇𝐔𝐏 𝐊𝐀𝐑𝐀𝐔𝐍𝐆𝐀** 🔥\n"
    "**𝐏𝐇𝐈𝐑 𝐓𝐄𝐑𝐈 𝐁𝐄𝐇𝐄𝐍 𝐊𝐎 𝐁𝐔𝐋𝐀 𝐊𝐄 𝐊𝐀𝐇𝐔𝐍𝐆𝐀 𝐀𝐀 𝐀𝐏𝐍𝐈 𝐌𝐀𝐀 𝐊𝐈 𝐓𝐀𝐑𝐀𝐇 𝐂𝐇𝐔𝐃𝐖𝐀** 🤣\n"
    "**𝐃𝐎𝐍𝐎 𝐌𝐀𝐀 𝐁𝐄𝐓𝐈 𝐌𝐄𝐑𝐄 𝐋𝐔𝐍𝐃 𝐊𝐈 𝐃𝐀𝐀𝐒𝐈 𝐁𝐀𝐍 𝐉𝐀𝐘𝐄𝐍𝐆𝐈** 💀\n"
    "**𝐓𝐄𝐑𝐀 𝐏𝐔𝐑𝐀 𝐆𝐇𝐀𝐑 𝐌𝐄𝐑𝐀 𝐑𝐀𝐍𝐃𝐈𝐊𝐇𝐀𝐍𝐀 𝐁𝐀𝐍 𝐂𝐇𝐔𝐊𝐀 𝐇𝐀𝐈** 😂🔥",

    "**𝐀𝐁𝐄 𝐋𝐔𝐍𝐃 𝐊𝐄 𝐁𝐀𝐀𝐋 𝐓𝐄𝐑𝐈 𝐌𝐀𝐀 𝐊𝐈 𝐂𝐇𝐔𝐓 𝐌𝐄 𝐒𝐔𝐓𝐋𝐈 𝐁𝐎𝐌𝐁 𝐃𝐀𝐀𝐋 𝐃𝐔𝐍𝐆𝐀** 💣😂\n"
    "**𝐉𝐀𝐁 𝐖𝐎 𝐏𝐇𝐀𝐓𝐄𝐆𝐀 𝐓𝐎 𝐔𝐒𝐊𝐈 𝐂𝐇𝐔𝐓 𝐊𝐄 𝐏𝐀𝐑𝐂𝐇𝐄 𝐔𝐃𝐓𝐄 𝐇𝐔𝐄 𝐍𝐀𝐙𝐀𝐑 𝐀𝐀𝐘𝐄𝐍𝐆𝐄** 🤣💀\n"
    "**𝐔𝐒𝐊𝐄 𝐁𝐀𝐀𝐃 𝐁𝐇𝐈 𝐌𝐀𝐈𝐍 𝐔𝐒𝐈 𝐂𝐇𝐔𝐓 𝐌𝐄 𝐋𝐔𝐍𝐃 𝐃𝐀𝐀𝐋 𝐊𝐄 𝐂𝐇𝐎𝐃𝐓𝐀 𝐑𝐀𝐇𝐔𝐍𝐆𝐀** 🔥\n"
    "**𝐓𝐄𝐑𝐈 𝐁𝐄𝐇𝐄𝐍 𝐊𝐈 𝐆𝐀𝐀𝐍𝐃 𝐌𝐄 𝐁𝐇𝐈 𝐖𝐀𝐇𝐈 𝐒𝐀𝐌𝐀𝐀𝐍 𝐃𝐀𝐀𝐋𝐔𝐍𝐆𝐀** 😈\n"
    "**𝐃𝐎𝐍𝐎 𝐊𝐈 𝐂𝐇𝐈𝐊𝐇𝐄𝐍 𝐒𝐔𝐍 𝐊𝐄 𝐌𝐀𝐙𝐀 𝐀𝐀𝐘𝐄𝐆𝐀** 😂😂\n"
    "**𝐁𝐎𝐋 𝐌𝐀𝐃𝐀𝐑𝐂𝐇𝐎𝐃 𝐀𝐁 𝐊𝐘𝐀 𝐊𝐀𝐑𝐄𝐆𝐀** 🤣",

    "**𝐓𝐄𝐑𝐈 𝐌𝐀𝐀 𝐊𝐀 𝐁𝐇𝐎𝐒𝐃𝐀 𝐅𝐀𝐀𝐃 𝐊𝐄 𝐔𝐒𝐌𝐄 𝐀𝐏𝐍𝐀 𝐋𝐔𝐍𝐃 𝐃𝐀𝐀𝐋 𝐃𝐔𝐍𝐆𝐀** 💀🔥\n"
    "**𝐈𝐓𝐍𝐈 𝐓𝐄𝐉𝐈 𝐒𝐄 𝐂𝐇𝐎𝐃𝐔𝐍𝐆𝐀 𝐊𝐈 𝐔𝐒𝐊𝐄 𝐀𝐀𝐍𝐒𝐔 𝐍𝐈𝐊𝐀𝐋 𝐉𝐀𝐘𝐄𝐍𝐆𝐄** 😂\n"
    "**𝐏𝐇𝐈𝐑 𝐁𝐇𝐈 𝐍𝐀𝐇𝐈 𝐑𝐔𝐊𝐔𝐍𝐆𝐀 𝐉𝐀𝐁 𝐓𝐀𝐊 𝐖𝐎 𝐁𝐄𝐇𝐎𝐒𝐇 𝐍𝐀𝐇𝐈 𝐇𝐎 𝐉𝐀𝐓𝐈** 🤣\n"
    "**𝐓𝐄𝐑𝐈 𝐁𝐄𝐇𝐄𝐍 𝐊𝐎 𝐁𝐇𝐈 𝐖𝐀𝐇𝐈 𝐇𝐀𝐀𝐋 𝐊𝐀𝐑𝐔𝐍𝐆𝐀** 😈\n"
    "**𝐃𝐎𝐍𝐎 𝐊𝐎 𝐄𝐊 𝐁𝐄𝐃 𝐏𝐄 𝐋𝐈𝐓𝐀 𝐊𝐄 𝐁𝐀𝐀𝐑 𝐁𝐀𝐀𝐑 𝐂𝐇𝐎𝐃𝐔𝐍𝐆𝐀** 🔥💀\n"
    "**𝐓𝐄𝐑𝐀 𝐏𝐔𝐑𝐀 𝐊𝐇𝐀𝐍𝐃𝐀𝐀𝐍 𝐌𝐄𝐑𝐄 𝐍𝐈𝐂𝐇𝐄 𝐀𝐀 𝐂𝐇𝐔𝐊𝐀 𝐇𝐀𝐈** 😂😂",

    "**𝐒𝐔𝐍 𝐁𝐄𝐇𝐄𝐍𝐂𝐇𝐎𝐃 𝐓𝐄𝐑𝐈 𝐌𝐀𝐀 𝐊𝐈 𝐂𝐇𝐔𝐓 𝐌𝐄𝐑𝐄 𝐋𝐔𝐍𝐃 𝐊𝐈 𝐏𝐔𝐑𝐀𝐍𝐈 𝐆𝐀𝐀𝐃𝐈 𝐇𝐀𝐈** 🚗😂\n"
    "**𝐌𝐀𝐈𝐍 𝐔𝐒𝐌𝐞 𝐑𝐎𝐙 𝐒𝐀𝐖𝐀𝐀𝐑𝐈 𝐊𝐀𝐑𝐓𝐀 𝐇𝐔𝐍** 🤣\n"
    "**𝐀𝐀𝐉 𝐓𝐄𝐑𝐈 𝐁𝐄𝐇𝐄𝐍 𝐊𝐈 𝐆𝐀𝐀𝐍𝐃 𝐁𝐇𝐈 𝐔𝐒𝐈 𝐆𝐀𝐀𝐃𝐈 𝐌𝐄 𝐁𝐀𝐈𝐓𝐇𝐄𝐆𝐈** 💀\n"
    "**𝐃𝐎𝐍𝐎 𝐊𝐎 𝐂𝐇𝐎𝐃 𝐂𝐇𝐎𝐃 𝐊𝐄 𝐓𝐇𝐀𝐊𝐀 𝐃𝐔𝐍𝐆𝐀** 🔥\n"
    "**𝐏𝐇𝐈𝐑 𝐔𝐍𝐊𝐄 𝐌𝐔𝐇 𝐏𝐄 𝐌𝐔𝐓𝐇 𝐌𝐀𝐀𝐑 𝐊𝐄 𝐂𝐇𝐀𝐋𝐀 𝐉𝐀𝐔𝐍𝐆𝐀** 😈😂\n"
    "**𝐓𝐔 𝐁𝐀𝐒 𝐃𝐄𝐊𝐇𝐓𝐀 𝐑𝐀𝐇 𝐉𝐀𝐈𝐒𝐄 𝐓𝐄𝐑𝐈 𝐌𝐀𝐀 𝐀𝐔𝐑 𝐁𝐄𝐇𝐄𝐍 𝐂𝐇𝐔𝐃 𝐑𝐀𝐇𝐈 𝐇𝐀𝐈𝐍** 🤣🤣",

    "**𝐓𝐄𝐑𝐈 𝐌𝐀𝐀 𝐊𝐈 𝐂𝐇𝐔𝐓 𝐌𝐄 𝐇𝐀𝐀𝐓𝐇 𝐃𝐀𝐀𝐋 𝐊𝐄 𝐁𝐀𝐂𝐂𝐇𝐄 𝐍𝐈𝐊𝐀𝐀𝐋 𝐃𝐔𝐍𝐆𝐀** 👶😂\n"
    "**𝐔𝐒𝐊𝐄 𝐁𝐀𝐀𝐃 𝐔𝐒𝐈 𝐂𝐇𝐔𝐓 𝐌𝐄 𝐋𝐔𝐍𝐃 𝐃𝐀𝐀𝐋 𝐊𝐄 𝐏𝐇𝐈𝐑 𝐒𝐄 𝐂𝐇𝐎𝐃𝐔𝐍𝐆𝐀** 🔥\n"
    "**𝐓𝐄𝐑𝐈 𝐁𝐄𝐇𝐄𝐍 𝐊𝐎 𝐃𝐄𝐊𝐇𝐍𝐄 𝐃𝐔𝐍𝐆𝐀 𝐊𝐈 𝐔𝐒𝐊𝐈 𝐌𝐀𝐀 𝐊𝐀𝐈𝐒𝐄 𝐑𝐀𝐍𝐃𝐈 𝐁𝐀𝐍 𝐑𝐀𝐇𝐈 𝐇𝐀𝐈** 🤣\n"
    "**𝐏𝐇𝐈𝐑 𝐓𝐄𝐑𝐈 𝐁𝐄𝐇𝐄𝐍 𝐊𝐈 𝐁𝐇𝐈 𝐂𝐇𝐔𝐓 𝐌𝐀𝐀𝐑𝐔𝐍𝐆𝐀** 💀\n"
    "**𝐃𝐎𝐍𝐎 𝐊𝐈 𝐂𝐇𝐔𝐓 𝐄𝐊 𝐉𝐀𝐈𝐒𝐈 𝐇𝐎 𝐉𝐀𝐘𝐄𝐆𝐈 𝐌𝐄𝐑𝐄 𝐋𝐔𝐍𝐃 𝐒𝐄** 😈\n"
    "**𝐀𝐁 𝐁𝐎𝐋 𝐊𝐀𝐇𝐀𝐍 𝐇𝐀𝐈 𝐓𝐄𝐑𝐀 𝐆𝐔𝐑𝐔𝐑 𝐌𝐀𝐃𝐀𝐑𝐂𝐇𝐎𝐃** 😂😂",

    "**𝐑𝐀𝐍𝐃𝐈 𝐊𝐄 𝐏𝐈𝐋𝐋𝐄 𝐓𝐄𝐑𝐈 𝐌𝐀𝐀 𝐊𝐎 𝐌𝐀𝐈𝐍𝐄 𝐈𝐓𝐍𝐀 𝐂𝐇𝐎𝐃𝐀 𝐊𝐈 𝐖𝐎 𝐌𝐄𝐑𝐄 𝐍𝐀𝐀𝐌 𝐒𝐄 𝐇𝐈 𝐆𝐈𝐋𝐈 𝐇𝐎 𝐉𝐀𝐓𝐈 𝐇𝐀𝐈** 💦😂\n"
    "**𝐀𝐀𝐉 𝐏𝐇𝐈𝐑 𝐔𝐒𝐄 𝐁𝐔𝐋𝐀 𝐊𝐄 𝐔𝐒𝐊𝐈 𝐂𝐇𝐔𝐓 𝐊𝐀 𝐏𝐀𝐀𝐍𝐈 𝐍𝐈𝐊𝐀𝐀𝐋𝐔𝐍𝐆𝐀** 🤣\n"
    "**𝐓𝐄𝐑𝐈 𝐁𝐄𝐇𝐄𝐍 𝐊𝐈 𝐆𝐀𝐀𝐍𝐃 𝐁𝐇𝐈 𝐔𝐒𝐈 𝐓𝐀𝐑𝐀𝐇 𝐆𝐈𝐋𝐈 𝐊𝐀𝐑𝐔𝐍𝐆𝐀** 🔥\n"
    "**𝐃𝐎𝐍𝐎 𝐊𝐎 𝐄𝐊 𝐒𝐀𝐀𝐓𝐇 𝐍𝐀𝐍𝐆𝐀 𝐊𝐀𝐑 𝐊𝐄 𝐂𝐇𝐎𝐃𝐓𝐀 𝐑𝐀𝐇𝐔𝐍𝐆𝐀** 💀😈\n"
    "**𝐓𝐄𝐑𝐀 𝐆𝐇𝐀𝐑 𝐌𝐄𝐑𝐀 𝐑𝐀𝐍𝐃𝐈𝐊𝐇𝐀𝐍𝐀 𝐁𝐀𝐍 𝐂𝐇𝐔𝐊𝐀 𝐇𝐀𝐈** 😂\n"
    "**𝐀𝐁 𝐓𝐔 𝐂𝐔𝐏 𝐑𝐀𝐇 𝐘𝐀 𝐏𝐇𝐈𝐑 𝐓𝐄𝐑𝐈 𝐌𝐀𝐀 𝐊𝐄 𝐒𝐀𝐀𝐓𝐇 𝐓𝐔𝐉𝐇𝐄 𝐁𝐇𝐈 𝐂𝐇𝐎𝐃𝐔𝐍𝐆𝐀** 🤣🔥",

    "**𝐓𝐄𝐑𝐈 𝐌𝐀𝐀 𝐊𝐈 𝐂𝐇𝐔𝐓 𝐌𝐄 𝐋𝐔𝐍𝐃 𝐃𝐀𝐀𝐋 𝐊𝐄 𝐔𝐒𝐞 𝐇𝐈𝐋𝐀 𝐇𝐈𝐋𝐀 𝐊𝐄 𝐂𝐇𝐎𝐃𝐔𝐍𝐆𝐀** 😂💀\n"
    "**𝐔𝐒𝐊𝐈 𝐂𝐇𝐈𝐊𝐇𝐄𝐍 𝐏𝐔𝐑𝐄 𝐌𝐎𝐇𝐀𝐋𝐋𝐄 𝐌𝐄 𝐒𝐔𝐍𝐀𝐈 𝐃𝐄𝐍𝐆𝐈** 🤣\n"
    "**𝐏𝐇𝐈𝐑 𝐓𝐄𝐑𝐈 𝐁𝐄𝐇𝐄𝐍 𝐊𝐎 𝐏𝐀𝐀𝐊𝐀𝐃 𝐊𝐄 𝐔𝐒𝐊𝐈 𝐆𝐀𝐀𝐍𝐃 𝐌𝐀𝐀𝐑𝐔𝐍𝐆𝐀** 🔥\n"
    "**𝐃𝐎𝐍𝐎 𝐊𝐎 𝐓𝐇𝐀𝐊𝐀 𝐃𝐄𝐍𝐄 𝐊𝐄 𝐁𝐀𝐀𝐃 𝐔𝐍𝐊𝐄 𝐌𝐔𝐇 𝐏𝐄 𝐋𝐔𝐍𝐃 𝐑𝐀𝐆𝐀𝐃𝐔𝐍𝐆𝐀** 😈\n"
    "**𝐓𝐄𝐑𝐀 𝐏𝐔𝐑𝐀 𝐅𝐀𝐌𝐈𝐋𝐘 𝐌𝐄𝐑𝐄 𝐋𝐔𝐍𝐃 𝐊𝐀 𝐂𝐇𝐀𝐓𝐍𝐄 𝐖𝐀𝐋𝐀 𝐁𝐀𝐍 𝐉𝐀𝐘𝐄𝐆𝐀** 😂😂\n"
    "**𝐁𝐎𝐋 𝐁𝐄𝐇𝐄𝐍𝐂𝐇𝐎𝐃 𝐀𝐁 𝐊𝐘𝐀 𝐇𝐀𝐀𝐋 𝐇𝐀𝐈** 🤣",

    "**𝐀𝐁𝐄 𝐂𝐇𝐔𝐓𝐈𝐘𝐄 𝐓𝐄𝐑𝐈 𝐌𝐀𝐀 𝐊𝐈 𝐂𝐇𝐔𝐓 𝐊𝐀 𝐌𝐄𝐑𝐀 𝐋𝐈𝐂𝐄𝐍𝐒𝐄 𝐇𝐀𝐈** 📜😂\n"
    "**𝐉𝐀𝐁 𝐌𝐀𝐑𝐉𝐈 𝐓𝐀𝐁 𝐔𝐒𝐌𝐞 𝐋𝐔𝐍𝐃 𝐃𝐀𝐀𝐋 𝐒𝐀𝐊𝐓𝐀 𝐇𝐔𝐍** 🔥\n"
    "**𝐀𝐀𝐉 𝐓𝐄𝐑𝐈 𝐁𝐄𝐇𝐄𝐍 𝐊𝐈 𝐆𝐀𝐀𝐍𝐃 𝐊𝐀 𝐁𝐇𝐈 𝐋𝐈𝐂𝐄𝐍𝐒𝐄 𝐁𝐀𝐍𝐀 𝐃𝐔𝐍𝐆𝐀** 🤣💀\n"
    "**𝐃𝐎𝐍𝐎 𝐊𝐎 𝐂𝐇𝐎𝐃 𝐊𝐄 𝐔𝐍𝐊𝐀 𝐈𝐃𝐄𝐀 𝐁𝐃𝐀𝐋 𝐃𝐔𝐍𝐆𝐀** 😈\n"
    "**𝐏𝐇𝐈𝐑 𝐖𝐄 𝐊𝐇𝐔𝐃 𝐌𝐄𝐑𝐄 𝐏𝐀𝐀𝐒 𝐀𝐀𝐘𝐄𝐍𝐆𝐈 𝐂𝐇𝐔𝐃𝐍𝐄 𝐊𝐄 𝐋𝐈𝐘𝐄** 😂\n"
    "**𝐓𝐔 𝐁𝐀𝐒 𝐑𝐎𝐓𝐀 𝐑𝐀𝐇 𝐌𝐀𝐃𝐀𝐑𝐂𝐇𝐎𝐃** 🔥🤣",

    "**𝐓𝐄𝐑𝐈 𝐌𝐀𝐀 𝐊𝐎 𝐁𝐄𝐃 𝐏𝐄 𝐋𝐈𝐓𝐀 𝐊𝐄 𝐔𝐒𝐊𝐈 𝐓𝐀𝐀𝐍𝐆𝐄𝐍 𝐅𝐀𝐈𝐋𝐀 𝐃𝐔𝐍𝐆𝐀** 😈\n"
    "**𝐏𝐇𝐈𝐑 𝐔𝐒𝐊𝐈 𝐂𝐇𝐔𝐓 𝐌𝐄 𝐋𝐔𝐍𝐃 𝐃𝐀𝐀𝐋 𝐊𝐄 𝐉𝐎𝐑 𝐉𝐎𝐑 𝐒𝐄 𝐏𝐄𝐋𝐔𝐍𝐆𝐀** 😂💀\n"
    "**𝐔𝐒𝐊𝐄 𝐌𝐔𝐇 𝐒𝐄 𝐀𝐀𝐖𝐀𝐀𝐙 𝐍𝐈𝐊𝐀𝐋𝐍𝐀 𝐁𝐀𝐍𝐃 𝐍𝐀𝐇𝐈 𝐇𝐎𝐆𝐀** 🤣\n"
    "**𝐓𝐄𝐑𝐈 𝐁𝐄𝐇𝐄𝐍 𝐊𝐎 𝐁𝐇𝐈 𝐔𝐒𝐈 𝐁𝐄𝐃 𝐏𝐄 𝐁𝐔𝐋𝐀 𝐊𝐄 𝐖𝐀𝐇𝐈 𝐇𝐀𝐀𝐋 𝐊𝐀𝐑𝐔𝐍𝐆𝐀** 🔥\n"
    "**𝐃𝐎𝐍𝐎 𝐊𝐈 𝐂𝐇𝐔𝐓 𝐀𝐔𝐑 𝐆𝐀𝐀𝐍𝐃 𝐄𝐊 𝐒𝐀𝐀𝐓𝐇 𝐌𝐀𝐀𝐑𝐔𝐍𝐆𝐀** 💀\n"
    "**𝐓𝐄𝐑𝐀 𝐆𝐇𝐀𝐑 𝐀𝐁 𝐌𝐄𝐑𝐀 𝐂𝐇𝐔𝐃𝐀𝐈 𝐊𝐀 𝐀𝐃𝐃𝐀 𝐇𝐀𝐈** 😂😂",

    "**𝐒𝐔𝐍 𝐑𝐀𝐍𝐃𝐈 𝐊𝐄 𝐁𝐀𝐂𝐇𝐇𝐄 𝐓𝐄𝐑𝐈 𝐌𝐀𝐀 𝐊𝐈 𝐂𝐇𝐔𝐓 𝐌𝐄 𝐌𝐄𝐑𝐀 𝐋𝐔𝐍𝐃 𝐀𝐁 𝐏𝐀𝐊𝐀 𝐇𝐎 𝐆𝐀𝐘𝐀 𝐇𝐀𝐈** 🔥\n"
    "**𝐖𝐎 𝐌𝐄𝐑𝐄 𝐁𝐈𝐍𝐀 𝐑𝐀𝐇 𝐍𝐀𝐇𝐈 𝐒𝐀𝐊𝐓𝐈** 😂\n"
    "**𝐀𝐀𝐉 𝐓𝐄𝐑𝐈 𝐁𝐄𝐇𝐄𝐍 𝐊𝐎 𝐁𝐇𝐈 𝐔𝐒𝐈 𝐀𝐃𝐃𝐈𝐂𝐓𝐈𝐎𝐍 𝐌𝐄 𝐃𝐀𝐀𝐋𝐔𝐍𝐆𝐀** 🤣💀\n"
    "**𝐃𝐎𝐍𝐎 𝐌𝐀𝐀 𝐁𝐄𝐓𝐈 𝐌𝐄𝐑𝐄 𝐋𝐔𝐍𝐃 𝐊𝐄 𝐏𝐈𝐂𝐇𝐇𝐄 𝐁𝐇𝐀𝐆𝐄𝐍𝐆𝐈** 😈\n"
    "**𝐓𝐔 𝐂𝐔𝐏 𝐂𝐇𝐀𝐏 𝐃𝐄𝐊𝐇𝐓𝐀 𝐑𝐀𝐇** 😂\n"
    "**𝐊𝐘𝐎𝐊𝐈 𝐓𝐄𝐑𝐈 𝐌𝐀𝐀 𝐀𝐔𝐑 𝐁𝐄𝐇𝐄𝐍 𝐃𝐎𝐍𝐎 𝐌𝐄𝐑𝐈 𝐑𝐀𝐍𝐃𝐈 𝐇𝐀𝐈𝐍** 🔥🤣",

    "**𝐓𝐄𝐑𝐈 𝐌𝐀𝐀 𝐊𝐈 𝐂𝐇𝐔𝐓 𝐌𝐄 𝐈𝐓𝐍𝐀 𝐋𝐔𝐍𝐃 𝐃𝐀𝐀𝐋𝐔𝐍𝐆𝐀 𝐊𝐈 𝐔𝐒𝐊𝐀 𝐏𝐄𝐓 𝐏𝐇𝐔𝐋 𝐉𝐀𝐘𝐄𝐆𝐀** 😂💀\n"
    "**𝐏𝐇𝐈𝐑 𝐁𝐇𝐈 𝐍𝐀𝐇𝐈 𝐍𝐈𝐊𝐀𝐋𝐔𝐍𝐆𝐀 𝐉𝐀𝐁 𝐓𝐀𝐊 𝐌𝐄𝐑𝐀 𝐌𝐀𝐍 𝐍𝐀𝐇𝐈 𝐁𝐇𝐀𝐑𝐓𝐀** 🔥\n"
    "**𝐓𝐄𝐑𝐈 𝐁𝐄𝐇𝐄𝐍 𝐊𝐈 𝐆𝐀𝐀𝐍𝐃 𝐌𝐄 𝐁𝐇𝐈 𝐖𝐀𝐇𝐈 𝐋𝐔𝐍𝐃 𝐃𝐀𝐀𝐋𝐔𝐍𝐆𝐀** 🤣\n"
    "**𝐃𝐎𝐍𝐎 𝐊𝐎 𝐄𝐊 𝐒𝐀𝐀𝐓𝐇 𝐂𝐇𝐎𝐃𝐓𝐄 𝐇𝐔𝐄 𝐕𝐈𝐃𝐄𝐎 𝐁𝐀𝐍𝐀𝐔𝐍𝐆𝐀** 😈\n"
    "**𝐀𝐔𝐑 𝐓𝐔𝐉𝐇𝐄 𝐁𝐇𝐄𝐉 𝐃𝐔𝐍𝐆𝐀 𝐉𝐀𝐑𝐔𝐑** 😂😂\n"
    "**𝐁𝐎𝐋 𝐌𝐀𝐃𝐀𝐑𝐂𝐇𝐎𝐃 𝐊𝐀𝐈𝐒𝐀 𝐋𝐀𝐆 𝐑𝐀𝐇𝐀 𝐇𝐀𝐈** 🔥",

    "**𝐀𝐁𝐄 𝐋𝐔𝐍𝐃𝐁𝐀𝐀𝐙 𝐓𝐄𝐑𝐈 𝐌𝐀𝐀 𝐊𝐈 𝐂𝐇𝐔𝐓 𝐊𝐀 𝐌𝐄𝐑𝐀 𝐊𝐇𝐀𝐓𝐀 𝐇𝐀𝐈 𝐏𝐔𝐑𝐀𝐍𝐀** 📖😂\n"
    "**𝐌𝐀𝐈𝐍𝐄 𝐔𝐒𝐊𝐎 𝐂𝐇𝐎𝐃 𝐂𝐇𝐎𝐃 𝐊𝐄 𝐔𝐒𝐊𝐈 𝐂𝐇𝐔𝐓 𝐁𝐀𝐃𝐀 𝐃𝐈𝐘𝐀 𝐇𝐀𝐈** 🤣\n"
    "**𝐀𝐀𝐉 𝐓𝐄𝐑𝐈 𝐁𝐄𝐇𝐄𝐍 𝐊𝐈 𝐂𝐇𝐔𝐓 𝐁𝐇𝐈 𝐁𝐀𝐃𝐀𝐔𝐍𝐆𝐀** 💀🔥\n"
    "**𝐃𝐎𝐍𝐎 𝐊𝐈 𝐂𝐇𝐔𝐓 𝐌𝐄𝐑𝐄 𝐋𝐔𝐍𝐃 𝐊𝐄 𝐀𝐍𝐔𝐒𝐀𝐀𝐑 𝐇𝐎 𝐉𝐀𝐘𝐄𝐆𝐈** 😈\n"
    "**𝐏𝐇𝐈𝐑 𝐔𝐍𝐊𝐎 𝐀𝐔𝐑 𝐊𝐎𝐈 𝐂𝐇𝐎𝐃 𝐍𝐀𝐇𝐈 𝐏𝐀𝐘𝐄𝐆𝐀** 😂\n"
    "**𝐊𝐘𝐎𝐊𝐈 𝐖𝐄 𝐒𝐈𝐑𝐅 𝐌𝐄𝐑𝐄 𝐋𝐔𝐍𝐃 𝐒𝐄 𝐇𝐈 𝐒𝐀𝐍𝐓𝐔𝐒𝐇𝐓 𝐇𝐎𝐆𝐈** 🔥🤣",

    "**𝐓𝐄𝐑𝐈 𝐌𝐀𝐀 𝐀𝐔𝐑 𝐁𝐄𝐇𝐄𝐍 𝐃𝐎𝐍𝐎 𝐊𝐎 𝐄𝐊 𝐊𝐀𝐌𝐑𝐄 𝐌𝐄 𝐁𝐀𝐍𝐃 𝐊𝐀𝐑 𝐊𝐄 𝐂𝐇𝐎𝐃𝐔𝐍𝐆𝐀** 😈💀\n"
    "**𝐔𝐍𝐊𝐈 𝐂𝐇𝐈𝐊𝐇𝐄𝐍 𝐁𝐀𝐇𝐀𝐑 𝐓𝐀𝐊 𝐒𝐔𝐍𝐀𝐈 𝐃𝐄𝐍𝐆𝐈** 😂\n"
    "**𝐌𝐀𝐈𝐍 𝐁𝐀𝐀𝐑 𝐁𝐀𝐀𝐑 𝐔𝐍𝐊𝐈 𝐂𝐇𝐔𝐓 𝐀𝐔𝐑 𝐆𝐀𝐀𝐍𝐃 𝐌𝐀𝐀𝐑𝐓𝐀 𝐑𝐀𝐇𝐔𝐍𝐆𝐀** 🔥🤣\n"
    "**𝐉𝐀𝐁 𝐓𝐇𝐀𝐊 𝐉𝐀𝐔𝐍𝐆𝐀 𝐓𝐎 𝐔𝐍𝐊𝐄 𝐌𝐔𝐇 𝐌𝐄 𝐋𝐔𝐍𝐃 𝐃𝐀𝐀𝐋 𝐊𝐄 𝐒𝐎 𝐉𝐀𝐔𝐍𝐆𝐀** 💀\n"
    "**𝐒𝐔𝐁𝐀𝐇 𝐏𝐇𝐈𝐑 𝐒𝐄 𝐖𝐀𝐇𝐈 𝐒𝐇𝐔𝐑𝐔** 😂\n"
    "**𝐓𝐄𝐑𝐀 𝐏𝐔𝐑𝐀 𝐊𝐇𝐀𝐍𝐃𝐀𝐀𝐍 𝐌𝐄𝐑𝐄 𝐋𝐔𝐍𝐃 𝐊𝐀 𝐆𝐔𝐋𝐀𝐀𝐌 𝐇𝐀𝐈** 🔥😈",
]

def load_json(file):
    if os.path.exists(file):
        try:
            with open(file, "r") as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_json(file, data):
    with open(file, "w") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def add_userbot_commands(client, owner_id):
    START_TIME = datetime.now()
    authorized_users = {owner_id}

    auth_data = load_json(AUTHORIZED_FILE)
    authorized_users.update(auth_data.get(str(owner_id), []))

    def save_authorized():
        data = load_json(AUTHORIZED_FILE)
        data[str(owner_id)] = list(authorized_users)
        save_json(AUTHORIZED_FILE, data)

    spam_active = {}
    raid_active = {}
    sraid_active = {}
    braid_active = {}
    tagall_active = {}

    def save_chat(chat_id):
        data = load_json(CHATS_FILE)
        chats = set(data.get(str(owner_id), []))
        chats.add(chat_id)
        data[str(owner_id)] = list(chats)
        save_json(CHATS_FILE, data)

    @client.on(events.NewMessage(incoming=True))
    async def track_chats(event):
        if event.is_group or event.is_channel:
            save_chat(event.chat_id)

    async def safe_delete(event):
        try:
            await event.delete()
        except:
            pass

    async def send_welcome(event, edit=False):
        welcome_data = load_json(WELCOME_FILE)
        custom = welcome_data.get(str(owner_id))

        try:
            real_owner = await event.client.get_entity(owner_id)
            owner_url = f"https://t.me/{real_owner.username}" if real_owner.username else f"tg://user?id={owner_id}"
        except:
            owner_url = f"tg://user?id={owner_id}"

        buttons = [
            [Button.url("👑 𝐎ᴡɴᴇʀ 👑", owner_url)],
            [Button.inline("📜 𝐂ᴏᴍᴍᴀɴᴅs 📜", data="show_commands")]
        ]

        default_text = (
            "╔══════════════════════╗\n"
            "     ✨ 𝐖𝐄𝐋𝐂𝐎𝐌𝐄 ✨\n"
            "╚══════════════════════╝\n\n"
            "❝ 𝐓𝐡𝐢𝐬 𝐢𝐬 𝐚 𝐩𝐨𝐰𝐞𝐫𝐟𝐮𝐥 𝐂𝐥𝐨𝐧𝐞 𝐁𝐨𝐭 ❞\n"
            "❝ 𝐇𝐨𝐬𝐭𝐞𝐝 𝐛𝐲 @userbot_hostbot ❞\n\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "🔹 𝐅𝐚𝐬𝐭 • 𝐒𝐞𝐜𝐮𝐫𝐞 • 𝐒𝐭𝐲𝐥𝐢𝐬𝐡\n"
            "🔹 𝐅𝐮𝐥𝐥 𝐜𝐨𝐧𝐭𝐫𝐨𝐥 𝐢𝐧 𝐲𝐨𝐮𝐫 𝐡𝐚𝐧𝐝𝐬\n"
            "━━━━━━━━━━━━━━━━━━━━\n\n"
            "👉 𝐓𝐚𝐩 **𝐂ᴏᴍᴍᴀɴᴅs** 𝐭𝐨 𝐞𝐱𝐩𝐥𝐨𝐫𝐞 𝐞𝐯𝐞𝐫𝐲𝐭𝐡𝐢𝐧𝐠\n"
            "👉 𝐎𝐧𝐥𝐲 𝐚𝐮𝐭𝐡𝐨𝐫𝐢𝐳𝐞𝐝 𝐮𝐬𝐞𝐫𝐬 𝐜𝐚𝐧 𝐮𝐬𝐞 𝐟𝐞𝐚𝐭𝐮𝐫𝐞𝐬\n\n"
            "「 𝐒𝐭𝐚𝐲 𝐩𝐨𝐰𝐞𝐫𝐟𝐮𝐥 」"
        )

        text = custom["text"] if custom and custom.get("text") else default_text

        if edit:
            await event.edit(text, buttons=buttons, parse_mode="md")
        else:
            await event.reply(text, buttons=buttons, parse_mode="md")

    # ===================== /start =====================
    @client.on(events.NewMessage(pattern=r"^/start$"))
    async def start_clone(event):
        await send_welcome(event)

    # ===================== COMMANDS MENU =====================
    @client.on(events.CallbackQuery(data=b"show_commands"))
    async def show_commands(event):
        if event.sender_id not in authorized_users:
            await event.answer("You are not authorized!", alert=True)
            return

        buttons = [
            [Button.inline("🏓 𝐏ɪɴɢ 🏓", data="cmd_ping"), Button.inline("🔐 𝐀ᴜᴛʜ 🔐", data="cmd_auth")],
            [Button.inline("❌ 𝐃ᴀᴜᴛʜ ❌", data="cmd_dauth"), Button.inline("👥 𝐀ᴜᴛʜᴜsᴇʀs 👥", data="cmd_authusers")],
            [Button.inline("💬 𝐒ᴘᴀᴍ 💬", data="cmd_spam"), Button.inline("💥 𝐑ᴀɪᴅ 💥", data="cmd_raid")],
            [Button.inline("💀 𝐁ʀᴀɪᴅ 💀", data="cmd_braid"), Button.inline("💌 𝐒ʀᴀɪᴅ 💌", data="cmd_sraid")],
            [Button.inline("📢 𝐓ᴀɢᴀʟʟ 📢", data="cmd_tagall"), Button.inline("📡 𝐁ʀᴏᴀᴅᴄᴀsᴛ 📡", data="cmd_broadcast")],
            [Button.inline("🚫 𝐁ᴀɴᴀʟʟ 🚫", data="cmd_banall"), Button.inline("👢 𝐊ɪᴄᴋᴀʟʟ 👢", data="cmd_kickall")],
            [Button.inline("🔇 𝐌ᴜᴛᴇᴀʟʟ 🔇", data="cmd_muteall"), Button.inline("🔊 𝐔ɴᴍᴜᴛᴇᴀʟʟ 🔊", data="cmd_unmuteall")],
            [Button.inline("🧹 𝐏ᴜʀɢᴇ 🧹", data="cmd_purge"), Button.inline("🗑️ 𝐃ᴇʟ 🗑️", data="cmd_del")],
            [Button.inline("🆔 𝐈ᴅ 🆔", data="cmd_id"), Button.inline("ℹ️ 𝐈ɴғᴏ ℹ️", data="cmd_info")],
            [Button.inline("⬆️ 𝐏ʀᴏᴍᴏᴛᴇ ⬆️", data="cmd_promote"), Button.inline("⬇️ 𝐃ᴇᴍᴏᴛᴇ ⬇️", data="cmd_demote")],
            [Button.inline("📌 𝐏ɪɴ 📌", data="cmd_pin"), Button.inline("📍 𝐔ɴᴘɪɴ 📍", data="cmd_unpin")],
            [Button.inline("🚪 𝐋ᴇᴀᴠᴇ 🚪", data="cmd_leave"), Button.inline("⚠️ 𝐖ᴀʀɴ ⚠️", data="cmd_warn")],
            [Button.inline("🌐 𝐆ʙᴀɴ 🌐", data="cmd_gban"), Button.inline("🔓 𝐔ɴɢʙᴀɴ 🔓", data="cmd_ungban")],
            [Button.inline("⏹ 𝐒ᴛᴏᴘ ⏹", data="cmd_stops")],
            [Button.inline("👋 𝐒ᴇᴛᴡᴇʟᴄᴏᴍᴇ 👋", data="cmd_setwelcome"), Button.inline("🔄 𝐑ᴇsᴇᴛᴡᴇʟᴄᴏᴍᴇ 🔄", data="cmd_resetwelcome")],
            [Button.inline("⬅️ 𝐁ᴀᴄᴋ ⬅️", data="back_to_start")]
        ]

        await event.edit(
            "╔══════════════════════╗\n"
            "   ✨ 𝐂𝐎𝐌𝐌𝐀𝐍𝐃 𝐌𝐄𝐍𝐔 ✨\n"
            "╚══════════════════════╝\n\n"
            "Select any command to view details 👇",
            buttons=buttons
        )

    @client.on(events.CallbackQuery(data=b"back_to_start"))
    async def back_to_start(event):
        await send_welcome(event, edit=True)

    @client.on(events.CallbackQuery(pattern=b"cmd_"))
    async def command_detail(event):
        if event.sender_id not in authorized_users:
            await event.answer("You are not authorized!", alert=True)
            return

        data = event.data.decode("utf-8")
        details = {
            "cmd_ping": "🏓 **Ping**\n\nCheck bot speed & uptime.",
            "cmd_auth": "🔐 **Auth**\n\n`/auth @user` or reply\nGrant access (Owner only).",
            "cmd_dauth": "❌ **Dauth**\n\n`/dauth @user` or reply\nRemove access (Owner only).",
            "cmd_authusers": "👥 **Authusers**\n\nList authorized users (Owner only).",
            "cmd_spam": "💬 **Spam**\n\n`/spam 10 hello`\n`/stopspam`",
            "cmd_raid": "💥 **Raid**\n\n`/raid 20`\n`/raid 20 @user`\n`/stopraid`",
            "cmd_braid": "💀 **Braid**\n\n`/braid 10`\n`/braid 10 @user`\n`/stopbraid`",
            "cmd_sraid": "💌 **Sraid**\n\n`/sraid 15`\n`/sraid 15 @user`\n`/stopsraid`",
            "cmd_tagall": "📢 **Tagall**\n\n`/tagall message`\n`/stoptagall`",
            "cmd_broadcast": "📡 **Broadcast**\n\n`/broadcast message`",
            "cmd_banall": "🚫 **Banall**\n\n`/banall`\n`/banall -100xxxxxxxxxx`",
            "cmd_kickall": "👢 **Kickall**\n\nKick all members from group.",
            "cmd_muteall": "🔇 **Muteall**\n\nMute all members.",
            "cmd_unmuteall": "🔊 **Unmuteall**\n\nUnmute all members.",
            "cmd_purge": "🧹 **Purge**\n\nReply to a message → delete from that message to latest.",
            "cmd_del": "🗑️ **Del**\n\nReply to a message to delete it.",
            "cmd_id": "🆔 **Id**\n\n`/id` or reply → show user/chat ID.",
            "cmd_info": "ℹ️ **Info**\n\n`/info` or reply → user details.",
            "cmd_promote": "⬆️ **Promote**\n\nReply or `/promote @user`",
            "cmd_demote": "⬇️ **Demote**\n\nReply or `/demote @user`",
            "cmd_pin": "📌 **Pin**\n\nReply to a message to pin it.",
            "cmd_unpin": "📍 **Unpin**\n\nUnpin the pinned message.",
            "cmd_leave": "🚪 **Leave**\n\nBot leaves the current group.",
            "cmd_warn": "⚠️ **Warn**\n\n`/warn` (reply) • `/warns` (reply)",
            "cmd_gban": "🌐 **Gban**\n\n`/gban` (reply) — ban in all known groups.",
            "cmd_ungban": "🔓 **Ungban**\n\n`/ungban` (reply)",
            "cmd_stops": "⏹ **Stop**\n\n`/stopspam` `/stopraid` `/stopbraid` `/stopsraid` `/stoptagall`",
            "cmd_setwelcome": "👋 **Setwelcome**\n\nReply to a message to set custom welcome.",
            "cmd_resetwelcome": "🔄 **Resetwelcome**\n\nReset to default welcome.",
        }

        text = details.get(data, "Command not found.")
        buttons = [[Button.inline("⬅️ 𝐁ᴀᴄᴋ ⬅️", data="show_commands")]]
        await event.edit(text, buttons=buttons, parse_mode="md")

    # ===================== /ping =====================
    @client.on(events.NewMessage(pattern=r"^/ping$"))
    async def ping_clone(event):
        if event.sender_id not in authorized_users:
            await event.reply("**You are not authorized!**")
            return

        msg = await event.reply("**Initializing system...**")
        await asyncio.sleep(0.35)
        await msg.edit("**Injecting payload...**\n`[█████▒▒▒▒▒] 50%`")
        await asyncio.sleep(0.35)
        await msg.edit("**Access granted**\n`[██████████] 100%`")
        await asyncio.sleep(0.4)

        uptime = datetime.now() - START_TIME
        days, rem = uptime.days, uptime.seconds
        hours, rem = divmod(rem, 3600)
        minutes, seconds = divmod(rem, 60)
        uptime_str = f"{days}d {hours}h {minutes}m {seconds}s"

        await msg.edit(
            f"**❏  ❖ 𝐙𝐔𝐃𝐎 ™ ╮**\n"
            f"**├• ❖ Speed — `FAST`**\n"
            f"**├• ❖ Uptime — `{uptime_str}`**\n"
            f"**├• ❖ Status — `ONLINE 🟢`**\n"
            f"**└• ❖ Hoster — @userbot_hostbot**"
        )

    # ===================== AUTH =====================
    @client.on(events.NewMessage(pattern=r"^/auth(?:\s+(.+))?$"))
    async def auth_user(event):
        if event.sender_id != owner_id:
            await event.reply("**Only owner can use this!**")
            return
        target = event.pattern_match.group(1)
        if event.is_reply:
            user_id = (await (await event.get_reply_message()).get_sender()).id
        elif target:
            target = target.strip()
            try:
                user = await event.client.get_entity(target if target.startswith("@") else int(target))
                user_id = user.id
            except:
                await event.reply("**Invalid username or ID!**")
                return
        else:
            await event.reply("**Reply to a user or provide username/ID.**")
            return
        if user_id in authorized_users:
            await event.reply("**Already authorized.**")
            return
        authorized_users.add(user_id)
        save_authorized()
        await event.reply(f"**User `{user_id}` authorized successfully.**")

    @client.on(events.NewMessage(pattern=r"^/dauth(?:\s+(.+))?$"))
    async def dauth_user(event):
        if event.sender_id != owner_id:
            await event.reply("**Only owner can use this!**")
            return
        target = event.pattern_match.group(1)
        if event.is_reply:
            user_id = (await (await event.get_reply_message()).get_sender()).id
        elif target:
            target = target.strip()
            try:
                user = await event.client.get_entity(target if target.startswith("@") else int(target))
                user_id = user.id
            except:
                await event.reply("**Invalid username or ID!**")
                return
        else:
            await event.reply("**Reply to a user or provide username/ID.**")
            return
        if user_id == owner_id:
            await event.reply("**Cannot remove owner.**")
            return
        if user_id not in authorized_users:
            await event.reply("**User is not authorized.**")
            return
        authorized_users.discard(user_id)
        save_authorized()
        await event.reply(f"**Access removed for `{user_id}`.**")

    @client.on(events.NewMessage(pattern=r"^/authusers$"))
    async def auth_users_list(event):
        if event.sender_id != owner_id:
            await event.reply("**Only owner can use this!**")
            return
        text = "**Authorized Users:**\n\n"
        for uid in authorized_users:
            text += f"• `{uid}` {'(Owner)' if uid == owner_id else ''}\n"
        await event.reply(text)

    # ===================== WELCOME =====================
    @client.on(events.NewMessage(pattern=r"^/setwelcome$"))
    async def set_welcome(event):
        if event.sender_id != owner_id:
            await event.reply("**Only owner can use this!**")
            return
        replied = await event.get_reply_message()
        if not replied:
            await event.reply("**Reply to a message to set it as welcome.**")
            return
        data = load_json(WELCOME_FILE)
        data[str(owner_id)] = {"text": replied.text or replied.message or "Welcome!"}
        save_json(WELCOME_FILE, data)
        await event.reply("**Welcome message updated successfully.**")

    @client.on(events.NewMessage(pattern=r"^/resetwelcome$"))
    async def reset_welcome(event):
        if event.sender_id != owner_id:
            await event.reply("**Only owner can use this!**")
            return
        data = load_json(WELCOME_FILE)
        if str(owner_id) in data:
            del data[str(owner_id)]
            save_json(WELCOME_FILE, data)
        await event.reply("**Welcome reset to default.**")

    # ===================== SPAM =====================
    @client.on(events.NewMessage(pattern=r"^/spam\s+(\d+)(?:\s+([\s\S]+))?$"))
    async def spam_command(event):
        if event.sender_id not in authorized_users:
            await event.reply("**You are not authorized!**")
            return
        try:
            count = int(event.pattern_match.group(1))
            custom_text = event.pattern_match.group(2)
            if count <= 0 or count > 150:
                await event.reply("**Count must be between 1-150.**")
                return
            key = (event.sender_id, event.chat_id)
            spam_active[key] = True
            replied = await event.get_reply_message()
            await safe_delete(event)
            for _ in range(count):
                if not spam_active.get(key):
                    break
                try:
                    if replied and custom_text:
                        await event.client.send_message(event.chat_id, custom_text.strip(), reply_to=replied.id)
                    elif replied and not custom_text:
                        if replied.media:
                            await event.client.send_file(event.chat_id, replied.media, caption=replied.text or None)
                        else:
                            await event.client.send_message(event.chat_id, replied.text or "")
                    elif custom_text:
                        await event.client.send_message(event.chat_id, custom_text.strip())
                    await asyncio.sleep(0.15)
                except:
                    continue
            spam_active.pop(key, None)
        except Exception as e:
            try:
                await event.client.send_message(event.chat_id, f"**Spam Error:** `{e}`")
            except:
                pass

    @client.on(events.NewMessage(pattern=r"^/stopspam$"))
    async def stop_spam(event):
        if event.sender_id not in authorized_users:
            return
        key = (event.sender_id, event.chat_id)
        if spam_active.get(key):
            spam_active[key] = False
            await event.reply("**Spam stopped.**")
        else:
            await event.reply("**No active spam.**")

    # ===================== RAID =====================
    @client.on(events.NewMessage(pattern=r"^/raid\s+(\d+)(?:\s+(@?\w+|\d+))?$"))
    async def raid_command(event):
        if event.sender_id not in authorized_users:
            await event.reply("**You are not authorized!**")
            return
        try:
            count = int(event.pattern_match.group(1))
            target = event.pattern_match.group(2)
            if count <= 0 or count > 200:
                await event.reply("**Count must be between 1-200.**")
                return
            mention = ""
            if target:
                try:
                    user = await event.client.get_entity(target if target.startswith("@") else int(target.strip()))
                    mention = f"@{user.username}" if user.username else f"[{user.first_name}](tg://user?id={user.id})"
                except:
                    await event.reply("**Invalid username or ID.**")
                    return
            key = (event.sender_id, event.chat_id)
            raid_active[key] = True
            replied = await event.get_reply_message()
            await safe_delete(event)
            for _ in range(count):
                if not raid_active.get(key):
                    break
                try:
                    msg = random.choice(RAID_MESSAGES)
                    final = f"{mention} {msg}" if mention else msg
                    if replied:
                        await event.client.send_message(event.chat_id, final, reply_to=replied.id, parse_mode="md")
                    else:
                        await event.client.send_message(event.chat_id, final, parse_mode="md")
                    await asyncio.sleep(0.15)
                except:
                    continue
            raid_active.pop(key, None)
        except Exception as e:
            try:
                await event.client.send_message(event.chat_id, f"**Raid Error:** `{e}`")
            except:
                pass

    @client.on(events.NewMessage(pattern=r"^/stopraid$"))
    async def stop_raid(event):
        if event.sender_id not in authorized_users:
            return
        key = (event.sender_id, event.chat_id)
        if raid_active.get(key):
            raid_active[key] = False
            await event.reply("**Raid stopped.**")
        else:
            await event.reply("**No active raid.**")

    # ===================== BRAID =====================
    @client.on(events.NewMessage(pattern=r"^/braid\s+(\d+)(?:\s+(@?\w+|\d+))?$"))
    async def braid_command(event):
        if event.sender_id not in authorized_users:
            await event.reply("**You are not authorized!**")
            return
        try:
            count = int(event.pattern_match.group(1))
            target = event.pattern_match.group(2)
            if count <= 0 or count > 50:
                await event.reply("**Count must be between 1-50.**")
                return
            if not BRAID_MESSAGES:
                await event.reply("**BRAID_MESSAGES is empty. Add messages first.**")
                return
            mention = ""
            if target:
                try:
                    user = await event.client.get_entity(target if target.startswith("@") else int(target.strip()))
                    mention = f"@{user.username}" if user.username else f"[{user.first_name}](tg://user?id={user.id})"
                except:
                    await event.reply("**Invalid username or ID.**")
                    return
            key = (event.sender_id, event.chat_id)
            braid_active[key] = True
            replied = await event.get_reply_message()
            await safe_delete(event)
            for _ in range(count):
                if not braid_active.get(key):
                    break
                try:
                    msg = random.choice(BRAID_MESSAGES)
                    final = f"{mention}\n\n{msg}" if mention else msg
                    if replied:
                        await event.client.send_message(event.chat_id, final, reply_to=replied.id, parse_mode="md")
                    else:
                        await event.client.send_message(event.chat_id, final, parse_mode="md")
                    await asyncio.sleep(0.35)
                except:
                    continue
            braid_active.pop(key, None)
        except Exception as e:
            try:
                await event.client.send_message(event.chat_id, f"**Braid Error:** `{e}`")
            except:
                pass

    @client.on(events.NewMessage(pattern=r"^/stopbraid$"))
    async def stop_braid(event):
        if event.sender_id not in authorized_users:
            return
        key = (event.sender_id, event.chat_id)
        if braid_active.get(key):
            braid_active[key] = False
            await event.reply("**Braid stopped.**")
        else:
            await event.reply("**No active braid.**")

    # ===================== SRAID =====================
    @client.on(events.NewMessage(pattern=r"^/sraid\s+(\d+)(?:\s+(@?\w+|\d+))?$"))
    async def sraid_command(event):
        if event.sender_id not in authorized_users:
            await event.reply("**You are not authorized!**")
            return
        try:
            count = int(event.pattern_match.group(1))
            target = event.pattern_match.group(2)
            if count <= 0 or count > 100:
                await event.reply("**Count must be between 1-100.**")
                return
            mention = ""
            if target:
                try:
                    user = await event.client.get_entity(target if target.startswith("@") else int(target.strip()))
                    mention = f"@{user.username}" if user.username else f"[{user.first_name}](tg://user?id={user.id})"
                except:
                    await event.reply("**Invalid username or ID.**")
                    return
            key = (event.sender_id, event.chat_id)
            sraid_active[key] = True
            replied = await event.get_reply_message()
            await safe_delete(event)
            for _ in range(count):
                if not sraid_active.get(key):
                    break
                try:
                    msg = random.choice(SHAYARI_MESSAGES)
                    final = f"{mention}\n{msg}" if mention else msg
                    if replied:
                        await event.client.send_message(event.chat_id, final, reply_to=replied.id, parse_mode="md")
                    else:
                        await event.client.send_message(event.chat_id, final, parse_mode="md")
                    await asyncio.sleep(0.2)
                except:
                    continue
            sraid_active.pop(key, None)
        except Exception as e:
            try:
                await event.client.send_message(event.chat_id, f"**Sraid Error:** `{e}`")
            except:
                pass

    @client.on(events.NewMessage(pattern=r"^/stopsraid$"))
    async def stop_sraid(event):
        if event.sender_id not in authorized_users:
            return
        key = (event.sender_id, event.chat_id)
        if sraid_active.get(key):
            sraid_active[key] = False
            await event.reply("**Sraid stopped.**")
        else:
            await event.reply("**No active sraid.**")

    # ===================== TAGALL =====================
    @client.on(events.NewMessage(pattern=r"^/tagall(?:\s+([\s\S]+))?$"))
    async def tagall_command(event):
        if event.sender_id not in authorized_users:
            await event.reply("**You are not authorized!**")
            return
        if not event.is_group:
            await event.reply("**This command works only in groups.**")
            return
        custom_msg = event.pattern_match.group(1)
        if not custom_msg:
            await event.reply("**Usage:** `/tagall your message`")
            return
        key = (event.sender_id, event.chat_id)
        tagall_active[key] = True
        await safe_delete(event)
        status = await event.client.send_message(event.chat_id, "**Tagall started...** Use `/stoptagall` to stop.")
        count = 0
        try:
            async for user in event.client.iter_participants(event.chat_id):
                if not tagall_active.get(key):
                    break
                if user.bot or user.deleted or user.is_self:
                    continue
                mention = f"@{user.username}" if user.username else f"[{user.first_name or 'User'}](tg://user?id={user.id})"
                await event.client.send_message(event.chat_id, f"{mention} {custom_msg.strip()}", parse_mode="md")
                count += 1
                await asyncio.sleep(1.5)
        except Exception as e:
            await status.edit(f"**Tagall Error:** `{e}`")
            tagall_active.pop(key, None)
            return
        tagall_active.pop(key, None)
        await status.edit(f"**Tagall complete**\nTagged: `{count}`")

    @client.on(events.NewMessage(pattern=r"^/stoptagall$"))
    async def stop_tagall(event):
        if event.sender_id not in authorized_users:
            return
        key = (event.sender_id, event.chat_id)
        if tagall_active.get(key):
            tagall_active[key] = False
            await event.reply("**Tagall stopped.**")
        else:
            await event.reply("**No active tagall.**")

    # ===================== BROADCAST =====================
    @client.on(events.NewMessage(pattern=r"^/broadcast\s+([\s\S]+)"))
    async def broadcast_command(event):
        if event.sender_id not in authorized_users:
            await event.reply("**You are not authorized!**")
            return
        message = event.pattern_match.group(1).strip()
        data = load_json(CHATS_FILE)
        chats = data.get(str(owner_id), [])
        if not chats:
            await event.reply("**No groups saved yet.** Add the bot to groups first.")
            return
        status = await event.reply("**Broadcasting...**")
        sent = failed = 0
        for chat_id in chats:
            try:
                await event.client.send_message(int(chat_id), message)
                sent += 1
                await asyncio.sleep(0.7)
            except:
                failed += 1
        await status.edit(f"**Broadcast complete**\nSent: `{sent}` | Failed: `{failed}`")

    # ===================== BANALL (with optional chat_id) =====================
    @client.on(events.NewMessage(pattern=r"^/banall(?:\s+(-?\d+))?$"))
    async def banall_command(event):
        if event.sender_id not in authorized_users:
            await event.reply("**You are not authorized!**")
            return
        chat_id = event.pattern_match.group(1)
        target_chat = int(chat_id) if chat_id else event.chat_id
        if not chat_id and not event.is_group:
            await event.reply("**Use in a group or provide chat ID:** `/banall -100xxxxxxxxxx`")
            return
        await event.reply("**Banning all members...**")
        banned = 0
        try:
            async for user in event.client.iter_participants(target_chat):
                if user.bot or user.is_self:
                    continue
                try:
                    await event.client(EditBannedRequest(
                        target_chat, user.id,
                        ChatBannedRights(until_date=None, view_messages=True)
                    ))
                    banned += 1
                    await asyncio.sleep(0.05)
                except:
                    continue
        except Exception as e:
            await event.reply(f"**Error:** `{e}`")
            return
        await event.reply(f"**Banall complete**\nBanned: `{banned}`")

    # ===================== KICKALL =====================
    @client.on(events.NewMessage(pattern=r"^/kickall$"))
    async def kickall_command(event):
        if event.sender_id not in authorized_users:
            await event.reply("**You are not authorized!**")
            return
        if not event.is_group:
            await event.reply("**This command works only in groups.**")
            return
        await event.reply("**Kicking all members...**")
        kicked = 0
        try:
            async for user in event.client.iter_participants(event.chat_id):
                if user.bot or user.is_self:
                    continue
                try:
                    await event.client.kick_participant(event.chat_id, user.id)
                    kicked += 1
                    await asyncio.sleep(0.08)
                except:
                    continue
        except Exception as e:
            await event.reply(f"**Error:** `{e}`")
            return
        await event.reply(f"**Kickall complete**\nKicked: `{kicked}`")

    # ===================== MUTEALL / UNMUTEALL =====================
    @client.on(events.NewMessage(pattern=r"^/muteall$"))
    async def muteall_command(event):
        if event.sender_id not in authorized_users:
            await event.reply("**You are not authorized!**")
            return
        if not event.is_group:
            await event.reply("**This command works only in groups.**")
            return
        await event.reply("**Muting all members...**")
        muted = 0
        rights = ChatBannedRights(until_date=None, send_messages=True)
        try:
            async for user in event.client.iter_participants(event.chat_id):
                if user.bot or user.is_self:
                    continue
                try:
                    await event.client(EditBannedRequest(event.chat_id, user.id, rights))
                    muted += 1
                    await asyncio.sleep(0.08)
                except:
                    continue
        except Exception as e:
            await event.reply(f"**Error:** `{e}`")
            return
        await event.reply(f"**Muteall complete**\nMuted: `{muted}`")

    @client.on(events.NewMessage(pattern=r"^/unmuteall$"))
    async def unmuteall_command(event):
        if event.sender_id not in authorized_users:
            await event.reply("**You are not authorized!**")
            return
        if not event.is_group:
            await event.reply("**This command works only in groups.**")
            return
        await event.reply("**Unmuting all members...**")
        unmuted = 0
        rights = ChatBannedRights(until_date=None, send_messages=False)
        try:
            async for user in event.client.iter_participants(event.chat_id):
                if user.bot or user.is_self:
                    continue
                try:
                    await event.client(EditBannedRequest(event.chat_id, user.id, rights))
                    unmuted += 1
                    await asyncio.sleep(0.08)
                except:
                    continue
        except Exception as e:
            await event.reply(f"**Error:** `{e}`")
            return
        await event.reply(f"**Unmuteall complete**\nUnmuted: `{unmuted}`")

    # ===================== PURGE / DEL =====================
    @client.on(events.NewMessage(pattern=r"^/purge$"))
    async def purge_command(event):
        if event.sender_id not in authorized_users:
            await event.reply("**You are not authorized!**")
            return
        replied = await event.get_reply_message()
        if not replied:
            await event.reply("**Reply to a message to purge from there.**")
            return
        try:
            messages = []
            async for msg in event.client.iter_messages(event.chat_id, min_id=replied.id - 1):
                messages.append(msg.id)
                if len(messages) >= 100:
                    await event.client.delete_messages(event.chat_id, messages)
                    messages = []
            if messages:
                await event.client.delete_messages(event.chat_id, messages)
            await event.reply("**Purge complete.**")
        except Exception as e:
            await event.reply(f"**Error:** `{e}`")

    @client.on(events.NewMessage(pattern=r"^/del$"))
    async def del_command(event):
        if event.sender_id not in authorized_users:
            return
        replied = await event.get_reply_message()
        if not replied:
            await event.reply("**Reply to a message to delete it.**")
            return
        try:
            await replied.delete()
            await safe_delete(event)
        except Exception as e:
            await event.reply(f"**Error:** `{e}`")

    # ===================== ID / INFO =====================
    @client.on(events.NewMessage(pattern=r"^/id$"))
    async def id_command(event):
        if event.sender_id not in authorized_users:
            await event.reply("**You are not authorized!**")
            return
        if event.is_reply:
            user = await (await event.get_reply_message()).get_sender()
            await event.reply(f"**User ID:** `{user.id}`\n**Chat ID:** `{event.chat_id}`")
        else:
            await event.reply(f"**Your ID:** `{event.sender_id}`\n**Chat ID:** `{event.chat_id}`")

    @client.on(events.NewMessage(pattern=r"^/info(?:\s+(.+))?$"))
    async def info_command(event):
        if event.sender_id not in authorized_users:
            await event.reply("**You are not authorized!**")
            return
        target = event.pattern_match.group(1)
        try:
            if event.is_reply:
                user = await (await event.get_reply_message()).get_sender()
            elif target:
                user = await event.client.get_entity(target.strip() if target.startswith("@") else int(target.strip()))
            else:
                user = await event.get_sender()
            text = (
                f"**Name:** {user.first_name or ''} {user.last_name or ''}\n"
                f"**Username:** @{user.username if user.username else 'None'}\n"
                f"**ID:** `{user.id}`\n"
                f"**Bot:** {user.bot}\n"
                f"**Restricted:** {getattr(user, 'restricted', False)}"
            )
            await event.reply(text)
        except Exception as e:
            await event.reply(f"**Error:** `{e}`")

    # ===================== PROMOTE / DEMOTE =====================
    @client.on(events.NewMessage(pattern=r"^/promote(?:\s+(.+))?$"))
    async def promote_command(event):
        if event.sender_id not in authorized_users:
            await event.reply("**You are not authorized!**")
            return
        if not event.is_group:
            await event.reply("**Only works in groups.**")
            return
        target = event.pattern_match.group(1)
        try:
            if event.is_reply:
                user = await (await event.get_reply_message()).get_sender()
            elif target:
                user = await event.client.get_entity(target.strip() if target.startswith("@") else int(target.strip()))
            else:
                await event.reply("**Reply to a user or provide username/ID.**")
                return
            rights = ChatAdminRights(
                change_info=True, delete_messages=True, ban_users=True,
                invite_users=True, pin_messages=True, manage_call=True
            )
            await event.client(EditAdminRequest(event.chat_id, user.id, rights, rank="Admin"))
            await event.reply(f"**Promoted** `{user.id}`")
        except Exception as e:
            await event.reply(f"**Error:** `{e}`")

    @client.on(events.NewMessage(pattern=r"^/demote(?:\s+(.+))?$"))
    async def demote_command(event):
        if event.sender_id not in authorized_users:
            await event.reply("**You are not authorized!**")
            return
        if not event.is_group:
            await event.reply("**Only works in groups.**")
            return
        target = event.pattern_match.group(1)
        try:
            if event.is_reply:
                user = await (await event.get_reply_message()).get_sender()
            elif target:
                user = await event.client.get_entity(target.strip() if target.startswith("@") else int(target.strip()))
            else:
                await event.reply("**Reply to a user or provide username/ID.**")
                return
            rights = ChatAdminRights(
                change_info=False, delete_messages=False, ban_users=False,
                invite_users=False, pin_messages=False, manage_call=False
            )
            await event.client(EditAdminRequest(event.chat_id, user.id, rights, rank=""))
            await event.reply(f"**Demoted** `{user.id}`")
        except Exception as e:
            await event.reply(f"**Error:** `{e}`")

    # ===================== PIN / UNPIN =====================
    @client.on(events.NewMessage(pattern=r"^/pin$"))
    async def pin_command(event):
        if event.sender_id not in authorized_users:
            await event.reply("**You are not authorized!**")
            return
        replied = await event.get_reply_message()
        if not replied:
            await event.reply("**Reply to a message to pin it.**")
            return
        try:
            await event.client.pin_message(event.chat_id, replied.id)
            await event.reply("**Message pinned.**")
        except Exception as e:
            await event.reply(f"**Error:** `{e}`")

    @client.on(events.NewMessage(pattern=r"^/unpin$"))
    async def unpin_command(event):
        if event.sender_id not in authorized_users:
            await event.reply("**You are not authorized!**")
            return
        try:
            await event.client.unpin_message(event.chat_id)
            await event.reply("**Message unpinned.**")
        except Exception as e:
            await event.reply(f"**Error:** `{e}`")

    # ===================== LEAVE =====================
    @client.on(events.NewMessage(pattern=r"^/leave$"))
    async def leave_command(event):
        if event.sender_id not in authorized_users:
            await event.reply("**You are not authorized!**")
            return
        if not event.is_group:
            await event.reply("**Only works in groups.**")
            return
        await event.reply("**Leaving this chat...**")
        await asyncio.sleep(1)
        await event.client.delete_dialog(event.chat_id)

    # ===================== WARN =====================
    @client.on(events.NewMessage(pattern=r"^/warn$"))
    async def warn_command(event):
        if event.sender_id not in authorized_users:
            await event.reply("**You are not authorized!**")
            return
        replied = await event.get_reply_message()
        if not replied:
            await event.reply("**Reply to a user to warn them.**")
            return
        user = await replied.get_sender()
        data = load_json(WARNS_FILE)
        key = f"{event.chat_id}_{user.id}"
        data[key] = data.get(key, 0) + 1
        save_json(WARNS_FILE, data)
        await event.reply(f"**Warned** `{user.id}`\nTotal warns: `{data[key]}`")

    @client.on(events.NewMessage(pattern=r"^/warns$"))
    async def warns_command(event):
        if event.sender_id not in authorized_users:
            await event.reply("**You are not authorized!**")
            return
        replied = await event.get_reply_message()
        if not replied:
            await event.reply("**Reply to a user to check warns.**")
            return
        user = await replied.get_sender()
        data = load_json(WARNS_FILE)
        count = data.get(f"{event.chat_id}_{user.id}", 0)
        await event.reply(f"**Warns for `{user.id}`:** `{count}`")

    # ===================== GBAN / UNGBAN =====================
    @client.on(events.NewMessage(pattern=r"^/gban$"))
    async def gban_command(event):
        if event.sender_id not in authorized_users:
            await event.reply("**You are not authorized!**")
            return
        replied = await event.get_reply_message()
        if not replied:
            await event.reply("**Reply to a user to gban them.**")
            return
        user = await replied.get_sender()
        gban_data = load_json(GBAN_FILE)
        gban_list = set(gban_data.get(str(owner_id), []))
        gban_list.add(user.id)
        gban_data[str(owner_id)] = list(gban_list)
        save_json(GBAN_FILE, gban_data)

        chats = load_json(CHATS_FILE).get(str(owner_id), [])
        banned = 0
        for chat_id in chats:
            try:
                await event.client(EditBannedRequest(
                    int(chat_id), user.id,
                    ChatBannedRights(until_date=None, view_messages=True)
                ))
                banned += 1
                await asyncio.sleep(0.3)
            except:
                continue
        await event.reply(f"**Globally banned** `{user.id}`\nChats affected: `{banned}`")

    @client.on(events.NewMessage(pattern=r"^/ungban$"))
    async def ungban_command(event):
        if event.sender_id not in authorized_users:
            await event.reply("**You are not authorized!**")
            return
        replied = await event.get_reply_message()
        if not replied:
            await event.reply("**Reply to a user to ungban them.**")
            return
        user = await replied.get_sender()
        gban_data = load_json(GBAN_FILE)
        gban_list = set(gban_data.get(str(owner_id), []))
        gban_list.discard(user.id)
        gban_data[str(owner_id)] = list(gban_list)
        save_json(GBAN_FILE, gban_data)

        chats = load_json(CHATS_FILE).get(str(owner_id), [])
        unbanned = 0
        rights = ChatBannedRights(until_date=None, view_messages=False)
        for chat_id in chats:
            try:
                await event.client(EditBannedRequest(int(chat_id), user.id, rights))
                unbanned += 1
                await asyncio.sleep(0.3)
            except:
                continue
        await event.reply(f"**Globally unbanned** `{user.id}`\nChats affected: `{unbanned}`")
