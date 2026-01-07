from pyrogram import filters
from pyrogram.enums import ChatMemberStatus
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message
from RessoMusic import app
import config

# --- 💾 Simple Database (Reset on Restart) ---
# Agar MongoDB chahiye toh bata dena, abhi simple rakhne ke liye ye use kar rahe hain
welcome_db = []

# --- 📝 Your Styled Template ---
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
        return await message.reply_text("❌ **Sirf Admins ye command use kar sakte hain!**")

    # Command Logic
    if len(message.command) < 2:
        return await message.reply_text("⚠️ **Usage:** `/welcome on` or `/welcome off`")
    
    state = message.command[1].lower()
    chat_id = message.chat.id

    if state == "on":
        if chat_id not in welcome_db:
            welcome_db.append(chat_id)
        await message.reply_text("✅ **Welcome System Enabled!** \nAb naye members ka swagat hoga. 🌸")
    
    elif state == "off":
        if chat_id in welcome_db:
            welcome_db.remove(chat_id)
        await message.reply_text("❌ **Welcome System Disabled!**")
    
    else:
        await message.reply_text("⚠️ **Sahi option chuno:** `on` ya `off`")


# --- 👋 Main Welcome Logic ---
@app.on_message(filters.new_chat_members, group=2)
async def auto_welcome(_, message: Message):
    chat_id = message.chat.id
    
    # Check if Welcome is ON
    if chat_id not in welcome_db:
        return

    for member in message.new_chat_members:
        try:
            # 1. Skip Bot (Optional - Agar bot ko welcome nahi karna)
            if member.is_bot:
                continue

            # 2. Get Group Owner for Button
            # Hum loop karke Owner dhundenge
            owner_id = None
            async for admin in app.get_chat_members(chat_id, filter=ChatMemberStatus.OWNERS):
                owner_id = admin.user.id
                break
            
            # Owner Button Link
            owner_link = f"tg://user?id={owner_id}" if owner_id else config.SUPPORT_GROUP

            # 3. Data Collect Karo
            name = member.mention
            username = member.username if member.username else "No Username"
            user_id = member.id
            chat_name = message.chat.title
            bot_username = app.username

            # 4. Photo Download Logic
            # Agar user ki photo hai toh download karo, nahi toh random photo ya support photo
            if member.photo:
                photo = await app.download_media(member.photo.big_file_id)
            else:
                photo = config.START_IMG_URL  # Fallback image

            # 5. Buttons Banao
            buttons = [
                [
                    InlineKeyboardButton("👑 ɢʀᴏᴜᴘ ᴏᴡɴᴇʀ", url=owner_link),
                    InlineKeyboardButton("🆘 sᴜᴘᴘᴏʀᴛ", url=config.SUPPORT_GROUP),
                ]
            ]

            # 6. Message Bhejo (With Spoiler ✨)
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
                has_spoiler=True  # 🔥 YE HAI WO MAGIC (Blur Effect)
            )

        except Exception as e:
            print(f"Welcome Error: {e}")
