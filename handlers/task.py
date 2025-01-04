from aiogram import Bot, F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, Message, \
    ReplyKeyboardMarkup
from sqlalchemy import select

from database import Notification, NotificationType, Project, Task, User
from filters.user import UserFilter
from globals import session
from handlers.project import open_project
from states.task import TaskStates
from utils import cancel_markup, hide_markup

router = Router()


@router.callback_query(F.data.split()[0] == 'task', UserFilter())
async def callback(callback: CallbackQuery, user: User, bot: Bot, state: FSMContext):
    data = callback.data.split()
    type = data[1]
    id = data[2]

    try:
        id = int(id)
    except ValueError:
        await callback.answer('Произошла непредвиденная ошибка')
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

    async def rename():
        msg = await bot.send_message(user.id, 'Введите новое название задачи', reply_markup=cancel_markup)
        await state.set_state(TaskStates.rename)
        await state.set_data({'message': msg, 'main': callback.message, 'task_id': id})

    async def notify():
        task = session.scalar(select(Task).where(Task.id == id))
        if task.notification:
            session.delete(task.notification)
            session.commit()
            session.refresh(task)
            await open_task(callback.message, task)
            return 'Оповещение удалено'

        msg = await bot.send_message(user.id, 'Выберите тип', reply_markup=ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text='Один раз')],
                      [KeyboardButton(text='Будни')],
                      [KeyboardButton(text='Каждый день')],
                      [KeyboardButton(text='Отмена')]]))
        await state.set_state(TaskStates.notify_type)
        await state.set_data({'message': msg, 'main': callback.message, 'task_id': id})

    types = {'new': lambda: new(),
             'open': lambda: open(),
             'subtask': lambda: subtask(),
             'edit': lambda: edit(),
             'delete': lambda: delete(),
             'rename': lambda: rename(),
             'notify': lambda: notify()}

    async def delete():
        task = session.scalar(select(Task).where(Task.id == id))
        if task:
            session.delete(task)
        await open_project(callback.message, task.project)

    await callback.answer(await types[type]())


async def open_task(message: Message, task: Task):
    await message.edit_text('—' * 12 +
                            f'\n[{task.project.name}/Задача]\n\n'
                            f'{task.name}\n'
                            f'{task.description}',
                            reply_markup=InlineKeyboardMarkup(
                                inline_keyboard=
                                [[InlineKeyboardButton(text=subtask.name, callback_data=f'task open {subtask.id}')]
                                 for subtask in task.subtasks]
                                + [[InlineKeyboardButton(text='📝', callback_data=f'task subtask {task.id}')],
                                   [InlineKeyboardButton(text='🔙', callback_data=f'project open {task.project_id}'),
                                    InlineKeyboardButton(text='✏️', callback_data=f'task rename {task.id}'),
                                    InlineKeyboardButton(text='⚙', callback_data=f'task edit {task.id}')]]))


async def edit_task(message: Message, task: Task):
    await message.edit_text(task.name, reply_markup=InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text='✏️ Переименовать', callback_data=f'task rename {task.id}')],
                         [InlineKeyboardButton(text=('🗓 Создать напоминание' if not task.notification
                                                     else '🗓 Удалить напоминание'),
                                               callback_data=f'task notify {task.id}')],
                         [InlineKeyboardButton(text='🗑 Удалить', callback_data=f'task delete {task.id}')],
                         [InlineKeyboardButton(text='🔙 Назад', callback_data=f'task open {task.id}')]]))


@router.message(TaskStates.rename)
async def rename_state(message: Message, state: FSMContext):
    await message.delete()
    await (await state.get_value('message')).delete()
    main_message = await state.get_value('main')
    task_id = await state.get_value('task_id')
    task = session.scalar(select(Task).where(Task.id == task_id))
    await state.clear()

    task.name = message.text
    session.commit()

    await open_task(main_message, task)


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


@router.message(TaskStates.notify_type, UserFilter())
async def notify_type(message: Message, user: User, state: FSMContext, bot: Bot):
    await message.delete()
    await (await state.get_value('message')).delete()
    data = await state.get_data()

    async def process():
        msg = await bot.send_message(user.id, 'Введите время (HH:MM) или (HH MM)')
        await state.set_state(TaskStates.notify_time)
        await state.set_data(data | {'message': msg})

    async def one():
        nonlocal data

        data |= {'type': NotificationType.one}
        await state.set_data(data)
        await process()

    async def every():
        nonlocal data

        data |= {'type': NotificationType.every}
        await state.set_data(data)
        await process()

    async def weekday():
        nonlocal data

        data |= {'type': NotificationType.weekday}
        await state.set_data(data)
        await process()

    async def cancel():
        main_message = await state.get_value('main')
        task_id = await state.get_value('task_id')
        task = session.scalar(select(Task).where(Task.id == task_id))
        await state.clear()
        await open_task(main_message, task)

    types = {'Один раз': lambda: one(),
             'Будни': lambda: weekday(),
             'Каждый день': lambda: every(),
             'Отмена': lambda: cancel()}
    await types[message.text]()


@router.message(TaskStates.notify_time, UserFilter())
async def notify_time(message: Message, user: User, state: FSMContext, bot: Bot):
    await message.delete()
    await (await state.get_value('message')).delete()
    type = await state.get_value('type')
    task_id = await state.get_value('task_id')
    main_message = await state.get_value('main')
    await state.clear()

    try:
        h, m = message.text.split()
    except ValueError:
        try:
            h, m = message.text.split(':')
        except ValueError:
            await bot.send_message(user.id, 'Не удалось распознать время', reply_markup=hide_markup)
            return

    task = session.scalar(select(Task).where(Task.id == task_id))
    time = ':'.join([h, m])

    notification = Notification(task=task, type=type, time=time)
    session.add(notification)
    session.commit()

    await open_task(main_message, task)
