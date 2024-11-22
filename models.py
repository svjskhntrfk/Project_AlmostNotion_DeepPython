from sqlalchemy import ForeignKey, JSON, text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from database1 import Base
import enum

class User(Base):
    username: Mapped[str] = mapped_column(unique=True)
    email: Mapped[str] = mapped_column(unique=True)
    password: Mapped[str]
    profile_id: Mapped[int | None] = mapped_column(ForeignKey('profiles.id'))

    profile: Mapped["Profile"] = relationship(
    "Profile",
    back_populates="user",
    uselist=False,  # Ключевой параметр для связи один-к-одному
    lazy="joined"  # Автоматически подгружает profile при запросе user
    )

class GenderEnum(str, enum.Enum):
    MALE = "мужчина"
    FEMALE = "женщина"

class Profile(Base):
    first_name: Mapped[str]
    last_name: Mapped[str | None]
    age: Mapped[int | None]
    gender: Mapped[GenderEnum]

    user: Mapped["User"] = relationship(
        "User",
        back_populates="profile",
        uselist=False
    )

