from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

cancel_markup = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text='Отмена', callback_data='cancel')]])
hide_markup = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text='Скрыть', callback_data='hide')]])
