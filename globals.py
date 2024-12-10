from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from telebot.async_telebot import AsyncTeleBot


engine = create_engine('sqlite:///:memory:', echo=True)
session = Session(engine)
bot = AsyncTeleBot('7667464125:AAGGh68G7OQuK_gVy9IBCORLC7afg-5fyKw', parse_mode='HTML', disable_web_page_preview=True)
bot_name: str