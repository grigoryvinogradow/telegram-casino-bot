
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from libraries.users import Users

class RatingHandler:
    def __init__(self, dp: Dispatcher, bot: Bot, database: Users):
        self.register(dp, bot, database)
    
    def register(self, dp: Dispatcher, bot: Bot, database: Users):
        # building the rating
        def build_rating(key: str):
            users = database.get_all('users')
            ranking = []

            for user in users:
                if key == 'winrate':
                    wins = sum([val for i, val in database.get('wins', user['id']).items() if i != 'id'])
                    tries = sum([val for i, val in database.get('tries', user['id']).items() if i != 'id'])
                    value = wins / tries if tries > 0 else 0
                elif key == 'jackpots':
                    value = database.get('jackpots', user['id']).get('slots', 0)
                else:
                    value = sum([val for i, val in database.get(key, user['id']).items() if i != 'id'])
                ranking.append((user, value))

            return sorted(ranking, key=lambda x: x[1], reverse=True)[:5]

        def find_user_place(id: str, ranking: list):
            for index, (user, _) in enumerate(ranking, start=1):
                if user['id'] == id:
                    return index
            return '–'
        
        # the main menu of rating
        @dp.callback_query_handler(lambda c: c.data == 'rating')
        async def rating_handler(callback: types.CallbackQuery):
            keyboard = InlineKeyboardMarkup()
            keyboard.add(
                InlineKeyboardButton('🎰 Выигрыши', callback_data='rating-wins'),
                InlineKeyboardButton('🎰 Попытки', callback_data='rating-tries')
            )
            keyboard.add(
                InlineKeyboardButton('🎰 Джекпоты', callback_data='rating-jackpots'),
                InlineKeyboardButton('🎰 Винрейт', callback_data='rating-winrate')
            )

            await bot.send_message(
                callback.message.chat.id,
                "<b>Выберите категорию рейтинга:</b>",
                reply_markup=keyboard,
                message_thread_id=callback.message.message_thread_id
            )
            await callback.answer()

        # proccessing callback
        @dp.callback_query_handler(lambda c: c.data.startswith('rating-'))
        async def rating_callback(callback: types.CallbackQuery):
            keys = {
                'wins': "🎰 <b>РЕЙТИНГ ПО ВЫИГРЫШАМ</b>",
                'tries': "🎰 <b>РЕЙТИНГ ПО ПОПЫТКАМ</b>",
                'jackpots': "🎰 <b>РЕЙТИНГ ПО ДЖЕКПОТАМ</b>",
                'winrate': "🎰 <b>РЕЙТИНГ ПО ВИНРЕЙТУ</b>",
            }

            key = callback.data.split('-')[-1]
            title = keys.get(key, "🎰 <b>РЕЙТИНГ</b>")

            rating = build_rating(key)
            place = find_user_place(callback.from_user.id, rating)
            text = '\n'.join(
                f"<b>{i+1}.</b> {user.get('name')} - {round(val, 2) if key == 'winrate' else val}"
                for i, (user, val) in enumerate(rating)
            )

            result = [
                f"{title}\n<i>Ваше место: {place}</i>\n\n{text}\n",
                "<b>Вернуться в главное меню - /casino</b>"
            ]

            keyboard = InlineKeyboardMarkup()
            keyboard.add(
                InlineKeyboardButton('🎰 Выигрыши', callback_data='rating-wins'),
                InlineKeyboardButton('🎰 Попытки', callback_data='rating-tries')
            )
            keyboard.add(
                InlineKeyboardButton('🎰 Джекпоты', callback_data='rating-jackpots'),
                InlineKeyboardButton('🎰 Винрейт', callback_data='rating-winrate')
            )

            await callback.message.edit_text(
                '\n'.join(result),
                reply_markup=keyboard,
            )
            await callback.answer()

