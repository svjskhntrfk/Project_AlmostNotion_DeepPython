from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.orm import DeclarativeBase, declared_attr
from sqlalchemy.ext.asyncio import AsyncAttrs, async_sessionmaker, create_async_engine
from sqlalchemy import Integer, func, Table, Column, String
from datetime import datetime
from sqlalchemy import ForeignKey, JSON, text
from typing import Any
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


class User(Base):
    username: Mapped[str]
    email: Mapped[str] = mapped_column(unique=True)
    password: Mapped[str]

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

    def __str__(self) -> str:
        return f'{self.subject}: {self.jti}'