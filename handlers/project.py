from aiogram import Bot, F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message
from sqlalchemy import select

from database import Project, User
from filters.user import UserFilter
from globals import session
from handlers.start import open_main
from states.project import ProjectStates
from utils import cancel_markup

router = Router()


@router.callback_query(F.data.split()[0] == 'project', UserFilter())
async def callback(callback: CallbackQuery, user: User, bot: Bot, state: FSMContext):
    data = callback.data.split()
    type = data[1]
    if len(data) > 2:
        id = data[2]

        try:
            id = int(id)
        except ValueError:
            await callback.answer('Error', True)
            return

    async def new():
        msg = await bot.send_message(user.id, 'Введите название проекта', reply_markup=cancel_markup)
        await state.set_state(ProjectStates.new)
        await state.set_data({'message': msg, 'main': callback.message})

    async def edit():
        project = session.scalar(select(Project).where(Project.id == id))
        if project:
            await edit_project(callback.message, project)

    async def delete():
        project = session.scalar(select(Project).where(Project.id == id))
        if project:
            session.delete(project)
        await open_main(callback.message, user)

    async def open():
        project = session.scalar(select(Project).where(Project.id == id))
        if project:
            await open_project(callback.message, project)

    types = {'new': lambda: new(),
             'edit': lambda: edit(),
             'delete': lambda: delete(),
             'open': lambda: open()}

    await types[type]()
    await callback.answer()


async def open_project(message: Message, project: Project):
    await message.edit_text(project.name, reply_markup=InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text=task.name, callback_data=f'task open {task.id}')]
                         for task in project.tasks]
                        + [[InlineKeyboardButton(text='Задача', callback_data=f'task new {project.id}'),
                            InlineKeyboardButton(text='Папка', callback_data=f'folder new {project.id}')],
                           [InlineKeyboardButton(text='Назад', callback_data='main'),
                            InlineKeyboardButton(text='Опции', callback_data=f'project edit {project.id}')]]))


async def edit_project(message: Message, project: Project):
    await message.edit_text(project.name, reply_markup=InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text='Переименовать', callback_data=f'project rename {project.id}')],
                         [InlineKeyboardButton(text='Удалить', callback_data=f'project delete {project.id}')],
                         [InlineKeyboardButton(text='Назад', callback_data=f'project open {project.id}')]]))


@router.message(ProjectStates.new, UserFilter())
async def new_state(message: Message, user: User, state: FSMContext):
    await message.delete()
    await (await state.get_value('message')).delete()
    main_message = await state.get_value('main')
    await state.clear()

    project = Project(user=user, name=message.text)
    session.add(project)
    session.commit()

    await open_main(main_message, user)
    # await open_project(main_message, user)
