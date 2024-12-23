from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.orm import DeclarativeBase, declared_attr
from sqlalchemy.ext.asyncio import AsyncAttrs, async_sessionmaker, create_async_engine
from sqlalchemy import Integer, func, Table, Column, Boolean, String
from datetime import datetime

from sqlalchemy import ForeignKey, JSON, text, DateTime

from typing import Any, List, Optional
from pydantic import BaseModel
from backend.src.conf.s3_storages import media_storage
import uuid
from sqlalchemy.dialects.postgresql import UUID as pgUUID
from sql_decorator import FilePath
from sqlalchemy import Boolean
from uuid import uuid4
import enum
from backend.src.conf.s3_client import S3StorageManager
from uuid import UUID



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


user_image_association = Table(
    "user_image_association",
    Base.metadata,
    Column("user_id", Integer, ForeignKey("users.id"), primary_key=True),
    Column("image_id", pgUUID, ForeignKey("images.id"), primary_key=True)
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

    images: Mapped[List["Image"]] = relationship(
        "Image",
        secondary=user_image_association,
        back_populates="user",
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
    
    # Пользоватеи, имеющие доступ к доске
    collaborators: Mapped[List["User"]] = relationship(
        "User",
        secondary=board_collaborators,
        back_populates="boards",
        lazy='joined'
    )

    images: Mapped[List["ImageBoard"]] = relationship(
        "ImageBoard",
        back_populates="board",
        cascade="all, delete-orphan",
        lazy="joined"
    )

class Image(Base):
    _file_storage = media_storage
    
    id: Mapped[UUID] = mapped_column(pgUUID, primary_key=True, default=uuid.uuid4)
    file: Mapped[str] = mapped_column(FilePath(_file_storage), nullable=True)

    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"))
    user: Mapped["User"] = relationship("User", secondary=user_image_association, back_populates="images", lazy="joined")
    
    @property
    def storage(self):
        return self._file_storage

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

class ImageBoard(Base):
    _file_storage = media_storage
    
    id: Mapped[UUID] = mapped_column(pgUUID, primary_key=True, default=uuid.uuid4)
    file: Mapped[str] = mapped_column(FilePath(_file_storage), nullable=True)

    board_id: Mapped[int] = mapped_column(Integer, ForeignKey("boards.id"))
    board: Mapped["Board"] = relationship("Board", back_populates="images", lazy="joined")

    @property
    def storage(self):
        return self._file_storage

    @property
    def url(self):
        from config import settings
        return f"http://{settings.MINIO_DOMAIN}/{settings.MINIO_MEDIA_BUCKET}/{self.file}"