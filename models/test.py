from database import Base
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import func, Float, ForeignKey
from datetime import datetime
from typing import Optional


class Test(Base):
    __tablename__ = 'tests'

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'), nullable=False)
    topic_id: Mapped[int] = mapped_column(ForeignKey('topics.id'), nullable=False)
    started_at: Mapped[datetime] = mapped_column(server_default=func.now())
    completed_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    score: Mapped[Optional[float]] = mapped_column(Float(precision=5), nullable=True)  # 0-100
