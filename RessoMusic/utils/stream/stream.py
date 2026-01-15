import time
import os
import asyncio
from random import randint
from typing import Union

from pyrogram.types import InlineKeyboardMarkup

import config
from RessoMusic import Carbon, YouTube, app
from RessoMusic.core.call import AMBOTOP
from RessoMusic.misc import db
from RessoMusic.utils.database import add_active_video_chat, is_active_chat
from RessoMusic.utils.exceptions import AssistantErr
from RessoMusic.utils.inline import aq_markup, close_markup, stream_markup
from RessoMusic.utils.pastebin import AMBOTOPBin
from RessoMusic.utils.stream.queue import put_queue, put_queue_index
from RessoMusic.utils.thumbnails import gen_thumb


async def stream(
    _,
    mystic,
    user_id,
    result,
    chat_id,
    user_name,
    original_chat_id,
    video: Union[bool, str] = None,
    streamtype: Union[bool, str] = None,
    spotify: Union[bool, str] = None,
    forceplay: Union[bool, str] = None,
):
    # 🔥 Timer Start
    start_time = time.time()

    if not result:
        return
    if forceplay:
        await AMBOTOP.force_stop_stream(chat_id)
    
    if streamtype == "playlist":
        msg = f"{_['play_19']}\n\n"
        count = 0
        
        # 🔥 FAST JOIN FOR PLAYLIST (NEW LOGIC)
        # Agar chat active nahi hai, to pehle VC join karlo (Silent)
        # Fir songs dhundo.
        status = True if video else None
        if not await is_active_chat(chat_id):
            if not forceplay:
                db[chat_id] = []
            
            # Silent file determine karo
            if status:
                silent_file = "RessoMusic/assets/silent_video.mp4"
            else:
                silent_file = "RessoMusic/assets/silent.mp3"
                
            # Instant Join (No Image to save time)
            try:
                await AMBOTOP.join_call(
                    chat_id,
                    original_chat_id,
                    silent_file,
                    video=status,
                    image=None, 
                )
            except Exception as e:
                # Agar join fail ho jaye to error handle
                pass
        
        # Ab songs fetch karna shuru
        first_track_downloaded = False
        
        for search in result:
            if int(count) == config.PLAYLIST_FETCH_LIMIT:
                continue
            try:
                (
                    title,
                    duration_min,
                    duration_sec,
                    thumbnail,
                    vidid,
                ) = await YouTube.details(search, False if spotify else True)
            except:
                continue
            if str(duration_min) == "None":
                continue
            if duration_sec > config.DURATION_LIMIT:
                continue
            
            # Add to Queue logic
            await put_queue(
                chat_id,
                original_chat_id,
                f"vid_{vidid}",
                title,
                duration_min,
                user_name,
                vidid,
                user_id,
                "video" if video else "audio",
            )
            
            # Agar ye pehla gana hai aur humne silent join kiya tha, to ab play karo
            # (Hot Swap logic for Playlist)
            if not first_track_downloaded and not await is_active_chat(chat_id): # Logic check: Chat is techincally active now due to silent join, but queue handling handles it.
                 # Actually, since we put_queue, we need to swap the silent stream if it's the 0th index
                 # But standard queue logic appends.
                 pass

            # Humne upar join kar liya hai, to ab bas queue update aur message
            position = len(db.get(chat_id)) - 1
            count += 1
            msg += f"{count}. {title[:70]}\n"
            msg += f"{_['play_20']} {position}\n\n"

            # Agar ye pehla song tha aur humne abhi fresh join kiya tha (Silent mode me)
            # To hame isko download karke stream replace karni padegi
            # Note: Complex logic avoided to keep it stable, currently it will play from queue next.
            # Lekin agar aap chahte hain ki playlist ka first song turant play ho:
            if count == 1 and not forceplay:
                 try:
                    file_path, direct = await YouTube.download(
                        vidid, mystic, video=status, videoid=True
                    )
                    # Skip the silent stream to real song
                    await AMBOTOP.skip_stream(chat_id, file_path, video=status)
                    # DB update
                    if db.get(chat_id):
                        db[chat_id][0]["file"] = file_path
                    
                    img = await gen_thumb(vidid)
                    button = stream_markup(_, chat_id)
                    run = await app.send_photo(
                        original_chat_id,
                        photo=img,
                        caption=_["stream_1"].format(
                            f"https://t.me/{app.username}?start=info_{vidid}",
                            title[:23],
                            duration_min,
                            user_name,
                        ),
                        reply_markup=InlineKeyboardMarkup(button),
                        has_spoiler=True
                    )
                    db[chat_id][0]["mystic"] = run
                    db[chat_id][0]["markup"] = "stream"
                    first_track_downloaded = True
                 except:
                    pass

        if count == 0:
            return
        else:
            link = await AMBOTOPBin(msg)
            lines = msg.count("\n")
            if lines >= 17:
                car = os.linesep.join(msg.split(os.linesep)[:17])
            else:
                car = msg
            carbon = await Carbon.generate(car, randint(100, 10000000))
            upl = close_markup(_)
            return await app.send_photo(
                original_chat_id,
                photo=carbon,
                caption=_["play_21"].format(position, link),
                reply_markup=upl,
                has_spoiler=True
            )
    
    # 🔥 UPDATED YOUTUBE BLOCK (Full Feature Set)
    elif streamtype == "youtube":
        link = result["link"]
        vidid = result["vidid"]
        title = (result["title"]).title()
        duration_min = result["duration_min"]
        thumbnail = result["thumb"]
        status = True if video else None
    
        current_queue = db.get(chat_id)
        if current_queue is not None and len(current_queue) >= 10:
            return await app.send_message(original_chat_id, "You can't add more than 10 songs to the queue.")

        if await is_active_chat(chat_id):
            # --- NORMAL QUEUE LOGIC (Download Now) ---
            try:
                if "http" in link and "youtube" not in link and "youtu.be" not in link:
                    file_path, direct = await YouTube.download(
                        link, mystic, videoid=None, video=status
                    )
                else:
                    file_path, direct = await YouTube.download(
                        vidid, mystic, videoid=True, video=status
                    )
            except Exception as e:
                # print(f"Download Error: {e}")
                raise AssistantErr(_["play_14"])

            await put_queue(
                chat_id,
                original_chat_id,
                file_path if direct else f"vid_{vidid}",
                title,
                duration_min,
                user_name,
                vidid,
                user_id,
                "video" if video else "audio",
            )
            position = len(db.get(chat_id)) - 1
            button = aq_markup(_, chat_id)
            await app.send_message(
                chat_id=original_chat_id,
                text=_["queue_4"].format(position, title[:27], duration_min, user_name),
                reply_markup=InlineKeyboardMarkup(button),
            )
        else:
            # --- FAST START LOGIC (Silent Join + Background Download) ---
            if not forceplay:
                db[chat_id] = []
            
            # 1. Determine Silent File (Audio vs Video)
            if status:
                silent_file = "RessoMusic/assets/silent_video.mp4"
            else:
                silent_file = "RessoMusic/assets/silent.mp3"

            # 2. Join VC Immediately
            # 🔥 CHANGE: image=None kiya hai taki thumbnail download ka wait na kare.
            try:
                await AMBOTOP.join_call(
                    chat_id,
                    original_chat_id,
                    silent_file,
                    video=status,
                    image=None, 
                )
            except Exception as e:
                # Agar join fail ho jaye (e.g. user VC me nahi hai)
                return await mystic.edit_text(f"Failed to join VC. Error: {e}")

            # 3. Add to Queue (Placeholder logic so bot knows it's busy)
            await put_queue(
                chat_id,
                original_chat_id,
                f"vid_{vidid}", 
                title,
                duration_min,
                user_name,
                vidid,
                user_id,
                "video" if video else "audio",
                forceplay=forceplay,
            )

            # 4. Background Download with Timeout
            try:
                async def download_track():
                    if "http" in link and "youtube" not in link and "youtu.be" not in link:
                        return await YouTube.download(
                            link, mystic, videoid=None, video=status
                        )
                    else:
                        return await YouTube.download(
                            vidid, mystic, videoid=True, video=status
                        )
                
                # Wait max 60 seconds for download
                file_path, direct = await asyncio.wait_for(download_track(), timeout=60.0)
            
            except asyncio.TimeoutError:
                db[chat_id] = []
                await AMBOTOP.leave_call(chat_id)
                return await mystic.edit_text("Sorry, download took too long. Try again.")
            
            except Exception as e:
                db[chat_id] = []
                await AMBOTOP.leave_call(chat_id)
                return await mystic.edit_text(_["play_14"])

            # Zombie Fix
            if not db.get(chat_id):
                try:
                    os.remove(file_path)
                except:
                    pass
                return await AMBOTOP.leave_call(chat_id)

            # 5. HOT SWAP: Replace Silent File with Real Song
            await AMBOTOP.skip_stream(chat_id, file_path, video=status)

            # 6. Update DB with real file path
            if db.get(chat_id):
                db[chat_id][0]["file"] = file_path

            # --- End Fast Logic ---

            # Thumbnail ab generate karenge, jab gana bajna shuru ho gaya
            img = await gen_thumb(vidid)
            button = stream_markup(_, chat_id)

            # Calculate Time
            load_time = round(time.time() - start_time, 2)

            run = await app.send_photo(
                original_chat_id,
                photo=img,
                caption=_["stream_1"].format(
                    f"https://t.me/{app.username}?start=info_{vidid}",
                    title[:23],
                    duration_min,
                    user_name,
                    load_time
                ),
                reply_markup=InlineKeyboardMarkup(button),
                has_spoiler=True
            )
            db[chat_id][0]["mystic"] = run
            db[chat_id][0]["markup"] = "stream"
            
    elif streamtype == "soundcloud":
        file_path = result["filepath"]
        title = result["title"]
        duration_min = result["duration_min"]
        if await is_active_chat(chat_id):
            await put_queue(
                chat_id,
                original_chat_id,
                file_path,
                title,
                duration_min,
                user_name,
                streamtype,
                user_id,
                "audio",
            )
            position = len(db.get(chat_id)) - 1
            button = aq_markup(_, chat_id)
            await app.send_message(
                chat_id=original_chat_id,
                text=_["queue_4"].format(position, title[:27], duration_min, user_name),
                reply_markup=InlineKeyboardMarkup(button),
            )
        else:
            if not forceplay:
                db[chat_id] = []
            await AMBOTOP.join_call(chat_id, original_chat_id, file_path, video=None)
            await put_queue(
                chat_id,
                original_chat_id,
                file_path,
                title,
                duration_min,
                user_name,
                streamtype,
                user_id,
                "audio",
                forceplay=forceplay,
            )
            button = stream_markup(_, chat_id)
            run = await app.send_photo(
                original_chat_id,
                photo=config.SOUNCLOUD_IMG_URL,
                caption=_["stream_1"].format(
                    config.SUPPORT_GROUP, title[:23], duration_min, user_name
                ),
                reply_markup=InlineKeyboardMarkup(button),
                has_spoiler=True
            )
            db[chat_id][0]["mystic"] = run
            db[chat_id][0]["markup"] = "tg"
    elif streamtype == "telegram":
        file_path = result["path"]
        link = result["link"]
        title = (result["title"]).title()
        duration_min = result["dur"]
        status = True if video else None
        if await is_active_chat(chat_id):
            await put_queue(
                chat_id,
                original_chat_id,
                file_path,
                title,
                duration_min,
                user_name,
                streamtype,
                user_id,
                "video" if video else "audio",
            )
            position = len(db.get(chat_id)) - 1
            button = aq_markup(_, chat_id)
            await app.send_message(
                chat_id=original_chat_id,
                text=_["queue_4"].format(position, title[:27], duration_min, user_name),
                reply_markup=InlineKeyboardMarkup(button),
            )
        else:
            if not forceplay:
                db[chat_id] = []
            await AMBOTOP.join_call(chat_id, original_chat_id, file_path, video=status)
            await put_queue(
                chat_id,
                original_chat_id,
                file_path,
                title,
                duration_min,
                user_name,
                streamtype,
                user_id,
                "video" if video else "audio",
                forceplay=forceplay,
            )
            if video:
                await add_active_video_chat(chat_id)
            button = stream_markup(_, chat_id)
            run = await app.send_photo(
                original_chat_id,
                photo=config.TELEGRAM_VIDEO_URL if video else config.TELEGRAM_AUDIO_URL,
                caption=_["stream_1"].format(link, title[:23], duration_min, user_name),
                reply_markup=InlineKeyboardMarkup(button),
                has_spoiler=True
            )
            db[chat_id][0]["mystic"] = run
            db[chat_id][0]["markup"] = "tg"
    elif streamtype == "live":
        link = result["link"]
        vidid = result["vidid"]
        title = (result["title"]).title()
        thumbnail = result["thumb"]
        duration_min = "Live Track"
        status = True if video else None
        if await is_active_chat(chat_id):
            await put_queue(
                chat_id,
                original_chat_id,
                f"live_{vidid}",
                title,
                duration_min,
                user_name,
                vidid,
                user_id,
                "video" if video else "audio",
            )
            position = len(db.get(chat_id)) - 1
            button = aq_markup(_, chat_id)
            await app.send_message(
                chat_id=original_chat_id,
                text=_["queue_4"].format(position, title[:27], duration_min, user_name),
                reply_markup=InlineKeyboardMarkup(button),
            )
        else:
            if not forceplay:
                db[chat_id] = []
            n, file_path = await YouTube.video(link)
            if n == 0:
                raise AssistantErr(_["str_3"])
            await AMBOTOP.join_call(
                chat_id,
                original_chat_id,
                file_path,
                video=status,
                image=thumbnail if thumbnail else None,
            )
            await put_queue(
                chat_id,
                original_chat_id,
                f"live_{vidid}",
                title,
                duration_min,
                user_name,
                vidid,
                user_id,
                "video" if video else "audio",
                forceplay=forceplay,
            )
            img = await gen_thumb(vidid)
            button = stream_markup(_, chat_id)
            run = await app.send_photo(
                original_chat_id,
                photo=img,
                caption=_["stream_1"].format(
                    f"https://t.me/{app.username}?start=info_{vidid}",
                    title[:23],
                    duration_min,
                    user_name,
                ),
                reply_markup=InlineKeyboardMarkup(button),
                has_spoiler=True
            )
            db[chat_id][0]["mystic"] = run
            db[chat_id][0]["markup"] = "tg"
    elif streamtype == "index":
        link = result
        title = "ɪɴᴅᴇx ᴏʀ ᴍ3ᴜ8 ʟɪɴᴋ"
        duration_min = "00:00"
        if await is_active_chat(chat_id):
            await put_queue_index(
                chat_id,
                original_chat_id,
                "index_url",
                title,
                duration_min,
                user_name,
                link,
                "video" if video else "audio",
            )
            position = len(db.get(chat_id)) - 1
            button = aq_markup(_, chat_id)
            await mystic.edit_text(
                text=_["queue_4"].format(position, title[:27], duration_min, user_name),
                reply_markup=InlineKeyboardMarkup(button),
            )
        else:
            if not forceplay:
                db[chat_id] = []
            await AMBOTOP.join_call(
                chat_id,
                original_chat_id,
                link,
                video=True if video else None,
            )
            await put_queue_index(
                chat_id,
                original_chat_id,
                "index_url",
                title,
                duration_min,
                user_name,
                link,
                "video" if video else "audio",
                forceplay=forceplay,
            )
            button = stream_markup(_, chat_id)
            run = await app.send_photo(
                original_chat_id,
                photo=config.STREAM_IMG_URL,
                caption=_["stream_2"].format(user_name),
                reply_markup=InlineKeyboardMarkup(button),
                has_spoiler=True
            )
            db[chat_id][0]["mystic"] = run
            db[chat_id][0]["markup"] = "tg"
            await mystic.delete()
