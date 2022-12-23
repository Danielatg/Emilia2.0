#Kanged From @TroJanZheX
import os
import time
import re
import math
import shutil
import psutil
import datetime
import pytz 
import heroku3
import logging
import requests
import asyncio

from info import AUTH_CHANNEL, AUTH_USERS, CUSTOM_FILE_CAPTION, API_KEY, AUTH_GROUPS, ADMINS, HEROKU_API_KEY, BOT_START_TIME
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from pyrogram import Client, filters
from imdbinfo import get_poster
from pyrogram.errors import UserNotParticipant, FloodWait, UserIsBlocked, PeerIdInvalid, InputUserDeactivated, MessageNotModified
from utils import get_search_results, get_file_details, is_subscribed,get_size
from plugins.commands import humanbytes
from database import (
    get_status,
    get_users,
    del_from_userbase
)

def wish():
    IST = pytz.timezone('Asia/Kolkata')
    currentTime = datetime.datetime.now(IST)
    if currentTime.hour < 12:
        return "Good Morning"
    elif 12 <= currentTime.hour < 18:
        return 'Good afternoon'
    else:
        return 'Good evening'

BUTTONS = {}
BOT = {}
@Client.on_message(filters.private & filters.command('stats') & filters.user(ADMINS))
async def getstatus(client, message):
    sts_msg = await message.reply('Getting Details..')
    stats = await get_status()
    await sts_msg.edit(f"Total Users {stats}")
    
@Client.on_message(filters.private & filters.command('broadcast') & filters.user(ADMINS) & filters.reply)
async def broadcast(client, message):
    broadcast_msg = message.reply_to_message
    broadcast_msg = await broadcast_msg.copy(
        chat_id = message.chat.id,
        reply_to_message_id = broadcast_msg.message_id
    )
    messaged = message.reply_to_message
    user_ids = await get_users()
    
    success = 0
    deleted = 0
    blocked = 0
    peerid = 0
    
    await message.reply(text = 'Broadcasting message, Please wait')
    
    for user_id in user_ids:
        try:
            await messaged.copy(int(user_id))
            success += 1
        except FloodWait as e:
            await asyncio.sleep(e.x)
            await messaged.copy(int(user_id))
            success += 1
        except UserIsBlocked:
            blocked += 1
        except PeerIdInvalid:
            peerid += 1
        except InputUserDeactivated:
            deleted += 1
            await del_from_userbase(user_id)
        except Exception as e:
            print(e)
            pass
            
    text = f"""<b>Broadcast Completed</b>
    
Total users: {str(len(user_ids))}
Blocked users: {str(blocked)}
Deleted accounts: {str(deleted)} (<i>Deleted from Database</i>)
Failed : {str(peerid)}"""

    await message.reply(text)



@Client.on_callback_query(filters.regex(r"^next"))
async def next_page(bot, query):

    ident, req, key, offset = query.data.split("_")
    if int(req) not in [query.from_user.id, 0]:
        return await query.answer("oKda", show_alert=True)
    try:
        offset = int(offset)
    except:
        offset = 0
    search = BUTTONS.get(key)
    if not search:
        await query.answer("You are using this for one of my old message, please send the request again.",show_alert=True)
        return

    files, n_offset, total = await get_search_results(search, offset=offset, filter=True)
    try:
        n_offset = int(n_offset)
    except:
        n_offset = 0

    if not files:
        return
    btn = [
        [
            InlineKeyboardButton(
                text=f"📂[{get_size(file.file_size)}]📂 {file.file_name}", url=f'https://t.me/TGMovieRobot?start=_-_-_-_{file.file_id}'
            ),
            
        ]
        for file in files
    ]

    if 0 < offset <= 10:
        off_set = 0
    elif offset == 0:
        off_set = None
    else:
        off_set = offset - 10
    if n_offset == 0:
        btn.append(
            [InlineKeyboardButton("⏪ BACK", callback_data=f"next_{req}_{key}_{off_set}"), InlineKeyboardButton(f"📃 Pages {round(int(offset)/10)+1} / {round(total/10)}", callback_data="pages")]
        )
    elif off_set is None:
        btn.append([InlineKeyboardButton(f"🗓 {round(int(offset)/10)+1} / {round(total/10)}", callback_data="pages"), InlineKeyboardButton("NEXT ⏩", callback_data=f"next_{req}_{key}_{n_offset}")])
    else:
        btn.append(
            [
                InlineKeyboardButton("⏪ BACK", callback_data=f"next_{req}_{key}_{off_set}"),
                InlineKeyboardButton(f"🗓 {round(int(offset)/10)+1} / {round(total/10)}", callback_data="pages"),
                InlineKeyboardButton("NEXT ⏩", callback_data=f"next_{req}_{key}_{n_offset}")
            ],
        )
    try:
        await query.edit_message_reply_markup( 
            reply_markup=InlineKeyboardMarkup(btn)
        )
    except MessageNotModified:
        pass
    await query.answer()

