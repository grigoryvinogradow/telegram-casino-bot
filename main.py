import json, os, time, logging
from dotenv import load_dotenv

from aiogram import Bot, Dispatcher, types
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.dispatcher.middlewares import BaseMiddleware
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils import executor
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.types import ContentType

from handlers.messages import MessagesHandler
from handlers.rating import RatingHandler

from libraries.users import Users
from database.database import Database

# variables

load_dotenv()

BOT = Bot(token = os.getenv('BOT_TOKEN'), parse_mode = 'HTML')
STORAGE = MemoryStorage()
DP = Dispatcher(BOT, storage=STORAGE)

DATABASE = Database(os.path.join('database', 'data.db'))
USERS = Users(DATABASE)

GAMES = {
    '🎰': {'name': 'slots', 'win': [1, 22, 43], 'jackpot': 64},
    '🏀': {'name': 'bask',  'win': [4, 5]},
    '🎯': {'name': 'dart',  'win': [6]},
    '⚽': {'name': 'foot',  'win': [3, 5]},
    '🎳': {'name': 'bowl',  'win': [6]},
    '🎲': {'name': 'dice',  'win': [1]},
}

# user register

class UserRegistrationMiddleware(BaseMiddleware):
    async def on_pre_process_message(self, message: types.Message, data: dict):
        if not USERS.get('users', message.from_user.id):
            USERS.add(message.from_user.id, message.from_user.full_name)

DP.middleware.setup(UserRegistrationMiddleware())

# main menu handler

@DP.message_handler(commands=['casino', 'start'])
async def main_menu(message: types.Message):
    user = message.from_user.id

    wins = USERS.get('wins', user)
    tries = USERS.get('tries', user)
    jackpots = USERS.get('jackpots', user)

    text = f"""🎰 <b>Здравствуйте, {f"@{message.from_user.username}" if message.from_user.username else message.from_user.full_name}!</b>
        
    ⭐ <b>Всего джекпотов</b>: {sum([val for i, val in jackpots.items() if i != 'id'])}
    ✔ <b>Всего выигрышей</b>: {sum([val for i, val in wins.items() if i != 'id'])}
    🏅 <b>Всего попыток</b>: {sum([val for i, val in tries.items() if i != 'id'])}

    🎮 <b>Игры</b>: /games
    📩 <b>Оповещение о выигрыше: /congratulate</b>"""

    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton('📊 Статистика', callback_data='stats'))
    keyboard.add(InlineKeyboardButton('🏆 Рейтинг', callback_data='rating'))

    await BOT.send_message(
        message.chat.id, text,
        message_thread_id = message.message_thread_id,
        reply_markup=keyboard
    )

# games

@DP.message_handler(commands=['games'])
async def games(message: types.Message):
    text = f"""🎰 <b>Слоты:</b> /slots
🎲 <b>Кубик:</b> /dice
⚽ <b>Футбол:</b> /foot
🎳 <b>Боулинг:</b> /bowl
🏀 <b>Баскетбол:</b> /bask
🎯 <b>Дартс:</b> /dart"""

    await BOT.send_message(
        message.chat.id, text,
        message_thread_id = message.message_thread_id
    )

# statistics handler

@DP.callback_query_handler(lambda c: c.data == 'stats')
async def full_stats(callback: types.CallbackQuery):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton("🎰", callback_data="stats-slots"), InlineKeyboardButton("🎲", callback_data="stats-dice"), InlineKeyboardButton("⚽", callback_data="stats-foot")],
        [InlineKeyboardButton("🎳", callback_data="stats-bowl"), InlineKeyboardButton("🏀", callback_data="stats-bask"), InlineKeyboardButton("🎯", callback_data="stats-dart")],
        [InlineKeyboardButton("♻️ Сбросить", callback_data="stats-reset")],
    ])

    await BOT.send_message(
        chat_id=callback.message.chat.id,
        text="📊 <b>Выберите категорию статистики:</b>",
        reply_markup=keyboard,
        message_thread_id=callback.message.message_thread_id
    )
    await callback.answer()

@DP.callback_query_handler(lambda c: c.data and c.data.startswith('stats-'))
async def handle_stats_callback(callback: types.CallbackQuery):
    user = callback.from_user.id
    category = callback.data.split('-')[1]

    wins = USERS.get('wins', user)
    tries = USERS.get('tries', user)
    jackpots = USERS.get('jackpots', user)

    if category == "slots":
        text = f"""🎰 <b>СТАТИСТИКА СЛОТОВ</b>
        Джекпоты: <b>{jackpots.get('slots')}</b>
        Выигрыши: <b>{wins.get('slots')}</b>
        Попытки: <b>{tries.get('slots')}</b>"""
        
    elif category == "dice":
        text = f"""🎲 <b>СТАТИСТИКА КУБИКА</b>
        Выигрыши: <b>{wins.get('dice')}</b>
        Попытки: <b>{tries.get('dice')}</b>"""
        
    elif category == "foot":
        text = f"""⚽ <b>СТАТИСТИКА ФУТБОЛА</b>
        Выигрыши: <b>{wins.get('foot')}</b>
        Попытки: <b>{tries.get('foot')}</b>"""

    elif category == "bowl":
        text = f"""🎳 <b>СТАТИСТИКА БОУЛИНГА</b>
        Выигрыши: <b>{wins.get('bowl')}</b>
        Попытки: <b>{tries.get('bowl')}</b>"""

    elif category == "bask":
        text = f"""🏀 <b>СТАТИСТИКА БАСКЕТБОЛА</b>
        Выигрыши: <b>{wins.get('bask')}</b>
        Попытки: <b>{tries.get('bask')}</b>"""

    elif category == "dart":
        text = f"""🎯 <b>СТАТИСТИКА ДАРТСА</b>
        Выигрыши: <b>{wins.get('dart')}</b>
        Попытки: <b>{tries.get('dart')}</b>"""

    elif category == "reset":
        USERS.reset(callback.from_user.id)
        await callback.message.edit_text(f'✅ Статистика игрока {f"@{callback.from_user.username}" if callback.from_user.username else callback.from_user.full_name} <b>сброшена</b>',)
        return

    elif category == "back":
        await full_stats(callback.message)
        return
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton("🎰", callback_data="stats-slots"), InlineKeyboardButton("🎲", callback_data="stats-dice"), InlineKeyboardButton("⚽", callback_data="stats-foot")],
        [InlineKeyboardButton("🎳", callback_data="stats-bowl"), InlineKeyboardButton("🏀", callback_data="stats-bask"), InlineKeyboardButton("🎯", callback_data="stats-dart")],
        [InlineKeyboardButton("♻️ Сбросить", callback_data="stats-reset")],
    ])

    await callback.message.edit_text(text, parse_mode='HTML', reply_markup=keyboard)

@DP.message_handler(commands=['congratulate'])
async def congratulate(message: types.Message):
    user = USERS.get('users', message.from_user.id)
    USERS.set('users', message.from_user.id, 'congratulate', False if user['congratulate'] else True)

    await BOT.send_message(
        message.chat.id,
        f'✅ <b>Настройка сохранена</b>\n<i>Переключено на <b>{"ДА" if not user["congratulate"] else "НЕТ"}</b></i>',
        message_thread_id=message.message_thread_id
    )
    
if __name__ == '__main__':
    MessagesHandler(DP, BOT, GAMES, USERS)
    RatingHandler(DP, BOT, USERS)

    executor.start_polling(DP, skip_updates=False, allowed_updates=["message", "callback_query"])
