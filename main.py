import logging
import os
import random
from datetime import datetime
import asyncio

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ChatMemberStatus
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, CallbackContext, MessageHandler, filters

from statics import *
# import sqlite3
# import json

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)


########################################################################################################################
########################################################################################################################

# def init_db():
#     conn = sqlite3.connect('user_requests.db')
#     c = conn.cursor()
#     c.execute('''
#         CREATE TABLE IF NOT EXISTS user_requests
#         (user_id INTEGER, username TEXT, user_request TEXT, created_at TIMESTAMP)
#     ''')
#     conn.commit()
#     conn.close()
#
# def save_user_request(user_id: int, username: str, request_text: str):
#     conn = sqlite3.connect('user_requests.db')
#     c = conn.cursor()
#     c.execute('''
#         INSERT INTO user_requests (user_id, username, user_request, created_at)
#         VALUES (?, ?, ?, ?)
#     ''', (user_id, username, request_text, datetime.now()))
#     conn.commit()
#     conn.close()
#
# def get_user_request(user_id: int):
#     conn = sqlite3.connect('user_requests.db')
#     c = conn.cursor()
#     c.execute('SELECT user_request FROM user_requests WHERE user_id = ? ORDER BY created_at DESC LIMIT 1', (user_id,))
#     result = c.fetchone()
#     conn.close()
#     return result[0] if result else None

########################################################################################################################
########################################################################################################################

async def handle_user_request(update: Update, context: CallbackContext) -> None:
    """Handle user's request text"""
    # if context.user_data.get('waiting_for_request_start'):
    #     user_request = update.message.text
    #     user_id = update.effective_user.id
    #     username = update.effective_user.username or update.effective_user.first_name
    #
    #     # Save to database
    #     save_user_request(user_id, username, user_request)
    #
    #     # Clear the state
    #     context.user_data['waiting_for_request_start'] = False
    #
    #     # Continue with the game
    #     # keyboard = [[InlineKeyboardButton("Продолжить игру", callback_data="start_game")]]
    #     # reply_markup = InlineKeyboardMarkup(keyboard)
    #     #
    #     # await update.message.reply_text(
    #     #     f"✅ Ваш запрос сохранен: \"{user_request}\"\n\nТеперь можем начать игру!",
    #     #     reply_markup=reply_markup
    #     # )
    #     await first_dice_roll(update, context)
    if context.user_data.get('waiting_for_request_first'):
        # Clear the state
        context.user_data['waiting_for_request_first'] = False
        await second_dice_roll(update, context)
    elif context.user_data.get('waiting_for_request_second'):
        # Clear the state
        context.user_data['waiting_for_request_second'] = False
        await third_dice_roll(update, context)


########################################################################################################################
async def check_subscription(user_id: int, context: CallbackContext) -> bool:
    """Проверяет, подписан ли пользователь на канал"""
    try:
        member = await context.bot.get_chat_member(chat_id=os.getenv('CHANNEL_USERNAME'), user_id=user_id)
        return member.status in [ChatMemberStatus.MEMBER, ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]
    except Exception as e:
        print(f"Ошибка проверки подписки: {e}")
        return False