@Client.on_message(filters.text & filters.group)
async def group(client, message):


    if re.findall("((^\/|^,|^!|^\.|^[\U0001F600-\U000E007F]).*)", message.text):
        return
    if 2 < len(message.text) < 100:
        
        search = message.text
        files, offset, total_results = await get_search_results(search.lower(), offset=0)
        if not files:
            return
        btn = [
            [
                InlineKeyboardButton(
                text=f"📂[{get_size(file.file_size)}]📂 {file.file_name}", url=f'https://t.me/TGMovieRobot?start=_-_-_-_{file.file_id}'
            ),
            ]
            for file in files
        ]

        if offset != "":
            key = f"{message.chat.id}-{message.message_id}"
            BUTTONS[key] = search
            req = message.from_user.id if message.from_user else 0
            mention = message.chat.title if message.sender_chat else message.from_user.mention
            print(f"req {mention}")
            btn.append(
                [InlineKeyboardButton(text=f"🗓 1/{round(int(total_results)/10)}",callback_data="pages"), InlineKeyboardButton(text="NEXT ⏩",callback_data=f"next_{req}_{key}_{offset}")]
            )
        else:
            btn.append(
                [InlineKeyboardButton(text="🗓 1/1",callback_data="pages")]
            )
        imdb = await get_poster(search) 
       # if imdb and imdb.get('poster'):
       #     a = await message.reply_photo(photo=imdb.get('poster'), caption=f"Requested By: {mention}\n🏷 Title: <a href={imdb['url']}>{imdb.get('title')}</a>\n🎭 Genres: {imdb.get('genres')}\nLanguage: {imdb.get('languages')}\n📆 Year: <a href={imdb['url']}/releaseinfo>{imdb.get('year')}</a>\n🌟 Rating: <a href={imdb['url']}/ratings>{imdb.get('rating')}</a> / 10", reply_markup=InlineKeyboardMarkup(btn))
       # elif imdb:
       #     a = await message.reply_text(f"Requested By: {mention}\n🏷 Title: <a href={imdb['url']}>{imdb.get('title')}</a>\n🎭 Genres: {imdb.get('genres')}\nLanguage: {imdb.get('languages')}\n📆 Year: <a href={imdb['url']}/releaseinfo>{imdb.get('year')}</a>\n🌟 Rating: <a href={imdb['url']}/ratings>{imdb.get('rating')}</a> / 10", reply_markup=InlineKeyboardMarkup(btn))
       # else:
        a = await message.reply_text(f"Requested By: {mention}\n<b>Here is What I Found In My Database For Your Query {search} ‌‎ </b>", reply_markup=InlineKeyboardMarkup(btn))
        

def get_size(size):
    """Get size in readable format"""

    units = ["Bytes", "KB", "MB", "GB", "TB", "PB", "EB"]
    size = float(size)
    i = 0
    while size >= 1024.0 and i < len(units):
        i += 1
        size /= 1024.0
    return "%.2f %s" % (size, units[i])

def split_list(l, n):
    for i in range(0, len(l), n):
        yield l[i:i + n]          

