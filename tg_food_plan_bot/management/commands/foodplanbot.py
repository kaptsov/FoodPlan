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
    INPUT_NAME,
    INPUT_PHONE,
    SELECT_ACTION,
    INPUT_PERSONS,
) = range(4)


def start(update: Update, context: CallbackContext):
    user = update.effective_user
    stored_user = get_stored_user(user.id)
    if not stored_user:
        context.user_data["tg_user_id"] = user.id
        context.user_data["full_name"] = user.full_name
        say_hello_new_user(update, context)
        return SELECT_ACTION

    context.user_data.update(stored_user)
    say_welcome(update, context)
    return SELECT_ACTION


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
        return None


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


def save_new_user(user_description: dict) -> dict:
    customer = Customer.objects.create(
        telegram_id=user_description["tg_user_id"],
        username=user_description["full_name"],
        phone_number=user_description["phone_number"],
    )
    customer.save()
    user_description["db_object"] = customer
    return user_description


def say_welcome(update: Update, context: CallbackContext):
    text = f"{context.user_data['full_name']}, добро пожаловать!"
    button_list = [
        [
            InlineKeyboardButton("Оформить подписку",
                                 callback_data="new_subscript"),
            InlineKeyboardButton(
                "Мои подписки", callback_data="select_subscript"),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(button_list)
    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=text,
        reply_markup=reply_markup
    )


def get_name(update: Update, context: CallbackContext):
    if update.message.text:
        context.user_data["full_name"] = update.message.text
    say_hello_new_user(update, context)
    return SELECT_ACTION


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


def share_contact(update: Update, context: CallbackContext):
    if update.message.contact:
        context.user_data["phone_number"] = update.message.contact.phone_number
    finish_registration(update, context)
    say_welcome(update, context)
    return SELECT_ACTION


def get_phone(update: Update, context: CallbackContext):
    if not update.message.text:  # todo добавить проверку валидности номера
        ask_phone(update, context)
        return INPUT_PHONE

    context.user_data["phone_number"] = update.message.text
    finish_registration(update, context)
    say_welcome(update, context)
    return SELECT_ACTION


def finish_registration(update: Update, context: CallbackContext):
    context.user_data.update(save_new_user(context.user_data))
    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Регистрация прошла успешно",
        reply_markup=ReplyKeyboardRemove()
    )


def handle_select_action(update: Update, context: CallbackContext):
    query = update.callback_query
    response = query.data
    query.answer()
    if response == "not_name":
        query.edit_message_text(text=f"Напишите как к Вам обращаться")
        return INPUT_NAME
    elif response == "yes_name":
        query.edit_message_reply_markup()
        ask_phone(update, context)
        return INPUT_PHONE
    elif response == "new_subscript":
        query.edit_message_text(text=f"Оформление новой подписки")
        text = f"Выберите число месяцев подписки"
        button_list = [
            [
                InlineKeyboardButton("1",
                                     callback_data="period_1"),
                InlineKeyboardButton("3",
                                     callback_data="period_3"),
                InlineKeyboardButton("6",
                                     callback_data="period_6"),
                InlineKeyboardButton("12",
                                     callback_data="period_12"),
            ]
        ]
        reply_markup = InlineKeyboardMarkup(button_list)
        context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=text,
            reply_markup=reply_markup
        )
        return SELECT_ACTION
    elif response == "select_subscript":
        return ConversationHandler.END
    elif response[:6] == "period":
        context.user_data["subscript_period"] = int(response[7:])
        query.edit_message_text(text=f"Подписка на {response[7:]} мес.")
        ask_menu_type(update, context)
        return SELECT_ACTION
    elif response[:4] == "menu":
        query.edit_message_text(text=f"Выбрано меню: {response[5:]}")
        context.bot.send_message(
            chat_id=update.effective_chat.id, text="Напишите число персон")
        return INPUT_PERSONS


def get_persons(update: Update, context: CallbackContext):
    say_welcome(update, context)
    return SELECT_ACTION


def ask_menu_type(update: Update, context: CallbackContext):
    text = f"Выберите тип меню"
    button_list = [
        [
            InlineKeyboardButton("Классическое",
                                 callback_data="menu_1"),
            InlineKeyboardButton("Вегетарианское",
                                 callback_data="menu_2"),
        ],
        [
            InlineKeyboardButton("Низкоуглеводное",
                                 callback_data="menu_3"),
            InlineKeyboardButton("Кето",
                                 callback_data="menu_4"),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(button_list)
    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=text,
        reply_markup=reply_markup
    )


class Command(BaseCommand):
    help = "Телеграм-бот"

    def handle(self, *args, **options):
        load_dotenv()
        TOKEN = os.getenv("TG_TOKEN")

        updater = Updater(token=TOKEN)
        dispatcher = updater.dispatcher

        start_handler = CommandHandler("start", start)
        login_states = {
            INPUT_PHONE: [
                MessageHandler(Filters.contact, share_contact),
                MessageHandler(Filters.text & ~Filters.command, get_phone)
            ],
            INPUT_NAME: [MessageHandler(Filters.text & ~Filters.command, get_name)],
            INPUT_PERSONS: [MessageHandler(Filters.text & ~Filters.command, get_persons)],
            SELECT_ACTION: [CallbackQueryHandler(handle_select_action)],
        }
        login_handler = ConversationHandler(
            entry_points=[start_handler],
            states=login_states,
            fallbacks=[start_handler])

        dispatcher.add_handler(login_handler)

        updater.start_polling()

        updater.idle()
