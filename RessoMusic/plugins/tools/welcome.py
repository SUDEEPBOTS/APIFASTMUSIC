from pyrogram import filters
from pyrogram.enums import ChatMemberStatus
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message
from RessoMusic import app
import config

# --- 💾 Database (Blacklist Logic) ---
# Is list mein jo group hoga, wahan welcome BAND rahega.
# Baaki sab jagah ON rahega.
welcome_off_db = []

# --- 📝 Your Styled Template (Small Caps English) ---
WELCOME_TEXT = """
🌸✨ ──────────────────── ✨🌸
         🎊 ᴡᴇʟᴄᴏᴍᴇ ᴛᴏ ᴏᴜʀ ғᴀᴍɪʟʏ 🎊

🌹 ɴᴀᴍᴇ ➤ {name}
🌺 ᴜsᴇʀɴᴀᴍᴇ ➤ @{username}
🆔 ᴜsᴇʀ ɪᴅ ➤ `{user_id}`
🏠 ɢʀᴏᴜᴘ ➤ {chat_name}

═════════════════════════

💕 ᴡᴇ'ʀᴇ sᴏ ʜᴀᴘᴘʏ ᴛᴏ ʜᴀᴠᴇ ʏᴏᴜ ʜᴇʀᴇ! 
🎵 ᴇɴᴊᴏʏ ᴛʜᴇ ʙᴇsᴛ ᴍᴜsɪᴄ ᴇxᴘᴇʀɪᴇɴᴄᴇ 🎵

✨ ғᴇᴇʟ ғʀᴇᴇ ᴛᴏ sʜᴀʀᴇ ᴀɴᴅ ᴇɴᴊᴏʏ! ✨

💝 ᴘᴏᴡᴇʀᴇᴅ ʙʏ ➤ @{bot_username} 🎶💖
🌸✨ ──────────────────── ✨🌸
"""

# --- 🔛 Command to Turn ON/OFF ---
@app.on_message(filters.command("welcome") & filters.group)
async def welcome_command(_, message: Message):
    # Check Admin Permissions
    member = await message.chat.get_member(message.from_user.id)
    if member.status not in [ChatMemberStatus.OWNER, ChatMemberStatus.ADMINISTRATOR]:
        return await message.reply_text("❌ **ᴏɴʟʏ ᴀᴅᴍɪɴs ᴄᴀɴ ᴜsᴇ ᴛʜɪs ᴄᴏᴍᴍᴀɴᴅ!**")

    # Command Logic
    if len(message.command) < 2:
        return await message.reply_text("⚠️ **ᴜsᴀɢᴇ:** `/welcome on` **ᴏʀ** `/welcome off`\n(By Default Welcome ON rehta hai)")
    
    state = message.command[1].lower()
    chat_id = message.chat.id

    if state == "off":
        if chat_id not in welcome_off_db:
            welcome_off_db.append(chat_id)
        await message.reply_text("❌ **ᴡᴇʟᴄᴏᴍᴇ sʏsᴛᴇᴍ ᴅɪsᴀʙʟᴇᴅ!**")

    elif state == "on":
        if chat_id in welcome_off_db:
            welcome_off_db.remove(chat_id)
        await message.reply_text("✅ **ᴡᴇʟᴄᴏᴍᴇ sʏsᴛᴇᴍ ᴇɴᴀʙʟᴇᴅ!**")
    
    else:
        await message.reply_text("⚠️ **ᴘʟᴇᴀsᴇ ᴄʜᴏᴏsᴇ:** `on` **ᴏʀ** `off`")


# --- 👋 Main Welcome Logic ---
@app.on_message(filters.new_chat_members, group=2)
async def auto_welcome(_, message: Message):
    chat_id = message.chat.id
    
    # 🔥 Logic: Agar group "OFF List" mein hai tabhi rukna hai.
    if chat_id in welcome_off_db:
        return

    for member in message.new_chat_members:
        try:
            # 1. Skip Bot (Optional)
            if member.is_bot:
                continue

            # 2. Get Group Owner for Button
            owner_id = None
            async for admin in app.get_chat_members(chat_id, filter=ChatMemberStatus.OWNERS):
                owner_id = admin.user.id
                break
            
            # Owner Button Link
            owner_link = f"tg://user?id={owner_id}" if owner_id else config.SUPPORT_GROUP

            # 3. Data Collection
            name = member.mention
            username = member.username if member.username else "ɴᴏ ᴜsᴇʀɴᴀᴍᴇ"
            user_id = member.id
            chat_name = message.chat.title
            bot_username = app.username

            # 4. Photo Download Logic
            if member.photo:
                photo = await app.download_media(member.photo.big_file_id)
            else:
                photo = config.START_IMG_URL  # Fallback image

            # 5. Buttons (Small Caps)
            buttons = [
                [
                    InlineKeyboardButton("👑 ɢʀᴏᴜᴘ ᴏᴡɴᴇʀ", url=owner_link),
                    InlineKeyboardButton("🆘 sᴜᴘᴘᴏʀᴛ", url=config.SUPPORT_GROUP),
                ]
            ]

            # 6. Send Message (With Spoiler ✨)
            await app.send_photo(
                chat_id,
                photo=photo,
                caption=WELCOME_TEXT.format(
                    name=name,
                    username=username,
                    user_id=user_id,
                    chat_name=chat_name,
                    bot_username=bot_username
                ),
                reply_markup=InlineKeyboardMarkup(buttons),
                has_spoiler=True  # 🔥 Blur Effect
            )

        except Exception as e:
            print(f"Welcome Error: {e}")
                 
