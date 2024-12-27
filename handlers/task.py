from aiogram import Bot, F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message, InlineKeyboardButton, InlineKeyboardMarkup
from sqlalchemy import select

from database import Project, Task, User
from filters.user import UserFilter
from globals import session
from handlers.project import open_project
from states.task import TaskStates
from utils import cancel_markup

router = Router()


@router.callback_query(F.data.split()[0] == 'task', UserFilter())
async def callback(callback: CallbackQuery, user: User, bot: Bot, state: FSMContext):
    data = callback.data.split()
    type = data[1]
    id = data[2]

    try:
        id = int(id)
    except ValueError:
        await callback.answer('Error', True)
        return

    async def new():
        msg = await bot.send_message(user.id, 'Введите название задачи', reply_markup=cancel_markup)
        await state.set_state(TaskStates.new)
        await state.set_data({'message': msg, 'main': callback.message, 'project_id': id})

    async def subtask():
        msg = await bot.send_message(user.id, 'Введите название подзадачи', reply_markup=cancel_markup)
        await state.set_state(TaskStates.subtask)
        await state.set_data({'message': msg, 'main': callback.message, 'task_id': id})

    async def open():
        task = session.scalar(select(Task).where(Task.id == id))
        if task:
            await open_task(callback.message, task)

    async def edit():
        task = session.scalar(select(Task).where(Task.id == id))
        if task:
            await edit_task(callback.message, task)

    types = {'new': lambda: new(),
             'open': lambda: open(),
             'subtask': lambda: subtask(),
             'edit': lambda: edit(),
             'delete': lambda: delete()}
    
    async def delete():
        task = session.scalar(select(Task).where(Task.id == id))
        if task:
            session.delete(task)
        await open_project(callback.message, task.project)

    await types[type]()
    await callback.answer()


async def open_task(message: Message, task: Task):
    await message.edit_text(f'{task.project.name}\n\n'
                            f'{task.name}\n'
                            f'{task.description}', reply_markup=InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text=subtask.name, callback_data=f'task open {subtask.id}')]
                         for subtask in task.subtasks]
                        + [[InlineKeyboardButton(text='📝', callback_data=f'task subtask {task.id}')],
                           [InlineKeyboardButton(text='🔙', callback_data=f'project open {task.project_id}'),
                            InlineKeyboardButton(text=f'✏️', callback_data=f'task rename {task.id}'),
                            InlineKeyboardButton(text='⚙', callback_data=f'task edit {task.id}')]]))

async def edit_task(message: Message, task: Task):
    await message.edit_text(task.name, reply_markup=InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text='Переименовать', callback_data=f'task rename {task.id}')],
                         [InlineKeyboardButton(text='Удалить', callback_data=f'task delete {task.id}')],
                         [InlineKeyboardButton(text='Назад', callback_data=f'task open {task.id}')]]))


@router.message(TaskStates.new, UserFilter())
async def new_state(message: Message, user: User, state: FSMContext):
    await message.delete()
    await (await state.get_value('message')).delete()
    main_message = await state.get_value('main')
    project = session.scalar(select(Project).where(Project.id == await state.get_value('project_id')))
    await state.clear()

    task = Task(user=user, name=message.text, project=project)
    session.add(task)
    session.commit()

    await open_project(main_message, project)
