from database import User
from globals import bot
from utils import get_link_button


async def open_main(user: User):
	await bot.edit_message_text('[Главная]\n\n'
								f'{get_link_button('Входящие', 'project-inbox')}\n'
								f'Проекты:'
								f'{'\n'.join([get_link_button(project.name, f'project-{project.id}') for project in user.projects])}\n\n'
								f'{get_link_button('Создать', 'new-project')}',
								chat_id=user.id, message_id=user.message_id)
