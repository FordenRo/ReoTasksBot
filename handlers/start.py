from aiogram import F, Router
from aiogram.filters import CommandStart
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message
from sqlalchemy import exists, select

from database import User, Project
from filters.user import UserFilter
from globals import bot, session

router = Router()


@router.message(CommandStart())
async def command(message: Message):
    if session.query(exists(User).where(User.id == message.from_user.id)).scalar():
        user = session.scalar(select(User).where(User.id == message.from_user.id))
    else:
        user = User(id=message.from_user.id)
        inbox = Project(user=user, name='Входящие', editable=False)
        session.add_all([user, inbox])
        session.commit()

        message = await bot.send_message(message.from_user.id, 'Добро пожаловать!', reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton(text='Главная', callback_data='main')]]))


@router.callback_query(F.data == 'main', UserFilter())
async def main_callback(callback: CallbackQuery, user: User):
    await open_main(callback.message, user)


async def open_main(message: Message, user: User):
    await message.edit_text('Главная', reply_markup=InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text='🗓 Сегодня', callback_data='project today')]]
                        + [[InlineKeyboardButton(text=project.name, callback_data=f'project open {project.id}')]
                           for project in user.projects]
                        + [[InlineKeyboardButton(text='📝 Создать', callback_data='project new')]]))