async def show_subscription_required(update: Update, context: CallbackContext) -> None:
    """Показывает сообщение о необходимости подписки"""
    keyboard = [
        [InlineKeyboardButton("Подписаться на канал", url=f"https://t.me/{os.getenv('CHANNEL_USERNAME')[1:]}")],
        [InlineKeyboardButton("✅ Я подписался", callback_data="check_subscription")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    text = (
        "📢 Для использования бота необходимо подписаться на наш канал!\n\n"
        "Подпишитесь на канал и нажмите кнопку '✅ Я подписался' для проверки."
    )

    if update.message:
        await update.message.reply_text(text, reply_markup=reply_markup)
    else:
        await update.callback_query.message.reply_text(text, reply_markup=reply_markup)


########################################################################################################################
async def start(update: Update, context: CallbackContext) -> None:
    print(f"Chat ID: {update.message.chat_id}  {update.effective_user.username or update.effective_user.first_name}")

    user_id = update.effective_user.id
    if not await check_subscription(user_id, context):
        await show_subscription_required(update, context)
        return


    welcome_text = """Сформулируйте свой запрос одним предложением.
Например:
Я хочу повысить уверенность в себе
Я хочу найти работу по душе  
Я хочу понять, как наладить свои отношения с мужем…

Сформулировали?"""

    keyboard = [[InlineKeyboardButton("Да!", callback_data="start_game")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(welcome_text, reply_markup=reply_markup)
    # await update.message.reply_text(welcome_text)

    # context.user_data['waiting_for_request_start'] = True

########################################################################################################################


########################################################################################################################
async def handle_callback(update: Update, context: CallbackContext) -> None:
    # user_id = update.effective_user.id
    # if not await check_subscription(user_id, context):
    #     await show_subscription_required(update, context)
    #     return

    """Обработка callback'ов"""
    query = update.callback_query
    await query.answer()

    data = query.data

    # Убираем кнопку у предыдущего сообщения
    await query.edit_message_reply_markup(reply_markup=None)

    if data == "check_subscription":
        user_id = query.from_user.id
        if await check_subscription(user_id, context):
            await query.edit_message_text("✅ Отлично! Вы подписаны. Теперь можете начать игру!")
            # Запускаем игру
            welcome_text = """Сформулируйте свой запрос одним предложением.
Например:
Я хочу повысить уверенность в себе
Я хочу найти работу по душе  
Я хочу понять, как наладить свои отношения с мужем…

Сформулировали?"""
            # await query.message.reply_text(welcome_text)
            # context.user_data['waiting_for_request_start'] = True

            keyboard = [[InlineKeyboardButton("Да!", callback_data="start_game")]]
            reply_markup = InlineKeyboardMarkup(keyboard)

            await query.message.reply_text(welcome_text, reply_markup=reply_markup)
        else:
            await query.edit_message_text(
                "❌ Вы еще не подписались на канал. Пожалуйста, подпишитесь и попробуйте снова.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("Подписаться на канал", url=f"https://t.me/{os.getenv('CHANNEL_USERNAME')[1:]}")],
                    [InlineKeyboardButton("✅ Я подписался", callback_data="check_subscription")]
                ])
            )
    elif data == "start_game":
        await first_dice_roll(query, context)
    elif data == "next_first":
        await second_dice_roll(query, context)
    elif data == "next_second":
        await third_dice_roll(query, context)
    elif data == "next_third":
        await ask_advice(query, context)
    elif data == "want_advice_yes":
        await show_advice_cards(query, context)
    elif data == "want_advice_no":
        await end_game(query, context, with_advice=False)
    elif data.startswith("advice_card_"):
        card_num = int(data.split("_")[2])
        await show_advice(query, context, card_num)
    elif data == "book_appointment_yes":
        await choose_format(query, context)
    elif data == "book_appointment_no":
        await query.message.reply_text("Хорошего вам дня! До встречи!")
    elif data.startswith("format_"):
        await choose_game(query, context, data.split("_")[1])
    elif data.startswith("game_"):

        # Получаем username пользователя
        username = query.from_user.username
        if not username:
            username = query.from_user.first_name or "Не указан"
        print(data)
        _g, game_v, game_format = data.split("_")
        games = [
            "Самосаботаж", "Верь в себя", "Пять дорог",
            "Ключ к себе", "Энергия рода", "Помогите выбрать"
        ]
        game_name = games[int(game_v)]
        await query.message.reply_text(
            f"Отлично! Ваша заявка на игру '{game_name}' принята!")

        user_id = query.from_user.id
        await send_booking_notification(context, game_name, game_format, username, user_id)


########################################################################################################################

async def send_booking_notification(context: CallbackContext, game_name: str, game_format: str, username: str, user_id: int):
    """Отправка уведомления администратору о записи на игру"""
    admin_chat_id = os.getenv('ADMIN_CHAT_ID')  # Замените на ваш chat_id

    notification_text = (
        "🎯 Новая запись на игру!\n\n"
        f"📝 Игра: {game_name} ({"индивидуальная" if game_format == "individual" else "групповая"})\n"
        f"👤 Пользователь: @{username}\n"
        f"🕐 Время: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    )

    try:
        await context.bot.send_message(
            chat_id=admin_chat_id,
            text=notification_text
        )
    except Exception as e:
        print(f"Ошибка отправки уведомления: {e}")

########################################################################################################################


async def first_dice_roll(query, context):
    """Первый бросок кубика"""
    keyboard = [[InlineKeyboardButton("🎲 Бросить кубик", callback_data="roll_first")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    # await query.message.reply_text("Появляется кубик", reply_markup=reply_markup)
    await query.message.reply_text("Интересно...", reply_markup=reply_markup)


async def second_dice_roll(query, context):
    """Второй бросок кубика"""
    keyboard = [[InlineKeyboardButton("🎲 Бросить кубик", callback_data="roll_second")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    # await query.message.reply_text("Появляется кубик", reply_markup=reply_markup)
    await query.message.reply_text("Хорошо. Первый шаг сделан.", reply_markup=reply_markup)


async def third_dice_roll(query, context):
    """Третий бросок кубика"""
    keyboard = [[InlineKeyboardButton("🎲 Бросить кубик", callback_data="roll_third")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    # await query.message.reply_text("Появляется кубик", reply_markup=reply_markup)
    await query.message.reply_text("Какая вы уникальная личность.", reply_markup=reply_markup)


########################################################################################################################
async def roll_dice(update: Update, context: CallbackContext) -> None:
    """Обработка бросков кубика"""
    query = update.callback_query
    await query.answer()

    # Убираем кнопку у предыдущего сообщения
    await query.edit_message_reply_markup(reply_markup=None)

    dice_message = await query.message.reply_dice()
    dice_value = dice_message.dice.value

    data = query.data

    await asyncio.sleep(1) # 5

    if data == "roll_first":
        question = FIRST_QUESTIONS[dice_value]
        # keyboard = [[InlineKeyboardButton("Далее", callback_data="next_first")]]
        await query.message.reply_text(f"🎲 Выпало: {dice_value}\n\nОтветьте себе на вопрос честно:\n\n",) # {question}
                                       # reply_markup=InlineKeyboardMarkup(keyboard))
        with open(f'images/Вопрос 1.{dice_value}.jpg', 'rb') as photo:
            await query.message.reply_photo(photo=photo)
        context.user_data['waiting_for_request_first'] = True

    elif data == "roll_second":
        question = SECOND_QUESTIONS[dice_value]
        # keyboard = [[InlineKeyboardButton("Далее", callback_data="next_second")]]
        await query.message.reply_text(f"🎲 Выпало: {dice_value}\n\nОтветьте себе на вопрос честно:\n\n",)
                                       # reply_markup=InlineKeyboardMarkup(keyboard))
        with open(f'images/Вопрос 2.{dice_value}.jpg', 'rb') as photo:
            await query.message.reply_photo(photo=photo)
        context.user_data['waiting_for_request_second'] = True

    elif data == "roll_third":
        resource = THIRD_RESOURCES[dice_value]
        keyboard = [[InlineKeyboardButton("Далее", callback_data="next_third")]]
        await query.message.reply_text(f"🎲 Выпало: {dice_value}\n\nЧто является для вас ресурсом?\n\n",)
        with open(f'images/Вопрос 3.{dice_value}.jpg', 'rb') as photo:
            await query.message.reply_photo(photo=photo, reply_markup=InlineKeyboardMarkup(keyboard))


########################################################################################################################


async def ask_advice(query, context):
    """Предложение получить карту-совет"""
    text = "Хотите получить карту-совет?\n\n(советы взяты из книги Ронды Берн «Тайна любви, здоровья и денег»)"

    keyboard = [
        [InlineKeyboardButton("Да", callback_data="want_advice_yes")],
        [InlineKeyboardButton("Нет", callback_data="want_advice_no")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.message.reply_text(text, reply_markup=reply_markup)


async def show_advice_cards(query, context):
    """Показать карты для выбора"""
    text = "Выберите одну карту:"

    keyboard = [
        [InlineKeyboardButton("Карта 1", callback_data="advice_card_1")],
        [InlineKeyboardButton("Карта 2", callback_data="advice_card_2")],
        [InlineKeyboardButton("Карта 3", callback_data="advice_card_3")],
        [InlineKeyboardButton("Карта 4", callback_data="advice_card_4")],
        [InlineKeyboardButton("Карта 5", callback_data="advice_card_5")],
        [InlineKeyboardButton("Карта 6", callback_data="advice_card_6")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.message.reply_text(text, reply_markup=reply_markup)


async def show_advice(query, context, card_num):
    """Показать выбранный совет"""

    advice = ADVICE_CARDS[card_num]

    text = f"Карта {card_num}:\n\n{advice}\n\nБлагодарю за игру! Пусть ваша мечта-запрос исполнится!"

    keyboard = [[InlineKeyboardButton("Записаться на игру", callback_data="book_appointment_yes")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.message.reply_text(text, reply_markup=reply_markup)


async def end_game(query, context, with_advice=True):
    """Завершение игры"""
    text = "Благодарю за игру! Пусть ваша мечта-запрос исполнится!"

    keyboard = [[InlineKeyboardButton("Записаться на игру", callback_data="book_appointment_yes")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.message.reply_text(text, reply_markup=reply_markup)


async def choose_format(query, context):
    """Выбор формата игры"""
    text = "Поздравляю Вас - вы сделали первый шаг в вашей мечте. Записать на полноценную игру для решения своего запроса?\n\nВыберите формат игры:"

    keyboard = [
        [InlineKeyboardButton("Индивидуальная", callback_data="format_individual")],
        [InlineKeyboardButton("Групповая", callback_data="format_group")],
        [InlineKeyboardButton("Назад", callback_data="want_advice_no")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.message.reply_text(text, reply_markup=reply_markup)


async def choose_game(query, context, format_type):
    """Выбор игры"""
    format_name = "индивидуальную" if format_type == "individual" else "групповую"
    text = f"Вы выбрали {format_name} игру. Выберите игру:"

    games = [
        "Самосаботаж", "Верь в себя", "Пять дорог",
        "Ключ к себе", "Энергия рода", "Помогите выбрать"
    ]

    keyboard = []
    for game_v, game in enumerate(games):
        callback_data = f"game_{game_v}_{format_type}"
        keyboard.append([InlineKeyboardButton(game, callback_data=callback_data)])

    keyboard.append([InlineKeyboardButton("Назад", callback_data="book_appointment_yes")])
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.message.reply_text(text, reply_markup=reply_markup)


def main() -> None:
    # Initialize database
    # init_db()


    """Запуск бота"""
    application = Application.builder().token(os.getenv("TOKEN")).build()

    # Обработчики команд
    application.add_handler(CommandHandler("start", start))


    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_user_request))


    # Обработчики callback'ов
    application.add_handler(CallbackQueryHandler(handle_callback,
                                                 pattern="^(check_subscription|start_game|next_first|next_second|next_third|want_advice_yes|want_advice_no|book_appointment_yes|book_appointment_no|format_|game_|advice_card_)"))

    application.add_handler(CallbackQueryHandler(roll_dice, pattern="^(roll_first|roll_second|roll_third)"))
    # application.add_handler(CallbackQueryHandler(show_advice, pattern="^advice_card_"))

    # Запуск бота
    application.run_polling()


if __name__ == '__main__':
    main()
