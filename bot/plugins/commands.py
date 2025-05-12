from hydrogram import filters
from hydrogram.types import Message
from bot import TelegramBot
from bot.config import Telegram
from bot.modules.static import *
from bot.modules.decorators import verify_user
from bot.plugins.files import verify_token, auto_delete_message

@TelegramBot.on_message(filters.command(['start', 'help']) & filters.private)
@verify_user
async def start_command(_, msg: Message):
    sender_id = msg.from_user.id
    if len(msg.command) > 1 and msg.command[1].startswith("token_"):
                input_token = msg.command[1][6:]
                token_msg = await verify_token(sender_id, input_token)
                reply = await msg.reply_text(token_msg)
                await TelegramBot.send_message(Telegram.CHANNEL_ID, f"User🕵️‍♂️{msg.from_user.first_name} with 🆔 {sender_id} @{Telegram.BOT_USERNAME} {token_msg}")
                await auto_delete_message(msg, reply)
                return
    await msg.reply(
        text = WelcomeText % {'first_name': msg.from_user.first_name},
        quote = True
    )

@TelegramBot.on_message(filters.command('privacy') & filters.private)
@verify_user
async def privacy_command(_, msg: Message):
    await msg.reply(text=PrivacyText, quote=True, disable_web_page_preview=True)

@TelegramBot.on_message(filters.command('log') & filters.chat(Telegram.OWNER_ID))
async def log_command(_, msg: Message):
    await msg.reply_document('event-log.txt', quote=True)

