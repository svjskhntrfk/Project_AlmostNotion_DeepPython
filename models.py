from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.orm import DeclarativeBase, declared_attr
from sqlalchemy.ext.asyncio import AsyncAttrs, async_sessionmaker, create_async_engine
from sqlalchemy import Integer, func, Table, Column, String
from datetime import datetime
from sqlalchemy import ForeignKey, JSON, text

from typing import Any, List
from pydantic import BaseModel
from backend.src.conf.s3_storages import media_storage
import uuid
from sqlalchemy.dialects.postgresql import UUID
from sql_decorator import FilePath
from sqlalchemy import Boolean
from uuid import uuid4
import enum
from backend.src.conf.s3_client import S3StorageManager



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
    Column("user_id", Integer, ForeignKey("users.id"), primary_key=True),
    Column("image_id", Integer, ForeignKey("images.id"), primary_key=True)
)


class User(Base):
    username: Mapped[str]
    email: Mapped[str] = mapped_column(unique=True)
    password: Mapped[str]

    image_files : Mapped[List["Image"]] = relationship("Image", secondary=user_image_association, back_populates="users", lazy="joined")

    boards: Mapped[list["Board"]] = relationship(
        "Board",
        secondary=user_board_association,
        back_populates="users",
        lazy='joined'
    )
    profile_id: Mapped[int | None] = mapped_column(ForeignKey('profiles.id'))

    images : Mapped[list["Image"]] = relationship("Image", secondary=user_image_association, back_populates="user", lazy="joined")

    profile: Mapped["Profile"] = relationship(
        "Profile",
        back_populates="user",
        uselist=False,  
        lazy="joined"  
    )

    tokens: Mapped[list["IssuedJWTToken"]] = relationship(
        "IssuedJWTToken",
        back_populates="subject",
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
    _file_storage = FilePath(media_storage)

    file: Mapped[str] = mapped_column(FilePath(_file_storage), nullable=True)
    is_main : Mapped[bool] = mapped_column(Boolean, default=False)

    user_id : Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    user : Mapped["User"] = relationship("User", secondary=user_image_association, back_populates="images", lazy="joined")
    
    @property
    def url(self):
        from config import settings
        return f"http://{settings.MINIO_DOMAIN}/{settings.MINIO_MEDIA_BUCKET}/{self.file}"

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

