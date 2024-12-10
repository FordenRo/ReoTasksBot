from asyncio import run as run_async

from sqlalchemy import select, exists, delete
from telebot.types import Message
from telebot.util import extract_arguments

from classes import *
from globals import *


@bot.message_handler(commands=['start'])
async def start(message: Message):
	await bot.delete_message(message.chat.id, message.id)

	if session.query(exists(User).where(User.id == message.chat.id)).scalar():
		user = session.scalar(select(User).where(User.id == message.chat.id))

		args = extract_arguments(message.text).split('-')
		if args[0] == 'project':
			await project_command(user, *args[1:])
		elif args[0] == 'open':
			await open_command(user, *args[1:])
	else:
		user = User(id=message.chat.id)
		session.add(user)
		session.commit()

		await bot.send_message(user.id, 'User created!')
		await open_main(user)


async def open_command(user: User, *args: str):
	command = args[0]
	if command == 'project':
		id = int(args[1])
		project = session.scalar(select(Project).where(Project.id == id))
		await open_project(project)
	elif command == 'main':
		await open_main(user)


async def project_command(user: User, *args: str):
	type = args[0]
	if type == 'new':
		print('test')


def get_link(string: str, data: str):
	return '<a href="t.me/projecttasksmanagerbot?start={}">{}</a>'.format(data, string)


async def open_main(user: User):
	message = (f'[Главная]\n\n'
			   f'{get_link('Входящие', 'open-inbox')}\n'
			   f'{get_link('Сегодня', 'open-now')}\n\n'
			   f'{get_link('Проекты' if user.projects else 'Нет проектов', 'project-new')}{':' if user.projects else ''}\n'
			   f'{'\n'.join([f'* {get_link(project.name, f'open-project-{project.id}')}' for project in user.projects])}')

	await bot.send_message(user.id, message)


async def open_project(project: Project):
	message = (f'[{get_link('Главная', 'open-main')}/Проекты]\n\n'
			   f'{get_link(project.name, f'project-edit-name-{project.id}')}\n'
			   f'{get_link('Описание' if project.description else 'Нет описания', f'project-edit-description-{project.id}')}{f': {project.description}' if project.description else ''}\n\n'
			   f'{get_link('Задачи' if project.tasks else 'Нет задач', f'project-new_task-{project.id}')}{':' if project.tasks else ''}\n'
			   f'{'\n'.join([f'* {task.name}' for task in project.tasks])}\n\n'
			   f'{get_link('Удалить', f'project-delete-{project.id}')}')

	await bot.send_message(project.user.id, message)


async def main():
	Base.metadata.create_all(engine)

	bot_name = (await bot.get_me()).username
	await bot.infinity_polling()


if __name__ == '__main__':
	run_async(main())
