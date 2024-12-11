from typing import Optional

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, DeclarativeBase, relationship


class Base(DeclarativeBase):
	pass


class User(Base):
	__tablename__ = 'users'

	id: Mapped[int] = mapped_column(primary_key=True)
	message_id: Mapped[int] = mapped_column()
	projects: Mapped[list['Project']] = relationship(back_populates='user')
	tasks: Mapped[list['Task']] = relationship(back_populates='user')


class Project(Base):
	__tablename__ = 'projects'

	id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
	name: Mapped[str] = mapped_column()
	tasks: Mapped[list['Task']] = relationship(back_populates='project')

	user_id: Mapped[int] = mapped_column(ForeignKey('users.id'))
	user: Mapped['User'] = relationship(back_populates='projects')


class Task(Base):
	__tablename__ = 'tasks'

	id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
	name: Mapped[str] = mapped_column()
	description: Mapped[str] = mapped_column()
	priority: Mapped[str] = mapped_column(default=0)
	subtasks: Mapped[list['Task']] = relationship(back_populates='parent')

	user_id: Mapped[int] = mapped_column(ForeignKey('users.id'))
	user: Mapped['User'] = relationship(back_populates='tasks')

	project_id: Mapped[int] = mapped_column(ForeignKey('projects.id'))
	project: Mapped['Project'] = relationship(back_populates='tasks')

	parent_id: Mapped[int] = mapped_column(ForeignKey('tasks.id'), nullable=True)
	parent: Mapped[Optional['Task']] = relationship(remote_side=id, back_populates='subtasks')
