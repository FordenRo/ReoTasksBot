from aiogram import Bot, F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy import select

from database import Project, Task, User
from filters.user import UserFilter
from globals import session
from handlers.start import open_main
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

    async def open():
        pass

    types = {'new': lambda: new(),
             'open': lambda: open()}

    await types[type]()
    await callback.answer()


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

    await open_main(main_message, user)
