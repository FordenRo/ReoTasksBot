from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from sqlalchemy import select, exists

from database import User
from filters.user import UserFilter
from globals import bot, session
from handlers.opening import open_main

router = Router()


@router.message(CommandStart())
async def command(message: Message):
	if session.query(exists(User).where(User.id == message.from_user.id)).scalar():
		user = session.scalar(select(User).where(User.id == message.from_user.id))
	else:
		message = await bot.send_message(message.from_user.id, 'Добро пожаловать!', reply_markup=InlineKeyboardMarkup(
			inline_keyboard=[[InlineKeyboardButton(text='Главная', callback_data='open_main')]]))

		user = User(id=message.from_user.id, message_id=message.message_id)
		session.add(user)
		session.commit()


@router.callback_query(F.data == 'open_main', UserFilter())
async def main(callback: CallbackQuery, user: User):
	await open_main(user)
	await callback.answer()
