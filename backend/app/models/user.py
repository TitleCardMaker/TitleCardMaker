from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


class User(Base):
    """
    SQL Table that defines a User.
    """

    __tablename__ = 'user'

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    username: Mapped[str]
    hashed_password: Mapped[str]