@Client.on_message(filters.text & filters.private)
async def privat_in(client, message):
    
    if re.findall("((^\/|^,|^!|^\.|^[\U0001F600-\U000E007F]).*)", message.text):
        return
    if 2 < len(message.text) < 100:
        
        search = message.text
        files, offset, total_results = await get_search_results(search.lower(), offset=0)
        if not files:
            return
        btn = [
            [
                InlineKeyboardButton(
                text=f"📂[{get_size(file.file_size)}]📂 {file.file_name}", url=f'https://t.me/TGMovieRobot?start=_-_-_-_{file.file_id}'
            ),
            ]
            for file in files
        ]

        if offset != "":
            key = f"{message.chat.id}-{message.message_id}"
            BUTTONS[key] = search
            req = message.from_user.id if message.from_user else 0
            mention = message.from_user.mention
            btn.append(
                [InlineKeyboardButton(text=f"🗓 1/{round(int(total_results)/10)}",callback_data="pages"), InlineKeyboardButton(text="NEXT ⏩",callback_data=f"next_{req}_{key}_{offset}")]
            )
        else:
            btn.append(
                [InlineKeyboardButton(text="🗓 1/1",callback_data="pages")]
            )
        imdb = await get_poster(search) 
      #  if imdb and imdb.get('poster'):
      #      await message.reply_photo(photo=imdb.get('poster'), caption=f"Requested By: {mention}\n🏷 Title: <a href={imdb['url']}>{imdb.get('title')}</a>\n🎭 Genres: {imdb.get('genres')}\n📆 Year: <a href={imdb['url']}/releaseinfo>{imdb.get('year')}</a>\n🌟 Rating: <a href={imdb['url']}/ratings>{imdb.get('rating')}</a> / 10", reply_markup=InlineKeyboardMarkup(btn))
      #  elif imdb:
      #      await message.reply_text(f"Requested By: {mention}\n🏷 Title: <a href={imdb['url']}>{imdb.get('title')}</a>\n🎭 Genres: {imdb.get('genres')}\n📆 Year: <a href={imdb['url']}/releaseinfo>{imdb.get('year')}</a>\n🌟 Rating: <a href={imdb['url']}/ratings>{imdb.get('rating')}</a> / 10", reply_markup=InlineKeyboardMarkup(btn))
      #  else:
        await message.reply_text(f"Requested By: {mention}\n<b>Here is What I Found In My Database For Your Query {search} ‌‌‌‌‎ </b>", reply_markup=InlineKeyboardMarkup(btn))
        

def get_size(size):
    """Get size in readable format"""

    units = ["Bytes", "KB", "MB", "GB", "TB", "PB", "EB"]
    size = float(size)
    i = 0
    while size >= 1024.0 and i < len(units):
        i += 1
        size /= 1024.0
    return "%.2f %s" % (size, units[i])

def split_list(l, n):
    for i in range(0, len(l), n):
        yield l[i:i + n]          



