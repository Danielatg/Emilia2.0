import os
import time
import pytz 
import math
import shutil
import psutil
import random
import asyncio
import heroku3
import logging
import requests
import datetime

from pyrogram import Client, filters
from utils import extract_user, get_file_id, last_online
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message
from info import START_MSG, CHANNELS, ADMINS, AUTH_CHANNEL, CUSTOM_FILE_CAPTION, AUTH_USERS, HEROKU_API_KEY, BOT_START_TIME
from utils import Media, get_file_details
from pyrogram.errors import UserNotParticipant
logger = logging.getLogger(__name__)
from database import present_in_userbase, add_to_userbase, total_users_count

def humanbytes(size):
    # https://stackoverflow.com/a/49361727/4723940
    # 2**10 = 1024
    if not size:
        return ""
    power = 2**10
    n = 0
    Dic_powerN = {0: ' ', 1: 'K', 2: 'M', 3: 'G', 4: 'T'}
    while size > power:
        size /= power
        n += 1
    return str(round(size, 2)) + " " + Dic_powerN[n] + 'B'

def wish():
    IST = pytz.timezone('Asia/Kolkata')
    currentTime = datetime.datetime.now(IST)
    if currentTime.hour < 12:
        return "Good Morning"
    elif 12 <= currentTime.hour < 18:
        return 'Good afternoon'
    else:
        return 'Good evening'

@Client.on_message(filters.command("start"))
async def start(bot, cmd):
    user_cmd = cmd.text
    if user_cmd == "/start":
        photos = [
        "https://telegra.ph/file/f5e5aa1e8fe785cb3cf56.jpg",
        "https://telegra.ph/file/0547145655f6add5e9f39.jpg",
        "https://telegra.ph/file/705e1950697c25b826354.jpg",
        "https://telegra.ph/file/4270a544eb17c21b15639.jpg",
        "https://telegra.ph/file/fdd82cbb90b99300d49e7.jpg",
        "https://telegra.ph/file/09c7f28fa34dd4279a5b0.jpg",
        "https://telegra.ph/file/28a5bf8ad3def94c51e7c.jpg",
        "https://telegra.ph/file/82a63609da5c47199f8bf.jpg",
        "https://telegra.ph/file/924919d0e107c88f17b0a.jpg",
        ]
        buttons = [[
            InlineKeyboardButton('❔ How To Use Me ❔', url='https://t.me/joinchat/s3ux_FYag2BmYzRk')
            ],[
            InlineKeyboardButton("Search Here🔎", switch_inline_query_current_chat=''),
            InlineKeyboardButton("Help⚙", callback_data="helpdata")
            ],[
            InlineKeyboardButton('MYdev👩‍💻', url='https://t.me/Physic_hybrid'),
            InlineKeyboardButton("About😎", callback_data="about")
            ],[
            InlineKeyboardButton('➕ Add Me To Your Group ', url='https://t.me/TGMovieRobot?startgroup=true'),]
            ]
            
        reply_markup = InlineKeyboardMarkup(buttons)
        await cmd.reply_photo(
            photo=random.choice(photos),
            caption=f"𝐘𝐨..𝐘𝐨..{wish()} {cmd.from_user.mention} 🙋, <b>I'm Powerful Auto-Filter Bot You Can Use Me As A Auto-filter in Your Group ....</b>\n\n<b>Its Easy To Use Me; Just Add Me To Your Group As Admin, Thats All, i will Provide Movies There...</b>🤓\n\n⚠️<b>More Help Check Help Button Below</b>\n\n©️MᴀɪɴᴛᴀɪɴᴇD Bʏ  <a href=tg://user?id=633942759>ᴘʜʏsɪᴄ_ʜʏʙʀɪᴅ🇵🇹/🇦🇪</a>",
            reply_markup=reply_markup
        )
    elif len(cmd.command) > 1 and cmd.command[1] == 'subscribe':
        invite_link = await bot.create_chat_invite_link(int(AUTH_CHANNEL))
        await bot.send_message(
            chat_id=cmd.from_user.id,
            text="**Hey..Bruh🙋‍♂️..Please Join My Updates Channel to use this Bot!**",
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton("♻️ JOIN CHANNNEL", url=invite_link.invite_link)
                    ]
                ]
            )
        )
    else:
        file_id = (cmd.text.split("_-_-_-_", 1))[1]
        try:
            user = await bot.get_chat_member('Movies_Land4U', cmd.from_user.id)
            if user.status=='kicked':
                await cmd.reply_text("You Are B A N N E D")
                return false
        except UserNotParticipant:
              await cmd.reply_text('<b>Hey..Bruh🙋‍♂️..Please Join My Updates Channel to use this Bot!</b>',
                                    reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton(text = "♻️ JOIN CHANNNEL",url = "https://t.me/Movies_Land4U")],[InlineKeyboardButton(text = "🔄 TRY AGAIN",callback_data = f"checksub#{file_id}")]]))

              return
        try:
           # file_id = cmd.text.split("_-_-_-_")
           # file_id = cmd.command[1]
            file_id = (cmd.text.split("_-_-_-_", 1))[1]
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
                    f_caption = f"{files.file_name}"
                buttons = [
                    [
                         InlineKeyboardButton('♻️Group', url='https://t.me/MovieZLandChat')
                    ]
                    ]
                await bot.send_cached_media(
                    chat_id=cmd.from_user.id,
                    file_id=file_id,
                    caption=f_caption,
                    reply_markup=InlineKeyboardMarkup(buttons)
                )
        except Exception as err:
            await cmd.reply_text(f"Something went wrong!\n**Error:** `{err}`")

