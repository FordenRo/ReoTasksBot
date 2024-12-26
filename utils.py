from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

cancel_markup = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text='Отмена', callback_data='cancel')]])
