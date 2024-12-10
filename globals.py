from aiogram import Bot
from sqlalchemy.orm import Session
from sqlalchemy import create_engine


token = '7839864987:AAH39L-9TzrfqsZaxb6EggyuC-ur4vxRaTo'
bot = Bot(token)
engine = create_engine('sqlite:///:memory:')
session = Session(engine)
