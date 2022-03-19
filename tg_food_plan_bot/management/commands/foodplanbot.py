import logging
import os

from django.conf import settings
from django.core.management.base import BaseCommand
from dotenv import load_dotenv
from telegram import (InlineKeyboardButton, InlineKeyboardMarkup,
                      KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove,
                      Update)
from telegram.ext import (CallbackContext, CallbackQueryHandler,
                          CommandHandler, ConversationHandler, Filters,
                          MessageHandler, Updater)
from tg_food_plan_bot.models import Customer

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

# states for conversation
(
    HELLO_NEW_USER,
    INPUT_NAME,
    ASK_PHONE,
    INPUT_PHONE,
) = range(4)


def get_stored_user(tg_user_id: int):
    try:
        customer = Customer.objects.get(telegram_id=tg_user_id)
        stored_user_description = {
            "tg_user_id": tg_user_id,
            "full_name": customer.username,
            "phone_number": customer.phone_number,
            "db_object": customer
        }
        print(stored_user_description)
        return stored_user_description
    except Customer.DoesNotExist:
        return


def save_new_user(user_description: dict) -> dict:
    customer = Customer.objects.create(
        telegram_id=user_description["tg_user_id"],
        username=user_description["full_name"],
        phone_number=user_description["phone_number"],
    )
    customer.save()
    user_description["db_object"] = customer
    return user_description


def say_hello_new_user(update: Update, context: CallbackContext):
    text = f"Здравствуйте {context.user_data['full_name']}!"
    button_list = [
        [
            InlineKeyboardButton("Да, это моё имя", callback_data="yes_name"),
            InlineKeyboardButton("Нет, другое имя", callback_data="not_name"),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(button_list)
    update.message.reply_text(text,
                              reply_markup=reply_markup)
    return HELLO_NEW_USER


def say_welcome(update: Update, context: CallbackContext):
    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=f"{context.user_data['full_name']}, добро пожаловать!"
    )


def input_name(update: Update, context: CallbackContext):
    query = update.callback_query
    response = query.data
    query.answer()
    if response == "not_name":
        query.edit_message_text(text=f"Напишите как к Вам обращаться")
        return INPUT_NAME
    elif response == "yes_name":
        query.edit_message_reply_markup()
        return ask_phone(update, context)


def get_name(update: Update, context: CallbackContext):
    if update.message.text:
        context.user_data["full_name"] = update.message.text
    return say_hello_new_user(update, context)


def ask_phone(update: Update, context: CallbackContext):
    text = "Какой номер телефона хотите указать? \nМожно поделится своим номером или указать его вручную"
    button_list = [
        [
            KeyboardButton("Поделиться контактом", request_contact=True),
        ]
    ]
    reply_markup = ReplyKeyboardMarkup(
        button_list, resize_keyboard=True, one_time_keyboard=True)
    context.bot.send_message(
        chat_id=update.effective_chat.id, text=text, reply_markup=reply_markup)

    return INPUT_PHONE


def share_contact(update: Update, context: CallbackContext):
    if update.message.contact:
        context.user_data["phone_number"] = update.message.contact.phone_number
    finish_registration(update, context)
    return ConversationHandler.END


def get_phone(update: Update, context: CallbackContext):
    if update.message.text:
        context.user_data["phone_number"] = update.message.text
    finish_registration(update, context)
    return ConversationHandler.END


def finish_registration(update: Update, context: CallbackContext):
    context.user_data.update(save_new_user(context.user_data))
    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Регистрация прошла успешно",
        reply_markup=ReplyKeyboardRemove()
    )
    say_welcome(update, context)


def start(update: Update, context: CallbackContext):
    user = update.effective_user
    stored_user = get_stored_user(user.id)
    if not stored_user:
        context.user_data["tg_user_id"] = user.id
        context.user_data["full_name"] = user.full_name
        return say_hello_new_user(update, context)

    context.user_data.update(stored_user)
    say_welcome(update, context)


class Command(BaseCommand):
    help = "Телеграм-бот"

    def handle(self, *args, **options):
        load_dotenv()
        TOKEN = os.getenv("TG_TOKEN")

        updater = Updater(token=TOKEN)
        dispatcher = updater.dispatcher

        start_handler = CommandHandler("start", start)
        login_states = {
            HELLO_NEW_USER: [CallbackQueryHandler(input_name)],
            INPUT_PHONE: [
                MessageHandler(Filters.contact, share_contact),
                MessageHandler(Filters.text & ~Filters.command, get_phone)
            ],
            INPUT_NAME: [MessageHandler(Filters.text & ~Filters.command, get_name)],
        }
        login_handler = ConversationHandler(
            entry_points=[start_handler],
            states=login_states,
            fallbacks=[start_handler])

        dispatcher.add_handler(login_handler)

        updater.start_polling()

        updater.idle()
