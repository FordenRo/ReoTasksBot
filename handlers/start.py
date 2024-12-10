from aiogram import Router, F
from aiogram.filters import CommandStart
from globals import bot

router = Router()


@router.message(CommandStart())
async def command(message):
    await bot.send_message(message.from_user.id, 'test')
