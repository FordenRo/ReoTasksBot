from aiogram import Bot
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

token = '7839864987:AAH39L-9TzrfqsZaxb6EggyuC-ur4vxRaTo'
bot = Bot(token)
engine = create_engine('sqlite:///:memory:', echo=True)
session = Session(engine)
