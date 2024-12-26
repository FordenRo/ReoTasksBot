from asyncio import run as run_async

from aiogram import Dispatcher

from database import Base
from globals import bot, engine, session
from handlers import project, start, task


async def main():
    dispatcher = Dispatcher()
    Base.metadata.create_all(engine)

    dispatcher.include_routers(start.router,
                               project.router,
                               task.router)

    await dispatcher.start_polling(bot)

    session.commit()
    engine.dispose()


if __name__ == '__main__':
    run_async(main())
