from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.orm import DeclarativeBase, declared_attr
from sqlalchemy.ext.asyncio import AsyncAttrs, async_sessionmaker, create_async_engine
from sqlalchemy import Integer, func, Table, Column, Boolean, String
from datetime import datetime
from sqlalchemy import ForeignKey, JSON, DateTime
from typing import Any
import enum
from typing import List, Optional


class Base(AsyncAttrs, DeclarativeBase):
    __abstract__ = True  
    type_annotation_map = {
        dict[str, Any]: JSON
    }

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now())

    @declared_attr.directive
    def __tablename__(cls) -> str:
        return cls.__name__.lower() + 's'


board_collaborators = Table(
    "board_collaborators",
    Base.metadata,
    Column("user_id", Integer, ForeignKey("users.id"), primary_key=True),
    Column("board_id", Integer, ForeignKey("boards.id"), primary_key=True)
)

class User(Base):
    username: Mapped[str] = mapped_column(String, nullable=False)
    email: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    password: Mapped[str] = mapped_column(String, nullable=False)

    owned_boards: Mapped[List["Board"]] = relationship(
        "Board",
        back_populates="owner",
        lazy='joined'
    )
    
    # Доски, к которым пользователь имеет доступ (не включая владение)
    boards: Mapped[List["Board"]] = relationship(
        "Board",
        secondary=board_collaborators,
        back_populates="collaborators",
        lazy='joined'
    )

    tokens: Mapped[list["IssuedJWTToken"]] = relationship(
        "IssuedJWTToken",
        back_populates="subject",
        lazy="joined"
    )

class Board(Base):
    title: Mapped[str] = mapped_column(String, nullable=False)
    content: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'), nullable=False)
    
    owner: Mapped["User"] = relationship(
        "User",
        back_populates="owned_boards",
        lazy='joined'
    )

    collaborators: Mapped[List["User"]] = relationship(
        "User",
        secondary=board_collaborators,
        back_populates="boards",
        lazy='joined'
    )

    todo_lists: Mapped[List["ToDoList"]] = relationship(
        "ToDoList",
        back_populates="board",
        cascade="all, delete-orphan",
        lazy="joined"
    )

class IssuedJWTToken(Base):
    jti: Mapped[str] = mapped_column(String(36), primary_key=True)
    
    subject_id: Mapped[int] = mapped_column(ForeignKey('users.id', ondelete='CASCADE'))
    subject: Mapped["User"] = relationship(
        "User",
        back_populates="tokens",
        lazy="joined"
    )
    
    device_id: Mapped[str] = mapped_column(String(36))
    revoked: Mapped[bool] = mapped_column(default=False)
    expired_time: Mapped[int] = mapped_column(Integer, nullable=False)

    def __str__(self) -> str:
        return f'{self.subject}: {self.jti}'

class ToDoList(Base):
    title: Mapped[str] = mapped_column(String, nullable=True)
    deadline: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    board_id: Mapped[int] = mapped_column(ForeignKey('boards.id'), nullable=False)
    board: Mapped["Board"] = relationship("Board", back_populates="todo_lists", lazy="joined")

    tasks: Mapped[List["Task"]] = relationship(
        "Task",
        back_populates="todo_list",
        cascade="all, delete-orphan",
        lazy="joined"
    )

class Task(Base):
    title: Mapped[str] = mapped_column(String, nullable=False)
    completed: Mapped[bool] = mapped_column(Boolean, default=False)
    deadline: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    todo_list_id: Mapped[int] = mapped_column(ForeignKey('todolists.id'), nullable=False)
    todo_list: Mapped["ToDoList"] = relationship("ToDoList", back_populates="tasks", lazy="joined")