@Client.on_callback_query()
async def cb_handler(client: Client, query: CallbackQuery):
    clicked = query.from_user.id
    try:
        typed = query.message.reply_to_message.from_user.id
    except:
        typed = query.from_user.id
        pass
    if (clicked == typed):

        
        if query.data == "samstart":
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton('❔ How To Use Me ❔', url='https://t.me/joinchat/s3ux_FYag2BmYzRk')
                    ],[                    
                        InlineKeyboardButton("Search Here🔎", switch_inline_query_current_chat=''),
                        InlineKeyboardButton("Help ⚙", callback_data="helpdata")
                    ],
                    [
                        InlineKeyboardButton('MYdev👩‍💻', url='https://t.me/Physic_hybrid'),
                        InlineKeyboardButton("About😎", callback_data="about")
                    ],
                    [   InlineKeyboardButton('➕ Add Me To Your Group ', url='https://t.me/TGMovieRobot?startgroup=true'),]
                ]
            )
            await query.message.edit(text=f"𝐘𝐨..𝐘𝐨..{wish()} {query.from_user.mention} 🙋, <b>I'm Powerful Auto-Filter Bot You Can Use Me As A Auto-filter Bot In Your Group ..</b>\n\n<b>Its Easy To Use Me; Just Add Me To Your Group As Admin, Thats All, i will Provide Movies There...</b>🤓\n\n⚠️<b>More Help Check Help Button Below</b>\n\n©️MᴀɪɴᴛᴀɪɴᴇD Bʏ  <a href=tg://user?id=633942759>ᴘʜʏsɪᴄ_ʜʏʙʀɪᴅ🇵🇹/🇦🇪</a>",reply_markup=reply_markup, disable_web_page_preview=True)
        elif query.data == "samclose":
            await query.message.delete()
        elif query.data == "check":
            await query.answer("⚠️ Search Google.com Find the Correct Spelling of Movie Name Type that in Group To Get the Files ⚠️", show_alert=True)
        elif query.data == "refresh":
            server = heroku3.from_key(HEROKU_API_KEY)

            user_agent = (
                'Mozilla/5.0 (Linux; Android 10; SM-G975F) '
                'AppleWebKit/537.36 (KHTML, like Gecko) '
                'Chrome/80.0.3987.149 Mobile Safari/537.36'
            )
            accountid = server.account().id
            headers = {
            'User-Agent': user_agent,
            'Authorization': f'Bearer {HEROKU_API_KEY}',
            'Accept': 'application/vnd.heroku+json; version=3.account-quotas',
            }

            path = "/accounts/" + accountid + "/actions/get-quota"

            request = requests.get("https://api.heroku.com" + path, headers=headers)

            if request.status_code == 200:
                result = request.json()

                total_quota = result['account_quota']
                quota_used = result['quota_used']

                quota_left = total_quota - quota_used
                
                total = math.floor(total_quota/3600)
                used = math.floor(quota_used/3600)
                hours = math.floor(quota_left/3600)
                minutes = math.floor(quota_left/60 % 60)
                days = math.floor(hours/24)

                usedperc = math.floor(quota_used / total_quota * 100)
                leftperc = math.floor(quota_left / total_quota * 100)

                quota_details = f"""
**Heroku Account Status**
> __Total Dyno Hours : **{total} hrs** Dyno Quota Available Each Month.__
> __Dyno Hours Used This Month__ ;
        - **{used} hours**  ( {usedperc}% )
> __Dyno Hours Remaining This Month__ ;
        - **{hours} hours**  ( {leftperc}% )
        - **Approximate Working {days} days!**
"""
            uptime = time.strftime("%Hh %Mm %Ss", time.gmtime(time.time() - BOT_START_TIME))

            try:
                t, u, f = shutil.disk_usage(".")
                total = humanbytes(t)
                used = humanbytes(u)
                free = humanbytes(f)

                disk = f"\n**Disk Details**\n\n> USED  :  {used} / {total}\n> FREE  :  {free}\n\n"
            except:
                disk = ""
            msg = f"**Current status Emilia clarke bot!**\n\n> __BOT Uptime__ : **{uptime}**\n\n{quota_details}\n{disk}"
            buttons = [[
                InlineKeyboardButton('Refresh♻️', callback_data="refresh")
                ],[
                InlineKeyboardButton('🔙 Back', callback_data="helpdata"),
                InlineKeyboardButton('Close 🔐', callback_data="samclose")
            ]]
            reply_markup = InlineKeyboardMarkup(buttons)
            await query.message.edit_text(
                text=msg,
                parse_mode="md",
                reply_markup=reply_markup
            )

        elif query.data == "helpdata":
            buttons = [
                [
                    InlineKeyboardButton('🔙 Back', callback_data="samstart"),
                    InlineKeyboardButton('Close 🔐', callback_data="samclose"),
                ],[
                    InlineKeyboardButton("About😎", callback_data="about"),
                    InlineKeyboardButton('Share Me🤝 ', url='https://t.me/share/url?url=https://t.me/TGMovieRobot'),

                ]
                ]
            await query.message.edit(text = """🙋🏻‍♂️   Hellooo    <code> {}🤓</code>

<b>○  it's Note Complicated...</b>🤓

<b>○  Search using inline mode
This methord works on any chat, Just type @TGMovieRobot and then leave a space and search any movie you want...</b>

<b>○<u> Available Commands</u></b>
     
 /start - Check I'm Alive..
 /Status - Bot Status
 /info - User info 
 /id - User id
 /broadcast - Broadcast (owner only)
 /stats - Db status  (owner only )

<b>○ <u>Notice </u>📙:-</b>

<b>○Dont Spam Me...</b>🤒\n\n©️MᴀɪɴᴛᴀɪɴᴇD Bʏ <a href=tg://user?id=633942759>ᴘʜʏsɪᴄ_ʜʏʙʀɪᴅ🇵🇹/🇦🇪</a>""".format(query.from_user.mention), reply_markup=InlineKeyboardMarkup(buttons), disable_web_page_preview=True)
        elif query.data == "about":
            buttons = [
                [
                    InlineKeyboardButton(' MYdev👩‍💻', url='https://t.me/Physic_hybrid'),
                    InlineKeyboardButton('Help⚙', callback_data="helpdata")
                ],
                [
                    InlineKeyboardButton(' close🔐', callback_data="samclose"),
                    InlineKeyboardButton('Home🏘️', callback_data="samstart"),
                ]
                ]
            await query.message.edit(text = """🙋🏻‍♂️   Hellooo    <code> {}🤓</code>
    
<b>○ My Name :</b> <code>Auto-Filter Bot </code>
<b>○ Creator :</b> <a href="https://t.me/Physic_hybrid">Physic_Hybrid🇵🇹</a>
<b>○ Credits :</b> <code>Everyone in this journey</code>
<b>○ Language :</b> <code>Python3</code>
<b>○ Library :</b> <a href="https://docs.pyrogram.org/">Pyrogram asyncio 0.17.1</a>
<b>○ Supported Site :</b> <a href="https://my.telegram.org/">Only Telegram</a>
<b>○ Source Code :</b> <a href="https://t.me/AdhavaaBiriyaniKittiyalo">👉 Click Here</a>
<b>○ Server :</b> <a href="https://herokuapp.com/">Heroku</a>
<b>○ Database :</b> <a href="https://www.mongodb.com/">MongoDB</a>
<b>○ Build Status :</b> <code>V2.1 [BETA]</code>
<b>📜 Quote :</b> <code>ആരും പേടിക്കണ്ട എല്ലാവർക്കും കിട്ടും™️</code>""".format(query.from_user.mention), reply_markup=InlineKeyboardMarkup(buttons), disable_web_page_preview=True)




        elif query.data.startswith("files"):
            ident, file_id = query.data.split("#")
            await query.answer(url = f"https://t.me/TGMovieRobot?start={file_id}")
        elif query.data.startswith("checksub"):
            if AUTH_CHANNEL and not await is_subscribed(client, query):
                await query.answer("I Like Your Smartness, But Don't Be Oversmart 😒",show_alert=True)
                return
            ident, file_id = query.data.split("#")
            filedetails = await get_file_details(file_id)
            for files in filedetails:
                title = files.file_name
                size=files.file_size
                f_caption=files.caption
                if CUSTOM_FILE_CAPTION:
                    try:
                        f_caption=CUSTOM_FILE_CAPTION.format(file_name=title, file_size=size, file_caption=f_caption)
                    except Exception as e:
                        print(e)
                        f_caption=f_caption
                if f_caption is None:
                    f_caption = f"{title}"
                buttons = [
                    [
                        InlineKeyboardButton('♻️Group', url='https://t.me/MovieZLandChat'),
                        InlineKeyboardButton('🎥 Channel', url='https://t.me/Movies_Land4U')
                    ]
                    ]
                
                await query.answer()
                await client.send_cached_media(
                    chat_id=query.from_user.id,
                    file_id=file_id,
                    caption=f_caption,
                    reply_markup=InlineKeyboardMarkup(buttons)
                    )
        elif query.data == 'perfect':
            await query.answer(url="https://t.me/TGMovieRobot?start=keyword")
        elif query.data == "pages":
            await query.answer()
     
    else:
        await query.answer("കൌതുകും ലേശം കൂടുതൽ ആണല്ലേ👀",show_alert=True)
