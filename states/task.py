from aiogram.fsm.state import State, StatesGroup


class TaskStates(StatesGroup):
    new = State()