@Client.on_message(filters.command('channel') & filters.user(ADMINS))
async def channel_info(bot, message):
    """Send basic information of channel"""
    if isinstance(CHANNELS, (int, str)):
        channels = [CHANNELS]
    elif isinstance(CHANNELS, list):
        channels = CHANNELS
    else:
        raise ValueError("Unexpected type of CHANNELS")

    text = '📑 **Indexed channels/groups**\n'
    for channel in channels:
        chat = await bot.get_chat(channel)
        if chat.username:
            text += '\n@' + chat.username
        else:
            text += '\n' + chat.title or chat.first_name

    text += f'\n\n**Total:** {len(CHANNELS)}'

    if len(text) < 4096:
        await message.reply(text)
    else:
        file = 'Indexed channels.txt'
        with open(file, 'w') as f:
            f.write(text)
        await message.reply_document(file)
        os.remove(file)

@Client.on_message(filters.command('id'))
async def showid(client, message):
    chat_type = message.chat.type
    if chat_type == "private":
        user_id = message.chat.id
        first = message.from_user.first_name
        last = message.from_user.last_name or ""
        username = message.from_user.username
        dc_id = message.from_user.dc_id or ""
        await message.reply_text(
            f"<b>➲ First Name:</b> {first}\n<b>➲ Last Name:</b> {last}\n<b>➲ Username:</b> {username}\n<b>➲ Telegram ID:</b> <code>{user_id}</code>\n<b>➲ Data Centre:</b> <code>{dc_id}</code>",
            quote=True
        )

    elif chat_type in ["group", "supergroup"]:
        _id = ""
        _id += (
            "<b>➲ Chat ID</b>: "
            f"<code>{message.chat.id}</code>\n"
        )
        if message.reply_to_message:
            _id += (
                "<b>➲ User ID</b>: "
                f"<code>{message.from_user.id}</code>"
                "<b>➲ Replied User ID</b>: "
                f"<code>{message.reply_to_message.from_user.id}</code>\n"
            )
            file_info = get_file_id(message.reply_to_message)
        else:
            _id += (
                "<b>➲ User ID</b>: "
                f"<code>{message.from_user.id}</code>\n"
            )
            file_info = get_file_id(message)
        if file_info:
            _id += (
                f"<b>{file_info.message_type}</b>: "
                f"<code>{file_info.file_id}</code>\n"
            )
        await message.reply_text(
            _id,
            quote=True
        )

@Client.on_message(filters.command(["info"]))
async def who_is(client, message):
    # https://github.com/SpEcHiDe/PyroGramBot/blob/master/pyrobot/plugins/admemes/whois.py#L19
    status_message = await message.reply_text(
        "`Fetching user info...`"
    )
    await status_message.edit(
        "`Processing user info...`"
    )
    from_user = None
    from_user_id, _ = extract_user(message)
    try:
        from_user = await client.get_users(from_user_id)
    except Exception as error:
        await status_message.edit(str(error))
        return
    if from_user is None:
        await status_message.edit("no valid user_id / message specified")
    else:
        message_out_str = ""
        message_out_str += f"<b>➲First Name:</b> {from_user.first_name}\n"
        last_name = from_user.last_name or "<b>None</b>"
        message_out_str += f"<b>➲Last Name:</b> {last_name}\n"
        message_out_str += f"<b>➲Telegram ID:</b> <code>{from_user.id}</code>\n"
        username = from_user.username or "<b>None</b>"
        dc_id = from_user.dc_id or "[User Doesnt Have A Valid DP]"
        message_out_str += f"<b>➲Data Centre:</b> <code>{dc_id}</code>\n"
        message_out_str += f"<b>➲User Name:</b> @{username}\n"
        message_out_str += f"<b>➲User 𝖫𝗂𝗇𝗄:</b> <a href='tg://user?id={from_user.id}'><b>Click Here</b></a>\n"
        if message.chat.type in (("supergroup", "channel")):
            try:
                chat_member_p = await message.chat.get_member(from_user.id)
                joined_date = datetime.fromtimestamp(
                    chat_member_p.joined_date or time.time()
                ).strftime("%Y.%m.%d %H:%M:%S")
                message_out_str += (
                    "<b>➲Joined this Chat on:</b> <code>"
                    f"{joined_date}"
                    "</code>\n"
                )
            except UserNotParticipant:
                pass
        chat_photo = from_user.photo
        if chat_photo:
            local_user_photo = await client.download_media(
                message=chat_photo.big_file_id
            )
            buttons = [[
                InlineKeyboardButton('🔐 Close', callback_data="samclose")
            ]]
            reply_markup = InlineKeyboardMarkup(buttons)
            await message.reply_photo(
                photo=local_user_photo,
                quote=True,
                reply_markup=reply_markup,
                caption=message_out_str,
                parse_mode="html",
                # ttl_seconds=,
                disable_notification=True
            )
            os.remove(local_user_photo)
        else:
            buttons = [[
                InlineKeyboardButton('🔐 Close', callback_data="samclose")
            ]]
            reply_markup = InlineKeyboardMarkup(buttons)
            await message.reply_text(
                text=message_out_str,
                reply_markup=reply_markup,
                quote=True,
                parse_mode="html",
                disable_notification=True
            )
        await status_message.delete()


