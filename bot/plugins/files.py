import uuid
import aiohttp
import asyncio
from hydrogram import filters
from hydrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from secrets import token_hex
from bot import TelegramBot, logger
from bot.config import Telegram, Server
from bot.modules.decorators import verify_user
from bot.modules.static import *
from time import time as tm

user_data = {}

@TelegramBot.on_message(
    filters.private
    & (
        filters.document
        | filters.video
        | filters.video_note
        | filters.audio
        | filters.voice
        | filters.photo
    )
)
@verify_user
async def handle_user_file(_, msg: Message):
    sender_id = msg.from_user.id
    secret_code = token_hex(Telegram.SECRET_CODE_LENGTH)
    file = await msg.copy(
        chat_id=Telegram.CHANNEL_ID,
        caption=f'||{secret_code}/{sender_id}||'
    )
    file_id = file.id
    dl_link = f'{Server.BASE_URL}/dl/{file_id}?code={secret_code}'

    if (msg.document and 'video' in msg.document.mime_type) or msg.video:
        stream_link = f'{Server.BASE_URL}/stream/{file_id}?code={secret_code}'
        if not await check_access(msg, sender_id):
            return
        await msg.reply(
            text=MediaLinksText % {'dl_link': dl_link, 'stream_link': stream_link},
            quote=True,
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton('Download', url=dl_link),
                        InlineKeyboardButton('Stream', url=stream_link)
                    ],
                    [
                        InlineKeyboardButton('Revoke', callback_data=f'rm_{file_id}_{secret_code}')
                    ]
                ]
            )
        )
    else:
        await msg.reply(
            text=FileLinksText % {'dl_link': dl_link},
            quote=True,
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton('Download', url=dl_link),
                        InlineKeyboardButton('Revoke', callback_data=f'rm_{file_id}_{secret_code}')
                    ]
                ]
            )
        )

async def verify_token(user_id, input_token):
    current_time = tm()

    # Check if the user_id exists in user_data
    if user_id not in user_data:
        return 'Token Mismatched ❌' 
    
    stored_token = user_data[user_id]['token']
    if input_token == stored_token:
        token = str(uuid.uuid4())
        user_data[user_id] = {"token": token, "time": current_time, "status": "verified", "file_count": 0}
        return f'Token Verified ✅'
    else:
        return f'Token Mismatched ❌'

async def check_access(message, user_id):
    if user_id == Telegram.OWNER_ID:
        return True

    if user_id in user_data:
        time = user_data[user_id]['time']
        status = user_data[user_id]['status']
        file_count = user_data[user_id].get('file_count', 0)
        expiry = time + Telegram.TOKEN_TIMEOUT
        current_time = tm()
        if current_time < expiry and status == "verified":
            if file_count < Telegram.USER_LIMIT:
                return True
            else:
                reply = await message.reply_text(f"You have reached the limit. Please wait until the token expires")
                await auto_delete_message(message, reply)
                return False
        else:
            button = await update_token(user_id)
            send_message = await message.reply_text(f"<b>It looks like your token has expired. Get Free 💎 Limited Access again!</b>", reply_markup=button)
            await auto_delete_message(message, send_message)
            return False
    else:
        button = await genrate_token(user_id)
        send_message = await message.reply_text(f"<b>It looks like you don't have a token. Get Free 💎 Limited Access now!</b>", reply_markup=button)
        await auto_delete_message(message, send_message)
        return False
    

async def update_token(user_id):
    bot_username = Telegram.BOT_USERNAME
    try:
        time = user_data[user_id]['time']
        expiry = time + Telegram.TOKEN_TIMEOUT
        if time < expiry:
            token = user_data[user_id]['token']
        else:
            token = str(uuid.uuid4())
        current_time = tm()
        user_data[user_id] = {"token": token, "time": current_time, "status": "unverified", "file_count": 0}
        urlshortx = await shorten_url(f'https://telegram.me/{bot_username}?start=token_{token}')
        button = InlineKeyboardMarkup([[InlineKeyboardButton("🎟️ Get Token", url=urlshortx)]])
        return button
    except Exception as e:
        logger.error(f"error in update_token: {e}")

async def shorten_url(url):
    try:
        api_url = f"https://{Telegram.SHORTERNER_URL}/api"
        params = {
            "api": Telegram.URLSHORTX_API_TOKEN,
            "url": url,
            "format": "text"
        }

        async with aiohttp.ClientSession() as session:
            async with session.get(api_url, params=params) as response:
                if response.status == 200:
                    return (await response.text()).strip()
                else:
                    logger.error(
                        f"URL shortening failed. Status code: {response.status}, Response: {await response.text()}"
                    )
                    return url
    except Exception as e:
        logger.error(f"URL shortening failed: {e}")
        return url

async def genrate_token(user_id):
    bot_username = Telegram.BOT_USERNAME
    try:
        token = str(uuid.uuid4())
        current_time = tm()
        user_data[user_id] = {"token": token, "time": current_time, "status": "unverified", "file_count": 0}
        urlshortx = await shorten_url(f'https://telegram.dog/{bot_username}?start=token_{token}')
        button = InlineKeyboardMarkup([[InlineKeyboardButton("🎟️ Get Token", url=urlshortx)]])
        return button
    except Exception as e:
        logger.error(f"error in genrate_token: {e}")


async def auto_delete_message(user_message, bot_message):
    try:
        await user_message.delete()
        await asyncio.sleep(60)
        await bot_message.delete()
    except Exception as e:
        print(f"{e}")