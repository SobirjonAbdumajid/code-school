from database import Base
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import func
from datetime import datetime
from typing import Optional


class Topic(Base):
    __tablename__ = 'topics'

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(unique=True, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())