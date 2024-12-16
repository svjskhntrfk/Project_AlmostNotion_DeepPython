from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.orm import DeclarativeBase, declared_attr
from sqlalchemy.ext.asyncio import AsyncAttrs, async_sessionmaker, create_async_engine
from sqlalchemy import Integer, func, Table, Column
from datetime import datetime
from sqlalchemy import ForeignKey, JSON, text
from typing import Any, List
from pydantic import BaseModel
from backend.src.conf.s3_storages import media_storage
import uuid
from sqlalchemy.dialects.postgresql import UUID
from sql_decorator import FilePath
from sqlalchemy import Boolean
import enum


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


user_board_association = Table(
    "user_board",
    Base.metadata,
    Column("user_id", Integer, ForeignKey("users.id"), primary_key=True),
    Column("board_id", Integer, ForeignKey("boards.id"), primary_key=True)
)

user_image_association = Table(
    'user_image_association', Base.metadata,
    Column('user_id', UUID(as_uuid=True), ForeignKey('user.id'), primary_key=True),
    Column('image_id', UUID(as_uuid=True), ForeignKey('image.id'), primary_key=True)
)


class User(Base):
    username: Mapped[str]
    email: Mapped[str] = mapped_column(unique=True)
    password: Mapped[str]

    image_files = relationship("Image", secondary=user_image_association, back_populates="users")

    boards: Mapped[list["Board"]] = relationship(
        "Board",
        secondary=user_board_association,
        back_populates="users",
        lazy='joined'
    )
    profile_id: Mapped[int | None] = mapped_column(ForeignKey('profiles.id'))

    profile: Mapped["Profile"] = relationship(
        "Profile",
        back_populates="user",
        uselist=False,  
        lazy="joined"  
    )

class Board(Base):
    title: Mapped[str]
    content: Mapped[dict | None] = mapped_column(JSON)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'))
    users: Mapped[list["User"]] = relationship(
        "User",
        secondary=user_board_association,  
        back_populates="boards",
        lazy='joined'
    )

class Profile(Base):
    first_name: Mapped[str | None]
    last_name: Mapped[str | None]
    age: Mapped[int | None]
    avatar: Mapped[str | None] = mapped_column(nullable=True) 
    user: Mapped["User"] = relationship(
        "User",
        back_populates="profile",
        uselist=False
    )

class Image(Base):
    __tablename__ = "images"
    _file_storage = media_storage

    file: Mapped[str] = mapped_column(FilePath(_file_storage), nullable=True)
    is_main: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    users: Mapped[List["User"]] = relationship(
        "User",
        secondary=user_image_association,
        back_populates="image_files"
    )

    def __repr__(self):
        return f"<Media(id={self.id}, file={self.file}, is_main={self.is_main})>"

    @property
    def storage(self) -> "S3StorageManager":
        """Возвращает объект storage, чтобы использовать его методы напрямую."""
        return self._file_storage

class ImageCreate(BaseModel):
    file: str
    is_main: bool

class ImageUpdate(ImageCreate):
    id: uuid.UUID