@Client.on_message(filters.command('logs') & filters.user(ADMINS))
async def log_file(bot, message):
    """Send log file"""
    try:
        await message.reply_document('TelegramBot.log')
    except Exception as e:
        await message.reply(str(e))

@Client.on_message(filters.private & filters.command('status'))
async def bot_status(client,message):
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
    await message.reply_text(
        text=msg,
        quote=True,
        parse_mode="md",
        reply_markup=reply_markup
    )


@Client.on_message(filters.private & filters.command("stats") & filters.user(ADMINS))
async def show_status_count(_, event: Message):
    total, used, free = shutil.disk_usage(".")
    total = humanbytes(total)
    used = humanbytes(used)
    free = humanbytes(free)
    cpu_usage = psutil.cpu_percent()
    ram_usage = psutil.virtual_memory().percent
    disk_usage = psutil.disk_usage('/').percent
    total_users = await total_users_count()
    await event.reply_text(
        text=f"**Total Disk Space:** {total} \n**Used Space:** {used}({disk_usage}%) \n**Free Space:** {free} \n**CPU Usage:** {cpu_usage}% \n**RAM Usage:** {ram_usage}%\n\n**Total Users in DB:** `{total_users}`",
        parse_mode="Markdown",
        quote=True
    )


@Client.on_message(filters.command('total') & filters.user(ADMINS))
async def total(bot, message):
    """Show total files in database"""
    msg = await message.reply("Processing...⏳", quote=True)
    try:
        total = await Media.count_documents()
        await msg.edit(f'📁 Saved files: {total}')
    except Exception as e:
        logger.exception('Failed to check total files')
        await msg.edit(f'Error: {e}')


@Client.on_message(filters.command('logger') & filters.user(ADMINS))
async def log_file(bot, message):
    """Send log file"""
    try:
        await message.reply_document('TelegramBot.log')
    except Exception as e:
        await message.reply(str(e))


@Client.on_message(filters.command('delete') & filters.user(ADMINS))
async def delete(bot, message):
    """Delete file from database"""
    reply = message.reply_to_message
    if reply and reply.media:
        msg = await message.reply("Processing...⏳", quote=True)
    else:
        await message.reply('Reply to file with /delete which you want to delete', quote=True)
        return

    for file_type in ("document", "video", "audio"):
        media = getattr(reply, file_type, None)
        if media is not None:
            break
    else:
        await msg.edit('This is not supported file format')
        return

    result = await Media.collection.delete_one({
        'file_name': media.file_name,
        'file_size': media.file_size,
        'mime_type': media.mime_type
    })
    if result.deleted_count:
        await msg.edit('File is successfully deleted from database')
    else:
        await msg.edit('File not found in database')
@Client.on_message(filters.command('about'))
async def bot_info(bot, message):
    buttons = [
        [
            InlineKeyboardButton('Channel🎥', url='https://t.me/Movies_Land4U'),
            InlineKeyboardButton('Group ♻️', url='https://t.me/MovieZLandChat')
        ]
        ]
    await message.reply(text = """🙋🏻‍♂️   Hellooo    <code> {}🤓</code>
    
<b>○ My Name :</b> <code>Auto-Filter Bot</code>
<b>○ Creator :</b> <a href="https://t.me/Physic_hybrid">Physic_Hybrid🇵🇹</a>
<b>○ Credits :</b> <code>Everyone in this journey</code>
<b>○ Language :</b> <code>Python3</code>
<b>○ Library :</b> <a href="https://docs.pyrogram.org/">Pyrogram asyncio 0.17.1</a>
<b>○ Supported Site :</b> <a href="https://my.telegram.org/">Only Telegram</a>
<b>○ Source Code :</b> <a href="https://t.me/AdhavaaBiriyaniKittiyalo">👉 Click Here</a>
<b>○ Server :</b> <a href="https://herokuapp.com/">Heroku</a>
<b>○ Database :</b> <a href="https://www.mongodb.com/">MongoDB</a>
<b>○ Build Status :</b> <code>V2.1 [BETA]</code>
<b>📜 Quote :</b> <code>ആരും പേടിക്കണ്ട എല്ലാവർക്കും കിട്ടും™️</code>""".format(update.from_user.mention), reply_markup=InlineKeyboardMarkup(buttons), disable_web_page_preview=True)
