from aiogram.fsm.state import State, StatesGroup


class ProjectStates(StatesGroup):
    new = State()
    rename = State()
