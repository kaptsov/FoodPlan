import logging
import os

from dotenv import load_dotenv
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup, Update
from telegram.ext import CommandHandler, Filters, MessageHandler, Updater, CallbackQueryHandler

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

REQUEST_RECIPE = "Что приготовить?"
REQUEST_SHOPLIST = "Что купить?"


def start(update, context):
    button_list = [
        [KeyboardButton(REQUEST_RECIPE),
         KeyboardButton(REQUEST_SHOPLIST)],
    ]
    reply_markup = ReplyKeyboardMarkup(button_list, resize_keyboard=True)
    context.bot.send_message(
        chat_id=update.effective_chat.id, text="Добро пожаловать", reply_markup=reply_markup)


def get_recipe():
    return "Съешь еще этих мягких французких булок, да выпей чаю"


def get_shoplist():
    return "Сахар и гречка"


def message(update, context):
    user_request = update.message.text
    if user_request == REQUEST_RECIPE:
        text = get_recipe()
    elif user_request == REQUEST_SHOPLIST:
        text = get_shoplist()
    else:
        text = "К такому меня жизнь не готовила..."
    context.bot.send_message(chat_id=update.effective_chat.id, text=text)


if __name__ == "__main__":

    load_dotenv()
    TOKEN = os.getenv("TG_TOKEN")

    updater = Updater(token=TOKEN)
    dispatcher = updater.dispatcher

    start_handler = CommandHandler("start", start)
    dispatcher.add_handler(start_handler)

    message_handler = MessageHandler(
        Filters.text & (~Filters.command), message)
    dispatcher.add_handler(message_handler)

    updater.start_polling()

    updater.idle()
