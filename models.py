from sqlalchemy import (
    Column,
    String,
    Boolean,
    Integer,
    DateTime,
    ForeignKey,
    JSON,
    Table,
    func,
)
from sqlalchemy.orm import (
    DeclarativeBase,
    declared_attr,
    Mapped,
    mapped_column,
    relationship,
)
from sqlalchemy.ext.asyncio import AsyncAttrs, create_async_engine, async_sessionmaker
from datetime import datetime
from typing import List, Optional
from sqlalchemy.dialects.postgresql import UUID as pgUUID
from backend.src.conf.s3_storages import media_storage
import uuid
from uuid import uuid4, UUID
from sqlalchemy.dialects.postgresql import UUID as pgUUID
from sql_decorator import FilePath

class Base(AsyncAttrs, DeclarativeBase):
    __abstract__ = True
    type_annotation_map = {
        dict[str, any]: JSON
    }

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), onupdate=func.now()
    )

    @declared_attr.directive
    def __tablename__(cls) -> str:
        return cls.__name__.lower() + "s"


# =============================
#       board_collaborators
# =============================
board_collaborators = Table(
    "board_collaborators",
    Base.metadata,
    Column("user_id", Integer, ForeignKey("users.id"), primary_key=True),
    Column("board_id", Integer, ForeignKey("boards.id"), primary_key=True),
)


# =============================
#     user_notification_association 
#    (многие-ко-многим User <-> Notification)
# =============================
user_notification_association = Table(
    "user_notification_association",
    Base.metadata,
    Column("user_id", Integer, ForeignKey("users.id"), primary_key=True),
    Column("notification_id", Integer, ForeignKey("notifications.id"), primary_key=True),
)


# =============================
#     user_image_association
#    (многие-ко-многим User <-> Image)
# =============================
user_image_association = Table(
    "user_image_association",
    Base.metadata,
    Column("user_id", Integer, ForeignKey("users.id"), primary_key=True),
    Column("image_id", pgUUID, ForeignKey("images.id"), primary_key=True)
)


# =============================
#              MODELS
# =============================

class User(Base):
    username: Mapped[str] = mapped_column(String, nullable=False)
    email: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    password: Mapped[str] = mapped_column(String, nullable=False)

    # Доски, которыми владеет
    owned_boards: Mapped[List["Board"]] = relationship(
        "Board",
        back_populates="owner",
        lazy="joined"
    )

    # Доски, к которым есть доступ
    boards: Mapped[List["Board"]] = relationship(
        "Board",
        secondary=board_collaborators,
        back_populates="collaborators",
        lazy="joined"
    )

    # Токены (один-ко-многим)
    tokens: Mapped[List["IssuedJWTToken"]] = relationship(
        "IssuedJWTToken",
        back_populates="subject",
        lazy="joined"
    )

    # Уведомления (многие-ко-многим)
    notifications: Mapped[List["Notification"]] = relationship(
        "Notification",
        secondary=user_notification_association,
        back_populates="users",
        lazy="joined"
    )

    # Фотографии (многие-ко-многим)
    images: Mapped[List["Image"]] = relationship(
        "Image",
        secondary=user_image_association,
        back_populates="user",
        lazy="joined"
    )


class Board(Base):
    title: Mapped[str] = mapped_column(String, nullable=False)
    content: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)

    owner: Mapped["User"] = relationship(
        "User",
        back_populates="owned_boards",
        lazy="joined"
    )

    collaborators: Mapped[List["User"]] = relationship(
        "User",
        secondary=board_collaborators,
        back_populates="boards",
        lazy="joined"
    )


    images: Mapped[List["ImageBoard"]] = relationship(
        "ImageBoard",
        back_populates="board",
        cascade="all, delete-orphan",
        lazy="joined"
    )

    todo_lists: Mapped[List["ToDoList"]] = relationship(
        "ToDoList",
        back_populates="board",
        cascade="all, delete-orphan",
        lazy="joined"
    )


class Image(Base):
    _file_storage = media_storage
    
    id: Mapped[UUID] = mapped_column(pgUUID(as_uuid=True), primary_key=True, default=uuid4)

    file: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"))
    user: Mapped["User"] = relationship("User", secondary=user_image_association, back_populates="images", lazy="joined")
    
    @property
    def storage(self):
        return self._file_storage

    @property
    def url(self):
        from config import settings
        return f"{settings.S3_ENDPOINT}/{settings.S3_BUCKET}/{self.file}"


    


class IssuedJWTToken(Base):
    jti: Mapped[str] = mapped_column(String(36), primary_key=True)
    subject_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    subject: Mapped["User"] = relationship("User", back_populates="tokens", lazy="joined")

    device_id: Mapped[str] = mapped_column(String(36))
    revoked: Mapped[bool] = mapped_column(Boolean, default=False)
    expired_time: Mapped[int] = mapped_column(Integer, nullable=False)



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

class Task(Base):
    title: Mapped[str] = mapped_column(String, nullable=False)
    completed: Mapped[bool] = mapped_column(Boolean, default=False)
    deadline: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    todo_list_id: Mapped[int] = mapped_column(ForeignKey("todolists.id"), nullable=False)
    todo_list: Mapped["ToDoList"] = relationship("ToDoList", back_populates="tasks", lazy="joined")

    # Связь "один-ко-одному" с Notification
    notification: Mapped["Notification"] = relationship(
        "Notification",
        back_populates="task",
        uselist=False,
        lazy="joined"
    )


class Notification(Base):
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Связь "один-ко-одному" с Task
    task_id: Mapped[int] = mapped_column(ForeignKey("tasks.id"), unique=True, nullable=False)
    task: Mapped["Task"] = relationship("Task", back_populates="notification", lazy="joined")

    message: Mapped[str] = mapped_column(String, nullable=False)
    send_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    sent: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Уведомления связаны многими-ко-многим с пользователями через user_notification_association
    users: Mapped[List["User"]] = relationship(
        "User",
        secondary=user_notification_association,
        back_populates="notifications",
        lazy="joined"
    )

